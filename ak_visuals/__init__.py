""" Experimental version of the basis of the Visuals layer.
"""


class Visual(object):
    
    def __init__(self, parent=None):
        self._transforms = []
        self._children = []
        self._parent = None
        self.parent = parent
    
    
    @property
    def transforms(self):
        return self._transforms
    
    
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
        pass



class Camera(Visual):
    """ The Camera class defines the viewpoint from which a World of
    Visual objects is visualized. It is itself a Visual (with
    transformations) but by default does not draw anything.
    """
    def __init__(self, parent=None):
        Visual.__init__(self, parent)
        
        # Can be orthograpic, perspective, log, polar, map, etc.
        self._view_transform = None
    
    
    def apply_view(self):
        pass



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
        
        self._world = World()
        self._engine = MiniEngine()
        self._camera = None
    
    
    @property
    def world(self):
        return self._world
    
    
    @world.setter
    def world(self, world):
        if not isinstance(world, World):
            raise ValueError('Viewport.world must be a World instance.')
        self._world = world
    
    
    def get_cameras(self):
        
        def getcams(val):
            cams = []
            for visual in val:
                if isinstance(visual, Camera):
                    cams.append(visual)
                if isinstance(visual, Visual):  # if, not elif!
                    cams.extend(getcams(visual))
        
        return getcams(self.world)
    
    
    def draw(self):
        # todo: set viewport or draw to FBO
        self._engine.draw_world(self.world)



class MiniEngine:
    """ Simple implementation of a drawing engine.
    """
    
    def draw_world(self, world):
        for visual in world:
            self.draw_visual(visual)
    
    def draw_visual(self, visual):
        #todo: apply_transforms(visual.transforms)
        visual.draw()
        
        for sub in visual:
            self.draw_visual(sub)

