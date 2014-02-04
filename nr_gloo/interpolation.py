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

from gloo import Program

vertex = """
    attribute vec2 a_texcoord;
    attribute vec2 a_position;
    varying vec2 v_texcoord;
    void main()
    {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_texcoord = a_texcoord;
    } """

fragment = """
    uniform sampler2D u_data;
    uniform vec2 u_shape;
    varying vec2 v_texcoord;
    void main()
    {
        // gl_FragColor = Nearest(u_data, u_shape, v_texcoord);
        // gl_FragColor = Bilinear(u_data, u_shape, v_texcoord);
        // gl_FragColor = Hanning(u_data, u_shape, v_texcoord);
        // gl_FragColor = Hamming(u_data, u_shape, v_texcoord);
        // gl_FragColor = Hermite(u_data, u_shape, v_texcoord);
        // gl_FragColor = Kaiser(u_data, u_shape, v_texcoord);
        // gl_FragColor = Quadric(u_data, u_shape, v_texcoord);
        gl_FragColor = Bicubic(u_data, u_shape, v_texcoord);
        // gl_FragColor = CatRom(u_data, u_shape, v_texcoord);
        // gl_FragColor = Mitchell(u_data, u_shape, v_texcoord);
        // gl_FragColor = Spline16(u_data, u_shape, v_texcoord);
        // gl_FragColor = Spline36(u_data, u_shape, v_texcoord);
        // gl_FragColor = Gaussian(u_data, u_shape, v_texcoord);
        // gl_FragColor = Bessel(u_data, u_shape, v_texcoord);
        // gl_FragColor = Sinc(u_data, u_shape, v_texcoord);
        // gl_FragColor = Lanczos(u_data, u_shape, v_texcoord);
        // gl_FragColor = Blackman(u_data, u_shape, v_texcoord);
    } """
fragment = open('spatial-filters.frag').read() + fragment

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    program['u_data'] = data
    program.draw(gl.GL_TRIANGLE_STRIP)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)

def keyboard( key, x, y ):
    if key == '\033': sys.exit( )

def on_idle():
    global t, t0, frames
    t = glut.glutGet( glut.GLUT_ELAPSED_TIME )
    frames = frames + 1
    if t-t0 > 2500:
        print( "FPS : %.2f (%d frames in %.2f second)"
               % (frames*1000.0/(t-t0), frames, (t-t0)/1000.0))
        t0, frames = t,0
    glut.glutPostRedisplay()

# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)
glut.glutCreateWindow('Spatial interpolation filters')
glut.glutReshapeWindow(512,512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard)
glut.glutDisplayFunc(display)
# glut.glutIdleFunc(on_idle)
t0, frames, t = glut.glutGet(glut.GLUT_ELAPSED_TIME),0,0

# Build program & data
# --------------------------------------
program = Program(vertex, fragment, 4)
program['a_position'] = (-1,-1), (-1,+1), (+1,-1), (+1,+1)
program['a_texcoord'] = ( 0, 0), ( 0,+1), (+1, 0), (+1,+1)
data = np.random.uniform(0,1,(32,32,1))
program['u_data'] = data
program['u_shape'] = data.shape[1], data.shape[0]
program['u_kernel'] = np.load("spatial-filters.npy")

# Start
# --------------------------------------
glut.glutMainLoop()
