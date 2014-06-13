import numpy as np
from vispy import app
from vispy import gloo

vertex = """
attribute float x;
attribute float y;
uniform vec4 u_color;
void main (void)
{
    gl_Position = vec4(x, y, 0., 1.0);
}
"""

fragment = """
uniform vec4 u_color;
void main()
{
    gl_FragColor = vec4(u_color.x, 1., 0., 1.);
}
"""

class Window(app.Canvas):
    def __init__(self, n=50):
        app.Canvas.__init__(self)
        self.program = gloo.Program(vertex, fragment)
        self.program['x'] = gloo.VertexBuffer(np.linspace(-1.0, +1.0, n).astype(np.float32))
        self.program['y'] = gloo.VertexBuffer(np.random.uniform(-0.5, +0.5, n).astype(np.float32))
        self.program['u_color'] = np.array((1., 0., 0., 1.), dtype=np.float32)

    def on_resize(self, event):
        gloo.set_viewport(0, 0, event.size[0], event.size[1])

    def on_draw(self, event):
        gloo.clear((0,0,0,0))
        self.program.draw('line_strip')

window = Window(n=1000)
window.show()
app.run()

from vispy_export import export_canvas
exp = export_canvas(window)

import json
with open('test1.json', 'w') as f:
    f.write(json.dumps(exp, indent=1))

