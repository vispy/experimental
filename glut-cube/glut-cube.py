#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2013 Nicolas P. Rougier. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY NICOLAS P. ROUGIER ''AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL NICOLAS P. ROUGIER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Nicolas P. Rougier.
# -----------------------------------------------------------------------------
import sys
import math
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut

from shader import Shader
from vertex_buffer import VertexBuffer
from transforms import perspective, translate, rotate, scale



def display():
    global projection, view
    global theta, phi

    theta += .5
    phi += .5


    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0,0,1)
    rotate(model, phi, 0,1,0)

    shader.bind()
    shader.uniform_matrixf('u_view', view)
    shader.uniform_matrixf('u_projection', projection)
    shader.uniform_matrixf('u_model', model)

    gl.glDisable( gl.GL_BLEND )
    gl.glEnable( gl.GL_DEPTH_TEST )
    gl.glEnable( gl.GL_POLYGON_OFFSET_FILL )

    shader.uniformf('u_color', 1.0, 1.0, 1.0, 1.0 )
    cube.draw( gl.GL_TRIANGLES )

    gl.glDisable( gl.GL_POLYGON_OFFSET_FILL )
    gl.glEnable( gl.GL_BLEND );
    gl.glDepthMask( gl.GL_FALSE );

    shader.uniformf('u_color', 0.0, 0.0, 0.0, 0.5 )
    outline.draw( gl.GL_LINES )

    gl.glDepthMask( gl.GL_TRUE )
    gl.glUseProgram( 0 )

    glut.glutSwapBuffers()


def reshape(width,height):
    global projection, view
    gl.glViewport(0, 0, width, height)
    projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
    view = np.identity(4,dtype=np.float32)
    translate(view, 0,0,-5)

def keyboard( key, x, y ):
    if key == '\033':
        sys.exit( )

def on_timer(fps):
    glut.glutTimerFunc(1000/fps, on_timer, fps)
    glut.glutPostRedisplay()


if __name__ == '__main__':
    fps = 60

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    glut.glutCreateWindow('glut-cube')
    glut.glutReshapeWindow(512,512)
    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(reshape)
    glut.glutKeyboardFunc(keyboard )
    glut.glutTimerFunc(1000/fps, on_timer, fps)

    gl.glPolygonOffset( 1, 1 )
    gl.glClearColor( .3, .3, .35, 1 )
    gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
    gl.glEnable( gl.GL_LINE_SMOOTH )

    projection = np.eye(4,dtype=np.float32)
    view       = np.eye(4,dtype=np.float32)
    
    theta, phi = 0,0

    vtype = [('position', np.float32, 3),
             ('normal'  , np.float32, 3),
             ('color',    np.float32, 4)] 

    # vertices
    v = [ [ 1, 1, 1],  [-1, 1, 1],  [-1,-1, 1], [ 1,-1, 1],
          [ 1,-1,-1],  [ 1, 1,-1],  [-1, 1,-1], [-1,-1,-1] ]
    # normals
    n = [ [ 0, 0, 1],  [ 1, 0, 0],  [ 0, 1, 0] ,
          [-1, 0, 1],  [ 0,-1, 0],  [ 0, 0,-1] ]
    # colors
    c = [ [0, 1, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1], [0, 1, 0, 1],
          [1, 1, 0, 1], [1, 1, 1, 1], [1, 0, 1, 1], [1, 0, 0, 1] ];
    V =  np.array([(v[0],n[0],c[0]), (v[1],n[0],c[1]), (v[2],n[0],c[2]), (v[3],n[0],c[3]),
                   (v[0],n[1],c[0]), (v[3],n[1],c[3]), (v[4],n[1],c[4]), (v[5],n[1],c[5]),
                   (v[0],n[2],c[0]), (v[5],n[2],c[5]), (v[6],n[2],c[6]), (v[1],n[2],c[1]),
                   (v[1],n[3],c[1]), (v[6],n[3],c[6]), (v[7],n[3],c[7]), (v[2],n[3],c[2]),
                   (v[7],n[4],c[7]), (v[4],n[4],c[4]), (v[3],n[4],c[3]), (v[2],n[4],c[2]),
                   (v[4],n[5],c[4]), (v[7],n[5],c[7]), (v[6],n[5],c[6]), (v[5],n[5],c[5]) ],
                  dtype = vtype)
    I = np.resize( np.array([0,1,2,0,2,3], dtype=np.uint32), 6*(2*3))
    I += np.repeat( 4*np.arange(2*3), 6)

    cube = VertexBuffer(vtype)
    cube.append(V,I)

    I = np.resize( np.array([0,1,1,2,2,3,3,0], dtype=np.uint32), 6*(2*4))
    I += np.repeat( 4*np.arange(6), 8)
    outline = VertexBuffer(vtype)
    outline.append(V,I)

    shader = Shader(open("./cube.vert").read(),
                    open("./cube.frag").read())
    glut.glutMainLoop()
