
This simple example shows how to use VertexBuffer (glut-cube.py) and Collection
(glut-cubes.py).


The VertexBuffer allows to have several objects sharing the same
transformation.

The Collection allows to have several objects with their own transformations
and to draw them with a single call. The "trick" is to have a dedicated texture
that store object parameters and to extract them friom within the vertex
shader. There are modern OpenGL ways of doing the same thing but it is not
compatible with earlier GL versions.


Note that neither Vertexbuffer nor Collection assumes anything about the object
structure. They're merly container in charge of syncinc buffers betwen CPU and GPU.
Only the shader code knowns about what to do with attributes and uniforms.
