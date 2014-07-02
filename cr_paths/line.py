from vispy import gloo
from vispy import app
import numpy as np
import math

n = 1000
x = np.linspace(-1., 1., n)
y = .5*np.sin(20*x)

data = np.zeros(n, dtype=[
    ('a_position', np.float32, 2),
])
data['a_position'][:,0] = x
data['a_position'][:,1] = y

VERT_SHADER = """
attribute vec2 a_position;
void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

FRAG_SHADER = """
void main() {
    gl_FragColor = vec4(1., 0., 0., 1.0);
}
"""

class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, close_keys='escape')
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program.bind(gloo.VertexBuffer(data))

    def on_initialize(self, event):
        gloo.set_state(clear_color=(1, 1, 1, 1), blend=True, 
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

    def on_draw(self, event):
        gloo.clear(color=(1.0, 1.0, 1.0, 1.0))
        self.program.draw('line_strip')

c = Canvas()
c.show()
app.run()
