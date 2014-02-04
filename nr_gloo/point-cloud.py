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
uniform float u_linewidth;
uniform float u_antialias;

attribute vec3  a_position;
attribute vec4  a_fg_color;
attribute vec4  a_bg_color;
attribute float a_size;
varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_size;
varying float v_linewidth;
varying float v_antialias;
void main (void) {
    v_size = a_size;
    v_linewidth = u_linewidth;
    v_antialias = u_antialias;
    v_fg_color = a_fg_color;
    v_bg_color = a_bg_color;
    gl_Position = u_projection * u_view * u_model * vec4(a_position,1.0);
    gl_PointSize = v_size + 2.0*(v_linewidth + 1.5*v_antialias);
}
"""

fragment = """
#version 120

varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_size;
varying float v_linewidth;
varying float v_antialias;
float disc(vec2 P, float size)
{
    float r = length((P.xy - vec2(0.5,0.5))*size);
    r -= v_size/2.0;
    return r;
}
void main()
{
    float size = v_size +2.0*(v_linewidth + 1.5*v_antialias);
    float t = v_linewidth/2.0-v_antialias;
    float r = disc(gl_PointCoord, size);
    float d = abs(r) - t;
    if( r > (v_linewidth/2.0+v_antialias))
        discard;
    else if( d < 0.0 )
       gl_FragColor = v_fg_color;
    else
    {
        float alpha = d/v_antialias;
        alpha = exp(-alpha*alpha);
        if (r > 0)
            gl_FragColor = vec4(v_fg_color.rgb, alpha*v_fg_color.a);
        else
            gl_FragColor = mix(v_bg_color, v_fg_color, alpha);
    }
}
"""


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_POINTS)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)
    projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
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
                     ('a_bg_color', np.float32, 4),
                     ('a_fg_color', np.float32, 4),
                     ('a_size',     np.float32, 1)])
data['a_position'] = 0.45 * np.random.randn(n,3)
data['a_bg_color'] = np.random.uniform(0.75,1.00,(n,4))
data['a_fg_color'] = 0,0,0,.5
data['a_size'] = np.random.uniform(5,10,n)

# Build program
# --------------------------------------
program = Program(vertex, fragment)
program.bind(VertexBuffer(data))
program['u_linewidth'] = 0.75
program['u_antialias'] = 1.00

# Build view, model, projection
# --------------------------------------
view = np.eye(4,dtype=np.float32)
model = np.eye(4,dtype=np.float32)
projection = np.eye(4,dtype=np.float32)
translate(view, 0, 0, -5)
program['u_model'] = model
program['u_view'] = view
phi, theta = 0,0

# OpenGL initalization
# --------------------------------------
gl.glClearColor(1,1,1,1)
gl.glEnable(gl.GL_DEPTH_TEST)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_VERTEX_PROGRAM_POINT_SIZE)
gl.glEnable(gl.GL_POINT_SPRITE)

# Start
# --------------------------------------
glut.glutMainLoop()
