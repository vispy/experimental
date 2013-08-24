#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
import os
import numpy as np
import OpenGL.GL as gl
from shader import Shader
from dash_atlas import DashAtlas
from collection import Collection
from vertex_buffer import VertexAttribute


# -----------------------------------------------------------------------------
class DashLines(Collection):

    join = { 'miter' : 0,
             'round' : 1,
             'bevel' : 2 }
    caps = { ''             : 0,
             'none'         : 0,
             '.'            : 0,
             'round'        : 1,
             ')'            : 1,
             '('            : 1,
             'o'            : 1,
             'triangl in'  : 2,
             '<'            : 2,
             'triangle out' : 3,
             '>'            : 3,
             'square'       : 4,
             '='            : 4,
             'butt'         : 4,
             '|'            : 5 }


    # ---------------------------------
    def __init__(self):
        self.vtype = np.dtype([('a_curr',      'f4', 3),
                               ('a_texcoord',  'f4', 2)])
        self.utype = np.dtype([('fg_color',    'f4', 4),
                               ('length',      'f4', 1),
                               ('linewidth',   'f4', 1),
                               ('antialias',   'f4', 1),
                               ('dash_phase',  'f4', 1),
                               ('dash_period', 'f4', 1),
                               ('dash_index',  'f4', 1),
                               ('dash_caps',   'f4', 2)])
        Collection.__init__(self, self.vtype, self.utype)
        self.dash_atlas = DashAtlas()

        dsize = self.vbuffer._dsize
        a_curr = self.vbuffer.attribute('a_curr')
        a_texcoord = self.vbuffer.attribute('a_texcoord')
        a_index = self.vbuffer.attribute('a_index')
        a_next = VertexAttribute(
            'a_next', a_curr.count, a_curr.gltype, a_curr.stride, a_curr.offset)
        a_prev = VertexAttribute(
            'a_prev', a_curr.count, a_curr.gltype, a_curr.stride, a_curr.offset)
        self.attributes.extend([a_prev, a_next])
        a_index.offset    += 2*dsize
        a_curr.offset     += 2*dsize
        a_texcoord.offset += 2*dsize
        a_next.offset     += 4*dsize

        shaders = os.path.join(os.path.dirname(__file__),'.')
        vertex_shader= os.path.join( shaders, 'dash-lines.vert')
        fragment_shader= os.path.join( shaders, 'dash-lines.frag')
        self.shader = Shader( open(vertex_shader).read(),
                              open(fragment_shader).read() )



    # ---------------------------------
    def append( self, points,  fg_color=(0, 0, 0, 1),
                linewidth=1.0, antialias=1.0, dash_pattern='densely dashed',
                dash_phase = 0.0, dash_caps = ('round','round')):

        P = np.array(points).astype(np.float32)
        n = len(P)
        V = np.zeros(2*(n+2),self.vtype)
        U = np.zeros(1, self.utype)

        I = (np.ones((2*n-2,3),dtype=np.uint32)*[0,1,2]).ravel()
        I += np.repeat(np.arange(2*n-2),3)
        I = I.ravel()

        D = ((P[:-1]-P[1:])**2).sum(axis=1)
        D = np.sqrt(D).cumsum().astype(np.float32)

        U['fg_color'] = fg_color
        U['linewidth'] = linewidth
        U['antialias'] = antialias
        dash_index, dash_period = self.dash_atlas[dash_pattern]
        U['dash_phase']  = dash_phase
        U['dash_index']  = dash_index
        U['dash_period'] = dash_period
        U['dash_caps']   = (self.caps.get(dash_caps[0], 'round'),
                            self.caps.get(dash_caps[1], 'round'))
        U['length'] = D[-1]

        V['a_curr'][2:2+2*n:2] = P
        V['a_curr'][3:3+2*n:2] = P
        V['a_curr'][:2]  = P[0]  - (P[ 1] - P[ 0])
        V['a_curr'][-2:] = P[-1] + (P[-1] - P[-2])

        V['a_texcoord'][4:4+2*(n-1):2,0] = D
        V['a_texcoord'][5:5+2*(n-1):2,0] = D
        V['a_texcoord'][0::2,1] = -1
        V['a_texcoord'][1::2,1] = +1

        Collection.append(self, V, I, U )

    # ---------------------------------
    def draw(self, uniforms = {}):
        mode = gl.GL_TRIANGLES #_STRIP
        if self._dirty:
            self.upload()
        shader = self.shader
        shader.bind()

        gl.glActiveTexture( gl.GL_TEXTURE0 )
        shader.uniformi( 'u_uniforms', 0 )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self._ubuffer_id )
        if self.dash_atlas:
            gl.glActiveTexture( gl.GL_TEXTURE1 )
            shader.uniformi('u_dash_atlas', 1)
            gl.glBindTexture( gl.GL_TEXTURE_2D, self.dash_atlas.texture_id )

        for name,value in uniforms.items():
            shader.uniform(name, value)
        shader.uniformf('u_uniforms_shape', *self._ushape)
        self._vbuffer.draw(mode)
        shader.unbind()
