#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
import sys
import math
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut

from shader import Shader
from collection import Collection
from transforms import perspective, translate


def display():
    global projection, view

    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    gl.glDisable( gl.GL_BLEND )
    gl.glEnable( gl.GL_DEPTH_TEST )
    gl.glEnable( gl.GL_POLYGON_OFFSET_FILL )
    cubes.uniforms['rotate'][:,1] += 0.05
    cubes.uniforms['rotate'][:,2] += 0.05
    cubes.upload_uniforms()
    cubes.draw(gl.GL_TRIANGLES,
               {'u_projection' : projection,
                'u_view' : view,
                'u_color' : (1.0,1.0,1.0,1.0) } )

    gl.glDisable( gl.GL_POLYGON_OFFSET_FILL )
    gl.glEnable( gl.GL_BLEND );
    gl.glDepthMask( gl.GL_FALSE );
    outlines.uniforms['rotate'][:,1] += 0.05
    outlines.uniforms['rotate'][:,2] += 0.05
    outlines.upload_uniforms()
    outlines.draw(gl.GL_LINES,
                  {'u_projection' : projection,
                   'u_view' : view,
                   'u_color' : (0.0,0.0,0.0,0.5) } )
    gl.glDepthMask( gl.GL_TRUE )

    glut.glutSwapBuffers()


def reshape(width,height):
    global projection, view
    gl.glViewport(0, 0, width, height)
    projection = perspective( 25.0, width/float(height), 2.0, 10.0 )
    view = np.identity(4,dtype=np.float32)
    translate(view, 0,0,-5)

def keyboard( key, x, y ):
    if key == '\033':
        sys.exit( )

def on_timer(fps):
    glut.glutTimerFunc(1000/fps, on_timer, fps)
    glut.glutPostRedisplay()

def on_idle():
    global t, t0, frames
    t = glut.glutGet( glut.GLUT_ELAPSED_TIME )
    frames = frames + 1
    if t-t0 > 2500:
        print( "FPS : %.2f (%d frames in %.2f second)"
               % (frames*1000.0/(t-t0), frames, (t-t0)/1000.0))
        t0, frames = t,0
    glut.glutPostRedisplay()



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    fps = 60

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    glut.glutCreateWindow('glut-cubes')
    glut.glutReshapeWindow(512,512)
    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(reshape)
    glut.glutKeyboardFunc(keyboard )
    glut.glutTimerFunc(1000/fps, on_timer, fps)
    # glut.glutIdleFunc(on_idle)

    projection = np.eye(4,dtype=np.float32)
    view       = np.eye(4,dtype=np.float32)
    t0, frames, t = glut.glutGet(glut.GLUT_ELAPSED_TIME),0,0
    theta, phi = 0,0

    gl.glPolygonOffset( 1, 1 )
    gl.glClearColor( .3, .3, .35, 1 )
    gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
    gl.glEnable( gl.GL_LINE_SMOOTH )



    vtype = [('a_position', np.float32, 3),
             ('a_normal'  , np.float32, 3),
             ('a_color',    np.float32, 4)] 
    utype = [('translate', np.float32, 4),
             ('rotate',    np.float32, 4),
             ('scale',     np.float32, 4) ]

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

    U = np.zeros(1,dtype=utype)
    U['translate'] = 1,1,1,0
    U['rotate'] = 0,0,0,0
    U['scale'] = 1,1,1,1

    n = 8

    cubes = Collection(vtype,utype)
    for i in xrange(n*n):
        cubes.append(V,I,U)

    I = np.resize( np.array([0,1,1,2,2,3,3,0], dtype=np.uint32), 6*(2*4))
    I += np.repeat( 4*np.arange(6), 8)
    outlines = Collection(vtype,utype)
    for i in xrange(n*n):
        outlines.append(V,I,U)

    X,Y = np.meshgrid(np.linspace(0,1,n), np.linspace(0,1,n))
    X,Y = -12.0 + X*24.0, -12.0 + Y*24.0

    cubes.uniforms['scale'] = 0.075
    cubes.uniforms['rotate'][:,1] = 0.5*np.arange(n*n)
    cubes.uniforms['rotate'][:,2] = 0.5*np.arange(n*n)
    cubes.uniforms['translate'][:,0] = X.flat
    cubes.uniforms['translate'][:,1] = Y.flat

    outlines.uniforms['scale'] = 0.075
    outlines.uniforms['rotate'][:,1] = 0.5*np.arange(n*n)
    outlines.uniforms['rotate'][:,2] = 0.5*np.arange(n*n)
    outlines.uniforms['translate'][:,0] = X.flat
    outlines.uniforms['translate'][:,1] = Y.flat

    cubes.shader = Shader(open("./cubes.vert").read(),
                          open("./cubes.frag").read())
    outlines.shader = Shader(open("./cubes.vert").read(),
                             open("./cubes.frag").read())

    glut.glutMainLoop()
