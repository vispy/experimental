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
import sys
import ctypes
import numpy as np
import OpenGL
import OpenGL.GL as gl


class VertexAttributeException(Exception):
    pass

class VertexAttribute(object):

    def __init__(self, name, count, gltype, stride, offset, normalized=False):
        self.index  = -1
        self.name   = name
        self.count  = count
        self.gltype = gltype
        self.stride = stride
        self.offset = ctypes.c_void_p(offset)
        self.normalized = normalized

    def enable(self):
        if self.index == -1:
            program = gl.glGetIntegerv( gl.GL_CURRENT_PROGRAM )
            if not program:
                return
            self.index = gl.glGetAttribLocation( program, self.name )
            if self.index == -1:
                return
        gl.glEnableVertexAttribArray( self.index )
        gl.glVertexAttribPointer( self.index, self.count, self.gltype,
                                  self.normalized, self.stride, self.offset )


class VertexBufferException(Exception):
    """ """
    pass

class VertexBuffer(object):

    def __init__(self, vertices, indices=None):

        self.vertices_data    = None
        self.vertices_size    = 0
        self.vertices_capcity = 0
        self.vertices_id      = 0

        self.indices_data     = None
        self.indices_size     = 0
        self.indices_capacity = 0
        self.indices_id       = 0

        self.objects = []
        self.dirty   = True


        """
        # In case we share vertices data with another object
        if type(vertices) is VertexBuffer:
            other = vertices
            self.vertices_data = other.vertices
            self.vertices_size = other.vertices_size
            self.vertices_capacity = other.vertices_capacity
            self.vertices_id = other.vertices_id
            self.attributes = other.attributes
            if indices is None:
                self.indices_data = other.indices
                self.indices_size = other.indices_size
                self.indices_size = other.indices_capacity
                self.indices_id = other.indices_id
            else:
                self.indices_data = indices.astype(np.uint32)
                self.indices_size = len(indices).astype(np.uint32)
                self.indices_id = gl.glGenBuffers(1)
                gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, self.indices_id )
                gl.glBufferData( gl.GL_ELEMENT_ARRAY_BUFFER, self.indices_data, gl.GL_STATIC_DRAW )
                gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, 0 )
            return
        """

        # Parse vertices dtype and generate attributes
        gltypes = { 'float32': gl.GL_FLOAT,
                    'float'  : gl.GL_DOUBLE, 'float64': gl.GL_DOUBLE,
                    'int8'   : gl.GL_BYTE,   'uint8'  : gl.GL_UNSIGNED_BYTE,
                    'int16'  : gl.GL_SHORT,  'uint16' : gl.GL_UNSIGNED_SHORT,
                    'int32'  : gl.GL_INT,    'uint32' : gl.GL_UNSIGNED_INT }

        if type(vertices) is np.ndarray:
            dtype = vertices.dtype
        else:
            dtype = np.dtype(vertices)

        names = dtype.names or []
        stride = dtype.itemsize
        offset = 0
        self.attributes = []
        for i,name in enumerate(names):
            if dtype[name].subdtype is not None:
                gtype = str(dtype[name].subdtype[0])
                count = reduce(lambda x,y:x*y, dtype[name].shape)
            else:
                gtype = str(dtype[name])
                count = 1
            if gtype not in gltypes.keys():
                raise VertexBufferException('Data type not understood')
            gltype = gltypes[gtype]
            attribute = VertexAttribute(name,count,gltype,stride,offset)
            self.attributes.append( attribute )
            offset += dtype[name].itemsize

        # Vertices data
        if type(vertices) is np.ndarray:
            self.vertices_data = vertices
            self.vertices_size = len(vertices)
            self.vertices_capacity = len(vertices)
            if indices is None:
                indices = np.arange( self.vertices_size, dtype=np.uint32 )
            self.indices_data = indices.astype(np.uint32)
            self.indices_size = len(indices)
            self.indices_capacity = len(indices)
        else:
            self.vertices_data = np.zeros(1,dtype)
            self.vertices_size = 0
            self.vertices_capacity = 1

            self.indices_data = np.zeros(1,np.uint32)
            self.indices_size = 0
            self.indices_capacity = 1
        self.vertices_id = gl.glGenBuffers(1)

        # Indices data
        self.indices_id = gl.glGenBuffers(1)


    def append(self, vertices, indices):
        """ """

        vertices = vertices.astype(self.vertices_data.dtype)
        indices  = indices.astype(self.indices_data.dtype)

        # Test if current vertices capacity is big enough to hold new data
        if self.vertices_size + vertices.size  >= self.vertices_capacity:
            capacity = int(2**np.ceil(np.log2(self.vertices_size + len(vertices))))
            self.vertices_data = np.resize(self.vertices_data, capacity)
            self.vertices_capacity = len(self.vertices_data)

        # Test if current indices capacity is big enough to hold new data
        if self.indices_size + indices.size  >= self.indices_capacity:
            capacity = int(2**np.ceil(np.log2(self.indices_size + len(indices))))
            self.indices_data = np.resize(self.indices_data, capacity)
            self.indices_capacity = len(self.indices_data)

        # Add vertices data
        vstart, vend = self.vertices_size, self.vertices_size+len(vertices)
        self.vertices_data[vstart:vend] = vertices.ravel()
        
        # Add indices data and update them relatively to vertices new place
        istart, iend = self.indices_size, self.indices_size+len(indices)
        self.indices_data[istart:iend] = indices.ravel() + self.vertices_size
        
        # Keep track of new object
        self.objects.append( (vstart,vend,istart,iend) )

        # Update vertices, indices and uniforms size
        self.vertices_size += vertices.size
        self.indices_size  += indices.size
        self.dirty = True

    def __delitem__(self, key):
        """
        """
        vstart,vend,istart,iend,ustart,uend = self.objects[key]
        del self.objects[key]

        # Remove vertices
        vsize = self.vertices_size-vend
        self.vertices_data[vstart:vstart+vsize] = self.vertices_data[vend:vend+vsize]
        self.vertices_size -= vsize

        # Remove indices and update remaining indices
        isize = self.indices_size-iend
        self.indices_data[iend:iend+isize] -= vend-vstart
        self.indices_data[istart:istart+isize] = self.indices_data[iend:iend+isize]
        self.indices_size -= isize

        # Update all subsequent objects 
        for i in range(key, len(self.objects)):
            _vstart,_vend,_istart,_iend,_ustart,_uend = self.objects[i]
            self.objects[i] = [_vstart-vsize, _vend-vsize, \
                               _istart-isize, _iend-isize ]
        self.dirty = True


    def get_vertices(self):
        """
        """
        return self.vertices_data[:self.vertices_size]
    vertices = property(get_vertices)

    def get_indices(self):
        """
        """
        return self.indices_data[:self.indices_size]
    indices = property(get_indices)

    def __len__(self):
        """
        """
        return len(self.objects)

    def __getitem__(self, key):
        """
        """
        vstart,vend,istart,iend,ustart,uend = self.objects[key]
        return Object( self.vertices_data[vstart:vend],      
                       self.indices_data[istart:iend]-vstart)


    def upload(self):
        gl.glBindBuffer( gl.GL_ARRAY_BUFFER, self.vertices_id )
        gl.glBufferData( gl.GL_ARRAY_BUFFER,
                         self.vertices_data[:self.vertices_size], gl.GL_STATIC_DRAW )
        gl.glBindBuffer( gl.GL_ARRAY_BUFFER, 0 )
        gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, self.indices_id )
        gl.glBufferData( gl.GL_ELEMENT_ARRAY_BUFFER,
                         self.indices_data[:self.indices_size], gl.GL_STATIC_DRAW )
        gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, 0 )
        self.dirty = False

    def draw( self, mode=gl.GL_TRIANGLES ):
        if self.dirty: self.upload()
        gl.glPushClientAttrib( gl.GL_CLIENT_VERTEX_ARRAY_BIT )
        gl.glBindBuffer( gl.GL_ARRAY_BUFFER, self.vertices_id )
        gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, self.indices_id )
        for attribute in self.attributes:
            attribute.enable()
        gl.glDrawElements( mode, self.indices_size, gl.GL_UNSIGNED_INT, None)
        gl.glBindBuffer( gl.GL_ELEMENT_ARRAY_BUFFER, 0 )
        gl.glBindBuffer( gl.GL_ARRAY_BUFFER, 0 )
        gl.glPopClientAttrib( )
