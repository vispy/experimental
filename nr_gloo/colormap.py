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
    uniform sampler1D u_colormap;
    uniform sampler2D u_data;
    varying vec2 v_texcoord;
    void main()
    {
        // Extract data value
        float value = texture2D(u_data, v_texcoord).r;

        // Map value to rgb color
        vec3 color = texture1D(u_colormap, value).rgb;

        // Trace contour
        float thickness = 1.0;
        vec3  v  = vec3(1.0, 1.0, value) * 16.0;
        vec3  f  = abs(fract(v)-0.5);
        vec3  df = fwidth(v);
        vec3  g  = smoothstep(-thickness * df, thickness * df, f);
        float c  = (1.0 - g.x * g.y * g.z);
        color = (1.0-c)*color + c*vec3(0,0,0);

        gl_FragColor = vec4(color,1.0);
    } """

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    # program['u_lut'].update()
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
glut.glutCreateWindow('Colormap interpolation + contours')
glut.glutReshapeWindow(512,512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)

# Build program
# --------------------------------------
program = Program(vertex, fragment, 4)
program['a_position'] = (-1,-1), (-1,+1), (+1,-1), (+1,+1)
program['a_texcoord'] = ( 0, 0), ( 0,+1), (+1, 0), (+1,+1)

# Build data
# --------------------------------------
def func3(x,y): return (1-x/2+x**5+y**3)*np.exp(-x**2-y**2)
x = np.linspace(-3.0, 3.0, 128).astype(np.float32)
y = np.linspace(-3.0, 3.0, 128).astype(np.float32)
X,Y = np.meshgrid(x, y)
Z = func3(X,Y)
program['u_data'] = (Z-Z.min())/(Z.max() - Z.min())
program['u_data'].interpolation = gl.GL_LINEAR

# Build colormap (hot colormap)
# --------------------------------------
colormap = np.zeros((512,3), np.float32)
colormap[:,0] = np.interp(np.arange(512), [0, 171, 342, 512], [0,1,1,1])
colormap[:,1] = np.interp(np.arange(512), [0, 171, 342, 512], [0,0,1,1])
colormap[:,2] = np.interp(np.arange(512), [0, 171, 342, 512], [0,0,0,1])
program['u_colormap'] = colormap

# Start
# --------------------------------------
glut.glutMainLoop()
