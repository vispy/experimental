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

from buffer import Buffer
from buffer import VertexBuffer
from buffer import VertexBufferView
from buffer import IndexBuffer



# -----------------------------------------------------------------------------
class BufferbleTest(unittest.TestCase):

    def test_init(self):
        buffer = Buffer()
        assert buffer._handle == 0
        assert buffer.dirty   == True
        assert buffer.status  == False
        assert buffer.data    == None
        assert buffer.size    == 0
        assert buffer.stride  == 0
        assert buffer.offset  == 0
        assert buffer.gtype   == 0

    def test_size_gtype(self):

        data = np.zeros(100, np.float32)
        buffer = Buffer(data)
        assert buffer.size == 100
        assert buffer.gtype == gl.GL_FLOAT

        data = np.zeros((100,4), np.float32)
        buffer = Buffer(data)
        assert buffer.size == 100
        assert buffer.gtype == gl.GL_FLOAT_VEC4

        data = np.zeros((100,4,4), np.float32)
        buffer = Buffer(data)
        assert buffer.size == 100
        assert buffer.gtype == gl.GL_FLOAT_MAT4

        data = np.zeros((100,4,4), np.float32)
        buffer = Buffer(data)
        assert buffer.size == 100
        assert buffer.gtype == gl.GL_FLOAT_MAT4

        data = np.zeros(100, [('a', np.float32, (4,4))])
        buffer = Buffer(data['a'])
        assert buffer.size == 100
        assert buffer.gtype == gl.GL_FLOAT_MAT4


if __name__ == "__main__":
    unittest.main()
