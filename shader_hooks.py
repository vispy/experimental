"""
Basic demonstration of shaders with customizable transformation
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
import vispy.app
import vispy.opengl as opengl

null_transform_shader = """
#version 120

vec4 global_transform(vec4 pos) {
    return pos;
}
"""

st_transform_shader = """
#version 120

uniform vec2 translate;
uniform vec2 scale;

vec4 global_transform(vec4 pos) {
    return (pos * vec4(scale, 1, 1)) + vec4(translate, 0, 0);
}
"""

matrix_transform_shader = """
#version 120

uniform mat4 transform;

vec4 global_transform(vec4 pos) {
    return transform * pos;
}
"""



vertex_shader = """
#version 120

// prototype for the transformation to be customized
vec4 global_transform(vec4);

attribute vec3 in_position;

void main(void) 
{
    // All vertex shaders should implement this line to allow
    // customizable transformation.
    gl_Position = global_transform(vec4(in_position, 1.0));
}
"""

fragment_shader = """
#version 120

void main(void) 
{
    gl_FragColor = vec4(1, 1, 1, 1);
}
"""

class PlotLine:
    def __init__(self, pos):
        self.data = pos
        self.transform_shader = opengl.VertexShader(null_transform_shader, compile_now=False)
        self.shader_attrs = {}
        self.program = None
        
    def init_gl(self):
        self.update_buffers()
        
    def set_transform_shader(self, shader):
        self.transform_shader = shader
        self.program = None
        
    def set_shader_attributes(self, **kwds):
        self.shader_attrs.update(kwds)
        
    def build_program(self):
        self.program = opengl.ShaderProgram(
            self.transform_shader,
            opengl.VertexShader(vertex_shader),
            opengl.FragmentShader(fragment_shader),
            )
        
    def update_buffers(self):
        self.vbo = opengl.DtypeVertexBuffer(data=self.data)
        
    def draw(self):
        if self.program is None:
            self.build_program()
        self.program.bind()
        
        self.program['in_position'] = self.vbo
        for k,v in self.shader_attrs.items():
            self.program[k] = v
        
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1)

        glDrawArrays(GL_LINE_STRIP, 0, self.data.shape[0])

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glUseProgram(0)
        

class Window(vispy.app.Canvas):
    """Just a simple display window"""
    def __init__(self, visuals):
        self.visuals = visuals
        
        vispy.app.Canvas.__init__(self)
        #self.resize(800,800)
        self.geometry = self.geometry[:2] + (800,800)
        self.show()
        
    def on_initialize(self, ev):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        for visual in self.visuals:
            visual.init_gl()
        
    def on_resize(self, ev):
        glViewport(0, 0, *ev.size)

    def on_paint(self, ev):
        glClear(GL_COLOR_BUFFER_BIT)
        for visual in self.visuals:
            visual.draw()
        self.swap_buffers()

if __name__ == '__main__':
    vispy.app.use('pyglet')
    N = 5000
    pos = np.empty(N, dtype=[('pos', np.float32, 2)])
    pos['pos'][:,0] = np.linspace(-1, 1, N)
    pos['pos'][:,1] = np.sin(pos['pos'][:,0] * 15.) * 0.3
    
    plots = []
    
    ## no transform; drawing in clip coords.
    line1 = PlotLine(pos)
    plots.append(line1)
    
    ## scale/translate
    line2 = PlotLine(pos)
    line2.set_transform_shader(opengl.VertexShader(st_transform_shader, compile_now=False))
    line2.set_shader_attributes(
        scale=np.array([0.5, 0.5]), 
        translate=np.array([0.0, -0.5]))
    plots.append(line2)
    
    ## matrix
    line3 = PlotLine(pos)
    line3.set_transform_shader(opengl.VertexShader(matrix_transform_shader, compile_now=False))
    line3.set_shader_attributes(transform=np.array([[0.2, 1,   0, 0],
                                                    [0.3, 0.2, 0, 0],
                                                    [0,   0,   1, 0],
                                                    [0,   0.5, 0, 1]]))
    plots.append(line3)
    
    win = Window(plots)
    vispy.app.run()

