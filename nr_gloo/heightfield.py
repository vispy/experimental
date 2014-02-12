#! /usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All rights reserved.
# Distributed under the terms of the new BSD License.
# -----------------------------------------------------------------------------
import sys
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut

from gloo import Program, VertexBuffer, IndexBuffer
from transforms import perspective, translate, rotate

vertex = """
    uniform mat4 u_model;
    uniform mat4 u_view;
    uniform mat4 u_projection;
    uniform mat4 u_normal;
    uniform float u_clock;

    uniform sampler2D u_data;
    uniform vec2 u_data_shape;
    uniform vec4 u_color;

    attribute vec2 a_texcoord;
    attribute vec2 a_position;

    varying vec3 v_position;
    varying vec2 v_texcoord;
    void main()
    {
        float c = 0.5+(1.0+cos(u_clock))/4.0;

        float z = c*Bicubic(u_data, u_data_shape, a_texcoord).r;
        gl_Position = u_projection * u_view * u_model * vec4(a_position,z,1.0);

        v_texcoord = a_texcoord;
        v_position = vec3(a_position,z);
    }
"""
vertex = open('spatial-filters.frag').read() + vertex

fragment = """
    uniform mat4 u_model;
    uniform mat4 u_view;
    uniform mat4 u_projection;
    uniform mat4 u_normal;
    uniform float u_clock;

    uniform sampler1D u_colormap;
    uniform sampler2D u_data;
    uniform vec2 u_data_shape;
    uniform vec4 u_color;

    uniform vec3 u_light_intensity[2];
    uniform vec3 u_light_position[2];

    varying vec3 v_position;
    varying vec2 v_texcoord;
    void main()
    {
        float c = 0.5+(1.0+cos(u_clock))/4.0;

        // Extract data value
        float value = c*Bicubic(u_data, u_data_shape, v_texcoord).r;

        // Compute surface normal using neighbour values
        float hx0 = c*Bicubic(u_data, u_data_shape, v_texcoord+vec2(+1,0)/u_data_shape).r;
        float hx1 = c*Bicubic(u_data, u_data_shape, v_texcoord+vec2(-1,0)/u_data_shape).r;
        float hy0 = c*Bicubic(u_data, u_data_shape, v_texcoord+vec2(0,+1)/u_data_shape).r;
        float hy1 = c*Bicubic(u_data, u_data_shape, v_texcoord+vec2(0,-1)/u_data_shape).r;
        vec3 dx = vec3(2.0/u_data_shape.x,0.0,hx0-hx1);
        vec3 dy = vec3(0.0,2.0/u_data_shape.y,hy0-hy1);
        vec3 v_normal = normalize(cross(dx,dy));

        // Map value to rgb color
        vec4 color = vec4(texture1D(u_colormap, value).rgb,1);
        //color = vec4(1,1,1,1);

        // Calculate normal in world coordinates
        vec3 normal = normalize(u_normal * vec4(v_normal,1.0)).xyz;

        // Calculate the location of this fragment (pixel) in world coordinates
        vec3 position = vec3(u_view*u_model * vec4(v_position, 1));

        // Calculate the vector from this pixels surface to the light source
        vec3 surface_to_light = u_light_position[0] - position;

        // Calculate the cosine of the angle of incidence (brightness)
        float brightness = dot(normal, surface_to_light) /
                          (length(surface_to_light) * length(normal));
        brightness = clamp(brightness,0.0,1.0);

        // Calculate final color of the pixel, based on:
        // 1. The angle of incidence: brightness
        // 2. The color/intensities of the light: light.intensities
        // 3. The texture and texture coord: texture(tex, fragTexCoord)

        gl_FragColor = 0.75*color + 0.25 * brightness * vec4(u_light_intensity[0], 1);

        // Trace contour
       float antialias = 1.5;
       float linewidth = 1. + antialias;

/*
       vec3 v  = vec3(v_position.yx, value) * vec3(24.0,24.0,24.0) + vec3(.5,.5,.5);
       vec3 dv = linewidth/2.0 * fwidth(v);
       vec3 f = abs(fract(v)-0.5);
       vec3 g = smoothstep(-dv, +dv, f);
       float d = g.x*g.y*g.z;
*/
       float v  = value * 24.0;
       float dv = linewidth/2.0 * fwidth(v);
       float f = abs(fract(v)-0.5);
       float d = smoothstep(-dv, +dv, f);


       float t = linewidth/2.0 - antialias;
       d = abs(d)*linewidth/2.0 - t;
       if( d < 0.0 )
       {
            gl_FragColor = vec4(0,0,0,1);
       }
       else
       {
           d /= antialias;
           gl_FragColor = d*gl_FragColor + (1.0-d)*vec4(0,0,0,1);
       }

       gl_FragColor *= u_color;

    } """
fragment = open('spatial-filters.frag').read() + fragment


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # Filled cube
    gl.glDisable(gl.GL_BLEND)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
    program['u_color'] = 1,1,1,1
    program.draw(gl.GL_TRIANGLES, indices)

    # Outlined cube
    gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
    gl.glEnable(gl.GL_BLEND)
    gl.glDepthMask(gl.GL_FALSE)
    program['u_color'] = 0,0,0,1
    program.draw(gl.GL_LINE_LOOP, outline)
    gl.glDepthMask(gl.GL_TRUE)


    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)
    projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
    program['u_projection'] = projection

def keyboard( key, x, y ):
    if key == '\033': sys.exit( )

def timer(fps):
    global theta,clock
    theta += .5

    clock += 0.01
    program["u_clock"] = clock

    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0,0,1)
    rotate(model, -45, 1,0,0)
    normal = np.array(np.matrix(np.dot(view,model)).I.T)
    program['u_model'] = model
    program['u_normal'] = normal

    glut.glutTimerFunc(1000/fps, timer, fps)
    glut.glutPostRedisplay()


# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow("Heightfield")
glut.glutReshapeWindow(800,800)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)
glut.glutTimerFunc(1000/60, timer, 60)


# Build program
# --------------------------------------
n = 64
program = Program(vertex, fragment, n*n)
V = np.zeros((n,n,2), dtype= np.float32)

T = np.linspace(-1, 1, n)
V[...,0], V[...,1] = np.meshgrid(T,T)
program['a_position'] = V.reshape(n*n,2)

T = np.linspace(0, 1, n)
V[...,0], V[...,1] = np.meshgrid(T,T)
program['a_texcoord'] = V.reshape(n*n,2)

I = (np.arange((n-1)*(n),dtype=np.uint32).reshape(n-1,n))[:,:-1].T
I = np.repeat(I.ravel(),6).reshape(n-1,n-1,6)
I[:,:] += 0,1,n+1, 0,n+1,n
indices = IndexBuffer(I.ravel())

I=[]
for i in xrange(n): I.append(i)
for i in xrange(1,n): I.append(n-1+i*n)
for i in xrange(n-1): I.append(n*n-1-i)
for i in xrange(n-1): I.append(n*(n-1) - i*n)
outline = IndexBuffer(I)



# program['a_position'] = (-1,-1), (-1,+1), (+1,-1), (+1,+1)
# program['a_texcoord'] = ( 0, 0), ( 0,+1), (+1, 0), (+1,+1)

# Build data
# --------------------------------------
def func3(x,y): return (1-x/2+x**5+y**3)*np.exp(-x**2-y**2)
x = np.linspace(-2.0, 2.0, 32).astype(np.float32)
y = np.linspace(-2.0, 2.0, 32).astype(np.float32)
X,Y = np.meshgrid(x, y)
Z = func3(X,Y)
program['u_data'] = (Z-Z.min())/(Z.max() - Z.min())
program['u_data'].interpolation = gl.GL_NEAREST
program['u_data_shape'] = Z.shape[1], Z.shape[0]
program['u_kernel'] = np.load("spatial-filters.npy")

# Build colormap (hot colormap)
# --------------------------------------
colormap = np.zeros((512,3), np.float32)
colormap[:,0] = np.interp(np.arange(512), [0, 171, 342, 512], [0,1,1,1])
colormap[:,1] = np.interp(np.arange(512), [0, 171, 342, 512], [0,0,1,1])
colormap[:,2] = np.interp(np.arange(512), [0, 171, 342, 512], [0,0,0,1])
program['u_colormap'] = colormap

# Build view, model, projection & normal
# --------------------------------------
view = np.eye(4,dtype=np.float32)
model = np.eye(4,dtype=np.float32)
projection = np.eye(4,dtype=np.float32)
translate(view, 0,0,-4)
normal = np.array(np.matrix(np.dot(view,model)).I.T)
program['u_model'] = model
program['u_view'] = view
program['u_normal'] = normal
program["u_light_position[0]"] = 2,2,2
program["u_light_intensity[0]"] = 1,1,1
program['u_clock'] = 0
clock,theta = 0,0

# OpenGL initalization
# --------------------------------------
gl.glClearColor( 1, 1, 1, 1 )
gl.glEnable(gl.GL_DEPTH_TEST)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glPolygonOffset(1, 1)
gl.glEnable(gl.GL_LINE_SMOOTH)
gl.glLineWidth(1.5)

# Start
# --------------------------------------
glut.glutMainLoop()
