
import numpy as np
from vispy import app, gloo
gl = gloo.gl

from vispy_experimental import ak_visuals as visuals



class PointsVisual(visuals.Visual):
    
    VERT_SHADER = """
        attribute vec3 a_position;
        
        varying vec4 v_color;
        void main (void) {
            gl_Position = vec4(a_position, 1.0);
            v_color = vec4(1.0, 0.5, 0.0, 0.8);
            gl_PointSize = 10.0; //size;
        }
    """
    
    FRAG_SHADER = """
        varying vec4 v_color;
        void main()
        {    
            float x = 2.0*gl_PointCoord.x - 1.0;
            float y = 2.0*gl_PointCoord.y - 1.0;
            float a = 1.0 - (x*x + y*y);
            gl_FragColor = vec4(v_color.rgb, a*v_color.a);
        }
        
    """

    def __init__(self, parent, N=1000):
        visuals.Visual.__init__(self, parent)
        
        data = np.random.normal(0, 0.25, (N,3)).astype('float32')
        
        self.program = gloo.Program(self.VERT_SHADER, self.FRAG_SHADER)
        self.program['a_position'] = gloo.VertexBuffer(data)
        
        
    def draw(self):
        self.program.draw('POINTS')



class Figure(app.Canvas):
    """ The Figure class represents the top-level object. It has a world
    with Visual objects.
    """
    
    def __init__(self, *args, **kwargs):
        self._viewport = visuals.Viewport()
        
        self._camera = visuals.Camera(self._viewport.world)
        self._line = PointsVisual(self._viewport.world)
        
        app.Canvas.__init__(self, *args, **kwargs)
    
    
    def on_initialize(self, event):
        # todo: this must be done in the engine ...
        gl.glClearColor(0,0,0,1);
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    def on_resize(self, event):
        width, height = event.size
        gl.glViewport(0, 0, width, height)
    
    def on_paint(self, event):
        self._viewport.draw()



if __name__ == '__main__':
    fig = Figure()
    fig.show()
    app.run()

