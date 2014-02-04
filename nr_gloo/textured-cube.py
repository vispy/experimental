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

from cube import cube
from gloo import Program, VertexBuffer, IndexBuffer
from transforms import perspective, translate, rotate

vertex = """
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform mat4 u_normal;

attribute vec3 a_position;
attribute vec2 a_texcoord;
varying vec2 v_texcoord;
void main()
{
    gl_Position = u_projection * u_view * u_model * vec4(a_position,1.0);
    v_texcoord = a_texcoord;
}
"""

fragment = """
uniform sampler2D u_texture;
varying vec2 v_texcoord;
void main()
{
    gl_FragColor = texture2D(u_texture, v_texcoord);
}
"""


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLES, indices)
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
    normal = np.array(np.matrix(np.dot(view,model)).I.T)
    program['u_normal'] = normal
    glut.glutTimerFunc(1000/fps, timer, fps)
    glut.glutPostRedisplay()


# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow('Textured Cube')
glut.glutReshapeWindow(512,512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)
glut.glutTimerFunc(1000/60, timer, 60)

# Build cube data
# --------------------------------------
vertices, indices, _ = cube()
vertices = VertexBuffer(vertices)
indices = IndexBuffer(indices)

# Build program
# --------------------------------------
program = Program(vertex, fragment)
program.bind(vertices)
program["u_texture"] = np.load("crate.npy")
program["u_texture"].interpolation = gl.GL_LINEAR

# Build view, model, projection & normal
# --------------------------------------
view = np.eye(4,dtype=np.float32)
model = np.eye(4,dtype=np.float32)
projection = np.eye(4,dtype=np.float32)
translate(view, 0,0,-5)
normal = np.array(np.matrix(np.dot(view,model)).I.T)
program['u_normal'] = normal
program['u_model'] = model
program['u_view'] = view
phi, theta = 0,0

# OpenGL initalization
# --------------------------------------
gl.glClearColor( .3, .3, .35, 1 )
gl.glEnable(gl.GL_DEPTH_TEST)

# Start
# --------------------------------------
glut.glutMainLoop()
