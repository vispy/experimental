""" Just a few Visuals to play with.
"""

import numpy as np
from vispy import app, gloo
gl = gloo.gl

from vispy_experimental import ak_visuals as visuals
from vispy.util import transforms


class PointsVisual(visuals.Visual):
    
    VERT_SHADER = """
        // Stuff that each visual must have ...
        uniform   mat4 transform_model;
        uniform   mat4 transform_view;
        uniform   mat4 transform_projection;


        attribute vec3 a_position;
        
        varying vec4 v_color;
        void main (void) {
            gl_Position = vec4(a_position, 1.0);
            gl_Position = transform_projection * transform_view 
                        * transform_model * gl_Position;
            v_color = vec4(1.0, 0.5, 0.0, 0.8);
            gl_PointSize = 10.0; //size;
        }
    """
    
    FRAG_SHADER = """
        varying vec4 v_color;
        void main()
        {    
            float x = 2.0*gl_PointCoord.x - 1.0;
            float y = 2.0*gl_PointCoord.y - 1.0;
            float a = 1.0 - (x*x + y*y);
            gl_FragColor = vec4(v_color.rgb, a*v_color.a);
        }
        
    """

    def __init__(self, parent, N=1000):
        visuals.Visual.__init__(self, parent)
        
        data = np.random.uniform(0, 400, (N,3)).astype('float32')
        
        self.program = gloo.Program(self.VERT_SHADER, self.FRAG_SHADER)
        self.program['a_position'] = gloo.VertexBuffer(data)
        
        
    def draw(self):
        visuals.Visual.draw(self)
        self.program.draw('POINTS')
