"""
Basic demonstration of line plotting
"""
import vispy.util.ptime as ptime

import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
#from PyQt4 import QtGui, QtCore, QtOpenGL
import vispy.app
import vispy.gloo as gloo
import vispy.util.event

#vispy.app.use('pyglet')


vertex_shader = """
attribute vec2 in_position;
uniform mat4 transform;

void main(void) 
{
    gl_Position = transform * vec4(
        in_position,
        0.0, 
        1.0
        );
}
"""

fragment_shader = """
uniform vec4 color;

void main(void) 
{
    gl_FragColor = color;
}
"""

class PlotLine:
    def __init__(self, pos, color, width):
        self.data = np.empty(pos.shape[0], dtype=[
            ('pos', np.float32, 2),
            ('color', np.float32, 4),
            ])
        self.program = gloo.Program(vertex_shader, fragment_shader)
        self.vbo = gloo.VertexBuffer(self.data)
        self.set_data(pos)
        self.set_color(color)
        #self.data['pos'] = pos
        #self.color = color
        self.width = width
        self.transform = np.eye(4,dtype=np.float32)
        
    def set_data(self, data):
        self.data['pos'][:] = data
        self.vbo.set_data(self.data)
        self.program['in_position'] = self.vbo['pos']

    def set_color(self, color):
        try:
            self.program['color'] = color
        except:
            print(self.color)
            raise
        
        
    def draw(self, transform):
        try:
            self.program['transform'] = np.dot(self.transform, transform)
            
            glEnable(GL_LINE_SMOOTH)
            glEnable(GL_BLEND)
            #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
            glLineWidth(self.width)
            self.program.draw(GL_LINE_STRIP)
        except:
            import sys, os
            print("=== Exiting due to paint error: ===")
            sys.excepthook(*sys.exc_info())
            os._exit(1)
        

class Canvas(vispy.app.Canvas):
    """Just a simple display window"""
    def __init__(self, visuals):
        vispy.app.Canvas.__init__(self)
        # automatically connected to self.on_smooth_wheel
        self.events['smooth_wheel'] = SmoothWheelEmitter(self)
        
        # need to limit frame rate when using pyglet--it will call paint
        # far too rapidly.
        #self.events['limited_paint'] = FrameRateLimiter(self, limit=60.0)
        #self.events.paint.disconnect((self, 'on_paint'))
        #self.events.limited_paint.connect((self, 'on_paint'))
        
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.visuals = visuals
        
        self.last_pos = None
        
        self.size = (800, 800)
        self.fps = 0.0
        self.last_draw = None
        self.fps_iter = 0
        self.show()
        
    #def on_initialize(self, ev):
        #glClearColor(0.0, 0.0, 0.0, 0.0)
        #for visual in self.visuals:
            #visual.init_gl()
        
    def on_resize(self, ev):
        glViewport(0, 0, *ev.size)

    def on_paint(self, ev):
        glClear(GL_COLOR_BUFFER_BIT)
        width,height = self.size
        transform = np.array([
            [self.zoom,0,0,0], 
            [0,self.zoom,0,0], 
            [0,0,1,0], 
            [self.pan[0],self.pan[1],0,1]
            ], dtype=np.float32)
        for visual in self.visuals:
            visual.draw(transform)
        #self.swap_buffers()
        
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
        
    def on_mouse_press(self, ev):
        self.last_pos = ev.pos
        ev.handled = True  # required to ensure that we receive 
                           # mouse move and release events
        
    def on_mouse_move(self, ev):
        if self.last_pos is None:
            return
        w,h = self.size
        scale = (2./w, 2./h)
        self.pan = [
            self.pan[0] + scale[0] * (ev.pos[0] - self.last_pos[0]),
            self.pan[1] - scale[1] * (ev.pos[1] - self.last_pos[1])]
        self.update()
        self.last_pos = ev.pos

    def on_mouse_release(self, ev):
        self.last_pos = None
        
    def on_smooth_wheel(self, ev):
        self.zoom *= 1.1 ** (ev.delta[1])
        self.update()

    def on_key_press(self, ev):
        if ev.key == 'Escape':
            self.app.quit()
        else:
            print("key_press: %s  modifiers: %s  text: %s" % (ev.key, ev.modifiers, repr(ev.text)))
            try:
                print("scan code:", ev.native.nativeScanCode())
            except:
                pass

        
import vispy.util.ptime as ptime        
class SmoothWheelEmitter(vispy.util.event.EventEmitter):
    """ Mouse wheel smoothing implemented as emitter """
    def __init__(self, source):
        vispy.util.event.EventEmitter.__init__(self,
                                          source=source,
                                          type='smooth_wheel',
                                          event_class=vispy.app.canvas.MouseEvent)
        self.timer = vispy.app.Timer(connect=self.timeout)
        self.speed = 5.0
        self.wheel = 0
        self.wheel_target = 0
        source.events.mouse_wheel.connect(self.input_event)
        self.last_time = None
    
    def input_event(self, ev):
        if ev.type == 'mouse_wheel':
            self.last_time = ptime.time()
            self.wheel_target += ev.delta[1]
            self.timeout()
            if not self.timer.running:
                self.timer.start(interval=0.015)
        
    def timeout(self, ev=None):
        now = ptime.time()
        dt = now - self.last_time
        self.last_time = now
        delta = (self.wheel_target - self.wheel) * (1.0-np.exp(-dt*self.speed))
        self.wheel += delta
        self(pos=(0,0), delta=(0,delta))
        
        if abs(self.wheel-self.wheel_target) < 0.01:
            self.timer.stop()



class FrameRateLimiter(vispy.util.event.EventEmitter):
    def __init__(self, source, limit=60):
        vispy.util.event.EventEmitter.__init__(self, source, type='limited_paint')
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
    import scipy.ndimage as ndi
    
    # Generate M trials of signal
    M = 100
    N = 10000
    pos = np.empty((M, N, 2), dtype=np.float32)
    pos[:,:,0] = np.linspace(-10, 10., N).reshape(1,N)
    pos[:,:,1] = np.sin(pos[:,:,0] * 10.) * 0.3
    pos[:,:,1] += np.sin((pos[:,:,0]+0.3) * 20.) * 0.15
    pos[:,:,1] += ndi.gaussian_filter(np.random.normal(size=(M,N))*0.2, (0.4, 8))
    pos[:,:,1] += ndi.gaussian_filter(np.random.normal(size=(M,N))*0.005, (0, 1))
    
    # find trigger locations
    trig = []
    for i in range(M):
        ind = np.argwhere((pos[i,1:,1]>0) & (pos[i,:-1,1]<0))[:,0]
        ind2 = np.argmin(np.abs(pos[i,1:,0][ind]))
        trig.append(ind[ind2]-(N/2.))
    
    alpha = np.linspace(0, 1, M)
    
    plots = []
    for i in range(M):
        plots.append(PlotLine(pos[i], color=(1, 1, 1, alpha[i]), width=2))
    
    win = Canvas(plots)
    
    timer = vispy.app.Timer(interval=0.0)
    timer.start()
    plot_ptr = 0
    data_ptr = 0
    
    @timer.connect
    def update(ev):
        global plot_ptr, data_ptr, plots, pos
        plots[plot_ptr].set_data(pos[data_ptr])
        tr = np.eye(4, dtype=np.float32)
        tr[3,0] = -trig[data_ptr] * 20./float(N)
        plots[plot_ptr].transform = tr
        for i in range(len(plots)):
            alpha = 0.5 * ((len(plots)-float(i))/len(plots))**8
            plots[(plot_ptr - i) % len(plots)].set_color((.1, 1.0, .1, alpha))
        data_ptr = (data_ptr + 1) % M
        plot_ptr = (plot_ptr + 1) % len(plots)
        win.update()
        
    @win.events.key_press.connect
    def on_key(ev):
        if ev.key == 'Space':
            if timer.running:
                timer.stop()
            else:
                timer.start()
    
    vispy.app.run()
    


