
import math
import numpy as np

from .base import Camera
from vispy.util import transforms



class NDCCamera(Camera):
    """ Camera that presents a view on the world in normalized device
    coordinates (-1..1).
    """
    pass



class PixelCamera(Camera):
    """ Camera that presents a view on the world in pixel coordinates.
    The coordinates map directly to the viewport coordinates. The origin
    is in the upper left.
    """
    def get_projection(self, viewport):
        w, h = viewport.resolution
        from vispy.util import transforms
        projection = np.eye(4)
        transforms.scale(projection, 2.0/w, 2.0/h)
        transforms.translate(projection, -1, -1)
        transforms.scale(projection, 1, -1)  # Flip y-axis
        return projection



class TwoDCamera(Camera):
    def __init__(self, parent=None):
        Camera.__init__(self, parent)
        self.fov = 1, 1
    
    # xlim and ylim are convenience methods to set the view using limits
    @property
    def xlim(self):
        x = self.transform[-1, 0]
        dx = self.fov[0] / 2.0
        return x-dx, x+dx
    
    @property
    def ylim(self):
        y = self.transform[-1, 1]
        dy = self.fov[1] / 2.0
        return y-dy, y+dy
    
    @xlim.setter
    def xlim(self, value):
        x = 0.5 * (value[0] + value[1])
        rx = max(value) - min(value)
        self.fov = rx, self.fov[1]
        self.transform[-1,0] = x
    
    
    @ylim.setter
    def ylim(self, value):
        y = 0.5 * (value[0] + value[1])
        ry = max(value) - min(value)
        self.fov = self.fov[0], ry
        self.transform[-1,1] = y
    
        
    def get_projection(self, viewport):
        w, h = self.fov
        from vispy.util import transforms
        projection = np.eye(4)
        transforms.scale(projection, 2.0/w, 2.0/h)
        transforms.scale(projection, 1, -1)  # Flip y-axis
        return projection
        
    
    def on_mouse_press(self, event):
        pass
    
    def on_mouse_move(self, event):
        if event.is_dragging:
            
            # Get (or set) the reference position)
            if hasattr(event.press_event, 'reflim'):
                pos, fov = event.press_event.reflim
            else:
                pos = self.transform[-1,0], self.transform[-1,1]
                pos, fov = event.press_event.reflim = pos, self.fov
            
            # Get the delta position
            startpos = event.press_event.pos
            curpos = event.pos
            dpos = curpos[0] - startpos[0], curpos[1] - startpos[1] 
            
            if 1 in event.buttons:
                # Pan
                self.transform[-1,0] = pos[0] - dpos[0] / 2
                self.transform[-1,1] = pos[1] - dpos[1] / 2
                #dx, dy = -dpos[0] / 2, -dpos[1] / 2
                #self.xlim = xlim[0]+dx, xlim[1]+dx
                #self.ylim = ylim[0]+dy, ylim[1]+dy
            elif 2 in event.buttons:
                # Zoom
                self.fov = (    fov[0] - dpos[0] / 2,
                                fov[1] + dpos[1] / 2  )
                #dx, dy = -dpos[0] / 2, dpos[1] / 2
                #self.xlim = xlim[0]-dx, xlim[1]+dx
                #self.ylim = ylim[0]-dy, ylim[1]+dy
            
            # Force redraw
            event.source.update()



class ThreeDCamera(Camera):
    def __init__(self, parent=None):
        Camera.__init__(self, parent)
        
        self._pos = 200, 200, 200
        self._fov = 45.0
        
        self._view_az = -10.0 # azimuth
        self._view_el = 30.0 # elevation
        self._view_ro = 0.0 # roll
        self._fov = 0.0 # field of view - if 0, use ortho view
    
    def on_mouse_move(self, event):
        
        if not event.is_dragging:
            return
        
        if 1 in event.buttons:
            # rotate
            
            # Get (or set) the reference position)
            if hasattr(event.press_event, '_refangles'):
                refangles = event.press_event._refangles
            else:
                refangles = self._view_az, self._view_el, self._view_ro
                event.press_event._refangles = refangles
            
            # Get the delta position
            startpos = event.press_event.pos
            curpos = event.pos
            dpos = curpos[0] - startpos[0], curpos[1] - startpos[1] 
            
            # get normalized delta values
            sze = 400, 400 # todo: get from viewport
            d_az = dpos[0] / sze[0]
            d_el = dpos[1] / sze[1]
            
            # change az and el accordingly
            self._view_az = refangles[0] - d_az * 90.0
            self._view_el = refangles[1] + d_el * 90.0
            
            # keep within bounds            
            while self._view_az < -180:
                self._view_az += 360
            while self._view_az >180:
                self._view_az -= 360
            if self._view_el < -90:
                self._view_el = -90
            if self._view_el > 90:
                self._view_el = 90
            #print(self._view_az, self._view_el)
            
            # Init matrix 
            M = np.eye(4)
            
            
            
            
            # Move camera backwards to account for perspective
            # this should actually be triggered by change in fov.
            transforms.translate(M, 0, 0, self._d)
            
            # Rotate it
            transforms.rotate(M, self._view_ro, 0, 0, 1)
            transforms.rotate(M, 270-self._view_el, 1, 0, 0)
            transforms.rotate(M, -self._view_az, 0, 0, 1)
            
            # Translate it
            transforms.translate(M, *self._pos)
            
            # Translate it with previous transform
            # This should also work, because position and rotation 
            # are stored in different elements of the matrix ...
            
#             transforms.translate(M, self.transform[-1, 0],
#                                     self.transform[-1, 1],
#                                     self.transform[-1, 2])
            
            # Apply
            self._transform = M
    
    
    def get_projection(self, viewport):
        
        w, h = viewport.resolution
        
        fov = self._fov
        aspect = 1.0
        fx, fy = 600.0, 600.0 # todo: hard-coded
        
        # Calculate distance to center in order to have correct FoV and fy.
        if fov == 0:
            M = transforms.ortho(-0.5*fx, 0.5*fx, -0.5*fy, 0.5*fy, -10000, 10000)
            self._d = 0
        else:
            d = fy / (2 * math.tan(math.radians(fov)/2))
            val = math.sqrt(10000)  # math.sqrt(getDepthValue())
            znear, zfar = d/val, d*val
            M = transforms.perspective(fov, aspect, znear, zfar)
            self._d = d
            #transforms.translate(M, 0, 0, d)  # move camera backwards - done in on_mouse_move
        
        
        # Translation and rotation is done by our 'transformation' parameter
        
        return M
        



class FirstPersonCamera(Camera):
    
    def __init__(self, parent=None):
        Camera.__init__(self, parent)
        
        self._pos = 200, 200, 200
        self._fov = 45.0
        
        # todo: we probably want quaternions here ...
        self._view_az = -10.0 # azimuth
        self._view_el = 30.0 # elevation
        self._view_ro = 0.0 # roll
        self._fov = 0.0 # field of view - if 0, use ortho view
    
    
    def update_angles(self):
        """ Temporary method to turn angles into our transform matrix.
        """
            
        # Init matrix 
        M = np.eye(4)
        
        # Rotate it
        transforms.rotate(M, self._view_ro, 0, 0, 1)
        transforms.rotate(M, 270-self._view_el, 1, 0, 0)
        transforms.rotate(M, -self._view_az, 0, 0, 1)
        
        # Translate it
        transforms.translate(M, *self._pos)
        
        # Apply
        self._transform = M
    
    
    def get_projection(self, viewport):
        
        w, h = viewport.resolution
        
        fov = self._fov
        aspect = 1.0
        fx = fy = 1.0 # todo: hard-coded
        
        # Calculate distance to center in order to have correct FoV and fy.
        if fov == 0:
            M = transforms.ortho(-0.5*fx, 0.5*fx, -0.5*fy, 0.5*fy, -10000, 10000)
            self._d = 0
        else:
            d = fy / (2 * math.tan(math.radians(fov)/2))
            val = math.sqrt(10000)  # math.sqrt(getDepthValue())
            znear, zfar = d/val, d*val
            M = transforms.perspective(fov, aspect, znear, zfar)
        
        # Translation and rotation is done by our 'transformation' parameter
        
        return M
    
        