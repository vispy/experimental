# #!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code of this example should be considered public domain.

""" 
Illustration of the worldwind jitter problem. Press SPACE to increase the translation on both CPU and GPU, CTRL+SPACE to decrease it. The image should stay the same independently from the translation, but the worldwind jitter problem becomes visible at large values of the translation.
"""

from vispy import oogl
from vispy import app
from vispy import gl
from vispy import keys
import numpy as np

VERT_SHADER = """ // simple vertex shader
attribute vec2 a_position;
uniform float u_translation;
uniform float u_scale;
void main (void) {
    gl_Position = vec4(u_scale * (a_position.x - u_translation), a_position.y, 0.0, 1.0);
}
"""

FRAG_SHADER = """ // simple fragment shader
void main()
{    
    gl_FragColor = vec4(1., 1., 0., 1.);
}
"""

class Canvas(app.Canvas):
    translation = 1.
    scale = 1.
    def __init__(self):
        app.Canvas.__init__(self)
        self.position = (200, 100)
        self.size = (800, 500)
        self._program = oogl.Program(VERT_SHADER, FRAG_SHADER)
        self.dt = 1./1000
        self.n = 2000
        self._position = np.zeros((self.n, 2))
        self._position[:, 1] = .25 * np.random.randn(self.n)
        prog = self._program
        prog['a_position'] = oogl.VertexBuffer(self._position)
        prog['u_translation'] = self.translation
        prog['u_scale'] = self.scale
    
    def on_initialize(self, event):
        gl.glClearColor(0, 0, 0, 1)
    
    def on_resize(self, event):
        width, height = event.size
        gl.glViewport(0, 0, width, height)
    
    def on_key_press(self, event):
        # Zoom with CTRL+LEFT or CTRL+RIGHT
        if event.key in (keys.LEFT, keys.RIGHT):
            dir = 1 if event.key == keys.LEFT else -1
            self.scale *= .9 ** dir
        elif event.key == keys.SPACE:
            if keys.CONTROL in event.modifiers:
                self.translation /= 10.
            else:
                self.translation *= 10.
        print self.translation, self.scale
        self.update()
    
    def on_paint(self, event):
        # Simulate the case where x values on the GPU are between N-1, N+1
        # with N very large. Translation back to [-1,1] happens on the GPU
        self._position[:, 0] = np.arange(-1, 1, self.dt) + self.translation
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        with self._program as prog:
            prog['a_position'] = oogl.VertexBuffer(self._position)
            prog['u_translation'] = self.translation
            prog['u_scale'] = self.scale
            prog.draw_arrays(gl.GL_LINE_STRIP)
    
if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
