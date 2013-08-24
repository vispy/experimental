#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
"""
A collection is a (virtual) container for several objects having the same
vertex structure (vtype) and same uniforms type (utype). A collection allows to
manipulate objects individually but they can be rendered at once (single call).

Each object can have its own set of uniforms provided they are a combination of
floats.

To modify a parameter (e.g. translate) for all items at once::

    collection.translate = x,y

To modify a parameter (e.g. translate) for a single item (e.g. index=1)::

   collection['translate'][1] = x,y

"""
import math
import numpy as np
import OpenGL.GL as gl
from operator import mul
from vertex_buffer import VertexBuffer
from dynamic_buffer import DynamicBuffer



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
class Item(object):
    """
    An item represent an object within a collection and is create on demand
    when accessing a specific object of the collection.
    """

    # ---------------------------------
    def __init__(self, parent, key, vertices, indices, uniforms):
        """
        Create a new item from an existing collection.

        Parameters
        ----------

        parent : Collection
            Collection this item belongs to

        key: int
            Key index of the item within the collection

        vertices: array-like
            Vertices of the item

        indices: array-like
            Indices of the item

        uniforms: array-like
            Uniform parameters of the item


        Notes
        -----

        Indices are given relatively to the whole collection.
        """
        
        self.parent = parent
        self.vertices = vertices
        self.indices  = indices
        self.uniforms = uniforms
        self.key = key


    # # ---------------------------------
    # def __getitem__(self, key):
    #     """
    #     Get a specific uniform parameters

    #     Parameters
    #     ----------

    #     key: string
    #         name of the parameter

    #     Returns
    #     -------

    #     Specified parameter if it exists.
    #     """

    #     if key in self.uniforms.dtype.names:
    #         return self.uniforms[key]
    #     raise KeyError


    # # ---------------------------------
    # def __setitem__(self, key, value):
    #     """
    #     Set a specific uniform parameters

    #     Parameters
    #     ----------

    #     key: string
    #         name of the parameter
    #     """

    #     if key in self.uniforms.dtype.names:
    #         self.uniforms[key] = value
    #         self.parent._dirty = True
    #         return
    #     raise KeyError


    # # ---------------------------------
    # def __getattr__(self, name):
    #     """
    #     Get a specific uniform parameters

    #     Parameters
    #     ----------

    #     key: string
    #         name of the parameter

    #     Returns
    #     -------

    #     Specified parameter if it exists.
    #     """

    #     if hasattr(self, 'uniforms'):
    #         uniforms = object.__getattribute__(self,'uniforms')
    #         if name in uniforms.dtype.names:
    #             return uniforms[name]
    #     return object.__getattribute__(self,name)


    # # ---------------------------------
    # def __setattr__(self, name, value):
    #     """
    #     Set a specific uniform parameters

    #     Parameters
    #     ----------

    #     key: string
    #         name of the parameter
    #     """

    #     if hasattr(self, 'uniforms'):
    #         uniforms = object.__getattribute__(self,'uniforms')
    #         if name in uniforms.dtype.names:
    #             # Is there a method at the parent level ?
    #             if( hasattr(self.parent, 'set_'+name) ):
    #                 getattr(self.parent,'set_'+name)(self.key, value)
    #                 return
    #             uniforms[name] = value
    #             self.parent._dirty = True
    #             return
    #     object.__setattr__(self, name, value)



# -----------------------------------------------------------------------------
class CollectionException(Exception):
    pass



# -----------------------------------------------------------------------------
class Collection(object):

    # ---------------------------------
    def __init__(self, vtype, utype):
        # Convert types to lists (in case they were already dtypes) such that
        # we can append new fields
        vtype = eval(str(np.dtype(vtype)))
        utype = eval(str(np.dtype(utype)))

        # We add a uniform index to access uniform data from texture
        vtype.append( ('a_index', 'f4') )

        # Check if given utype is made of float32 only
        rutype = dtype_reduce(utype)
        if type(rutype[0]) is not str or rutype[2] != 'float32':
            raise CollectionError("Uniform type cannot de reduced to float32 only")
        else:
            count = rutype[1]
            count2 = int(math.pow(2, math.ceil(math.log(count, 2))))
            if (count2 - count) > 0:
                utype.append(('unused', 'f4', count2-count))
            self._count = count2
            self.utype = utype
        
        self._vbuffer = VertexBuffer(vtype)
        self._ubuffer = DynamicBuffer( utype )
        self._ubuffer_id = 0
        self._max_texture_size = gl.glGetInteger(gl.GL_MAX_TEXTURE_SIZE)
        self._compute_ushape(1)
        self._ubuffer.reserve( self._ushape[1] / (count/4) )
        self._dirty = True


    # ---------------------------------
    def _compute_ushape(self, size=1):
        max_texsize = self._max_texture_size
        cols = max_texsize//(self._count/4)
        rows = (size // cols)+1
        self._ushape = rows, cols*(self._count/4), self._count


    # ---------------------------------
    def __len__(self):
        return len(self._vbuffer)


    # ---------------------------------
    def __getitem__(self, key):
        V = self._vbuffer.vertices[key]
        I = self._vbuffer.indices[key]
        U = self._ubuffer[key]
        return Item(self, key, V, I, U)


    # ---------------------------------
    def __delitem__(self, key):
        start,end = self._vbuffer.vertices.range(key)
        del self._vbuffer[key]
        del self._ubuffer[key]
        self._vbuffer.vertices.data['a_index'][start:] -= 1
        self._vbuffer._dirty = True
        self._dirty = True



    # ---------------------------------
    def get_vbuffer(self):
        return self._vbuffer
    vbuffer = property(get_vbuffer)

    # ---------------------------------
    def get_vertices(self):
        return self._vbuffer.vertices
    vertices = property(get_vertices)


    # ---------------------------------
    def get_indices(self):
        return self._vbuffer.indices
    indices = property(get_indices)


    # ---------------------------------
    def get_uniforms(self):
        return self._ubuffer
    uniforms = property(get_uniforms)


    # ---------------------------------
    def get_attributes(self):
        return self._vbuffer._attributes
    attributes = property(get_attributes)


    # ---------------------------------
    def __getattr__(self, name):
        if hasattr(self, '_ubuffer'):
            buffer = object.__getattribute__(self,'_ubuffer')
            if name in buffer.dtype.names:
                return buffer.data[name]
        return object.__getattribute__(self,name)


    # ---------------------------------
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if hasattr(self, '_ubuffer'):
            buffer = object.__getattribute__(self,'_ubuffer')
            if name in buffer.dtype.names:
                buffer.data[name] = value
                # buffer._dirty = True
                object.__setattr__(self, '_dirty', True)
        object.__setattr__(self, name, value)


    # ---------------------------------
    def clear(self):
        self._vbuffer.clear()
        self._ubuffer.clear()
        self._dirty = True


    # ---------------------------------
    def append(self, vertices, indices, uniforms, splits=None):
        vertices = np.array(vertices).astype(self._vbuffer.vertices.dtype)
        indices  = np.array(indices).astype(self._vbuffer.indices.dtype)
        uniforms = np.array(uniforms).astype(self._ubuffer.dtype)

        if splits is None:
            vertices['a_index'] = len(self)
            self._vbuffer.append( vertices, indices )
            self._ubuffer.append( uniforms )
            self._compute_ushape(len(self))
        elif len(splits) == 2:
            vsize,isize = splits[0], splits[1]
            if (vertices.size % vsize) != 0:
                raise( RuntimeError,
                       "Cannot split vertices data into %d pieces" % vsize)
            if (indices.size % isize) != 0:
                raise( RuntimeError,
                       "Cannot split indices data into %d pieces" % vsize)
            vcount = vertices.size//vsize
            icount = indices.size//isize
            ucount = uniforms.size
            n = ucount
            if vcount != icount or vcount != ucount:
                raise( RuntimeError,
                       "Vertices/indices/uniforms cannot be split")
            vertices['a_index'] = len(self)+np.repeat(np.arange(n),vsize)
            self._vbuffer.append( vertices, indices, (vsize,isize))
            self._ubuffer.append( uniforms )
            self._compute_ushape(len(self))
        else:
            raise(RuntimeError, "Splits argument not understood")
        self._dirty = True


    # ---------------------------------
    def upload(self):

        if not self._dirty:
            return
        self._vbuffer.upload()
        self.upload_uniforms()
        self._dirty = False


    # ---------------------------------
    def upload_uniforms(self):

        gl.glActiveTexture( gl.GL_TEXTURE0 )
        data = self._ubuffer.data.view(np.float32)
        shape = self._ushape

        if not self._ubuffer_id:
            self._ubuffer_id = gl.glGenTextures(1)

            gl.glBindTexture( gl.GL_TEXTURE_2D, self._ubuffer_id )
            gl.glPixelStorei( gl.GL_UNPACK_ALIGNMENT, 1 )
            gl.glPixelStorei( gl.GL_PACK_ALIGNMENT, 1 )
            gl.glTexParameterf( gl.GL_TEXTURE_2D,
                                gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST )
            gl.glTexParameterf( gl.GL_TEXTURE_2D,
                                gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST )
            gl.glTexParameterf( gl.GL_TEXTURE_2D,
                                gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE )
            gl.glTexParameterf( gl.GL_TEXTURE_2D,
                                gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BASE_LEVEL, 0)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 0)
            gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F,
                             shape[1], shape[0], 0, gl.GL_RGBA, gl.GL_FLOAT, data )
        gl.glActiveTexture( gl.GL_TEXTURE0 )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self._ubuffer_id )
        gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F,
                         shape[1], shape[0], 0, gl.GL_RGBA, gl.GL_FLOAT, data )


    # ---------------------------------
    def draw(self, mode=gl.GL_TRIANGLES, uniforms = {}):
        if self._dirty:
            self.upload()
        shader = self.shader
        shader.bind()
        gl.glActiveTexture( gl.GL_TEXTURE0 )
        shader.uniformi( 'u_uniforms', 0 )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self._ubuffer_id )
        for name,value in uniforms.items():
            shader.uniform(name, value)
        shader.uniformf('u_uniforms_shape', *self._ushape)
        self._vbuffer.draw(mode)
        shader.unbind()
