import sys, json, threading, base64, cStringIO
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut

from PIL import Image

from vispy.gloo import Program, VertexBuffer, IndexBuffer
from vispy.util.transforms import perspective, translate, rotate
from vispy.util.cube import cube
from vispy.gloo import gl

from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


### SERVER PART ###

class WSHandler(WebSocketHandler):
    def open(self):
        print "Connection opened"

    def on_message(self, message):
        # Send PNG on every message
        self.write_message(send_PNG())

    def on_close(self):
      print "Connection closed"


class Server(threading.Thread):
    def __init__(self):
        super(Server, self).__init__()
        application = Application([(r'/', WSHandler),])
        self.http_server = HTTPServer(application)

    def run(self):
        self.http_server.listen(9000)
        IOLoop.instance().start()

# Start the server thread
server = Server()
server.start()


### GLUT PART ###

vertex = """
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
attribute vec3 position;
attribute vec4 color;
varying vec4 v_color;
void main()
{
    v_color = color;
    gl_Position = projection * view * model * vec4(position,1.0);
}
"""

fragment = """
varying vec4 v_color;
void main()
{
    gl_FragColor = v_color;
}
"""

#Global variable that main thread changes and server thread uses
PNG = ""

# Main thread (glut) calls this function
def save_PNG():
    """
    since Image module can convert numpy.ndarray into a PNG image with
    fromarray() function, I used it.
    However I couldn't get the bytes from it so every time it is saving the
    image onto stream and reads it again in order to convert to base64 string.
    """
    global PNG

    img = screenshot()
    img = Image.fromarray(img)

    # Save the image onto stream
    # This is still too slow!
    stream = cStringIO.StringIO()
    img.save(stream, "PNG")
    PNG = stream.getvalue().encode("base64")

    stream.close()


# Server thread calls this function
def send_PNG():
    return json.dumps({"image" : PNG})


def screenshot(viewport=None):
    """ Take a screenshot using glReadPixels.
    """
    # gl.glReadBuffer(gl.GL_BACK) Not avaliable in ES 2.0
    if viewport is None:
        viewport = gl.glGetParameter(gl.GL_VIEWPORT)
    x, y, w, h = 0, 0, 500, 500
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1) # PACK, not UNPACK
    im = gl.glReadPixels(x, y, w, h, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 4)

    # reshape, flip, and return
    if not isinstance(im, np.ndarray):
        im = np.frombuffer(im, np.uint8)
    im.shape = h, w, 3
    im = np.flipud(im)
    return im


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLES, indices)
    glut.glutSwapBuffers()

    # Save screen in every display()
    save_PNG()


def reshape(width, height):
    gl.glViewport(0, 0, width, height)
    projection = perspective(45.0, width / float(height), 2.0, 10.0)
    program['projection'] = projection


def keyboard(key, x, y):
    if key == '\033':
        sys.exit()


def timer(fps):
    global theta, phi
    theta += .5
    phi += .5
    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0, 0, 1)
    rotate(model, phi, 0, 1, 0)
    program['model'] = model
    glut.glutTimerFunc(1000 / fps, timer, fps)
    glut.glutPostRedisplay()


# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow('Colored Cube')
glut.glutReshapeWindow(512, 512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard)
glut.glutDisplayFunc(display)
glut.glutTimerFunc(1000 / 60, timer, 60)

# Build cube data
# --------------------------------------
V, I, _ = cube()
vertices = VertexBuffer(V)
indices = IndexBuffer(I)

# Build program
# --------------------------------------
program = Program(vertex, fragment)
program.bind(vertices)

# Build view, model, projection & normal
# --------------------------------------
view = np.eye(4, dtype=np.float32)
model = np.eye(4, dtype=np.float32)
projection = np.eye(4, dtype=np.float32)
translate(view, 0, 0, -5)
program['model'] = model
program['view'] = view
phi, theta = 0, 0

# OpenGL initalization
# --------------------------------------
gl.glClearColor(0.30, 0.30, 0.35, 1.00)
gl.glEnable(gl.GL_DEPTH_TEST)

# Start
# --------------------------------------
glut.glutMainLoop()
