"""
This module implements the core classed of the vispy scenegraph. The
scenegraph is a graph of which the nodes are made up of Entity objects.

"""

import numpy as np


class Entity(object):
    """ Base class to represent a citizen of a scene. Typically an
    Entity is used to visualize something, although this is not strictly
    necessary. It may for instance also be used as a container to apply
    a certain transformation to a group of objects, or an object that
    performs a specific task without being visible.
    
    Each entity can have zero or more children. Each entity will
    typically have one parent, although multiple parents are allowed.
    It is recommended to use multi-parenting with care.
    """
    
    def __init__(self, parent=None):
        
        # Entities are organized in a parent-children hierarchy
        self._children = []
        self._parents = ()
        self._parent = None
        self.parent = parent
        
        # Components that all entities in vispy have
        self._transform = np.eye(4)
        self._visual = None
        
        # variables where temporary transforms are written by engine
        self._shaderTransforms = {} # todo: where to store this, or not store at all?
    
    
    @property
    def children(self):
        """ The list of children of this entity.
        """
        return [c for c in self._children]
    
    
    @property
    def parent(self):
        """ The parent entity. In case there are multiple parents,
        the first parent is given. During a draw, however, the parent
        from which the draw originated is given.
        """
        return self._parent
    
    @parent.setter
    def parent(self, value):
        if value is None:
            self.parents = ()
        else:
            self.parents = (value,)
    
    
    @property
    def parents(self):
        """ Get/set the tuple of parents. Typically the tuple will have
        one element. 
        """
        return self._parents
    
    @parents.setter
    def parents(self, parents):
        
        # Test input
        if not isinstance(parents, (tuple, list)):
            raise ValueError("Entity.parents must be a tuple of list.")
        
        # Test that all parents are entities
        for p in parents:
            if not isinstance(p, Entity):
                raise ValueError('A parent of an entity must be an entity too,'
                                 ' not %s.' % p.__class__.__name__)
        
        # Test that each parent occurs exactly once
        parentids = set([id(p) for p in parents])
        if len(parentids) != len(parents):
            raise ValueError('An entity cannot have thw same parent twice '
                             '(%r)' % self)
        
        # Remove from old parents (and from new parents just to be sure)
        oldparents = self.parents
        for oldparent in oldparents:
            while self in oldparent._children:
                oldparent._children.remove(self)
        for parent in parents:
            while self in parent._children:
                parnt._children.remove(self)
        
        # Set new parents and add ourself to their list of children
        self._parents = tuple(parents)
        for parent in parents:
            parent._children.append(self)
        
        # Set singleton parent
        self._parent = self._parents[0] if self._parents else None
        
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
    """ The Camera class defines the viewpoint from which a scene is
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
        """ The the transformation matrix of the camera to the scene
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
            if object is None:
                break  # Root viewport
            elif isinstance(object, Viewport):
                break  # Go until the any parent viewport
            assert isinstance(object, Entity)
            if object.transform is not None:
                camtransform[...] = np.dot(camtransform, object.transform)
        
        # We are only interested in translation and rotation,
        # so we set the scaling to unit
        #camtransform[np.eye(4,dtype=np.bool)] = 1.0
        # NO! This screws up rotations. So either we live with the fact 
        # that scaling also scales the camera view, or we find a real way
        # of normalizing the homography matrix for scale.
        
        # Return inverse!
        return np.linalg.inv(camtransform)



class Viewport(Entity):
    """ The Viewport acts as the "portal" from one scene to another.
    It is an Entity that exists in one scene, while exposing a view on
    another. Note that there is always one toploevel Viewport that does
    *not* live in a scene, but is attached to a canvas.
    
    Each ViewPort also has a camera associated with it.
    """
    
    def __init__(self, parent=None):
        Entity.__init__(self, parent)
        
        self._visual = ViewportVisual(self)
        
        # Components of the viewport
        self._bgcolor = (0.0, 0.0, 0.0, 1.0)
        
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
    def camera(self):
        if self._camera is None:
            cams = self.get_cameras()
            if cams:
                self._camera = cams[0]
        return self._camera
    
    @camera.setter
    def camera(self, value):
        # todo: check whether given camera is in self._children
        self._camera = value
    
    
    def get_cameras(self):
        
        def getcams(val):
            cams = []
            for entity in val:
                if isinstance(entity, Camera):
                    cams.append(entity)
                if isinstance(entity, Viewport):
                    pass # Do not go into subscenes
                elif isinstance(entity, Entity):  # if, not elif!
                    cams.extend(getcams(entity))
            return cams
        
        return getcams(self)
    
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


class CanvasWithScene(app.Canvas):
    """ The CanvasWithScene class provides a region of screen that the root scene
    can be rendered to. It has a Viewport instance for which the size
    is kept in sync with the underlying GL widget.
    """
    
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self._viewport = Viewport()
    
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
    scene. There is one system for each task and systems can be added
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
        for entity in viewport:
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
#         for visual in viewport:
#             _draw_visual(visual, unittransform)


class EventSystem:
    pass

class SomeOtherSystem:
    pass
