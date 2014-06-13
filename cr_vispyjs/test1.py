import numpy as np
from vispy import app
from vispy import gloo

vertex = """
attribute float x;
attribute float y;
uniform float c;
void main (void)
{
    gl_Position = vec4(x, y, c, 1.0);
}
"""

fragment = """
uniform float c;
void main()
{
    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
}
"""

class Window(app.Canvas):
    def __init__(self, n=50):
        app.Canvas.__init__(self)
        self.program = gloo.Program(vertex, fragment)
        self.program['x'] = gloo.VertexBuffer(np.linspace(-1.0, +1.0, n).astype(np.float32))
        self.program['y'] = gloo.VertexBuffer(np.random.uniform(-0.5, +0.5, n).astype(np.float32))
        self.program['c'] = 2.

    def on_resize(self, event):
        gloo.set_viewport(0, 0, event.size[0], event.size[1])

    def on_draw(self, event):
        gloo.clear((1,1,1,1))
        self.program.draw('line_strip')

####################################################""
        
import base64

def _encode_data(data):
    return base64.b64encode(data)
        
def _decode_data(s, dtype):
    """Return a Numpy array from its encoded Base64 string. The dtype
    must be provided."""
    return np.fromstring(base64.b64decode(s), dtype=dtype)
        

def export_shader(shader):
    return shader.code
    
def export_data(data):
    return {'dtype': data.dtype.descr,
            'buffer': _encode_data(data)}
    
def export_attribute(attr):
    return {'gtype': attr.gtype,
            'data': export_data(attr.data._data)}
    
def export_uniform(uni):
    return {'gtype': uni._gtype,
            'data': export_data(uni._data)}

def export_program(prog):

    attributes = {name: export_attribute(attr) 
                    for name, attr in prog._attributes.iteritems()}
    uniforms = {name: export_uniform(attr)
                    for name, attr in prog._uniforms.iteritems()}

    vs = export_shader(prog.shaders[0])
    fs = export_shader(prog.shaders[1])

    return { 'attributes': attributes,
             'uniforms': uniforms,
             'vertex_shader': vs,
             'fragment_shader': fs}


window = Window(n=1000)
prog = window.program
import json
print json.dumps(export_program(prog), indent=1)
