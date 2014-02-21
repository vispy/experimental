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
#version 120

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec3 u_light_position;

attribute vec3  a_position;
attribute vec3  a_color;
attribute float a_radius;

varying vec3  v_color;
varying vec4  v_eye_position;
varying float v_radius;
varying vec3  v_light_direction;

void main (void) {
    v_radius = a_radius;
    v_color = a_color;

    v_eye_position = u_view * u_model * vec4(a_position,1.0);
    v_light_direction = normalize(u_light_position);
    float dist = length(v_eye_position.xyz);

    gl_Position = u_projection * v_eye_position;

    // stackoverflow.com/questions/8608844/...
    //  ... resizing-point-sprites-based-on-distance-from-the-camera
    vec4  proj_corner = u_projection * vec4(a_radius, a_radius, v_eye_position.z, v_eye_position.w);
    gl_PointSize = 512.0 * proj_corner.x / proj_corner.w;
}
"""

fragment = """
#version 120

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec3 u_light_position;

varying vec3  v_color;
varying vec4  v_eye_position;
varying float v_radius;
varying vec3  v_light_direction;
void main()
{
    // r^2 = (x - x0)^2 + (y - y0)^2 + (z - z0)^2
    vec2 texcoord = gl_PointCoord* 2.0 - vec2(1.0);
    float x = texcoord.x;
    float y = texcoord.y;
    float d = 1.0 - x*x - y*y;
    if (d <= 0.0)
        discard;

    float z = sqrt(d);
    vec4 pos = v_eye_position;
    pos.z += v_radius*z;
    pos = u_projection * pos;
    gl_FragDepth = 0.5*(pos.z / pos.w)+0.5;
    vec3 normal = vec3(x,y,z);
    float diffuse = clamp(dot(normal, v_light_direction), 0.0, 1.0);
    gl_FragColor = vec4(vec3(0.15,0.15,0.15) +  diffuse * v_color, 1.0);
}
"""


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_POINTS)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)
    projection = perspective( 25.0, width/float(height), 2.0, 100.0 )
    program['u_projection'] = projection

def keyboard(key, x, y):
    if key == '\033': sys.exit( )

def timer(fps):
    global theta, phi
    theta += .5
    phi += .5
    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0,0,1)
    rotate(model, phi, 0,1,0)
    program['u_model'] = model
    glut.glutTimerFunc(1000/fps, timer, fps)
    glut.glutPostRedisplay()


# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow('Cloud')
glut.glutReshapeWindow(800, 800)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)
glut.glutTimerFunc(1000/60, timer, 60)

# Build cloud data
# --------------------------------------
n = 100000
data = np.zeros(n, [ ('a_position', np.float32, 3),
                     ('a_color',    np.float32, 3),
                     ('a_radius',   np.float32, 1)])
data['a_position'] = np.random.randn(n,3) + (0,0,0)
data['a_color'] = np.random.uniform(0.75,1.00,(n,3))
data['a_radius'] = np.random.uniform(5,10,n)/100.

# Build program
# --------------------------------------
program = Program(vertex, fragment)
program.bind(VertexBuffer(data))
program['u_light_position'] = 2,2,2


# Build view, model, projection
# --------------------------------------
view = np.eye(4,dtype=np.float32)
model = np.eye(4,dtype=np.float32)
projection = np.eye(4,dtype=np.float32)
translate(view, 0, 0,-10)
#view = look_at((4.0,3.0,1.0), (0.0,0.0,0.0), (0.0,0.0,1.0))
program['u_model'] = model
program['u_view'] = view
phi, theta = 0,0

# OpenGL initalization
# --------------------------------------
gl.glClearColor(1,1,1,1)
gl.glEnable(gl.GL_DEPTH_TEST)
#gl.glEnable(gl.GL_BLEND)
#gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_VERTEX_PROGRAM_POINT_SIZE)
gl.glEnable(gl.GL_POINT_SPRITE)

# Start
# --------------------------------------
glut.glutMainLoop()
