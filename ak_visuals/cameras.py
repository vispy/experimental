
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
        w, h = viewport.size
        from vispy.util import transforms
        projection = np.eye(4)
        transforms.scale(projection, 2.0/w, 2.0/h)
        transforms.translate(projection, -1, -1)
        transforms.scale(projection, 1, -1)  # Flip y-axis
        return projection


class TwoDCamera(Camera):
    def __init__(self, parent=None):
        Camera.__init__(self, parent)
        self.xlim = -1, 1
        self.ylim = -1, 1
    
    def get_projection(self, viewport):
        w, h = self.xlim[1] - self.xlim[0], self.ylim[1] - self.ylim[0]
        x, y = self.xlim[0], self.ylim[0]
        from vispy.util import transforms
        projection = np.eye(4)
        transforms.translate(projection, -x, -y)
        transforms.scale(projection, 2.0/w, 2.0/h)
        transforms.translate(projection, -1, -1)
        transforms.scale(projection, 1, -1)  # Flip y-axis
        return projection 
    
    
    def on_mouse_press(self, event):
        pass
    
    def on_mouse_move(self, event):
        if event.is_dragging:
            
            # Get (or set) the reference position)
            if hasattr(event.press_event, 'reflim'):
                xlim, ylim = event.press_event.reflim
            else:
                xlim, ylim = event.press_event.reflim = self.xlim, self.ylim
            
            # Get the delta position
            startpos = event.press_event.pos
            curpos = event.pos
            dpos = curpos[0] - startpos[0], curpos[1] - startpos[1] 
            
            if 1 in event.buttons:
                # Pan
                dx, dy = -dpos[0] / 2, -dpos[1] / 2
                self.xlim = xlim[0]+dx, xlim[1]+dx
                self.ylim = ylim[0]+dy, ylim[1]+dy
            elif 2 in event.buttons:
                # Zoom
                dx, dy = -dpos[0] / 2, dpos[1] / 2
                self.xlim = xlim[0]-dx, xlim[1]+dx
                self.ylim = ylim[0]-dy, ylim[1]+dy
            
            # Force redraw
            event.source.update()
