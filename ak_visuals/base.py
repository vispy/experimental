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
    
    Next to the normal transformation, a camera also defines a
    projection tranformation that defines the camera view. This can for
    instance be orthogrpaic, perspective, log, polar, etc.
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
    
    def get_camera_transform(self):
        """ Get the absolute position of the camera in the world.
        Returns an (x,y,z) tuple.
        """
        # todo: perhaps a camera should have a transform that can only 
        # translate and rotate... on the other hand, a parent visual
        # could have a scaling in it, so we need to remove the scaling anyway...
        
        # Get total transform of the camera
        object = self
        camtransform = object.transform.copy()
        
        while True:
            object = object.parent
            if not isinstance(object, Visual):
                break
            if object.transform is not None:
                camtransform[...] = np.dot(camtransform, object.transform)
        
        # We are only interested in translation and rotation,
        # to we set the scaling to unit
        camtransform[np.eye(4,dtype=np.bool)] = 1.0
        
        # Return inverse!
        return np.linalg.inv(camtransform)


class World(object):
    """ Collection of visuals, that is used by one or more
    Viewports. A World is *not* a Visual itself.
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
    
    
    


class BaseViewport(object):
    """ The Viewport defines a view on a world that is populated by
    Visual objects. It also has a camera associated with it, which
    is a Visual object in the world itself.
    
    There is one toplevel visual in each canvas.
    """
    
    def __init__(self, parent=None):
        
        self._bgcolor = (0.0, 0.0, 0.0, 1.0)
        self._resolution = 1, 1
        self._world = World()
        self._engine = MiniEngine()
        self._camera = None
    
    
    @property
    def bgcolor(self):
        return self._bgcolor
    
    @bgcolor.setter
    def bgcolor(self, value):
        # Check / convert
        value = [float(v) for v in value]
        if len(value) < 3:
            raise ValueError('bgcolor must be 3 or 4 floats.')
        elif len(value) == 3:
            value.append(1.0)
        elif len(value) == 4:
            pass
        else:
            raise ValueError('bgcolor must be 3 or 4 floats.')
        # Set
        self._bgcolor = tuple(value)
    
    
    @property
    def resolution(self):
        return self._resolution
    
    
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
        w, h = self.resolution
        x, y = 0, 0
        
        # nice rectangle, we can use viewport and scissors
        gl.glViewport(x, y, w, h)
        gl.glScissor(x, y, w, h)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        # Draw bgcolor
        gl.glClearColor(*self.bgcolor)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        self._engine.draw(self)
    



class Viewport(Visual, BaseViewport):
    """ 
    """
    
    def __init__(self, parent=None):
        Visual.__init__(self, parent)
        BaseViewport.__init__(self, parent)
    
    
    @property
    def resolution(self):
        return self.transform[0,0], self.transform[1,1]
    
    
    def draw(self):
        M = self.transform
        w, h = int(M[0,0]), int(M[1,1])
        x, y = int(M[-1,0]), int(M[-1,1])
        
        need_FBO = False
        need_FBO |= bool( M[0,1] or M[0,2] or M[1,0] or M[1,2] or M[2,0] or M[2,1] )
        need_FBO |= (w,h) != self.resolution
        
        if need_FBO:
            # todo: we cannot use a viewport or scissors, but need an FBO
            raise NotImplementedError('Need FBO to draw this viewport')
        else:
            # nice rectangle, we can use viewport and scissors
            gl.glViewport(x, y, w, h)
            gl.glScissor(x, y, w, h)
            gl.glEnable(gl.GL_SCISSOR_TEST)
            # Draw bgcolor
            gl.glClearColor(*self.bgcolor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
        self._engine.draw(self)
    


from vispy import app
from vispy import app, gloo
gl = gloo.gl

class Figure(app.Canvas, BaseViewport):
    """ The Figure class represents the top-level object. It has a world
    with Visual objects (and a camera). And a Viewport object to look onto 
    that world.
    """
    
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        BaseViewport.__init__(self)
    
    def on_initialize(self, event):
        # todo: this must be done in the engine ...
        gl.glClearColor(0,0,0,1);
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    def on_resize(self, event):
        width, height = event.size
        #gl.glViewport(0, 0, width, height)
        #self.viewport.size = width, height
        self._resolution = width, height
    
    def on_paint(self, event):
        gl.glClearColor(0,0,0,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.draw()
    
    def on_mouse_move(self, event):
        self.camera.on_mouse_move(event)



class MiniEngine:
    """ Simple implementation of a drawing engine.
    This functionality should probably be separated from the visuals layer.
    """
    
    def draw(self, viewport):
        if not isinstance(viewport, BaseViewport):
            raise ValueError('MiniEngine.draw expects a Viewport instance.')
        
        camtransform = viewport.camera.get_camera_transform()
        projection = viewport.camera.get_projection(viewport)
        
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
