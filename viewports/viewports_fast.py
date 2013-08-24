"""
Demonstration of fast line plotting in multiple viewports, each having its own transform.
Uses texture data to specify clipping coordinates, allowing all viewports to be rendered in a single pass.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import vispy.util.ptime as ptime

import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
#from PyQt4 import QtGui, QtCore, QtOpenGL
import vispy.app
import vispy.opengl as opengl
import vispy.event

# vispy.app.use('qt')


vertex_shader = """
#version 120

attribute vec3 in_position;
varying float index;
uniform sampler2D viewports;

void main(void) 
{
    index = in_position.z;
    vec4 sr = texture2D(viewports, vec2(0.5, index));
    vec4 tr = texture2D(viewports, vec2(1, index));
    mat4 transform = mat4(
        vec4(sr.x, sr.y, 0, 0),
        vec4(sr.z, sr.w, 0, 0),
        vec4(0, 0, 1, 0),
        vec4(tr.x, tr.y, 0, 1)
        );
    gl_Position = transform * vec4(
        in_position.x,
        in_position.y,
        0.0,
        1.0
        );
}
"""

fragment_shader = """
#version 120

uniform vec4 color;
uniform sampler2D viewports;
varying float index;

void main(void) 
{
    vec4 viewport = texture2D(viewports, vec2(0, index));
    if( gl_FragCoord.x < viewport.x || gl_FragCoord.x > viewport.x+viewport.z)
        discard;
    if( gl_FragCoord.y < viewport.y || gl_FragCoord.y > viewport.y+viewport.w)
        discard;

    gl_FragColor = color;
}
"""





class PlotLines:
    def __init__(self, pos, color, width, viewports):
        self.data = np.empty(pos.shape[0], dtype=[
            ('pos', pos.dtype, pos.shape[-1]),
            ])
        self.data['pos'] = pos
        self.color = color
        self.width = width
        self.transform = np.eye(4)
        self.vbo = None
        self.initialized = False
        self.viewports = viewports
        
    def init_gl(self):
        self.program = opengl.ShaderProgram(
            opengl.VertexShader(vertex_shader),
            opengl.FragmentShader(fragment_shader),
            )
            
        self.vbo = opengl.DtypeVertexBuffer(data=self.data)

        glActiveTexture( GL_TEXTURE0 )
        self.tex = glGenTextures(1)
        glBindTexture( GL_TEXTURE_2D, self.tex )
        glPixelStorei( GL_UNPACK_ALIGNMENT, 1 )
        glPixelStorei( GL_PACK_ALIGNMENT, 1 )
        glTexParameterf( GL_TEXTURE_2D,
                            GL_TEXTURE_MIN_FILTER, GL_NEAREST )
        glTexParameterf( GL_TEXTURE_2D,
                            GL_TEXTURE_MAG_FILTER, GL_NEAREST )
        glTexParameterf( GL_TEXTURE_2D,
                            GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE )
        glTexParameterf( GL_TEXTURE_2D,
                            GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)

        self.set_data(self.data, self.viewports)
        self.initialized = True
        
    def set_data(self, data, viewports):
        if self.vbo is None:
            print('trying to set_data before gl init')
            return
        self.vbo.bind()
        try:
            self.vbo.set_data(data)
        finally:
            self.vbo.unbind()

        glActiveTexture( GL_TEXTURE0 )
        glBindTexture( GL_TEXTURE_2D, self.tex )
        glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA32F,
                         viewports.shape[1], viewports.shape[0], 
                         0, GL_RGBA, GL_FLOAT, viewports )

        
    def draw(self):
        if not self.initialized:
            self.init_gl()
        self.program.bind()

        self.program['in_position'] = self.vbo['pos']
        self.program['color'] = self.color
        self.program['viewports'] = 0
        
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
        glLineWidth(self.width)

        glDrawArrays(GL_LINE_STRIP, 0, self.data.shape[0])

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glUseProgram(0)





class Viewport(object):
    """Rectangular sub-region of a canvas."""
    def __init__(self, canvas, region):
        self.region = region
        self.canvas = canvas
        self.visuals = []
        self.transform = np.eye(4)

    def add_visual(self, vis):
        self.visuals.append(vis)

    def draw(self):
        glViewport(*self.region)
        for visual in self.visuals:
            visual.draw(self.transform)

        glColor4f(.4,.4,.5,1)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glBegin(GL_LINE_LOOP)
        x = 1
        glVertex2f(-x, -x)
        glVertex2f( x, -x)
        glVertex2f( x,  x)
        glVertex2f(-x,  x)
        glEnd()






class Canvas(vispy.app.Canvas):
    """Just a simple display window"""
    def __init__(self):
        vispy.app.Canvas.__init__(self)
        
        self.visuals = []
        
        self.geometry = None, None, 800, 800
        self.fps = 0.0
        self.last_draw = None
        self.fps_iter = 0
        self.show()

    def add_visual(self, vis):
        self.visuals.append(vis)
        self.update()
        
    def on_initialize(self, ev):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        
    def on_resize(self, ev):
        glViewport(0, 0, *ev.size)

    def on_paint(self, ev):
        glClear(GL_COLOR_BUFFER_BIT)
        for visual in self.visuals:
            visual.draw()
        self.swap_buffers()
        
        now = ptime.time()
        if self.last_draw is None:
            self.last_draw = now
        else:
            dt = now - self.last_draw
            self.last_draw = now
            self.fps = 0.9*self.fps + 0.1/dt
            if self.fps_iter > 100:
                self.fps_iter = 0
                print('FPS: %0.2f' % self.fps)
            self.fps_iter += 1

    def on_key_press(self, ev):
        if ev.key == 'Escape':
            self.app.quit()
        else:
            print("key_press: %s  modifiers: %s  text: %s" % (ev.key, ev.modifiers, repr(ev.text)))
            try:
                print("scan code:", ev.native.nativeScanCode())
            except:
                pass







if __name__ == '__main__':
    import scipy.ndimage as ndi
    
    # Generate plot data
    rows = 10
    cols = 10
    npts = 10000
    pos = np.zeros((cols, rows, npts*2, 3), dtype=np.float32)
    pos[:,:,:,0] = np.linspace(-1, 1, npts*2).reshape(1,1,npts*2)
    pos[:,:,:,1] = np.nan
    pos[:,:,-1,1] = 0
    # pos[:,:,:,1] = np.sin(pos[:,:,:,0]*np.pi) + np.random.normal(size=(cols,rows,npts*2)) * 0.3
    
    win = Canvas()
    viewports = np.zeros((rows*cols, 3, 4), dtype=np.float32)
    vw = 800/cols
    vh = 800/rows
    for x in range(cols):
        for y in range(rows):
            region = (x*vw, y*vh, vw, vh)
            n = x*rows + y
            viewports[n][0] = region
            viewports[n][1] = [10*1.0/cols,0,0,0.9*1.0/rows] # scale/rotate
            viewports[n][2] = [(2*x - (cols-1.) + 0.5)/cols, (2*y - (rows-1.))/rows,0,0] # translate
            pos[x,y,:,2] = (n+0.5)/float(rows*cols)
    #pos[:,:,:,2] = .75
    plt = PlotLines(pos[:,:,:npts].reshape(rows*cols*npts,3), color=(1,1,1,.1), width=1., viewports=viewports)
    win.add_visual(plt)

    
    
    timer = vispy.app.Timer(interval=0.0)
    timer.start()
    ptr = 0
    step = npts/100

    @timer.connect
    def update(ev):
        global ptr, plots, pos
        # generate new data
        noise = np.random.normal(size=(cols,rows,step)) * 0.1
        lastframe = pos[:,:,ptr-1,1].reshape(cols,rows,1)
        pos[:,:,ptr:ptr+step,1] = np.clip(lastframe + noise, -1, 1)
        # copy to mirror location in circular buffer
        pos[:,:,ptr+npts:ptr+npts+step,1] = pos[:,:,ptr:ptr+step,1]
        ptr = (ptr+step) % npts
        # for x in range(cols):
        #     for y in range(rows):
        #         plots[x][y].set_data(pos[x,y,ptr:ptr+npts])
                # viewports[x][y].transform[3,0] = 1-ptr*viewports[x][y].transform[0,0]/float(npts)
        vp2 = viewports.copy()
        vp2[:,2,0] -= ptr*vp2[:,1,0]/float(npts)
        plt.set_data(pos[:,:,ptr:ptr+npts].reshape(rows*cols*npts,3), vp2)
        win.update()
        
    @win.events.key_press.connect
    def on_key(ev):
        if ev.key == 'Space':
            if timer.running:
                timer.stop()
            else:
                timer.start()
    
    vispy.app.run()
    


