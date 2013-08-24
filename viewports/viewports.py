"""
Basic demonstration of line plotting in multiple viewports, each having its own transform.
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

#vispy.app.use('glut')


vertex_shader = """
#version 120

attribute vec3 in_position;
uniform mat4 transform;

void main(void) 
{
    gl_Position = transform * vec4(
        in_position,
        1.0
        );
}
"""

fragment_shader = """
#version 120

uniform vec4 color;

void main(void) 
{
    gl_FragColor = color;
}
"""





class PlotLine:
    def __init__(self, pos, color, width):
        self.data = np.empty(pos.shape[0], dtype=[
            ('pos', pos.dtype, pos.shape[-1]),
            ])
        self.data['pos'] = pos
        self.color = color
        self.width = width
        self.transform = np.eye(4)
        self.vbo = None
        self.initialized = False
        
    def init_gl(self):
        self.program = opengl.ShaderProgram(
            opengl.VertexShader(vertex_shader),
            opengl.FragmentShader(fragment_shader),
            )
            
        self.vbo = opengl.DtypeVertexBuffer(data=self.data)
        self.initialized = True
        
    def set_data(self, data):
        if self.vbo is None:
            print('trying to set_data before gl init')
            return
        self.vbo.bind()
        try:
            self.vbo.set_data(data)
        finally:
            self.vbo.unbind()
        
    def draw(self, transform):
        if not self.initialized:
            self.init_gl()
        self.program.bind()

        self.program['transform'] = np.dot(self.transform, transform)
        self.program['in_position'] = self.vbo['pos']
        self.program['color'] = self.color
        
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
    pos = np.zeros((cols, rows, npts*2, 2), dtype=np.float32)
    pos[:,:,:,0] = np.linspace(-1, 1, npts*2).reshape(1,1,npts*2)
    pos[:,:,:,1] = np.nan
    pos[:,:,-1,1] = 0
    # pos[:,:,:,1] = np.sin(pos[:,:,:,0]*np.pi) + np.random.normal(size=(cols,rows,npts*2)) * 0.3
    
    win = Canvas()

    vw = 800/cols
    vh = 800/rows
    viewports = []
    plots = []
    for x in range(cols):
        vcol = []
        pcol = []
        viewports.append(vcol)
        plots.append(pcol)
        for y in range(rows):
            region = (x*vw, y*vh, vw, vh)
            vp = Viewport(win, region)
            vp.transform[0,0] = 10.
            vp.transform[1,1] = 0.9
            vcol.append(vp)
            win.add_visual(vp)
            plt = PlotLine(pos[x,y,:npts], color=(1,1,1,.1), width=1)
            vp.add_visual(plt)
            pcol.append(plt)


    
    
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
        for x in range(cols):
            for y in range(rows):
                plots[x][y].set_data(pos[x,y,ptr:ptr+npts])
                viewports[x][y].transform[3,0] = 1-ptr*viewports[x][y].transform[0,0]/float(npts)
        win.update()
        
    @win.events.key_press.connect
    def on_key(ev):
        if ev.key == 'Space':
            if timer.running:
                timer.stop()
            else:
                timer.start()
    
    vispy.app.run()
    


