"""
This module implements the core classes for the vispy scenegraph. The
scenegraph is a graph of which the nodes are made up of Entity objects.

Some definitions:

* Scene graph: a weakly connected directed acyclic graph. There is
  typically one root node, but there can be multiple roots in some
  situations. The graph represents the hierarchy of transformations.
  
* Entity: a node in the scene graph, a "thing" inside the scene. Most
  entities are visible. Each entity has its own coordinate system. The
  transform attribute defines how its coordinate system is transformed
  from the coordinate system of the parent.

* ViewBox: An Entity whose purposes are to: 1) provide a rectangular
  region to render the scene within the viewbox to; 2) provide a
  user-definable transformation for rendering the scene within the
  viewbox (via a camera entity that is inside the viewbox itself); 3)
  provide clipping when rendering. --- The "scene within the viewbox"
  is simply the list of its children. As such, the total scenegraph is
  a complete graph without interruptions (i.e. contiguous). The way
  that a viewBox renders its scene may depend on the situations. The
  easiest would be to use glViewport and glScissor. Other options are
  to use an FBO, or chaining the scenes transformation with the viewbox'
  own transformations and then using fragment-clipping or a stencil
  buffer.

* Scene: The part of the scenegraph that is within a ViewBox. Any ViewBox
  is itself part of a scene (except the root ViewBox). The children of a
  ViewBox make up its "sub-scene". The "total scene" would be analogous
  to the whole scene graph.

* Camera: An entity in a scene that defines the viewpoint (by its position
  and orientation) and the projection (e.g. field of view, perspective, log, 
  polar, ...) with which the scene is projected onto the rectangular region
  of the viewbox.

* Visual: A component of an entity that specifies how that entity is drawn.
  A visual is passive and agnostic about the scene graph.

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
    
    Visual = None
    
    def __init__(self, parent=None, **kwargs):
        
        # Entities are organized in a parent-children hierarchy
        self._children = []
        self._parents = ()
        self._parent = None
        self.parent = parent
        
        # Components that all entities in vispy have
        self._transform = np.eye(4)
        self._visuals = {}
        self._visual_kwargs = kwargs
    
    
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
        """ The transform for this entity; how the local coordinate system
        is transformed with respect to the parent coordinate syste.
        Right now, this is simply a 4x4 matrix.
        """
        return self._transform
    
    
#     @property
#     def visual(self):
#         """ The visual object that can draw this entity. Can be None.
#         """
#         return self._visual
    
    
    def get_visual(self, root):
        """ Get the visual for this entity, based on the given root.
        May be overloaded to enable the use of multiple visuals.
        """
        if self.Visual is None:
            return None
        try:
            visual = self._visuals[id(root)]
        except KeyError:
            visual = self._visuals[id(root)] = self.Visual(**self._visual_kwargs)
        return visual



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
        # Default unit
        self._projection = np.eye(4)
    
    
    def get_projection(self, viewbox):
        """ Get the projection matrix. Should be overloaded by camera
        classes to define the projection of view.
        """
        return self._projection

    
    def on_mouse_press(self, event):
        pass
    
    def on_mouse_move(self, event):
        pass
    
    def get_camera_transform(self):
        """ Calculate the transformation matrix of the camera to the scene
        (i.e. the transformation is already inverted).
        This is used by the drawing system to establish the view matrix.
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
                break  # Root viewbox
            elif isinstance(object, ViewBox):
                break  # Go until the any parent ViewBox
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
        # todo: I don't like depending on np on this ...
        # glsl can do this for us too. Or is 4x4 matrix inversion easy?
        return np.linalg.inv(camtransform)



class ViewBox(Entity):
    """ The ViewBox acts as the "portal" from one scene to another. It
    is an Entity that exists in one scene, while exposing a view on
    another. Note that there is always at least one toploevel ViewBox
    that does not* live in a scene, but is attached to a canvas.
    
    The purpose of a viewbox is to: 1) provide a rectangular region to
    render the scene within the viewbox to; 2) provide a user-definable
    transformation for rendering the scene within the viewbox (via a
    camera entity that is inside the viewbox itself); 3) provide
    clipping when rendering.
    
    Each ViewBox has its own set of systems that operate on the ViewBox' 
    subscene.
    
    """
    
    def __init__(self, parent=None):
        Entity.__init__(self, parent)
        
        # Components of the ViewBox
        self._bgcolor = (0.0, 0.0, 0.0, 1.0)
        self._camera = None
        
        # Initialize systems
        self._systems = {}
        self._systems['draw'] = DrawingSystem()
    
    
    @property
    def bgcolor(self):
        """ The background color of the scene. within the viewbox.
        """
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
        the ViewBox.
        
        Note: it would perhaps make sense to call this "size", because
        for the CanvasWithScene, size and resolution are equal by
        definition. However, perhaps we want to give entities a "size"
        property later.
        """
        return int(self.transform[0,0]), int(self.transform[1,1])
    
    
    @property
    def camera(self):
        """ The camera associated with this viewbox. Can be None if there
        are no cameras in the scene.
        """
        if self._camera is None:
            cams = self.get_cameras()
            if cams:
                self._camera = cams[0]
        return self._camera
    
    @camera.setter
    def camera(self, value):
        if value not in self.get_cameras():
            raise ValueError('Given camera is not in the scene of the ViewBox.')
        self._camera = value
    
    
    def get_cameras(self):
        """ Get a list of all cameras that live in this scene.
        """
        def getcams(val):
            cams = []
            for entity in val:
                if isinstance(entity, Camera):
                    cams.append(entity)
                if isinstance(entity, ViewBox):
                    pass # Do not go into subscenes
                elif isinstance(entity, Entity):  # if, not elif!
                    cams.extend(getcams(entity))
            return cams
        
        return getcams(self)
    
    
    def process(self, root, *system_names):
        """ Process all systems.
        """
        if not system_names:
            # Process all
            for system in self._systems.values():
                system.process(self, root)
        else:
            # Process selection
            for system_name in system_names:
                self._systems[system_name].process(self, root)



# Imports for the Canvas subclass
from vispy import app
from vispy import app, gloo
gl = gloo.gl


class CanvasWithScene(app.Canvas):
    """ The CanvasWithScene class provides a window or widget that the
    root scene can be rendered to. It has a ViewBox instance for which
    the size is kept in sync with the underlying GL widget.
    """
    
    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self._viewbox = ViewBox()
    
    @property
    def viewbox(self):
        """ The root viewbox object for this canvas.
        """
        return self._viewbox
    
    def on_initialize(self, event):
        # Initialize opengl
        gl.glClearColor(0,0,0,1);
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    def on_resize(self, event):
        self._viewbox.transform[0,0] = event.size[0]
        self._viewbox.transform[1,1] = event.size[1]
    
    def on_paint(self, event):
        gl.glClearColor(0,0,0,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        #print('painting ...')
        
        # Draw viewbox
        self._process_entity_count = 0
        self._viewbox.process(self, 'draw')
        #print(self._process_entity_count)
    
    def on_mouse_move(self, event):
        # todo: we need a proper way to deal with events
        self._viewbox.camera.on_mouse_move(event)



class System(object):
    """ A system is an object that does stuff to the Entities in the
    scene. There is one system for each task and systems can be added
    dynamically (also custom ones) to perform specific tasks.
    
    A system typically operates on a specific subset of components of
    the Entities.
    """
    
    def __init__(self):
        pass
    
    
    def process(self, viewbox, root):
        """ Process the given viewbox.
        """
        if not isinstance(viewbox, ViewBox):
            raise ValueError('DrawingSystem.draw expects a ViewBox instance.')
        # Init and turn result into a tuple if necessary
        result = self._process_init(viewbox, root)
        if result is None: result = ()
        elif not isinstance(result, tuple): result = (result,)
        # Iterate over entities
        for entity in viewbox:
            self.process_entity(entity, *result)
    
    
    def process_entity(self, entity, *args):
        """ Process the given entity.
        """
        self._root._process_entity_count += 1
        #print('process', entity)
        # Process and turn result into a tuple if necessary
        result = self._process_entity(entity, *args)
        if result is None: result = ()
        elif not isinstance(result, tuple): result = (result,)
        # Iterate over sub entities
        for sub_entity in entity:
            sub_entity._parent = entity  # as promised in the docs of .parent
            self.process_entity(sub_entity, *result)
    
    
    def _process_init(self, viewbox, root):
        """ Called before the system starts processing. Overload this.
        """ 
        return ()
    
    def _process_entity(self, entity, *args):
        """ Called to process an entity. args is what was returned
        from processing the parent. Overload this.
        """
        return ()
    



class DrawingSystem(System):
    """ Simple implementation of a drawing engine.
    """
    
    def _process_init(self, viewbox, root):
        # Camera transform and projection are the same for the
        # entire scene
        self._camtransform = viewbox.camera.get_camera_transform()
        self._projection = viewbox.camera.get_projection(viewbox)
        # Prepare the viewbox (e.g. set up glViewport)
        self._prepare_viewbox(viewbox)
        # Store viewbox and root
        self._viewbox, self._root = viewbox, root
        # Return unit transform
        return np.eye(4)
    
    
    def _process_entity(self, entity, transform):
        #print('processing entity', entity)
        # Set transformation
        if entity.transform is not None:
            transform = np.dot(transform, entity.transform)
        # Store all components of the transform
        shaderTransforms = {}
        shaderTransforms['transform_model'] = transform
        shaderTransforms['transform_view'] = self._camtransform
        shaderTransforms['transform_projection'] = self._projection
        # Draw
        visual = entity.get_visual(self._root)
        if visual is not None:
            if visual.program is not None:
                visual.program.set_vars(shaderTransforms)
            visual.draw()
        # If a viewbox, render the subscene. 
        if isinstance(entity, ViewBox):
            entity.process(self._root, 'draw')
        # Return new transform
        return transform
    
    
    def _prepare_viewbox(self, viewbox):
        # print('preparing viewbox', viewbox )
        M = viewbox.transform
        w, h = int(M[0,0]), int(M[1,1])
        x, y = int(M[-1,0]), int(M[-1,1])
        
        need_FBO = False
        need_FBO |= bool( M[0,1] or M[0,2] or M[1,0] or M[1,2] or M[2,0] or M[2,1] )
        need_FBO |= (w,h) != viewbox.resolution
        
        # todo: take parent viewboxes into account.
        
        if need_FBO:
            # todo: we cannot use a viewbox or scissors, but need an FBO
            raise NotImplementedError('Need FBO to draw this viewbox')
        else:
            # nice rectangle, we can use viewbox and scissors
            gl.glViewport(x, y, w, h)
            gl.glScissor(x, y, w, h)
            gl.glEnable(gl.GL_SCISSOR_TEST)
            # Draw bgcolor
            gl.glClearColor(*viewbox.bgcolor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)


class EventSystem:
    pass


class SomeOtherSystem:
    pass
