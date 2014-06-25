### Alternative user-exposed API to create and reuse components

In the current implementation, a `VisualComponent` mixes two different things: the logic that describes what the component does, and the plumbing required to link variables to a visual's objects. I think a component should stick to the first thing. It should be the job of the `Visual` to take a component, and plumb the variables to its own objects. What if, in the `WobbleComponent`, I want `theta` to be a uniform in visual A, but an attribute in visual B?

Here is an example: I want to create a reusable `WobbleComponent`. All I want to provide is really just this bit of code (just a string!):

```python
WobbleComponent = Component('''
    // My variables are here:
    float $theta = 0.;  // default value
    float $phase = 0.;  // default value

    vec4 main(vec4 pos) {
        float x = pos.x + 0.01 * cos($theta + $phase);
        float y = pos.y + 0.01 * sin($theta + $phase);
        return vec4(x, y, pos.z, pos.w);
    }
    ''')
```

Here I have all information I need to define my reusable component with some GLSL code (encapsulated in a function) and typed variables.

Now, say that I want to use that component in an existing visual. I should be able to do something like this:

```python
class MyVisual(Visual):
    # Using traits is a minor detail that is independent from the question
    # of visual components. It just shows a mechanism that can automatically
    # update a uniform whenever a Python variable is updated.
    WOBBLE_PHASE = Float(0.)  # a trait property with a default value
    
    def __init__(...):
        ...
        # note the use of "local_position" directly here
        # note also the use of + instead of a list (?)
        self.local_position = XYPosComponent(pos) + WobbleComponent(
                                    theta=np.array(...),  # automatically create attribute + VBO, but I could also create my VBO explicitly
                                    phase=self.WOBBLE_PHASE  # automatically create a uniform bound to the trait variable
                                    )
                                
    def wobble(self):
        self.WOBBLE_PHASE += .1  # automatically update the uniform
```
    
Now, a more complicated example. The complication comes from the fact that:

  * we need to deal with varying variables,
    
  * the component needs to know the distance along the line, which, in the current implementation, requires it to know the position and the current visual transformation.

I imagine that an example like this one motivated the current design where a visual component is a kind of "companion" class to the visual. I'm not sure that it's a good solution. To me, a visual component should really be isolated. I propose the following:

  * The DashComponent accepts a generic float `$distance` variable.
    
  * We implement a reusable standalone function that computes the distance along a line (takes a `N*D` array in transformed coordinates).
    
  * We let a visual link the `$distance` variable of the component to the distance along the line.
    
Also, for the varying, I propose an interface that abstracts that complication away (but good luck with the implementation! ;)).
    
More precisely:
    
```python
DashComponent = Component('''
    const M_PI = 3.14159265358979323846;
    float $distance = 0.;
    float $dash_len = 20.;

    vec4 main(vec4 color) {
        float mod = $distance / $dash_len;
        mod = mod - int(mod);
        color.a = 0.5 * sin(2*M_PI * mod) + 0.5;
        return color;
    }
''')
    
class MyVisual(Visual):
    def set_pos(self, pos):
        self.pos = pos
        # ...
        # If you want that logic to be encapsulated somewhere,
        # what about creating a mixin that implements a method
        # `set_curvilinear()`?
        pixel_tr = STTransform(scale=(400, 400)) * self.transform
        pixel_pos = pixel_tr.map(self.pos)
        self.curvilinear = curvilinear_abscissa(pixel_pos)

    def __init__(...):
        ...
        self.set_pos(pos)
        self.dash = DashComponent(distance=self.curvilinear)
        self.frag_color = VertexColorComponent(color) + self.dash
```
            
Note how all the varying-related plumbing is gone. Ideally, that should be taken care of automatically by Vispy. I have provided all necessary information here. My `DashComponent` is being used in `frag_color`, i.e. the fragment shader, and its variable `distance` is linked to a NumPy array. It means that an attribute + a varying need to be automatically created so that the dash component can receive the information.

