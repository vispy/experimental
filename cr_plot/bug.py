from __future__ import division
from collections import namedtuple
import numpy as np
from math import exp

from vispy import app
from vispy import gloo
from vispy.scene.shaders import Function, ModularProgram
from vispy.scene.visuals import Visual
from vispy.scene.transforms import STTransform


class PanZoomTransform(STTransform):
    pan = (0., 0.)
    
    def move(self, (dx, dy)):
        """I call this when I want to translate."""
        self.pan = (self.pan[0] + dx/self.scale[0],
                    self.pan[1] + dy/self.scale[1])
        self.translate = (self.pan[0]*self.scale[0],
                          self.pan[1]*self.scale[1])
        
    def zoom(self, (dx, dy), center=(0., 0.)):
        """I call this when I want to zoom."""
        scale = (self.scale[0] * exp(2.5*dx),
                 self.scale[1] * exp(2.5*dy))
        tr = self.pan
        self.pan = (tr[0] - center[0] * (1./self.scale[0] - 1./scale[0]),
                    tr[1] + center[1] * (1./self.scale[1] - 1./scale[1]))
        self.scale = scale
        self.translate = (self.pan[0]*self.scale[0],
                          self.pan[1]*self.scale[1])


class LineVisual(app.Canvas):
    VERTEX_SHADER = """
        #version 120
        vec4 transform(vec4);
        attribute vec2 a_position;
        
        void main (void)
        {
            gl_Position = transform(vec4(a_position, 0., 1.0));
        }
    """

    FRAGMENT_SHADER = """
        #version 120
        uniform vec3 u_color;
        void main()
        {
            gl_FragColor = vec4(u_color.xyz, 1.);
        }
    """
    
    def __init__(self, pos=None, color=None):
        super(LineVisual, self).__init__(close_keys='escape')
        self._dirty = False
        self._program = ModularProgram(self.VERTEX_SHADER, self.FRAGMENT_SHADER)
        self.panzoom = PanZoomTransform()
        self._program['transform'] = self.panzoom.shader_map()
        self.set_data(pos=pos, color=color)
        
    def set_options(self):
        gloo.set_state(clear_color=(1, 1, 1, 1), blend=True, 
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def set_data(self, pos=None, color=None):
        self._pos = pos
        self._color = color
        self._dirty = True
        
    def on_draw(self, event):
        gloo.clear()
        self.set_options()
        
        if self._dirty:  # add `or 1` ==> zoom with wheel works
            self._program._create()
            self._program._build()
            self._program['a_position'] = gloo.VertexBuffer(self._pos)
            self._program['u_color'] = self._color
            self._dirty = False
        
        self._program.draw(gloo.gl.GL_LINE_STRIP, 'line_strip')

    def _normalize(self, (x, y)):
        w, h = float(self.size[0]), float(self.size[1])
        return x/(w/2.)-1., y/(h/2.)-1.
    
    def on_mouse_wheel(self, event):
        c = event.delta[1] * .1
        x, y = self._normalize(event.pos)
        self.panzoom.zoom((c, c), center=(x, y))
        self.update()
        self.panzoom.shader_map()
        
    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

if __name__ == '__main__':
    
    n = 1000
    
    x = np.linspace(-1.0, +1.0, n).astype(np.float32)
    y = np.random.uniform(-0.5, +0.5, n).astype(np.float32)
    pos = np.c_[x,y]
    
    line = LineVisual(pos, color=(1., 0., 0.))
    line.show()
    app.run()
