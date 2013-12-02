

class Entity:
    def __init__(self):
        self.transform = []
        self._children = []
        self._parent = None
        


class LineEntity(Entity):
    def __init__(self, data):
        self._data = data
        self.visual = LineVisual(self._data)
        
class MarkerEntity(Entity):
    def __init__(self, data):
        self._data = data
        self.visual = MarkerVisual(self._data)


class PlotEntity(Entity):
    def __init__(self, data):
        self.visual = None
        self.children.append(LineEntity(data))
        self.children.append(MarkerEntity(data)


class CameraEntity(Entity):
    def __init__(self):
        self.visual = None
    
    def get_projection(self):
        pass


class System():
    pass

class DrawingSystem(System):
    def process(self):
        
        for entity in world:
            if entity.visual is not None:
                entity.visual.draw()
            for sub_entity in entity.children:
                ...
            
    