## Visuals

A visual has properties that affect OpenGL objects such as attributes, uniforms, textures...
For instance, the "position" property can contain the data of the "position" attribute, but there's not necessarily a one-to-one mapping between a visual property and an OpenGL object. A TextVisual may have a "text" property that affect many objects (textures, VBOs...).

A visual can come with shader code. The code can be templated using jinja2 (widespread, pure Python, Python 2.6+ & 3.x, on GitHub, natively included in Anaconda, WinPython, ActivePython, canopy mandatory dependency for the IPython notebook). Template variables = visual properties. If statements possible in the code (might be faster than if in GLSL?).

## Chaining shaders
   
Define input and output variables, and code body

    // easing shift
    in vec2 i_pos;
    in float t;
    in float i_easing_c;
    in vec2 i_shift;
    out vec2 o_pos;
    void main(){
        o_pos = i_pos + i_shift * (1-exp(-i_easing_c * t));
    }
    
    // panning and zooming
    in vec2 i_pos;
    in vec2 i_pan;
    in vec2 i_zoom;
    out vec2 o_pos;
    void main(){
        o_pos = u_zoom * (a_position + u_pan);
    }
    

Variable
    name
    type
    
OutputVariable
InputVariable
    
ShaderNode:
    parents (other ShaderNode, or None if root)
    code_body
    vars_input (list of InputVariable)
    vars_output (list of OutputVariable)
  
ShaderGraph
    nodes
    uniforms = list of InputVariables
    attributes = list of InputVariables
    textures = list of InputVariables
    add_node(node, parents=[])
    compile()


Each visual has a shader snippet. In the ShaderGraph, the user concatenates shader snippets like Lego bricks and compiles the full shader. To add transformation to a visual, we just concatenate its shader node with the shader node of the transformation. The ShaderGraph checks that output of pre-node = input of post-node (same type, same name i_myvar=o_myvar only if there are 2+ inputs/outputs).

## Transformations

The user creates coordinate systems, assigns them to data or in relation to another coordinate system. In the latter case, one needs to provide two Python functions that take a NxD array (N points in R^D) and return a NxD' array (and conversely), as well as the equivalent GLSL snippet (vecD ==> vecD' and conversely). We can create templates for common transformations (e.g. AffineTransform with coefficients).

Then, a TransformManager keeps track of all defined coordinate systems (specified by their names). One can transform any data from any system to any other system. The scientific plotting lib will implement on top of this:

RawDataCoordinates
NormalizedDataCoordinates (on GPU)
ViewCoordinates (pan/zoom)
WindowCoordinates (pixels).

The last system can has a "ratio" property, that specifies how [-1,1] is mapped onto the pixels of the window (taking the width/height of the window into account).

## Worked example

A very simple example through the different layers.

### Plotting API (the one that people will actually use)

    x = np.random.randn(1000, 2)
    plt.scatter(x)
    plt.show()

### Visuals API

No panning/zooming here.

    x = np.random.randn(1000, 2)
    discs = DiscCollection(position=x, color='blue', size=10, lw=2, lc='black')
    
    @c.connect()
    def on_paint(event):
        discs.draw()
    
### Visuals API with scene graph

A SceneGraph contains a bunch of visuals, and a bunch of coordinate systems.
Each visual belongs to a coordinate system.
There are a few special builtin coordinate systems (the user can create new systems)

    UnitCoordinates: window = [-1, 1]^2 or [-r, r]^2 with ratio
    WindowCoordinates: window = [0, w] x [0, h]

These systems are universal, i.e. they are common to video games, art visualization, and scientific plotting. For scientific plotting, there are additional systems like DataCoordinates, NormalizedDataCoordinates and ViewCoordinates (zoom/pan).
    
    x = np.random.rand(1000, 2)
    discs = DiscCollection(position=x, color='blue', size=10, lw=2, lc='black')
    
    scene_graph = SceneGraph()
    scene_graph.add('scatter_plot_1', discs, coords='view')  # enable zoom/pan
    
    # what the line above is to add the visual to the scene graph, and assign
    # it to a coordinate system. When the user pans/zooms, the coordinate system
    # is updated, and the u_zoom and u_pan uniforms are updated. For all visuals
    # in this system, the vertex shader node
    # from the 'view' coordinate system is appended to the visual's shader node.

    @c.connect()
    def on_paint(event):
        scene_graph.
        scene_graph.draw()
    
    
    

    

