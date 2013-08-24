#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2013 Nicolas P. Rougier. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY NICOLAS P. ROUGIER ''AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL NICOLAS P. ROUGIER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Nicolas P. Rougier.
# -----------------------------------------------------------------------------
"""
A collection is a container for several objects having the same vertex
structure (dtype) and same uniforms type (utype). A collection allows to
manipulate objects individually but they can be rendered at once (single call).

Each object can have its own set of uniforms provided they are a combination of
floats.

"""
import re
import numpy as np
import OpenGL.GL as gl
from operator import mul
from vertex_buffer import VertexBuffer


# -----------------------------------------------------------------------------
def dtype_reduce(dtype, level=0, depth=0):
    """
    Try to reduce dtype up to a given level when it is possible

    dtype =  [ ('vertex',  [('x', 'f4'), ('y', 'f4'), ('z', 'f4')]),
               ('normal',  [('x', 'f4'), ('y', 'f4'), ('z', 'f4')]),
               ('color',   [('r', 'f4'), ('g', 'f4'), ('b', 'f4'), ('a', 'f4')])]

    level 0: ['color,vertex,normal,', 10, 'float32']
    level 1: [['color', 4, 'float32']
              ['normal', 3, 'float32']
              ['vertex', 3, 'float32']]
    """
    dtype = np.dtype(dtype)
    fields = dtype.fields
    
    # No fields
    if fields is None:
        if dtype.shape:
            count = reduce(mul, dtype.shape)
        else:
            count = 1
        size = dtype.itemsize/count
        if dtype.subdtype:
            name = str( dtype.subdtype[0] )
        else:
            name = str( dtype )
        return ['', count, name]
    else:
        items = []
        name = ''
        # Get reduced fields
        for key,value in fields.items():
            l =  dtype_reduce(value[0], level, depth+1)
            if type(l[0]) is str:
                items.append( [key, l[1], l[2]] )
            else:
                items.append( l )
            name += key+','

        # Check if we can reduce item list
        ctype = None
        count = 0
        for i,item in enumerate(items):
            # One item is a list, we cannot reduce
            if type(item[0]) is not str:
                return items
            else:
                if i==0:
                    ctype = item[2]
                    count += item[1]
                else:
                    if item[2] != ctype:
                        return items
                    count += item[1]
        if depth >= level:
            return [name, count, ctype]
        else:
            return items

# -----------------------------------------------------------------------------
class Object(object):
    def __init__(self, parent, vertices, indices, uniforms):
        self.parent = parent
        self.vertices = vertices
        self.indices  = indices
        self.uniforms = uniforms

    def __getitem__(self, key):
        if key in self.uniforms.dtype.names:
            return float(self.uniforms[key])
        raise KeyError

    def __setitem__(self, key, value):
        if key in self.uniforms.dtype.names:
            self.uniforms[key] = value
            parent.dirty = True
            return
        raise KeyError

    def __getattr__(self, name):
        if hasattr(self, 'uniforms'):
            uniforms = object.__getattribute__(self,'uniforms')
            if name in uniforms.dtype.names:
                return float(uniforms[name])
        return object.__getattribute__(self,name)

    def __setattr__(self, name, value):
        if hasattr(self, 'uniforms'):
            uniforms = object.__getattribute__(self,'uniforms')
            if name in uniforms.dtype.names:
                uniforms[name] = value
                parent.dirty = True
                return
        object.__setattr__(self, name, value)


# -----------------------------------------------------------------------------
class Collection(VertexBuffer):
    def __init__(self, vtype, utype):
        # Convert vtype to a list (in case it was already a dtype) such that we
        # can append new fields
        vtype = eval(str(np.dtype(vtype)))

        # Convert utype to a list (in case it was already a dtype) such that we
        # can append new fields
        utype = eval(str(np.dtype(utype)))

        # We add a uniform index to access uniform data from texture
        vtype.append( ('index', 'f4') )

        VertexBuffer.__init__(self, vtype)

        # Check if given utype is made of float32 only
        rutype = dtype_reduce(utype)
        if type(rutype[0]) is not str or rutype[2] != 'float32':
                print "Uniform type cannot de reduced to float32 only"
        else:
            count = rutype[1]
            size = count//4
            if count % 4:
                size += 1
                utype.append(('unnused', 'f4', size*4-count))

        self.uniforms_data = np.zeros((1,1), dtype=utype)
        self.uniforms_size = 0
        self.uniforms_capacity = 1
        self.uniforms_shape = None
        self._uniforms_id = 0



    def append(self, vertices, indices, uniforms):
        vertices = vertices.astype(self.vertices_data.dtype)
        indices  = indices.astype(self.indices_data.dtype)
        uniforms = uniforms.astype(self.uniforms_data.dtype)

        VertexBuffer.append(self, vertices, indices)

        # Test if current uniforms capacity is big enough to hold new data
        if self.uniforms_size + 1  >= self.uniforms_capacity:
            capacity = int(2**np.ceil(np.log2(self.uniforms_size + 1)))
            self.uniforms_data = np.resize( self.uniforms_data, (capacity,1) )
            self.uniforms_capacity = len(self.uniforms_data)

        # Add uniforms data
        ustart, uend = self.uniforms_size, self.uniforms_size+1
        self.uniforms_data[ustart] = uniforms

        # Keep track of new object
        vstart,vend,istart,iend = self.objects[-1]
        self.objects[-1] = self,vstart,vend,istart,iend,ustart,uend

        # Update uniforms size
        self.uniforms_size += 1

        self.dirty = True

        """
        # Update uniform index for all objects
        for i in range(len(self.objects)):
            vstart,vend,_,_,_,_ = self.objects[i]
            self.vertices_data[vstart:vend]['index'] = i/float(len(self.uniforms_data))
        """


    def get_uniforms(self):
        return self.uniforms_data[:self.uniforms_size]
    uniforms = property(get_uniforms)


    def get_uniforms_id(self):
        if not self._uniforms_id:
            self.upload()
        return self._uniforms_id
    uniforms_id = property(get_uniforms_id)

    def __getitem__(self, key):
        vstart,vend,istart,iend,ustart,uend = self.objects[key]
        return Object( self,
                       self.vertices_data[vstart:vend],      
                       self.indices_data[istart:iend]-vstart,
                       self.uniforms_data[ustart:uend] )

    def __delitem__(self, key):
        _,vstart,vend,istart,iend,ustart,uend = self.objects[key]
        vsize = self.vertices_size-vend
        usize = self.uniforms_size-tend
        isize = self.indices_size-iend
        VertexBuffer.__delitem__(self,key)

        # Remove uniforms
        self.uniforms_data[ustart:ustart+usize] = self.uniforms_data[tend:tend+usize]
        self.uniforms_size -= 1

        # Update all subsequent objects 
        for i in range(key, len(self.objects)):
            _, _vstart,_vend,_istart,_iend,_ustart,_uend = self.objects[i]
            self.objects[i] = [self,                       \
                               _vstart-vsize, _vend-vsize, \
                               _istart-isize, _iend-isize, \
                               _ustart-usize, _uend-usize]

#        # Update uniform index for all objects
#        for i in range(len(self.objects)):
#            vstart,vend,_,_,_,_ = self.objects[i]
#            self.vertices_data[vstart:vend]['index'] = i/float(len(self.uniforms_data))

    def upload(self):

        # Update uniform index for all objects
        # TODO: vectorize
        for i in range(len(self.objects)):
            _,vstart,vend,_,_,_,_ = self.objects[i]
            self.vertices_data[vstart:vend]['index'] = i/float(len(self.uniforms_data))

        VertexBuffer.upload(self)

        if not self._uniforms_id:
            self._uniforms_id = gl.glGenTextures(1)
        gl.glActiveTexture( gl.GL_TEXTURE0 )
        gl.glPixelStorei( gl.GL_UNPACK_ALIGNMENT, 1 )
        gl.glPixelStorei( gl.GL_PACK_ALIGNMENT, 1 )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self._uniforms_id )
        gl.glTexParameterf( gl.GL_TEXTURE_2D,
                            gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST )
        gl.glTexParameterf( gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST )
        gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE )
        gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )

        data = self.uniforms_data.view(np.float32)
        self.uniforms_shape = data.shape[1]//4, data.shape[0]
        gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F_ARB,
                         data.shape[1]//4, data.shape[0], 0, gl.GL_RGBA, gl.GL_FLOAT, data )

