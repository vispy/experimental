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
import OpenGL.GL as gl
from shader import VertexShader
from shader import FragmentShader
from shader import ShaderException



# -----------------------------------------------------------------------------
class VertexShaderTest(unittest.TestCase):

    def test_init(self):
        shader = VertexShader()
        assert shader.type == gl.GL_VERTEX_SHADER

# -----------------------------------------------------------------------------
class FragmentShaderTest(unittest.TestCase):

    def test_init(self):
        shader = FragmentShader()
        assert shader.type == gl.GL_FRAGMENT_SHADER


# -----------------------------------------------------------------------------
class ShaderTest(unittest.TestCase):

    def test_init(self):
        shader = VertexShader()
        assert shader._handle == 0
        assert shader.dirty   == True
        assert shader.status  == False
        assert shader.code    == None
        assert shader.source  == None

    def test_sourcecode(self):
        code = "/* Code */"
        shader = VertexShader(code)
        assert shader.code == code
        assert shader.source == "<string>"

    def test_setcode(self):
        shader = VertexShader()
        shader._dirty = False
        shader.code = ""
        assert shader.dirty == True

    def test_empty_build(self):
        shader = VertexShader()
        with self.assertRaises(ShaderException):
            shader.build()

    def test_delete_no_context(self):
        shader = VertexShader()
        shader.delete()

    def test_uniform_float(self):
        shader = VertexShader("uniform float color;")
        assert shader.uniforms == [ ("color", gl.GL_FLOAT) ]

    def test_uniform_vec4(self):
        shader = VertexShader("uniform vec4 color;")
        assert shader.uniforms == [ ("color", gl.GL_FLOAT_VEC4) ]

    def test_uniform_array(self):
        shader = VertexShader("uniform float color[2];")
        assert shader.uniforms == [ ("color[0]", gl.GL_FLOAT),
                                    ("color[1]", gl.GL_FLOAT)  ]

    def test_attribute_float(self):
        shader = VertexShader("attribute float color;")
        assert shader.attributes == [ ("color", gl.GL_FLOAT) ]

    def test_attribute_vec4(self):
        shader = VertexShader("attribute vec4 color;")
        assert shader.attributes == [ ("color", gl.GL_FLOAT_VEC4) ]

if __name__ == "__main__":
    unittest.main()
