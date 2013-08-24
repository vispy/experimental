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
import unittest
import numpy as np
import OpenGL.GL as gl

from variable import Uniform
from variable import Variable
from variable import Attribute
from variable import VariableException



# -----------------------------------------------------------------------------
class VariableTest(unittest.TestCase):

    def test_init(self):
        variable = Variable(None, "A", gl.GL_FLOAT)
        assert variable._handle == 0
        assert variable.dirty   == True
        assert variable.status  == False
        assert variable.name    == "A"
        assert variable.data    is None
        assert variable.gtype   == gl.GL_FLOAT
        assert variable.active  == True


    def test_init_wrong_type(self):
        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_INT_VEC2)
        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_INT_VEC3)
        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_INT_VEC4)

        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_BOOL_VEC2)
        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_BOOL_VEC3)
        with self.assertRaises(VariableException):
            v = Variable(None, "A", gl.GL_BOOL_VEC4)



# -----------------------------------------------------------------------------
class UniformTest(unittest.TestCase):

    def test_init(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT)
        assert uniform.texture_unit == -1

    def test_float(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 1

    def test_vec2(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_VEC2)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 2

    def test_vec3(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_VEC2)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 2

    def test_vec4(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_VEC2)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 2

    def test_int(self):
        uniform = Uniform(None, "A", gl.GL_INT)
        assert uniform.data.dtype == np.int32
        assert uniform.data.size == 1

    def test_mat2(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_MAT2)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 4

    def test_mat3(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_MAT3)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 9

    def test_mat4(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_MAT4)
        assert uniform.data.dtype == np.float32
        assert uniform.data.size == 16

    def test_set(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_VEC4)

        uniform.set_data(1)
        assert (uniform.data == 1).all()

        uniform.set_data([1,2,3,4])
        assert (uniform.data == [1,2,3,4]).all()

    def test_set_exception(self):
        uniform = Uniform(None, "A", gl.GL_FLOAT_VEC4)

        with self.assertRaises(VariableException):
            uniform.set_data([1,2])

        with self.assertRaises(VariableException):
            uniform.set_data([1,2,3,4,5])


# -----------------------------------------------------------------------------
class AttributeTest(unittest.TestCase):

    def test_init(self):
        attribute = Attribute(None, "A", gl.GL_FLOAT)
        assert attribute.size == 0

    def test_set_generic(self):
        attribute = Attribute(None, "A", gl.GL_FLOAT_VEC4)

        attribute.set_data([1,2,3,4])
        assert type(attribute.data) is np.ndarray

        attribute.set_data(1)
        assert type(attribute.data) is np.ndarray


if __name__ == "__main__":
    unittest.main()
