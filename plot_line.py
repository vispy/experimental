"""
Basic demonstration of line plotting
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
#from PyQt4 import QtGui, QtCore, QtOpenGL
import vispy.app
#import vispy.opengl as opengl
import vispy.oogl as oogl
from vispy import gl

import vispy.event

vispy.app.use('qt')


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
    gl_FragColor[3] = color[3] * d;
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
        self.program = oogl.ShaderProgram(
            oogl.VertexShader(vertex_shader),
            oogl.FragmentShader(fragment_shader),
            )
            
        self.update_buffers()
        
    def update_buffers(self):
        self.width_max = self.data['width'].max()
        self.vbo = oogl.VertexBuffer(self.data)
        
    def draw(self, transform, view_transform):
        #self.program.bind()
        with self.program:
            
            self.program.uniforms['transform'] = transform
            ## maps final clipping rect to viewport coordinates (needed for antialiasing)
            self.program.uniforms['view_transform'] = view_transform

            self.program.attributes['in_position'] = self.vbo['pos']
            self.program.attributes['in_color'] = self.vbo['color']
            self.program.attributes['in_width'] = self.vbo['width']
            self.program.attributes['in_connect'] = self.vbo['connect']
            
            #glEnable(GL_LINE_SMOOTH)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            #glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
            glLineWidth(self.width_max+1)

            glDrawArrays(GL_LINE_STRIP, 0, self.data.shape[0])

            glBindBuffer(GL_ARRAY_BUFFER, 0)
        #glUseProgram(0)
        

class Canvas(vispy.app.Canvas):
    """Just a simple display window"""
    def __init__(self, visuals):
        vispy.app.Canvas.__init__(self)
        # automatically connected to self.on_smooth_wheel
        #self.events['smooth_wheel'] = SmoothWheelFilter(self)
        SmoothWheelFilter(self.events) # install an event filter providing 
                                       # smooth wheel events
        
        # need to limit frame rate when using pyglet--it will call paint
        # far too rapidly.
        self.events['limited_paint'] = FrameRateLimiter(self, limit=60.0)
        self.events.paint.disconnect((self, 'on_paint'))
        self.events.limited_paint.connect((self, 'on_paint'))
        
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.visuals = visuals
        
        #QtOpenGL.QGLWidget.__init__(self)
        self.geometry = None, None, 800, 800    #self.resize(800,800)
        self.show()
        
    def on_initialize(self, ev):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        for visual in self.visuals:
            visual.init_gl()
        
    def on_resize(self, ev):
        glViewport(0, 0, *ev.size)

    def on_paint(self, ev):
        glClear(GL_COLOR_BUFFER_BIT)
        x,y,width,height = self.geometry
        transform = np.array([
            [self.zoom,0,0,0], 
            [0,self.zoom,0,0], 
            [0,0,1,0], 
            [self.pan[0],self.pan[1],0,1]
            ], dtype=np.float32)
        view_transform = np.array([
            [width/2.,0,0,0], 
            [0,height/2.,0,0], 
            [0,0,1,0], 
            [width/2.,height/2.,0,1]
            ], dtype=np.float32)
        for visual in self.visuals:
            visual.draw(transform, view_transform)
        self.swap_buffers()
        
    def on_mouse_press(self, ev):
        self.last_pos = ev.pos
        ev.handled = True  # required to ensure that we receive 
                           # mouse move and release events
        
    def on_mouse_move(self, ev):
        if not hasattr(self, 'last_pos'):
            return  # Pyglet also fires mouse_move when not first pressed
        x,y,w,h = self.geometry
        scale = (2./w, 2./h)
        self.pan = [
            self.pan[0] + scale[0] * (ev.pos[0] - self.last_pos[0]),
            self.pan[1] - scale[1] * (ev.pos[1] - self.last_pos[1])]
        self.update()
        self.last_pos = ev.pos
        
    def on_smooth_wheel(self, ev):
        self.zoom *= 1.1 ** (ev.delta[1])
        self.update()

    def on_key_press(self, ev):
        if ev.key == 'Escape':
            'Quitting ..'
            self.app.quit()
        else:
            print("key_press: %s  modifiers: %s  text: %s" % (ev.key, ev.modifiers, repr(ev.text)))
            try:
                print("scan code:", ev.native.nativeScanCode())
            except:
                pass

        
class SmoothWheelEmitter(vispy.event.EventEmitter):
    """ Mouse wheel smoothing implemented as emitter """
    def __init__(self, source):
        vispy.event.EventEmitter.__init__(self,
                                          source=source,
                                          type='smooth_wheel',
                                          event_class=vispy.app.canvas.MouseEvent)
        self.timer = vispy.app.Timer(connect=self.timeout)
        self.wheel = 0
        self.wheel_target = 0
        source.events.mouse_wheel.connect(self.input_event)
    
    def input_event(self, ev):
        if ev.type == 'mouse_wheel':
            self.wheel_target += ev.delta[1]
            self.timeout()
            if not self.timer.running:
                self.timer.start(interval=0.015)
        
    def timeout(self, ev=None):
        delta = (self.wheel_target - self.wheel) * 0.1
        self.wheel += delta
        self(pos=(0,0), delta=delta)
        
        if abs(delta) < 0.01:
            self.timer.stop()

class SmoothWheelFilter:
    """ Mouse wheel smoothing implemented as filter from one emitter to another """
    def __init__(self, event_emitter):
        self._event_emitter = event_emitter
        self.timer = vispy.app.Timer(connect=self.timeout)
        self.wheel = 0
        self.wheel_target = 0
        self._event_emitter.mouse_wheel.connect(self.input_event)
        self._event_emitter.add(smooth_wheel=vispy.app.canvas.MouseEvent)
        
    
    def input_event(self, ev):
        if ev.type == 'mouse_wheel':# and vispy.keys.SHIFT in ev.modifiers: # uncomment to test modifiers
            self.wheel_target += ev.delta[1]
            self.timeout()
            if not self.timer.running:
                self.timer.start(interval=0.015)
        
    def timeout(self, ev=None):
        delta = (self.wheel_target - self.wheel) * 0.1
        self.wheel += delta
        self._event_emitter.smooth_wheel(pos=(0,0), delta=(0.0,delta))
        
        if abs(delta) < 0.01:
            self.timer.stop()


import vispy.util.ptime as ptime        
class FrameRateLimiter(vispy.event.EventEmitter):
    def __init__(self, source, limit=60):
        vispy.event.EventEmitter.__init__(self, source, type='limited_paint')
        source.events.paint.connect(self.input_event)
        self._interval = 1.0 / limit
        self.timer = vispy.app.Timer(connect=self.timeout)
        self._need_paint = False
        self._last_paint = None
        self._last_event = None
    
    def input_event(self, ev):
        self._last_event = ev
        self._need_paint = True
        self.timer.start(self._interval)
        # paint immediately if we can
        if self._last_paint is None or self._last_paint + self._interval < ptime.time():
            self.timeout()
        
    def timeout(self, ev=None):
        if self._need_paint:
            # todo: need to join all regions
            self._last_paint = ptime.time()
            self(self._last_event)
            self._need_paint = False
        else:
            self.timer.stop()
        

if __name__ == '__main__':
    
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
        
        width = np.ones(N, dtype=np.float32) * (i+1)/2.
        #width = np.random.normal(size=N, scale=0.5, loc=3).astype(np.float32)
        plots.append(PlotLine(pos.copy(), color, width, connect))
        pos[:,1] += 0.5
        #connect[i::50] = 0
    
    win = Canvas(plots)
    
    ## Connect to all events for debugging
    @win.events.connect
    def event(ev):
        pass #print( ev )
    
    vispy.app.run()
    


