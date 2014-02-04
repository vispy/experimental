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

vertex = """
    attribute vec4 a_color;
    attribute vec2 a_position;
    varying vec4 v_color;
    void main()
    {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_color = a_color;
    } """

fragment = """
    varying vec4 v_color;
    void main()
    {
        gl_FragColor = v_color;
    } """

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLE_STRIP)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)

def keyboard( key, x, y ):
    if key == '\033': sys.exit( )

# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)
glut.glutCreateWindow('Hello world!')
glut.glutReshapeWindow(512,512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)

# ----------------------------------------
# First version (implicit buffer)
# ----------------------------------------
program = Program(vertex, fragment, 4)
program['a_color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]

# ----------------------------------------
# Second version (direct upload)
# ----------------------------------------
# program = Program(vertex, fragment) # ,direct=True)
# program['a_color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
# program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]

# ----------------------------------------
# Third version (explicit grouped binding)
# ----------------------------------------
# program = Program(vertex, fragment)
# vertices = np.zeros(4, [('a_position', np.float32, 2),
#                         ('a_color',    np.float32, 4)])
# program.bind(VertexBuffer(vertices)
# program['a_color'] = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
# program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]

# ----------------------------------------
# Fourth version (explicit binding)
# ----------------------------------------
# program = Program(vertex, fragment)
# position = VertexBuffer(np.zeros((4,2), np.float32))
# position[:] = [((-1,-1),), ((-1,+1),), ((+1,-1),), ((+1,+1),)]
# program['a_position'] = position
# color = VertexBuffer(np.zeros((4,4), np.float32))
# color[:] = [((1,0,0,1),), ((0,1,0,1),), ((0,0,1,1),), ((1,1,0,1),)]
# program['a_color'] = color

# Start
# --------------------------------------
glut.glutMainLoop()
