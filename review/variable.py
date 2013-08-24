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

import ctypes
import numpy as np
import OpenGL.GL as gl

from globject import GLObject
from globject import gl_typeinfo
from buffer import VertexBuffer, VertexBufferView



# ------------------------------------------------- VariableException class ---
class VariableException(Exception):
    """ Variable Data exception class """
    pass



# --------------------------------------------------- Variable class ---
class Variable(GLObject):
    """
    A variable is an interface between a program and some data.
    """


    # ---------------------------------
    def __init__(self, program, name, gtype):
        """ Initialize the data into default state """

        # Make sure variable type is allowed (for ES 2.0 shader)
        if gtype not in  [ gl.GL_FLOAT,        gl.GL_FLOAT_VEC2,
                           gl.GL_FLOAT_VEC3,   gl.GL_FLOAT_VEC4,
                           gl.GL_INT,          gl.GL_BOOL,
                           gl.GL_FLOAT_MAT2,   gl.GL_FLOAT_MAT3,
                           gl.GL_FLOAT_MAT4,   gl.GL_SAMPLER_2D,
                           gl.GL_SAMPLER_CUBE]:
            raise VariableException("Unknown variable type")

        GLObject.__init__(self)
        
        # Program this variable belongs to
        self._program = program

        # Name of this variable in the program
        self._name = name

        # GL type
        self._gtype = gtype

        # CPU data
        self._data = None

        # Whether this variable is active
        self._active = True

        # Location of the variable in the program slots
        self._location = 0


    # ---------------------------------
    def _get_name(self):
        return self._name
    name = property(_get_name,
                    doc = "Variable name")


    # ---------------------------------
    def _get_program(self):
        return self._program
    program = property(_get_program,
                    doc = "Program this variable belongs to")


    # ---------------------------------
    def _get_gtype(self):
        return self._gtype
    gtype = property(_get_gtype,
                     doc = "Type of the underlying variable (as a GL constant)")


    # ---------------------------------
    def _get_active(self):
        return self._active
    def _set_active(self,active):
        self._active = active
    active = property(_get_active, _set_active,
                      doc = "Whether this variable is active in the program")

    # ---------------------------------
    def _get_data(self):
        return self._data
    data = property(_get_data,
                      doc = "CPU data")





# ----------------------------------------------------------- Uniform class ---
class Uniform(Variable):
    """ A Uniform represents a program uniform variable. """

    _ufunctions = { 
        gl.GL_FLOAT:        gl.glUniform1fv,
        gl.GL_FLOAT_VEC2:   gl.glUniform2fv,
        gl.GL_FLOAT_VEC3:   gl.glUniform3fv,
        gl.GL_FLOAT_VEC4:   gl.glUniform4fv,
        gl.GL_INT:          gl.glUniform1iv,
        gl.GL_BOOL:         gl.glUniform1iv,
        gl.GL_FLOAT_MAT2:   gl.glUniformMatrix2fv,
        gl.GL_FLOAT_MAT3:   gl.glUniformMatrix3fv,
        gl.GL_FLOAT_MAT4:   gl.glUniformMatrix4fv,
        gl.GL_SAMPLER_2D:   gl.glUniform1i,
        gl.GL_SAMPLER_CUBE: gl.glUniform1i,
    }


    # ---------------------------------
    def __init__(self, program, name, gtype):
        """ Initialize the input into default state """

        Variable.__init__(self, program, name, gtype)

        size, _, dtype = gl_typeinfo[self._gtype]
        self._data = np.zeros(size, dtype)
        self._ufunction = Uniform._ufunctions[self._gtype]
        self._texture_unit = -1


    # ---------------------------------
    def _get_texture_unit(self):
        return self._texture_unit
    def _set_texture_unit(self, unit):
        self._texture_unit = unit
    texture_unit = property(_get_texture_unit, _set_texture_unit,
                            doc = "Texture unit if relevant (depends on gtype)")


    # ---------------------------------
    def set_data(self, data):
        """ Set data (no upload) """

        # Textures need special handling
        if self._gtype in (gl.GL_SAMPLER_2D, gl.GL_SAMPLER_CUBE):
            self._data = data
        else:
            try:
                self._data[...] = np.array(data)
            except ValueError:
                raise VariableException("Wrong data format")

        # Mark variable as dirty
        self._dirty = True


    # ---------------------------------
    def upload_data(self):
        """ Actual upload of data to GPU memory """

        # Check active status (mandatory)
        if not self._active:
            raise VariableException("Uniform is not active")

        # Location has not been changed and data has been uploaded

        # WARNING : Uniform are supposed to keep their value between program
        #           activation/deactivation (from the GL documentation). It has
        #           been tested on some machines but if it is not the case on
        #           every machine, we can expect nasty bugs from this early
        #           return
        if self._status and not self._dirty:
            return

        # Matrices (need a transpose argument)
        if self._gtype in (gl.GL_FLOAT_MAT2, gl.GL_FLOAT_MAT3, gl.GL_FLOAT_MAT4):
            # OpenGL ES 2.0 does not support transpose
            transpose = False 
            self._function(self.location, 1, transpose, self._data)

        # Textures (need to get texture count)
        elif self._gtype in (gl.GL_SAMPLER_2D, gl.GL_SAMPLER_CUBE):
            texture = self.data
            unit = self.texture_unit
            gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
            gl.glBindTexture(texture.target, texture.handle)
            gl.glUniform1i(self.location, unit)

        # Regular uniform
        else:
            self._ufunction(self.location, 1, self._data)

        # Sane state
        self._dirty = False


    # ---------------------------------
    def _get_location(self):
        """ Get data location from GPU """

        if not self._status:
            self._location = gl.glGetUniformLocation(self._program.handle, self._name)
            self._status = True
        return self._location
    location = property(_get_location,
                        doc = "Data location from GPU" )


    



# --------------------------------------------------------- Attribute class ---
class Attribute(Variable):
    """
    An Attribute represents a program attribute variable.
    """

    _afunctions = { 
        gl.GL_FLOAT:        gl.glVertexAttrib1f,
        gl.GL_FLOAT_VEC2:   gl.glVertexAttrib2f,
        gl.GL_FLOAT_VEC3:   gl.glVertexAttrib3f,
        gl.GL_FLOAT_VEC4:   gl.glVertexAttrib4f
    }

    # ---------------------------------
    def __init__(self, program, name, gtype):
        """ Initialize the input into default state """

        Variable.__init__(self, program, name, gtype)

        # Number of elements this attribute links to (in the attached buffer)
        self._size = 0

        # Whether this attribure is generic
        self._generic = False


    # ---------------------------------
    def set_data(self, data):
        """ Set data (no upload) """

        # Data is a tuple with size <= 4, we assume this designates a generate
        # vertex attribute.
        if (type(data) in (float,int) or
            (type(data) in (tuple,list) and len(data) in [1,2,3,4])):

            # Let numpy convert the data for us
            _, _, dtype = gl_typeinfo[self._gtype]
            self._data = np.array(data).astype(dtype)

            self._generic = True
            self._dirty = True
            self._afunction = Attribute._afunctions[self._gtype]
            return

        # For array-like, we need to build a proper VertexBuffer to be able to
        # upload it later to GPU memory.
        if type(data) not in (VertexBuffer, VertexBufferView):
            # We could keep track of whether we (this object) previously
            # created a VertexBuffer and use it to only update the data. This
            # would require to distinguish the origin of the vertex buffer (or
            # the view). This might be not worth the trouble in terms of
            # performances since we only save the buffer generation and the
            # whole data would be uploaded anyway
            data = VertexBuffer(data)

        self._dirty = True
        self._data = data
        self._generic = False


    # ---------------------------------
    def upload_data(self):
        """ Actual upload of data to GPU memory  """

        # Check active status (mandatory)
        if not self._active:
            # Maybe too rude...
            # raise VariableException("Uniform is not active")
            return

        # Location has not been changed and data has been uploaded
        if self._status and not self._dirty:
            return

        # Generic vertex attribute (all vertices receive the same value)
        if self._generic:
            if self.location >= 0:
                gl.glDisableVertexAttribArray(self.location)
                self._afunction(self.location, *self._data)

        # Regular vertex buffer
        elif self.location >= 0:
            data = self._data
            if data.offset == -1:
                raise VariableException(
                    "Incompatible dtype for this attribute (%s)" % self.name)
            data.upload_data()
            self._dirty = False
          
            # Get relevant information from gl_typeinfo
            size, gtype, dtype = gl_typeinfo[self._gtype]
            stride = data.stride

            # Make offset a pointer, or it will be interpreted as a small array
            offset = ctypes.c_void_p(data.offset)

            gl.glEnableVertexAttribArray(self.location)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._data.handle)
            gl.glVertexAttribPointer(
                self.location, size, gtype,  gl.GL_FALSE, stride, offset)


    # ---------------------------------
    def _get_location(self):
        """ Get data location from GPU """

        if not self._status:
            self._location = gl.glGetAttribLocation(self._program.handle, self.name)
            self._status = True
        return self._location
    location = property(_get_location,
                        doc = "Data location from GPU" )


    # ---------------------------------
    def _get_size(self):
        """ Get size of the underlying vertex buffer """
        if self._data is None:
            return 0
        return self._data.size
    size = property(_get_size,
                     doc = "Size of the underlying vertex buffer")



# -----------------------------------------------------------------------------
if __name__ == '__main__':

    u = Uniform(0, "color", "vec4")
    a = Attribute(0, "color", "vec4")

    # Check setting data
    color = 1,1,1,1
    u.set_data(color)

    # Check size mismatch
#    color = 0,0,0
#    u.set_data(color)


    # Check setting data
    color = 1,1,1,1
    a.set_data(color)

    # Check size mismatch
    color = 0,0,0
    a.set_data(color)

