




class VisualCollection(Visual):
    pass
    
class LineCollection(VisualCollection):
    # The vertex shader. We just declare the *types* of our variables.
    VERTEX_SHADER = """

    // Polymorphic variables. This code snippet will be overriden by Vispy.
    variable vec2 position;
    variable float line_width;
    variable float z;

    void main() {
        // The code for variable initialization will be inserted here by Vispy.
        gl_Position = vec4(position, z, 1.);
    }

    """
    
    # The fragment shader. We just declare the *types* of our variables.
    FRAGMENT_SHADER = """
    variable vec4 color;
    
    void main() {
        gl_FragColor = color;
    }
    """

    # Here, we specify the memory level of each variable. This can be changed
    # by the visual itself, or by the user, depending on the use case.
    VARIABLES = {
        'position': 'local',
        'line_width': 'global',
        'color': 'shared',
        'z': 'local_dynamic',
    }
    
    def __init__(self, positions=[], colors=[]):
        super(LineCollection, self).__init__(self)
        
        # We set the global variables here.
        self['line_width'] = 1.
        
        # Now we add a few elements in our collection.
        for position, color in zip(positions, colors):
            # Case 1: baking can occur here, resulting in three variables per iteration:
            # * V: a NumPy array with the values of all local variables
            # * U: a NumPy array with 1 element, or a dict, with the values of all shared v
            #      variables for the current element.
            # * I: a list of indices (offset at 0) for the index buffer, for the current element
            # In this case we can just do:
            #
            #   self.add(V, U, I)
            # 
            # Case 2. Otherwise, we can specify all variables expicitly.
            self.add(position=pos,  # a (N, 2) NumPy array.
                     z=np.zeros(pos.shape[0]),  # a (N,) array.
                     color=color,  # a tuple.
                     _index=None  # a special variable, with the indices for the index buffer
                     )
                     
            # self['varname'] can be get/set
            # * local variable ==> all concatenated buffers into a single NumPy array
            # * shared variable ==> all concatenated values (size=Nelements)
            # * global variable ==> a single value (scalar or tuple)
            
            # self[i]['varname'] can be get/set
            # * local variable ==> one NumPy Array
            # * shared variable ==> a single value (scalar or tuple)
            # * global variable ==> error?

    def draw(self):
        self.program.draw('line_strip', indices=self.index_buffer)

