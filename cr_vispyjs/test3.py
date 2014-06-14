from vispy import gloo
from vispy import app
import numpy as np
from math import exp

n = 1000
v_position = 0.25 * np.random.randn(n, 2).astype(np.float32)
v_color = np.random.uniform(0, 1, (n, 3)).astype(np.float32)
v_size = np.random.uniform(2, 12, (n, 1)).astype(np.float32)

VERT_SHADER = """
attribute vec2 a_position;
attribute vec3 a_color;
attribute float a_size;

uniform vec2 u_pan;
uniform vec2 u_scale;

varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_radius;
varying float v_linewidth;
varying float v_antialias;

void main (void) {
    v_radius = a_size;
    v_linewidth = 2.0;
    v_antialias = 1.0;
    v_fg_color  = vec4(0.0,0.0,0.0,0.5);
    v_bg_color  = vec4(a_color,    1.0);
    
    vec2 position_tr = u_scale * (a_position + u_pan);
    gl_Position = vec4(position_tr, 0.0, 1.0);
    gl_PointSize = 2.0*(v_radius + v_linewidth + 1.5*v_antialias);
}
"""

FRAG_SHADER = """

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

class Canvas(app.Canvas):

    def __init__(self):
        app.Canvas.__init__(self, close_keys='escape')

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)

        self.program['a_color'] = gloo.VertexBuffer(v_color)
        self.program['a_position'] = gloo.VertexBuffer(v_position)
        self.program['a_size'] = gloo.VertexBuffer(v_size)
        
        self.program['u_pan'] = (0., 0.)
        self.program['u_scale'] = (1., 1.)

    def on_initialize(self, event):
        gloo.set_state(clear_color=(1, 1, 1, 1), blend=True, 
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def on_mouse_move(self, event):
        
        def _normalize((x, y)):
            w, h = float(self.width), float(self.height)
            return x/(w/2.)-1., y/(h/2.)-1.
            
        if event.is_dragging:
            x0, y0 = _normalize(event.press_event.pos)
            x1, y1 = _normalize(event.last_event.pos)
            x, y = _normalize(event.pos)
            dx, dy = x - x1, -(y - y1)
            button = event.press_event.button
            
            pan_x, pan_y = self.program['u_pan']
            scale_x, scale_y = self.program['u_scale']
            
            if button == 1:
                self.program['u_pan'] = (pan_x+dx/scale_x, pan_y+dy/scale_y)
            elif button == 2:
                scale_x_new, scale_y_new = scale_x * exp(2.5*dx), scale_y * exp(2.5*dy)
                self.program['u_scale'] = (scale_x_new, scale_y_new)
                self.program['u_pan'] = (pan_x - x0 * (1./scale_x - 1./scale_x_new), 
                                         pan_y + y0 * (1./scale_y - 1./scale_y_new))
            self.update()
        
    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('points')

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()

    from vispy_export import export_canvas_json
    export_canvas_json(c, 'test3.json')