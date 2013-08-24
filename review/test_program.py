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

from program import Program
from shader import VertexShader
from shader import FragmentShader
from program import ProgramException




# -----------------------------------------------------------------------------
class ProgramTest(unittest.TestCase):

    def test_init(self):
        program = Program()
        assert program._handle == 0
        assert program.dirty   == True
        assert program.status  == False
        assert program.shaders == []

    def test_delete_no_context(self):
        program = Program()
        program.delete()

    def test_init_from_string(self):
        program = Program("A","B")
        assert len(program.shaders) == 2
        assert program.shaders[0].code == "A"
        assert program.shaders[1].code == "B"

    def test_init_from_shader(self):
        program = Program(VertexShader("A"),FragmentShader("B"))
        assert len(program.shaders) == 2
        assert program.shaders[0].code == "A"
        assert program.shaders[1].code == "B"

    def test_unique_shader(self):
        vert = VertexShader("A")
        frag = FragmentShader("B")
        program = Program([vert,vert],[frag,frag,frag])
        assert len(program.shaders) == 2

    def test_uniform(self):
        vert = VertexShader("uniform float A;")
        frag = FragmentShader("uniform float A; uniform vec4 B;")
        program = Program(vert,frag)
        assert program.all_uniforms == [ ("A", gl.GL_FLOAT),
                                         ("B", gl.GL_FLOAT_VEC4) ]

    def test_attributes(self):
        vert = VertexShader("attribute float A;")
        frag = FragmentShader("")
        program = Program(vert,frag)
        assert program.all_attributes == [ ("A", gl.GL_FLOAT) ]

    def test_attach(self):
        vert = VertexShader("A")
        frag = FragmentShader("B")
        program = Program(vert)
        program.attach(frag)
        assert len(program.shaders) == 2
        assert program.shaders[0].code == "A"
        assert program.shaders[1].code == "B"

    def test_detach(self):
        vert = VertexShader("A")
        frag = FragmentShader("B")
        program = Program(vert, frag)
        program.detach(frag)
        assert len(program.shaders) == 1
        assert program.shaders[0].code == "A"

    def test_failed_build(self):
        vert = VertexShader("A")
        frag = FragmentShader("B")

        program = Program(verts = vert)
        with self.assertRaises(ProgramException):
            program.build()

        program = Program(frags = frag)
        with self.assertRaises(ProgramException):
            program.build()

    def test_setitem(self):
        vert = VertexShader("")
        frag = FragmentShader("")

        program = Program(vert,frag)
        with self.assertRaises(ProgramException):
            program["A"] = 1



if __name__ == "__main__":
    unittest.main()
