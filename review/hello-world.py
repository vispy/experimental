import sys
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut
from program import Program
from buffer import VertexBuffer


vertex = """
    uniform vec4 u_color;
    attribute vec4 a_color;
    attribute vec2 a_position;
    varying vec4 v_color;
    void main()
    {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_color = a_color;
    }
"""

fragment = """
    uniform vec4 u_color;
    varying vec4 v_color;
    void main()
    {
        gl_FragColor = v_color*u_color;
    }
"""


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLE_STRIP)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)

def keyboard( key, x, y ):
    if key == '\033': sys.exit( )

glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow('Hello world!')
glut.glutReshapeWindow(512,512)
glut.glutDisplayFunc(display)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )



program = Program(vertex,fragment)


pos = np.zeros(4, dtype=[('a_position',  np.float32, 2)])
pos['a_position'] = [ (-1,-1), (-1,+1), (+1,-1), (+1,+1) ]
col = np.zeros(4, dtype=[('a_color',  np.float32, 4)])
col['a_color'] = [(1,0,0,1),(0,1,0,1),(0,0,1,1),(1,1,0,1)]


data = np.zeros(4, dtype=[ ('a_position',  np.float32, 2),
                           ('a_color',     np.float32, 4) ])
data['a_position'] = [ (-1,-1), (-1,+1), (+1,-1), (+1,+1) ]
data['a_color'] = [(1,0,0,1),(0,1,0,1),(0,0,1,1),(1,1,0,1)]


vbo = VertexBuffer(data)

# 2 implicit buffers = 2 uploads
program['a_position'] = pos
program['a_color']    = col
program['u_color']    = 0.75

# 2 implicit buffers = 2 uploads
# program['a_position'] = data['a_position']
# program['a_color']    = data['a_color']
# program['u_color']    = 0.75

# 1 buffer = 1 upload
# program['a_position'] = vbo['a_position']
# program['a_color']    = vbo['a_color']
# program['u_color']    = 0.75


glut.glutMainLoop()
