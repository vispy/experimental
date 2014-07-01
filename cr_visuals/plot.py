from __future__ import division
from collections import namedtuple
import numpy as np
from math import exp

from vispy import app
from vispy import gloo
from vispy.scene.shaders import Function, ModularProgram
from vispy.scene.visuals import Visual
from vispy.scene.transforms import STTransform

from scatter_transform import PanZoomTransform, MarkerVisual


class PlotCanvas(app.Canvas):
    def _normalize(self, (x, y)):
        w, h = float(self.size[0]), float(self.size[1])
        return x/(w/2.)-1., y/(h/2.)-1.
    
    def __init__(self):
        app.Canvas.__init__(self, close_keys='escape')
        self._visuals = []
        self.panzoom = PanZoomTransform()

    def __setattr__(self, name, value):
        super(PlotCanvas, self).__setattr__(name, value)
        if isinstance(value, Visual):
            self._visuals.append(value)
            value._program['transform'] = self.panzoom.shader_map()
        
    def on_mouse_move(self, event):
        if event.is_dragging:
            x0, y0 = self._normalize(event.press_event.pos)
            x1, y1 = self._normalize(event.last_event.pos)
            x, y = self._normalize(event.pos)
            dxy = ((x - x1), -(y - y1))
            center = (x0, y0)
            button = event.press_event.button
            
            if button == 1:
                self.panzoom.move(dxy)
            elif button == 2:
                self.panzoom.zoom(dxy, center=center)
                
            self.update()
            self.panzoom.shader_map()
        
    def on_mouse_wheel(self, event):
        c = event.delta[1] * .1
        x, y = self._normalize(event.pos)
        self.panzoom.zoom((c, c), center=(x, y))
        self.update()
        self.panzoom.shader_map()
        
    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

    def on_draw(self, event):
        gloo.clear()
        for v in self._visuals:
            v.draw()

      
class MyCanvas(PlotCanvas):
    def __init__(self):
        super(MyCanvas, self).__init__()
        
    def scatter(self, pos, color=None, size=None):
        self.points = MarkerVisual(pos=pos, color=color, size=size)
        
    def show(self):
        super(MyCanvas, self).show()
        app.run()
        

def figure():
    return MyCanvas()


if __name__ == '__main__':
    n = 10000
    
    pos = 0.25 * np.random.randn(n, 2).astype(np.float32)
    color = np.random.uniform(0, 1, (n, 3)).astype(np.float32)
    size = np.random.uniform(2, 12, (n, 1)).astype(np.float32)
    
    ax = figure()
    ax.scatter(pos, color=color, size=size)
    
    ax.show()
