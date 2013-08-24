"""
Basic demonstration of line plotting. Based on Luke's lines example.
Modified the shader to disable antialiasing there. Added code to
add a render pass at the end to perform aa.

The remaining artifacts where the line gets thin at some points are due
to limitations in producing a line with constant width.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from PySide import QtGui, QtCore, QtOpenGL
import vispy.opengl as opengl

import OpenGL.GL as gl 
import OpenGL.GLU as glu
from globjects import TextureObject, Shader, RenderTexture, FrameBuffer


vertex_shader = """
#version 120

attribute vec3 in_position;
attribute vec4 in_color;
attribute float in_width;
attribute float in_connect;
uniform mat4 transform;
uniform mat4 view_transform;

varying vec4 color;
varying vec4 position;
varying float width;
varying float connect;

void main(void) 
{
    gl_Position = transform * vec4(
        in_position,
        1.0
        );
        
    // pass expected window position to fragment shader 
    // so it knows how far from the center of the line it is
    position = view_transform * gl_Position; 
    color = in_color;
    width = in_width;
    connect = in_connect;
}
"""

fragment_shader = """
#version 120

varying vec4 color;
varying vec4 position;
varying float width;
varying float connect;

void main(void) 
{
    if (connect < 1.0)
        discard;
    float w = width*0.5 - 0.7071;
    float dist = length(vec3(position - gl_FragCoord));
    float d1 = dist - w;
    d1 = d1 > 1.4142 ? 1.4142 : (d1 < 0.0 ? 0.0 : d1);
    float d2 = -dist - w;
    d2 = d2 > 1.4142 ? 1.4142 : (d2 < 0.0 ? 0.0 : d2);
    
    float d = (1.4142 - (d1 + d2)) / 1.4142;
    d = pow(d, 0.7);  // would be different for each monitor..
    
    gl_FragColor = color;
    
    gl_FragColor[3] = color[3] * float(d>0.1);
    gl_FragColor.a = 1.0 * float((d>0.0) || (d<=0.0));
    //gl_FragColor[3] = color[3] * d;
}
"""





class PlotLine:
    def __init__(self, pos, color, width, connect):
        self.data = np.empty(pos.shape[0], dtype=[
            ('pos', pos.dtype, pos.shape[-1]),
            ('color', color.dtype, color.shape[-1]),
            ('width', width.dtype),
            ('connect', connect.dtype),
            ])
        self.data['pos'] = pos
        self.data['color'] = color
        self.data['width'] = width
        self.data['connect'] = connect
        
    def init_gl(self):
        self.program = opengl.ShaderProgram(
            opengl.VertexShader(vertex_shader),
            opengl.FragmentShader(fragment_shader),
            )
        
        self.update_buffers()
        
    def update_buffers(self):
        self.width_max = self.data['width'].max()
        self.vbo = opengl.Buffer(data=self.data)
        
    def draw(self, transform, view_transform):
        self.program.bind()
        
        
        self.program['transform'] = transform
        ## maps final clipping rect to viewport coordinates (needed for antialiasing)
        self.program['view_transform'] = view_transform

        self.program['in_position'] = self.vbo['pos']
        self.program['in_color'] = self.vbo['color']
        self.program['in_width'] = self.vbo['width']
        self.program['in_connect'] = self.vbo['connect']
        
        #glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
        glLineWidth(self.width_max+1)

        glDrawArrays(GL_LINE_STRIP, 0, self.data.shape[0])

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        #glUseProgram(0)
        

class Window(QtOpenGL.QGLWidget):
    """Just a simple display window"""
    def __init__(self, visuals):
        self.zoom = 1.0
        self.visuals = visuals
        
        QtOpenGL.QGLWidget.__init__(self)
        self.resize(800,800)
        self.show()
        
    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        for visual in self.visuals:
            visual.init_gl()
        
        # Get AA shader
        fname = os.path.join(os.path.dirname(__file__), 'ddaa.glsl')
        DDAA_SHADER = open(fname , 'rb').read().decode('ascii', 'ignore')
        DDAA_SHADER0, DDAA_SHADER1, DDAA_SHADER2 = DDAA_SHADER.split('='*80)
        self._aaShader =  Shader(None, DDAA_SHADER0)
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
#         self._paint()
#         return
        
        W, H = self.width(), self.height()
        
        # Set up FBO
        fb = FrameBuffer(W, H)
        tex = RenderTexture(2)
        tex.create_empty_texture(W, H) # Must match depth buffer!
        fb.attach_texture(tex)
        fb.add_depth_buffer()
        fb.check()
        
        # Draw scene to off-screen buffer
        fb.enable()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self._setup_scene(0,0,W,H)
        self._paint()
        fb.disable()
        
    
        # Draw texture to screen
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self._setup_scene(0,0,W,H)
        tex.Enable(0)
        self._aaShader.bind()
        #shader.uniformi('texture', tex._texId)
        self._aaShader.uniformf('shape', W, H)
        self._aaShader.uniformi('texture', 0)
        
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord(0,0); gl.glVertex(0,0); 
        gl.glTexCoord(0,1); gl.glVertex(0,1); 
        gl.glTexCoord(1,1); gl.glVertex(1,1); 
        gl.glTexCoord(1,0); gl.glVertex(1,0); 
        gl.glEnd()
        self._aaShader.unbind()
        tex.Disable()
    
    def _setup_scene(self, *args):
        gl.glViewport(*args);
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity();
        glu.gluOrtho2D(0.0, 1.0, 0.0, 1.0);
        gl.glMatrixMode(gl.GL_MODELVIEW);
        gl.glLoadIdentity();
        
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_BLEND)
    
    def _paint(self):
        transform = np.array([
            [self.zoom,0,0,0], 
            [0,self.zoom,0,0], 
            [0,0,1,0], 
            [0,0,0,1]
            ], dtype=np.float32)
        view_transform = np.array([
            [self.width()/2.,0,0,0], 
            [0,self.height()/2.,0,0], 
            [0,0,1,0], 
            [self.width()/2.,self.height()/2.,0,1]
            ], dtype=np.float32)
        for visual in self.visuals:
            visual.draw(transform, view_transform)
        
    def wheelEvent(self, ev):
        self.zoom *= 1.05 ** (ev.delta()/120.)
        self.update()

if __name__ == '__main__':
    app = QtGui.QApplication([])
    
    N = 5000
    pos = np.empty((N, 2), dtype=np.float32)
    pos[:,0] = np.linspace(-1, 1, N)
    pos[:,1] = np.sin(pos[:,0] * 15.) * 0.3 - 0.5
    #pos[:,1] = np.random.normal(size=N, scale=0.1)
    
    color = np.ones((N,4), dtype=np.float32)
    color[:,0] = np.linspace(0,1,N)
    
    connect = np.ones(N, dtype=np.float32)
    
    plots = []
    for i in range(3):
        
        width = np.ones(N, dtype=np.float32) * (i+1)#/2.
        #width = np.random.normal(size=N, scale=0.5, loc=3).astype(np.float32)
        plots.append(PlotLine(pos.copy(), color, width, connect))
        pos[:,1] += 0.5
        #connect[i::50] = 0
    
    win = Window(plots)
    app.exec_()

