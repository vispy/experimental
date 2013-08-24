#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
import sys
import math
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut

from shader import Shader
from vertex_buffer import VertexBuffer
from transforms import perspective, translate, rotate, scale


def load_obj(filename):
    '''
    Load vertices and faces from a wavefront .obj file and generate normals.
    '''
    data = np.genfromtxt(filename, dtype=[('type', np.character, 1),
                                          ('points', np.float32, 3)])

    # Get vertices and faces
    vertices = data['points'][data['type'] == 'v']
    faces = (data['points'][data['type'] == 'f']-1).astype(np.uint32)

    # Build normals
    T = vertices[faces]
    N = np.cross(T[::,1 ]-T[::,0], T[::,2]-T[::,0])
    L = np.sqrt(N[:,0]**2+N[:,1]**2+N[:,2]**2)
    N /= L[:, np.newaxis]
    normals = np.zeros(vertices.shape)
    normals[faces[:,0]] += N
    normals[faces[:,1]] += N
    normals[faces[:,2]] += N
    L = np.sqrt(normals[:,0]**2+normals[:,1]**2+normals[:,2]**2)
    normals /= L[:, np.newaxis]

    # Scale vertices such that object is contained in [-1:+1,-1:+1,-1:+1]
    vmin, vmax =  vertices.min(), vertices.max()
    vertices = 2*(vertices-vmin)/(vmax-vmin) - 1

    # Center
    X,Y,Z = vertices[:,0],vertices[:,1],vertices[:,2]
    xmin, xmax = X.min(), X.max()
    ymin, ymax = Y.min(), Y.max()
    zmin, zmax = Z.min(), Z.max()
    X -= (xmax+xmin)/2.
    Y -= (ymax+ymin)/2.
    Z -= (zmax+zmin)/2.
      
    return vertices, normals, faces


def display():
    global projection, view
    global theta, phi

    theta += .43
    phi += .37
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0,0,1)
    rotate(model, phi, 0,1,0)
    shader.bind()
    shader.uniformf('u_color', 1.0, 1.0, 1.0, 1.0 )
    shader.uniform_matrixf('u_view', view)
    shader.uniform_matrixf('u_projection', projection)
    shader.uniform_matrixf('u_model', model)
    gl.glDisable( gl.GL_BLEND )
    gl.glEnable( gl.GL_DEPTH_TEST )
    gl.glEnable( gl.GL_POLYGON_OFFSET_FILL )
    obj.draw( gl.GL_TRIANGLES )
    gl.glDisable( gl.GL_POLYGON_OFFSET_FILL )
    gl.glEnable( gl.GL_BLEND );
    gl.glDepthMask( gl.GL_FALSE );
    shader.uniformf('u_color', 0.0, 0.0, 0.0, 0.25 )
    outline.draw( gl.GL_LINES )
    gl.glDepthMask( gl.GL_TRUE )
    gl.glUseProgram( 0 )

    glut.glutSwapBuffers()


def reshape(width,height):
    global projection, view
    gl.glViewport(0, 0, width, height)
    projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
    view = np.identity(4,dtype=np.float32)
    translate(view, 0,0,-3)

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
    vertices, normals, faces = load_obj('./bunny.obj')
    V = np.zeros(len(vertices), dtype=vtype)
    V['position'] = vertices
    V['color'] = 1,1,1,1
    V['normal'] = normals

    obj = VertexBuffer(vtype)
    obj.append(V, faces)

    outline = VertexBuffer(vtype)

    I = []
    for f in faces:
        I.extend([f[0],f[1],f[1],f[2],f[2],f[0]])
    outline.append(V, I)

    shader = Shader(open("./cube.vert").read(),
                    open("./cube.frag").read())
    glut.glutMainLoop()
