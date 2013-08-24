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
import numpy as np
import OpenGL.GL as gl

def bake(vertices, closed=False):
    """
    Bake a list of 2D vertices for rendering them as thick line. Each line
    segment must have its own vertices because of antialias (this means no
    vertex sharing between two adjacent line segments even). Furthermore, for
    miter control, each vertex need to access previous and next vertices, but
    also the previous of previous and next of next vertices.

    This is a small price to pay since the vertex and fragment shader are made
    simpler (and this faster).
    """
    n = len(vertices)
    dtype = np.dtype(
        [('prev2', 'f4', 2),
         ('prev',  'f4', 2),
         ('curr',  'f4', 2),
         ('next',  'f4', 2),
         ('next2', 'f4', 2),
         ('vid',   'f4', 1) ] )
    # if closed, make sure first vertex != last vertex
    # (because we'll take care of that)
    vs, ve = np.array([vertices[0], vertices[-1]])
    if closed and ((ve-vs)**2).sum() == 0:
        vertices = vertices[:-1]
        n -= 1
    V = np.zeros(n, dtype=dtype)
    V['curr'][ :  ] = vertices
    V['next'][ :-1] = vertices[+1:]
    V['next2'][ :-2] = vertices[+2:]
    V['prev'][ +1:] = vertices[:-1]
    V['prev2'][ +2:] = vertices[:-2]
    if closed:
        V['next'][ -1] = vertices[ 0]
        V['next2'][-1] = vertices[ 1]
        V['next2'][-2] = vertices[ 0]
        V['prev'][  0] = vertices[-1]
        V['prev2'][ 0] = vertices[-2]
        V['prev2'][ 1] = vertices[-1]
    else:
        V['next'][ -1] = vertices[-1]
        V['next2'][-1] = vertices[-1]
        V['next2'][-2] = vertices[-1]
        V['prev'][  0] = vertices[ 0]
        V['prev2'][ 0] = vertices[ 0]
        V['prev2'][ 1] = vertices[ 0]
    V = np.repeat(V,2)
    V['vid'][0::2] = 2
    V = np.repeat(V,2)
    V['vid'][1::2] += 1
    if not closed:
        I = np.repeat([[0,1,2,0,2,3]],n-1,axis=0)
        I += 4*np.arange(n-1).reshape(n-1,1)
        return V[2:-2], I.ravel()
    else:
        I = np.repeat([[0,1,2,0,2,3]],n,axis=0)
        I += 4*np.arange(n).reshape(n,1)
        return np.roll(V,-2), I.ravel()

def on_display():
    gl.glClearColor(1,1,1,1);
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_BLEND)

    shader.bind()
    _,_,width,height = gl.glGetIntegerv( gl.GL_VIEWPORT )
    P = orthographic( 0, width, 0, height, -1, +1 )
    V = np.eye(4).astype( np.float32 )
    M = np.eye(4).astype( np.float32 )
    shader.uniform_matrixf( 'M', M )
    shader.uniform_matrixf( 'V', V )
    shader.uniform_matrixf( 'P', P )
    shader.uniformf( 'width', 1.0 )
    shader.uniformf( 'blur',  1.0 )
    shader.uniformf( 'color',  0.0, 0.0, 0.0, 1.0)
    shader.uniformf( 'miter_limit',  4.0 )
    line.draw( )
    shader.unbind()
    glut.glutSwapBuffers()
    
def on_reshape(width, height):
    gl.glViewport(0, 0, width, height)

def on_keyboard(key, x, y):
    if key == '\033': sys.exit()

def star( r1=100, r2=200, n=5):
    points = []
    n *= 2
    for i in np.arange(n):
        if i%2: r = r1
        else:   r = r2
        theta = np.pi/12 + 2*np.pi * i/float(n)
        x = int(r*np.cos(theta))
        y = int(r*np.sin(theta))
        points.append( [x,y])
    return np.array(points).reshape(n,2)

def on_idle():
    global t, t0, frames
    t = glut.glutGet( glut.GLUT_ELAPSED_TIME )
    frames = frames + 1
    if t-t0 > 2500:
        print "FPS : %.2f (%d frames in %.2f second)" % (frames*1000.0/(t-t0), frames, (t-t0)/1000.0)
        t0, frames = t,0
    glut.glutPostRedisplay()


if __name__ == '__main__':
    import sys
    import OpenGL.GLUT as glut
    from shader import Shader
    from vertex_buffer import VertexBuffer
    from transforms import orthographic

    t0, frames, t = 0,0,0
    t0 = glut.glutGet(glut.GLUT_ELAPSED_TIME)

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
    glut.glutCreateWindow("Thick lines")
    glut.glutReshapeWindow(800, 800)
    glut.glutDisplayFunc(on_display)
    glut.glutReshapeFunc(on_reshape)
    glut.glutKeyboardFunc(on_keyboard)
    glut.glutIdleFunc(on_idle)

    shader = Shader( open('line-uniform.vert').read(),
                     open('line-uniform.frag').read() )

    S = star()
    vtype = np.dtype([('prev2', 'f4', 2),
                      ('prev',  'f4', 2),
                      ('curr',  'f4', 2),
                      ('next',  'f4', 2),
                      ('next2', 'f4', 2),
                      ('vid',   'f4', 1) ] )
    line = VertexBuffer(vtype)
    np.random.seed(1)
    for i in range(1000):
        s = np.random.uniform(0.025,0.100)
        x,y = np.random.uniform(0,800,2)
        V,I = bake( S*s + (x,y), closed=True)
        line.append(V,I)

    glut.glutMainLoop()
