#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
import numpy as np
import OpenGL.GL as gl
from transforms import perspective, ortho, translate, rotate


def on_display():
    global theta, phi
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    theta += 0.05
    phi += 0.05
    u_view[...] = np.identity(4,dtype=np.float32)
    rotate(u_view, theta, 0,1,0)
    rotate(u_view, phi, 1,0,0)
    translate(u_view, 0,0,-5)

    gl.glPolygonOffset( 1, 1 )
    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
    gl.glEnable( gl.GL_POLYGON_OFFSET_FILL )
    u_viewport = gl.glGetIntegerv( gl.GL_VIEWPORT )
    u_viewport = np.array(u_viewport,dtype=np.float32)
    lines.draw( uniforms= {'u_projection': u_projection,
                           'u_model' :     u_model,
                           'u_view' :      u_view,
                           'u_viewport' :  u_viewport})

    glut.glutSwapBuffers()
    
def on_reshape(width, height):
    gl.glViewport(0, 0, width, height)
    u_projection[...] = perspective( 25.0, width/float(height), 2.0, 10.0 )


def on_keyboard(key, x, y):
    if key == '\033': sys.exit()

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
    import sys
    import math
    import OpenGL.GLUT as glut
    from lines import Lines

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
    glut.glutInitWindowSize(1000, 1000)
    glut.glutCreateWindow("3D antialiased lines")
    glut.glutDisplayFunc(on_display)
    glut.glutReshapeFunc(on_reshape)
    glut.glutKeyboardFunc(on_keyboard)
    fps = 60
    glut.glutTimerFunc(1000/fps, on_timer, fps)
    t0, frames, t = glut.glutGet(glut.GLUT_ELAPSED_TIME),0,0
    # glut.glutIdleFunc(on_idle)
    
    # Some init
    gl.glPolygonOffset( 1, 1 )
    gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
    gl.glEnable( gl.GL_LINE_SMOOTH )
    gl.glEnable( gl.GL_DEPTH_TEST )
    gl.glEnable( gl.GL_BLEND )
    gl.glClearColor(1.0,1.0,1.0,1.0)
    gl.glClearColor(0.4,0.4,0.5,1.0)

    u_projection = np.eye(4).astype( np.float32 )
    u_view = np.eye(4).astype( np.float32 )
    u_model = np.eye(4).astype( np.float32 )
    phi,theta = 45,45

    lines = Lines()

    n = 2000
    points = np.zeros((n,3))
    T = np.linspace(0,24*2*np.pi,n)
    Z = np.linspace(-1,1,n)
    U = np.sqrt(1-Z*Z)
    X,Y = np.cos(T) * U, np.sin(T) * U
    points[:,0] = X
    points[:,1] = Y
    points[:,2] = Z
    lines.append( points, fg_color=(1,1,1,1), linewidth = 0.015)

    glut.glutMainLoop()
