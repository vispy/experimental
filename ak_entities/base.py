import numpy as np


class Entity(object):
    """ Base class to represent a citizen of a World object. Typically
    an Entity is used to visualize something, although this is not
    strictly necessary. It may for instance also be used as a container
    to apply a certain transformation to a group of objects, or a camera
    object.
    """
    
    def __init__(self, parent=None):
        
        # Entities are organized in a parent-children hierarchy
        self._children = []
        self._parent = None
        self.parent = parent
        
        # Components that all entities in vispy have
        self._transform = np.eye(4)
        self._visual = None
        
        # variables where temporary transforms are written by engine
        self._shaderTransforms = {} # todo: where to store this, or not store at all?
    
    
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
        elif isinstance(oldparent, (Entity, World)):
            oldlist = oldparent._children
        else:
            print('This should not happen: old parent was not an Entity or World')
        
        # Establish the new list we should add ourselves to
        newlist = None
        if value is None:
            pass
        elif value is self:
            raise ValueError('An Entity cannot have itself as parent.')
        elif isinstance(value, (Entity, World)):
            newlist = value._children
        else:
            raise ValueError('Entity.parent must be an Entity or world.')
        
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
    
    
    @property
    def transform(self):
        return self._transform
    
    @property
    def visual(self):
        return self._visual
    



class Camera(Entity):
    """ The Camera class defines the viewpoint from which a World is
    visualized. It is itself an Entity (with transformations) but by
    default does not draw anything.
    
    Next to the normal transformation, a camera also defines a
    projection tranformation that defines the camera view. This can for
    instance be orthographic, perspective, log, polar, etc.
    """
    
    def __init__(self, parent=None):
        Entity.__init__(self, parent)
        
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
        """ The the transformation matrix of the camera to the world
        (i.e. the transformation is already inverted).
        """
        # note: perhaps a camera should have a transform that can only 
        # translate and rotate... on the other hand, a parent entity
        # could have a scaling in it, so we need to remove the scaling anyway...
        
        # Get total transform of the camera
        object = self
        camtransform = object.transform.copy()
        
        while True:
            object = object.parent
            if not isinstance(object, Entity):
                break
            if object.transform is not None:
                camtransform[...] = np.dot(camtransform, object.transform)
        
        # We are only interested in translation and rotation,
        # to we set the scaling to unit
        camtransform[np.eye(4,dtype=np.bool)] = 1.0
        
        # Return inverse!
        return np.linalg.inv(camtransform)



class World(object):
    """ A World object represents a collection of Entities, that is used
    by one or more Viewports. A World is *not* an Entity itself.
    
    The abstraction of a world allows one collection of Entity objects
    to be shown in two Viewports. Whereas an Entity always has one parent,
    a World does not have the concept of a parent.
    
    """
    
    def __init__(self):
        # todo: a world should probably know which viewports use it
        self._children = []
    
    
    def __iter__(self):
        return self._children.__iter__()
    
    
    @property
    def children(self):
        return [c for c in self._children]
    
    
    def __repr__(self):
        return "<World populated with %i Entities>" % len(self._children)
    
    
    


class Viewport(Entity):
    """ The Viewport acts as the "portal" from one world to another.
    It is an Entity that exists in one world, while exposing a view on
    another. Note that there is always one toploevel Viewport that does
    *not* live in a world, but is attached to a canvas.
    
    Each ViewPort also has a camera associated with it.
    """
    
    def __init__(self, parent=None):
        Entity.__init__(self, parent)
        
        self._visual = ViewportVisual(self)
        
        # Components of the viewport
        self._bgcolor = (0.0, 0.0, 0.0, 1.0)
        self._world = World()
        
        self._engine = DrawingSystem()
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
        """ The number of pixels (in x and y) that are avalailable in
        the viewport.
        
        Note: it would perhaps make sense to call this "size", because for
        the Figure, size and resolution are equal by definition. However,
        perhaps we want to give entities a "size" property later.
        """
        return int(self.transform[0,0]), int(self.transform[1,1])
    
    
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
            for entity in val:
                if isinstance(entity, Camera):
                    cams.append(entity)
                if isinstance(entity, Entity):  # if, not elif!
                    cams.extend(getcams(entity))
            return cams
        
        return getcams(self.world)
    
    def process(self):
        self._engine.process(self)
        #self._eventSystem.process(self)
        # etc. ...



class ViewportVisual:
    """ the thing that draws a viewport.
    """
    def __init__(self, vieport):
        self._viewport = vieport
        self.program = None
    
    
    def draw(self):
        M = self._viewport.transform
        w, h = int(M[0,0]), int(M[1,1])
        x, y = int(M[-1,0]), int(M[-1,1])
        
        need_FBO = False
        need_FBO |= bool( M[0,1] or M[0,2] or M[1,0] or M[1,2] or M[2,0] or M[2,1] )
        need_FBO |= (w,h) != self._viewport.resolution
        
        if need_FBO:
            # todo: we cannot use a viewport or scissors, but need an FBO
            raise NotImplementedError('Need FBO to draw this viewport')
        else:
            # nice rectangle, we can use viewport and scissors
            gl.glViewport(x, y, w, h)
            gl.glScissor(x, y, w, h)
            gl.glEnable(gl.GL_SCISSOR_TEST)
            # Draw bgcolor
            gl.glClearColor(*self._viewport.bgcolor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
        self._viewport._engine.process(self._viewport)


from vispy import app
from vispy import app, gloo
gl = gloo.gl


class Figure(app.Canvas):
    """ The Figure class provides a region of screen that the root world
    can be rendered to. It has a Viewport instance for which the size
    is kept in sync with the underlying GL widget.
    """
    
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self._viewport = Viewport()
    
    @property
    def world(self):
        """ The world object of the root viewport.
        """
        return self._viewport.world
    
    @property
    def viewport(self):
        """ The root viewport object for this canvas.
        """
        return self._viewport
    
    def on_resize(self, event):
        self._viewport.transform[0,0] = event.size[0]
        self._viewport.transform[1,1] = event.size[1]
    
    def on_initialize(self, event):
        # todo: this must be done in the engine ...
        gl.glClearColor(0,0,0,1);
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    def on_paint(self, event):
        gl.glClearColor(0,0,0,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Draw viewport
        self._viewport.visual.draw()
        self._viewport.process()
    
    def on_mouse_move(self, event):
        # todo: we need a proper way to deal with events
        self._viewport.camera.on_mouse_move(event)



class System(object):
    """ A system is an object that does stuff to the Entities in the
    world. There is one system for each task and systems can be added
    dynamically (also custom ones) to perform specific tasks.
    
    A system typically operates on a specific subset of components of
    the Entities.
    """
    
    def __init__(self):
        pass
    
    
    def process(self, viewport):
        if not isinstance(viewport, Viewport):
            raise ValueError('DrawingSystem.draw expects a Viewport instance.')
        # Init and turn result into a tuple if necessary
        result = self._process_init(viewport)
        if result is None: result = ()
        elif not isinstance(result, tuple): result = (result,)
        # Iterate over entities
        for entity in viewport.world:
            self.process_entity(entity, *result)
    
    
    def process_entity(self, entity, *args):
        # Process and turn result into a tuple if necessary
        result = self._process_entity(entity, *args)
        if result is None: result = ()
        elif not isinstance(result, tuple): result = (result,)
        # Iterate over sub entities
        for sub_entity in entity:
            self.process_entity(sub_entity, *result)
    
    
    def _process_init(self, viewport):
        return ()
    
    def _process_entity(self, entity, *args):
        return ()
    



class DrawingSystem(System):
    """ Simple implementation of a drawing engine.
    """
    
    def _process_init(self, viewport):
        self._camtransform = viewport.camera.get_camera_transform()
        self._projection = viewport.camera.get_projection(viewport)
        return np.eye(4)
    
    
    def _process_entity(self, entity, transform):
        #print('processing entity', entity)
        # Set transformation
        if entity.transform is not None:
            transform = np.dot(transform, entity.transform)
        # Store all components of the transform
        entity._shaderTransforms['transform_model'] = transform
        entity._shaderTransforms['transform_view'] = self._camtransform
        entity._shaderTransforms['transform_projection'] = self._projection
        # Draw
        if entity.visual is not None:
            if entity.visual.program is not None:
                entity.visual.program.set_vars(entity._shaderTransforms)
            entity.visual.draw()
        return transform
    
    
#     def draw(self, viewport):
#         if not isinstance(viewport, BaseViewport):
#             raise ValueError('DrawingSystem.draw expects a Viewport instance.')
#         
#         camtransform = viewport.camera.get_camera_transform()
#         projection = viewport.camera.get_projection(viewport)
#         
#         def _draw_visual(visual, transform):
#             # Set transformation
#             if visual.transform is not None:
#                 transform = np.dot(transform, visual.transform)
#             # Store all components of the transform
#             visual._shaderTransforms['transform_model'] = transform
#             visual._shaderTransforms['transform_view'] = camtransform
#             visual._shaderTransforms['transform_projection'] = projection
#             # Draw
#             visual.draw()
#             # Process children
#             for sub in visual:
#                 _draw_visual(sub, transform)
#         
#         unittransform = np.eye(4)
#         for visual in viewport.world:
#             _draw_visual(visual, unittransform)


class EventSystem:
    pass

class SomeOtherSystem:
    pass
