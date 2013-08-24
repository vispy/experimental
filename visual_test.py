"""
Basic demonstration of line plotting
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import vispy.app
from vispy.visuals import LineVisual
import vispy.shaders.transforms as transforms
from vispy import gl as gl

vispy.app.use('qt')


class Canvas(vispy.app.Canvas):
    """Just a simple display window"""
    def __init__(self, visuals):
        vispy.app.Canvas.__init__(self)
        
        self.region = np.array([[-5., -5.], [5., 5.]])
        self.visuals = visuals
        self.last_pos = None
        self._view_transform = transforms.STTransform()
        self._view_transform_dirty = True
        #for vis in visuals:
            #vis.my_item_transform = transforms.STTransform()
            #vis.transform = transforms.STTransform()
        #QtOpenGL.QGLWidget.__init__(self)
        self.geometry = None, None, 800, 800    #self.resize(800,800)
        self.show()
        
    def on_initialize(self, ev):
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        for visual in self.visuals:
            visual.init_gl()
        
    def on_resize(self, ev):
        gl.glViewport(0, 0, *ev.size)
        self._view_transform_dirty = True

    def on_paint(self, ev):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        for visual in self.visuals:
            #view_transform = transforms.STTransform(scale=(self.zoom, self.zoom), translate=self.pan)
            view_transform = self.view_transform()
            visual.transforms = [view_transform] + visual.my_transforms
                
            visual.draw()
        self.swap_buffers()
        
        
    def view_transform(self):
        target = np.array([[-1., -1.], [1., 1.]])
        #self._view_transform.translate = target[0] - self.region[0]
        scale = (target[1]-target[0]) / (self.region[1]-self.region[0])
        self._view_transform.scale = scale
        self._view_transform.translate = target[0] - (scale * self.region[0])
        return self._view_transform

    def on_mouse_press(self, ev):
        self.last_pos = ev.pos
        self._press_btn = ev.button
        ev.handled = True  # required to ensure that we receive 
                           # mouse move and release events
        
    def on_mouse_move(self, ev):
        if self.last_pos is None:
            return
        if self._press_btn == 1:
            x,y,w,h = self.geometry
            rgn_size = self.region[1] - self.region[0]
            self.region += np.array([
                -(ev.pos[0] - self.last_pos[0]) * rgn_size[0] / w, 
                (ev.pos[1] - self.last_pos[1]) * rgn_size[1] / h])
        elif self._press_btn == 2:
            center = self.region.mean(axis=0)
            d = self.region - center
            s = np.array([
                1.02 ** -(ev.pos[0] - self.last_pos[0]), 
                1.02 **  (ev.pos[1] - self.last_pos[1])])
            self.region = center + d * s
        self._view_transform_dirty = True
        self.update()
        self.last_pos = ev.pos

    def on_mouse_release(self, ev):
        self.last_pos = None
        
    def on_mouse_wheel(self, ev):
        #self.zoom *= 1.1 ** (ev.delta[1])
        center = self.region.mean(axis=0)
        dr = self.region[1] - center
        self.region[0] = center - dr * 1.1 ** -(ev.delta[1])
        self.region[1] = center + dr * 1.1 ** -(ev.delta[1])
        self._view_transform_dirty = True
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

        

if __name__ == '__main__':
    N = 5000
    pos = np.empty((N, 2), dtype=np.float32)
    pos[:,0] = np.linspace(-1, 1, N)
    pos[:,1] = np.sin(pos[:,0] * 15.) * 0.3
    #pos[:,1] = np.random.normal(size=N, scale=0.1)
    
    color = np.ones((N,4), dtype=np.float32)
    color[:,0] = np.linspace(0,1,N)
    color[:,3] = np.sin(pos[:,0] * 130.) * 0.5 + 0.5
    
    connect = np.ones(N, dtype=np.float32)
    
    plots = []
    
    # uniform color
    lv1 = LineVisual(pos=pos.copy(), color=(1,1,1,.1), width=1)
    lv1.my_transforms = [transforms.STTransform(translate=(0, -0.5))]
    # note: the name 'my_transforms' is just made up for the purposes
    # of this demonstration. The canvas picks up these transforma later
    # to build a chain.
    lv1._opts['mode'] = 'quality'
    
    # RGB color
    lv2 = LineVisual(pos=pos.copy(), color=color[:,:3], width=1)
    lv2.my_transforms = [transforms.STTransform(scale=(0.5, 0.5), translate=(0.0, 0.5))]
    
    # RGBA color
    lv3 = LineVisual(pos=pos.copy(), color=color, width=1)
    lv3.my_transforms = [transforms.LogTransform(base=(10., 0.)), transforms.STTransform(scale=(1, 1), translate=(1.0, 0))]
    
    win = Canvas([lv1, lv2, lv3])
    
    
    vispy.app.run()
    


