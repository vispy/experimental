#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
import os
import numpy as np
import OpenGL.GL as gl
from shader import Shader
from collection import Collection


# -----------------------------------------------------------------------------
class Scatter(Collection):
    # ---------------------------------
    def __init__(self):
        self.vtype = np.dtype([('a_center',    'f4', 3),
                               ('a_texcoord',  'f4', 2)])
        self.utype = np.dtype([('fg_color',    'f4', 4),
                               ('bg_color',    'f4', 4),
                               ('translate',   'f4', 3),
                               ('scale',       'f4', 1),
                               ('radius',      'f4', 1),
                               ('linewidth',   'f4', 1),
                               ('antialias',   'f4', 1)])
        Collection.__init__(self, self.vtype, self.utype)
        shaders = os.path.join(os.path.dirname(__file__),'.')
        vertex_shader= os.path.join( shaders, 'scatter.vert')
        fragment_shader= os.path.join( shaders, 'scatter.frag')
        self.shader = Shader( open(vertex_shader).read(),
                              open(fragment_shader).read() )



    # ---------------------------------
    def append( self, centers=(0, 0, 0), radius=3.0,
                fg_color=(0, 0, 0, 1), bg_color=(1, 1, 1, 1),
                linewidth=1.5, antialias=1.5,
                translate=(0, 0, 0), scale=1.0, rotate=0.0 ):

        centers = np.atleast_2d(np.array(centers))
        n = len(centers)
        V = np.zeros(4*n, self.vtype)
        U = np.zeros(n, self.utype)
        V['a_center'][0::4]  = centers
        V['a_center'][1::4] = V['a_center'][::4]
        V['a_center'][2::4] = V['a_center'][::4]
        V['a_center'][3::4] = V['a_center'][::4]
        V['a_texcoord'][0::4] = -1, -1
        V['a_texcoord'][1::4] = -1, +1
        V['a_texcoord'][2::4] = +1, -1
        V['a_texcoord'][3::4] = +1, +1
        U['fg_color'][:]  = fg_color
        U['bg_color'][:]  = bg_color
        U['radius'][:]    = radius
        U['scale'][:]     = scale
        U['linewidth'][:] = linewidth
        U['antialias'][:] = antialias
        I = np.resize(np.array([0,1,2,1,2,3], dtype=np.uint32), n*(2*3))
        Collection.append(self, V, I, U, (4,6) )
