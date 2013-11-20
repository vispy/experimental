""" Experimental version of the basis of the Visuals layer.
"""

import numpy as np



class Visual(object):
    """ Base class to represent a citizen of a World object. Typically
    a visual is used to visualize something, although this is not
    strictly necessary. It may for instance also be used as a container
    to apply a certain transformation to a group of objects.
    """
    
    def __init__(self, parent=None):
        self._transform = np.eye(4)
        self._children = []
        self._parent = None
        self.parent = parent
        
        self.program = None  
        # variables where temporary transforms are written by engine
        self._shaderTransforms = {}
    
    
    @property
    def transform(self):
        return self._transform
    
    
    @property
    def children(self):
        return [c for c in self._children]
    
    
    @property
    def parent(self):
        return self._parent
    
    @parent.setter
    def parent(self, value):
        
        # Establish old parent and old list where self was in
        oldparent = self.parent
        oldlist = None
        if oldparent is None:
            pass
        elif isinstance(oldparent, (Visual, World)):
            oldlist = oldparent._children
        else:
            print('This should not happen: old parent was not a Visual or World')
        
        # Establish the new list we should add ourselves to
        newlist = None
        if value is None:
            pass
        elif value is self:
            raise ValueError('A visual cannot have itself as parent.')
        elif isinstance(value, (Visual, World)):
            newlist = value._children
        else:
            raise ValueError('Visual.parent must be a visual or world.')
        
        # Remove from old list (and from new list just to be sure)
        if oldlist is not None:
            while self in oldlist:
                oldlist.remove(self)
        if newlist is not None:
            if newlist is not oldlist:
                while self in newlist:
                    newlist.remove(self)
        
        # Set parent and add to its list 
        self._parent = value
        if newlist is not None:
            newlist.append(self)
        
        # todo: Should we destroy GL objects (because we are removed)
#         # from an OpenGL context)? 
#         canvas1 = self.get_canvas()
#         canvas2 = value.get_canvas()
#         if canvas1 and (canvas1 is not canvas2):
#             self.clear_gl()

    
    def __iter__(self):
        return self._children.__iter__()
    
    
    #def traverse(self):
    
    
    def draw(self):
        """ Draw ouselves.
        """
        if self.program is not None:
            self.program.set_vars(self._shaderTransforms)



class Camera(Visual):
    """ The Camera class defines the viewpoint from which a World of
    Visual objects is visualized. It is itself a Visual (with
    transformations) but by default does not draw anything.
    """
    def __init__(self, parent=None):
        Visual.__init__(self, parent)
        
        # Can be orthograpic, perspective, log, polar, map, etc.
        self._projection = np.eye(4)
    
    
    def get_projection(self, viewport):
        return self._projection

    
    def on_mouse_press(self, event):
        pass
    
    def on_mouse_move(self, event):
        pass
    
    def draw(sef):
        pass


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


class World(object):
    """ Collection of visuals, that is used by one or more
    Viewports. A World is *not* a Visual.
    """
    
    def __init__(self):
        #Visual.__init__(self, None)
        self._children = []
    
    
    def __iter__(self):
        return self._children.__iter__()
    
    
    @property
    def children(self):
        return [c for c in self._children]
    
    
    def __repr__(self):
        return "<World populated with %i Visuals>" % len(self._children)
    
    
    


class Viewport(Visual):
    """ The Viewport defines a view on a world that is populated by
    Visual objects. It also has a camera associated with it, which
    is a Visual object in the world itself.
    
    There is one toplevel visual in each canvas.
    """
    
    def __init__(self, parent=None):
        Visual.__init__(self, parent)
        
        self.bgcolor = (0,0,0)
        
        self._size = 1, 1
        self._world = World()
        self._engine = MiniEngine()
        self._camera = None
    
    
    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, value):
        return int(M[0,0]), int(M[1,1])
        #self._size = value
    
    
    @property
    def world(self):
        return self._world
    
    
    @world.setter
    def world(self, world):
        if not isinstance(world, World):
            raise ValueError('Viewport.world must be a World instance.')
        self._world = world
    
    
    @property
    def camera(self):
        if self._camera is None:
            cams = self.get_cameras()
            if cams:
                self._camera = cams[0]
        return self._camera
    
    @camera.setter
    def camera(self, value):
        # todo: check whether given camera is in self.world
        self._camera = value
    
    
    def get_cameras(self):
        
        def getcams(val):
            cams = []
            for visual in val:
                if isinstance(visual, Camera):
                    cams.append(visual)
                if isinstance(visual, Visual):  # if, not elif!
                    cams.extend(getcams(visual))
            return cams
        
        return getcams(self.world)
        
    
    def draw(self):
        M = self.transform
        w, h = int(M[0,0]), int(M[1,1])
        x, y = int(M[-1,0]), int(M[-1,1])
        
        if M[0,1] or M[0,2] or M[1,0] or M[1,2] or M[2,0] or M[2,1]:
            pass # todo: we cannot use a viewport or scissors, but need an FBO
        else:
            # nice rectangle, we can use viewport and scissors
            gl.glViewport(x, y, w, h)
            gl.glScissor(x, y, w, h)
            gl.glEnable(gl.GL_SCISSOR_TEST)
            # Draw bgcolor
            gl.glClearColor(*(self.bgcolor+(1,)))
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
        self._engine.draw(self)


from vispy import app
from vispy import app, gloo
gl = gloo.gl

class Figure(app.Canvas):
    """ The Figure class represents the top-level object. It has a world
    with Visual objects (and a camera). And a Viewport object to look onto 
    that world.
    """
    
    def __init__(self, *args, **kwargs):
        self.viewport = Viewport()
        app.Canvas.__init__(self, *args, **kwargs)
    
    def on_initialize(self, event):
        # todo: this must be done in the engine ...
        gl.glClearColor(0,0,0,1);
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    def on_resize(self, event):
        width, height = event.size
        #gl.glViewport(0, 0, width, height)
        #self.viewport.size = width, height
        self.viewport.transform[0,0] = width
        self.viewport.transform[1,1] = height
    
    def on_paint(self, event):
        gl.glClearColor(0,0,0,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.viewport.draw()
    
    def on_mouse_move(self, event):
        self.viewport.camera.on_mouse_move(event)



class MiniEngine:
    """ Simple implementation of a drawing engine.
    """
    
    def draw(self, viewport):
        if not isinstance(viewport, Viewport):
            raise ValueError('MiniEngine.draw expects a Viewport instance.')
        
        # Get total transform of the camera
        # todo: this should probably be inverted and whatnot
        projection = viewport.camera.get_projection(viewport)
        object = viewport.camera
        camtransform = object.transform
        while True:
            object = object.parent
            if not isinstance(object, Visual):
                break
            if object.transform is not None:
                camtransform[...] = np.dot(camtransform, object.transform)
        
        # We are only interested in translation and rotation,
        # to we set the scaling to unit
        camtransform[np.eye(4,dtype=np.bool)] = 1.0
        
        def _draw_visual(visual, transform):
            # Set transformation
            if visual.transform is not None:
                transform = np.dot(transform, visual.transform)
            # Store all components of the transform
            visual._shaderTransforms['transform_model'] = transform
            visual._shaderTransforms['transform_view'] = camtransform
            visual._shaderTransforms['transform_projection'] = projection
            # Draw
            visual.draw()
            # Process children
            for sub in visual:
                _draw_visual(sub, transform)
        
        unittransform = np.eye(4)
        for visual in viewport.world:
            _draw_visual(visual, unittransform)

