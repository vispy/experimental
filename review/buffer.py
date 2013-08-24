# -----------------------------------------------------------------------------
# VisPy - Copyright (c) 2013, Vispy Development Team
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of Vispy Development Team nor the names of its
#   contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
from __future__ import print_function, division

import numpy as np
import OpenGL.GL as gl
from globject import GLObject
from globject import gl_typeinfo





# --------------------------------------------------- BufferException class ---
class BufferException(Exception):
    """ Program Data exception class """
    pass



# ------------------------------------------------------------ Buffer class ---
class Buffer(GLObject):
    """ Data Buffer class """
    
    # ---------------------------------
    def __init__(self, data=None):
        """ Initialize the data buffer """

        GLObject.__init__(self)

        # CPU data
        self._data = None
        
        # Size of buffer in terms of element
        self._size = 0

        # Number of bytes separating two consecutive values
        self._stride = 0

        # Where does the actual data start relative to buffer start
        self._offset = 0

        # Element type
        self._gtype = 0

        # Set data if any
        if data is not None:
            self.set_data(data)


    # ---------------------------------
    def build(self):
        """
        Build the buffer and checks everything's ok.

        Note
        ----

        A GL context must be available to be able to build
        """

        if not self._handle:
            self._handle = gl.glGenBuffers(1)

        # Status ok (can the previous line ever fails ?)
        self._status = True

    
    # ---------------------------------
    def delete(self):
        """ Delete the buffer from GPU memory """

        if self._handle:
            gl.glDeleteBuffers(self._handle)


    # ---------------------------------
    def set_data(self, data):
        """ Set data (no upload) """

        self._data = np.array(data)
        self._dirty = True

        try:
            self.compute_gtype(self._data)
        except BufferException:
            self._offset = -1
            self._gtype = 0
            self._size = data.size


    # ---------------------------------
    def upload_data(self):
        """ Actual upload of data to GPU memory 

        Note
        ----

        A GL context must be available
        """

        # Check if actual upload is necessary
        if self._status and not self._dirty:
            return

        # Actual upload
        handle = self.handle
        gl.glBindBuffer( self._type, self.handle)
        gl.glBufferData( self._type, self._data, gl.GL_DYNAMIC_DRAW )
        gl.glBindBuffer( self._type, 0 )

        # Sane state
        self._dirty = False


    # ---------------------------------
    def _get_size(self):
        """ Get number of elements """
        return self._size
    size = property(_get_size,
                     doc = "Number of elements")


    # ---------------------------------
    def _get_stride(self):
        """ Get number of bytes separating two consecutive values """
        if self._data is not None:
            self._stride = self._data.strides[0]
        else:
            self._stride = 0
        return self._stride
    stride = property(_get_stride,
                     doc = "Number of bytes separating two consecutive values")


    # ---------------------------------
    def _get_offset(self):
        """ Get offset in GPU memory if relevant """
        return self._offset
    offset = property(_get_offset,
                     doc = "Offset in GPU memory if relevant")


    # ---------------------------------
    def _get_gtype(self):
        """ Get OpenGL element type  """
        return self._gtype
    gtype = property(_get_gtype,
                     doc = "Element type (OpenGL constant or 0)")


    # ---------------------------------
    def _get_data(self):
        """ Get CPU data """
        return self._data
    data = property(_get_data,
                     doc = "CPU data")


    # ---------------------------------
    def compute_gtype(self, data):
        """Compute the GL type and size corresponding to the given numpy array.

        Note
        ----
        
        There are a few ambiguous cases that need to be arbitrary solved.

        Examples
        --------
        
        dtype = float32, shape = 100
                     or  shape = (100,1)
         -> 100 x gl.GL_FLOAT
        
        dtype = float32, shape = 1000
                     or  shape = (100,10,1)
         -> 1000 x gl.GL_FLOAT
        
        dtype = float32, shape = (100,4)
         -> 100 x gl.GL_FLOAT_VEC4
         -> 400 x gl.GL_FLOAT
         -> Ambiguous case: we choose the first conversion (VEC4)

        dtype = float32, shape = (10,2,2)
         -> 10 x gl.GL_FLOAT_MAT2
         -> 20 x gl.GL_FLOAT_VEC2
         -> 40 x gl.GL_FLOAT
         -> Ambiguous case: we choose the first conversion (MAT2)

        """
        
        dtype = data.dtype
        shape = data.shape
        size  = data.size

        # If data is a structured array, whe nedd more check
        if dtype.fields is not None:
            # More than one field, we cannot convert
            if len(dtype.names) > 1:
                raise BufferException("Cannot convert dtype to gtype")

            # Only one field, we can convert (maybe, checked later)
            else:
                name = dtype.names[0]
                shape = dtype.fields[name][0].shape
                dtype = dtype.fields[name][0].subdtype[0]
                

        # If data dtype is not compatible, we cannot convert
        if dtype not in [np.float32, np.int32, np.uint32, np.bool]:
            raise BufferException("Cannot convert dtype to gtype")

        types = { 'float32' : { 1 : gl.GL_FLOAT,
                                2 : gl.GL_FLOAT_VEC2,
                                3 : gl.GL_FLOAT_VEC3,
                                4 : gl.GL_FLOAT_VEC4,
                                (2,2) : gl.GL_FLOAT_MAT2,
                                (3,3) : gl.GL_FLOAT_MAT3,
                                (4,4) : gl.GL_FLOAT_MAT4},
                  'int32' :   { 1 : gl.GL_INT,
                                2 : gl.GL_INT_VEC2,
                                3 : gl.GL_INT_VEC3,
                                4 : gl.GL_INT_VEC4 },
                  'uint32' :  { 1 : gl.GL_UNSIGNED_INT},
                  'bool' :    { 1 : gl.GL_BOOL,
                                2 : gl.GL_BOOL_VEC2,
                                3 : gl.GL_BOOL_VEC3,
                                4 : gl.GL_BOOL_VEC4 } }
        # data is one dimensional
        if len(shape) == 1:
            n = 1
        # data is two dimensional
        elif len(shape) == 2:
            n = shape[1]
            if n > 4:
                n = 1
            else:
                size /= n
        # data has more than two dimensions
        else:
            n = tuple(shape[-2:])
            if n not in ( (2,2), (3,3), (4,4) ):
                n = shape[-1]
            else:
                size = shape[0]
                for s in shape[1:-2]: size *= s

        self._gtype = types[str(dtype)][n]
        self._size = int(size)



# ------------------------------------------------------ VertexBuffer class ---
class VertexBuffer(Buffer):
    """ Vertex Buffer class """
    
    # ---------------------------------
    def __init__(self, data=None):
        """ Initialize the buffer and type it """

        Buffer.__init__(self, data)
        self. _type = gl.GL_ARRAY_BUFFER


    # ---------------------------------
    def __getitem__(self, name):
        """ Get a view on the buffer """

        # If there is not data, we cannot get a subfield
        if self._data is None:
            raise KeyError(name)

        # Dummy line to raise numpy exception if needed
        data = self._data[name]
        return VertexBufferView(self, name)


    # ---------------------------------
    def __setitem__(self, name, data):
        """ Set a specific field in the buffer """

        # If there is not data, we cannot set a subfield
        if self._data is None:
            raise KeyError(name)

        self._data[name][...] = data
        self._dirty = True




# -------------------------------------------------- VertexBufferView class ---
class VertexBufferView(VertexBuffer):
    """ View on a Vertex Buffer object """
    
    # ---------------------------------
    def __init__(self, buffer, name):
        """ Create a view on a field of an existing vertex buffer """

        VertexBuffer.__init__(self)
        self._buffer = buffer
        self._name = name

        data = buffer._data
        self._data = data[name]
        try:
            self.compute_gtype(data[name])
            self._offset = data.dtype.fields[name][1]
        except BufferException:
            self._offset = -1
            self._gtype  = 0


    # ---------------------------------
    def set_data(self, data):
        """ Set data (no upload) """

        # No check on type or size, numpy will do it for us
        self.buffer.data[self._name] = data
        self.buffer._dirty = True



    # ---------------------------------
    def upload_data(self):
        """ Actual upload of data to GPU memory 

        Note
        ----

        Since this is a view, we ask the original buffer to upload the data
        """
        self.buffer.upload_data()


    # ---------------------------------
    def _get_dirty(self):
        """ Get dirty flag (indicating if object needs updated) """
        return self.buffer.dirty
    dirty = property(_get_dirty, doc = "Whether object needs update")


    # ---------------------------------
    def _get_status(self):
        """ Get object build status """
        return self.buffer.status
    status = property(_get_status, doc = "Object build status ")


    # ---------------------------------
    def _get_handle(self):
        """ Get object name (and build the object if necessary) """
        return self.buffer.handle
    handle = property(_get_handle, doc = "Object name in GPU")


    # ---------------------------------
    def _get_type(self):
        """ Get object type """
        return self.buffer.type
    type = property(_get_type, doc = "Object type")


    # ---------------------------------
    def _get_size(self):
        """ Get number of elements """
        
        return self.buffer.size
    size = property(_get_size,
                     doc = "Number of elements")

    # ---------------------------------
    def _get_buffer(self):
        """ Get underlying linked buffer """
        
        return self._buffer
    buffer = property(_get_buffer,
                     doc = "Underlying linked buffer")



# ------------------------------------------------------- IndexBuffer class ---
class IndexBuffer(Buffer):
    """ Data Buffer class """
    
    # ---------------------------------
    def __init__(self, data):
        Buffer.__init__(self, data)
        self. _type = gl.GL_ELEMENT_ARRAY_BUFFER





# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    import OpenGL.GLUT as glut

    def display():
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        glut.glutSwapBuffers()
    def reshape(width,height):
        gl.glViewport(0, 0, width, height)
    def keyboard( key, x, y ):
        if key == '\033': sys.exit( )

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    glut.glutCreateWindow('Shader test')
    glut.glutReshapeWindow(512,512)
    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(reshape)
    glut.glutKeyboardFunc(keyboard )

    # No GL context required
    # ----------------------
    n = 1000

    # Simple array
    data = np.zeros((n,3), dtype=np.float32)
    vbo = VertexBuffer(data)
    print("%s %d (%d)\n" % ( vbo.gtype, vbo.size, vbo.offset))

    # Simple/Structured array
    data = np.zeros(n, dtype=[('a_position',  np.float32, 3)])
    vbo = VertexBuffer(data)['a_position']
    print("%s %d (%d)\n" % ( vbo.gtype, vbo.size, vbo.offset))

    # Structured array
    data = np.zeros(n, dtype=[('a_position',  np.float32, 3), 
                              ('a_color',     np.float32, 4), 
                              ('a_normal',    np.float32, 4), 
                              ('a_texcoords', np.float32, 2),
                              ('a_model',     np.float32, (4,4))])


    vbo = VertexBuffer(data)
    for name in data.dtype.names:
        Z = vbo[name]
        print("%-12s: %s %d (%d)" % (name, Z.gtype, Z.size, Z.offset))

    
    # No GL context required
    # ----------------------
    vbo.build()

    vbo.upload_data()
    print(vbo.dirty)

    vbo['a_position'] = np.zeros((n,3))
    print(vbo.dirty)
    vbo.upload_data()
    print(vbo.dirty)
