"""
Basic demonstration of line plotting
"""
import numpy as np
import vispy.app
import vispy.gloo as gloo
from vispy.gloo import gl

vertex_shader = """
attribute vec3 in_position;
attribute vec4 in_color;
varying vec4 color;

void main(void) 
{
    gl_Position = vec4(in_position.x, in_position.y, 0.0, 1.0);
    color = in_color;
}
"""

fragment_shader = """
varying vec4 color;

void main(void) 
{
    gl_FragColor = color;
}
"""

# vertex positions of rectangle to draw
N = 20
pos = np.zeros((N,3), dtype=np.float32)
pos[:,0] = np.linspace(-0.9, 0.9, N)
pos[:,1] = np.random.normal(size=N, scale=0.2).astype(np.float32)
color = np.ones((N,4), dtype=np.float32)
color[:,0] = np.linspace(0, 1, N)


class Canvas(vispy.app.Canvas):
    def __init__(self):
        self.program = gloo.Program(
            gloo.VertexShader(vertex_shader),
            gloo.FragmentShader(fragment_shader),
            )
        
        # prepare data as numpy record array
        data = np.empty(len(pos), dtype=[('pos', np.float32, 3), ('color', np.float32, 4)])
        data['pos'] = pos
        data['color'] = color
        
        # create vertex buffer from data
        self.vbo = gloo.VertexBuffer(data)
        
        # assign buffer fields to program variables
        self.program['in_position'] = self.vbo['pos']
        self.program['in_color'] = self.vbo['color']
        
        vispy.app.Canvas.__init__(self)
        self.size = (800, 800)
        self.show()
        
    def on_paint(self, ev):
        gl.glViewport(0, 0, *self.size)
        self.program.draw(gl.GL_LINE_STRIP)

        

if __name__ == '__main__':
    win = Canvas()    
    vispy.app.run()
    


