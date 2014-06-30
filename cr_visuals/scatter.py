from __future__ import division
from collections import namedtuple
import numpy as np
from math import exp

from vispy import app
from vispy import gloo
from vispy.scene.shaders import Function, ModularProgram
from vispy.scene.visuals import Visual

PAN_ZOOM = """
    // I'd like to remove that DOLLAR before the function name
    // BUG: I can't put a DOLLAR sign in comment ==> crash
    vec4 $pan_zoom(vec2 position){
        vec2 position_tr = $scale * position + $pan;
        return vec4(position_tr, 0.0, 1.0);
    }
"""

class PanZoomComponent(Function):
    """This is just a convenient class that I want to use with PAN_ZOOM.
    The only convention I'm following is that, for every $variable in PAN_ZOOM,
    there's a self.$variable in this instance.
    """
    def __init__(self):
        Function.__init__(self, PAN_ZOOM)
        self.pan = (0., 0.)
        self.scale = (1., 1.)
        self._update()
        
    def move(self, (dx, dy)):
        """I call this when I want to translate."""
        self.pan = (self.pan[0] + dx/self.scale[0],
                    self.pan[1] + dy/self.scale[1])
        self._update()
                         
    def zoom(self, (dx, dy), center=(0., 0.)):
        """I call this when I want to zoom."""
        scale = (self.scale[0] * exp(2.5*dx),
                 self.scale[1] * exp(2.5*dy))
        self.pan = (self.pan[0] - center[0] * (1./self.scale[0] - 1./scale[0]),
                    self.pan[1] + center[1] * (1./self.scale[1] - 1./scale[1]))
        self.scale = scale
        self._update()

    def _update(self):
        self['pan'] = ('uniform', 'vec2', (self.pan[0]*self.scale[0],
                                           self.pan[1]*self.scale[1]))
        self['scale'] = ('uniform', 'vec2', self.scale)


class MarkerVisual(Visual):
    # My full vertex shader, with just a `transform` hook.
    VERTEX_SHADER = """
        #version 120
        
        vec4 transform(vec2);
        
        attribute vec2 a_position;
        attribute vec3 a_color;
        attribute float a_size;

        varying vec4 v_fg_color;
        varying vec4 v_bg_color;
        varying float v_radius;
        varying float v_linewidth;
        varying float v_antialias;

        void main (void) {
            v_radius = a_size;
            v_linewidth = 1.0;
            v_antialias = 1.0;
            v_fg_color  = vec4(0.0,0.0,0.0,0.5);
            v_bg_color  = vec4(a_color,    1.0);
            
            gl_Position = transform(a_position);
            
            gl_PointSize = 2.0*(v_radius + v_linewidth + 1.5*v_antialias);
        }
    """

    FRAGMENT_SHADER = """
        #version 120
        varying vec4 v_fg_color;
        varying vec4 v_bg_color;
        varying float v_radius;
        varying float v_linewidth;
        varying float v_antialias;
        void main()
        {
            float size = 2.0*(v_radius + v_linewidth + 1.5*v_antialias);
            float t = v_linewidth/2.0-v_antialias;
            float r = length((gl_PointCoord.xy - vec2(0.5,0.5))*size);
            float d = abs(r - v_radius) - t;
            if( d < 0.0 )
                gl_FragColor = v_fg_color;
            else
            {
                float alpha = d/v_antialias;
                alpha = exp(-alpha*alpha);
                if (r > v_radius)
                    gl_FragColor = vec4(v_fg_color.rgb, alpha*v_fg_color.a);
                else
                    gl_FragColor = mix(v_bg_color, v_fg_color, alpha);
            }
        }
    """
    
    def __init__(self, pos=None, color=None, size=None):
        self._program = ModularProgram(self.VERTEX_SHADER, self.FRAGMENT_SHADER)
        self.set_data(pos=pos, color=color, size=size)
        
    def set_options(self):
        """Special function that is used to set the options. Automatically
        called at initialization."""
        gloo.set_state(clear_color=(1, 1, 1, 1), blend=True, 
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def set_data(self, pos=None, color=None, size=None):
        """I'm not required to use this function. We could also have a system
        of trait attributes, such that a user doing
        `visual.position = myndarray` results in an automatic update of the 
        buffer. Here I just set the buffers manually."""
        self._pos = pos
        self._color = color
        self._size = size
        
    def draw(self):
        self.set_options()
        self._program._create()
        self._program._build()  # attributes / uniforms are not available until program is built
        self._program['a_position'] = gloo.VertexBuffer(self._pos)
        self._program['a_color'] = gloo.VertexBuffer(self._color)
        self._program['a_size'] = gloo.VertexBuffer(self._size)
        self._program.draw(gloo.gl.GL_POINTS, 'points')
    
    
class Canvas(app.Canvas):

    def _normalize(self, (x, y)):
        w, h = float(self.size[0]), float(self.size[1])
        return x/(w/2.)-1., y/(h/2.)-1.
    
    def __init__(self):
        app.Canvas.__init__(self, close_keys='escape')

        n = 10000
        pos = 0.25 * np.random.randn(n, 2).astype(np.float32)
        color = np.random.uniform(0, 1, (n, 3)).astype(np.float32)
        size = np.random.uniform(2, 12, (n, 1)).astype(np.float32)

        self.points = MarkerVisual(pos=pos, color=color, size=size)
        
        # This is just an instance I choose to use, nothing required in the
        # Visual API here.
        self.panzoom = PanZoomComponent()
        
        # Here, I set the `transform` hook to my PAN_ZOOM function.
        # In addition, I provide a component instance.
        # Vispy knows that every $variable in the Function is bound to
        # component.$variable. Here, since pan and zoom are tuples,
        # Vispy understands that it has to create two uniforms (u_$variable 
        # for example).
        self.points._program['transform'] = self.panzoom

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
        
    def on_mouse_wheel(self, event):
        c = event.delta[1] * .1
        x, y = self._normalize(event.pos)
        self.panzoom.zoom((c, c), center=(x, y))
        self.update()
        
    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

    def on_draw(self, event):
        gloo.clear()
        self.points.draw()

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
