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
import re
import os.path
import numpy as np
import OpenGL.GL as gl
from globject import GLObject
from globject import gl_typeinfo



# --------------------------------------------------- ShaderException class ---
class ShaderException(Exception):
    """Shader exception class. """
    pass



# ------------------------------------------------------------ Shader class ---
class Shader(GLObject):
    """Abstract shader class."""
    
    _gtypes = {
        'float':       gl.GL_FLOAT,
        'vec2':        gl.GL_FLOAT_VEC2,
        'vec3':        gl.GL_FLOAT_VEC3,
        'vec4':        gl.GL_FLOAT_VEC4,
        'int':         gl.GL_INT,
        'ivec2':       gl.GL_INT_VEC2,
        'ivec3':       gl.GL_INT_VEC3,
        'ivec4':       gl.GL_INT_VEC4,
        'bool':        gl.GL_BOOL,
        'bvec2':       gl.GL_BOOL_VEC2,
        'bvec3':       gl.GL_BOOL_VEC3,
        'bvec4':       gl.GL_BOOL_VEC4,
        'mat2':        gl.GL_FLOAT_MAT2,
        'mat3':        gl.GL_FLOAT_MAT3,
        'mat4':        gl.GL_FLOAT_MAT4,
        'sampler2D':   gl.GL_SAMPLER_2D,
        'samplerCube': gl.GL_SAMPLER_CUBE
    }

    # ---------------------------------
    def __init__(self, code=None):
        """
        Initialize the shader and get code if possible.

        Parameters
        ----------

        code: str
            code can be a filename or the actual code
        """

        GLObject.__init__(self)
        self._code = None
        self._source = None

        if code is not None:
            self._set_code(code)


    # ---------------------------------
    def _get_code(self):
        """ Get shader code """
        return self._code

    def _set_code(self, code):
        """ Set shader code """
        if os.path.exists(code):
            with open(code) as file:
                self._code   = file.read()
                self._source = os.path.basename(code)
        else:
            self._code   = code
            self._source = '<string>'
        self._dirty  = True
        self._status = False
    code = property(_get_code, _set_code,
                    doc = "Shader code")


    # ---------------------------------
    def _get_source(self):
        """ Get shader source (string or filename) """
        return self._source
    source = property(_get_source,
                      doc = "Shader source")


    # ---------------------------------
    def build(self):
        """ Compile the source and checks eveyrthing's ok """

        # Check if we have something to compile
        if not self._code:
            raise ShaderException("No code has been given")

        # Check if compilation is needed
        if self.status and not self.dirty:
            return

        # Check shader type is vertex or fragment
        if self._type not in [gl.GL_VERTEX_SHADER,
                              gl.GL_FRAGMENT_SHADER]:
            raise ShaderException("Shader type must be vertex or fragment")

        # Check that shader object has been created
        if not self._handle:
            self._handle = gl.glCreateShader(self._type)
            if not self._handle:
                raise ShaderException("Cannot create shader object")


        # Set shader source
        gl.glShaderSource(self._handle, self._code)

        # Actual compilation
        gl.glCompileShader(self._handle)
        status = gl.glGetShaderiv(self._handle, gl.GL_COMPILE_STATUS)
        if not status:
            error = gl.glGetShaderInfoLog(self._handle)
            lineno, mesg = self.parse_error(error)
            self.print_error(mesg, lineno-1)
            raise ShaderException("Shader compilation error")

        # Compilation ok
        self._status = True

        # Sane state
        self._dirty = False


    # ---------------------------------
    def delete(self):
        """ Delete shader from GPU memory (if it was present). """

        # Only delete if the shader was present in GPU
        if self._handle:
            gl.glDeleteShader(self._handle)

            # Reset internal state
            self._handle = 0
            self._dirty = True
            self._status = False


    # ---------------------------------
    def parse_error(self, error):
        """
        Parses a single GLSL error and extracts the line number and error
        description.

        Parameters
        ----------
        error : str
            An error string as returned byt the compilation process
        """

        # Nvidia
        # 0(7): error C1008: undefined variable "MV"
        m = re.match(r'(\d+)\((\d+)\):\s(.*)', error )
        if m: return int(m.group(2)), m.group(3)

        # ATI / Intel
        # ERROR: 0:131: '{' : syntax error parse error
        m = re.match(r'ERROR:\s(\d+):(\d+):\s(.*)', error )
        if m: return int(m.group(2)), m.group(3)

        # Nouveau
        # 0:28(16): error: syntax error, unexpected ')', expecting '('
        m = re.match( r'(\d+):(\d+)\((\d+)\):\s(.*)', error )
        if m: return int(m.group(2)), m.group(4)

        raise ValueError('Unknown GLSL error format')


    # ---------------------------------
    def print_error(self, error, lineno):
        """
        Print error and show the faulty line + some context

        Parameters
        ----------
        error : str
            An error string as returned byt the compilation process

        lineno: int
            Line where error occurs
        """
        OFF = '\033[0m'
        BOLD = '\033[1m'
        BLACK = '\033[30m'
        RED = '\033[31m'
        lines = self._code.split('\n')
        start = max(0,lineno-2)
        end = min(len(lines),lineno+1)

        print('%sError in %s%s' % (BOLD, repr(self),OFF))
        print(' -> %s' % error)
        print()
        if start > 0:
            print(' ...')
        for i, line in enumerate(lines[start:end]):
            if (i+start) == lineno:
                print(' %03d %s' % (i+start, BOLD+RED+line+OFF))
            else:
                if len(line):
                    print(' %03d %s' % (i+start,line))
        if end < len(lines):
            print(' ...')
        print()


    # ---------------------------------
    def _get_uniforms(self):
        """
        Extract uniforms (name and type) from code
        """

        uniforms = []
        regex = re.compile("""\s*uniform\s+(?P<type>\w+)\s+"""
                           """(?P<name>\w+)\s*(\[(?P<size>\d+)\])?\s*;""")
        for m in re.finditer(regex,self._code):
            size = -1
            gtype = Shader._gtypes[m.group('type')]
            if m.group('size'):
                size = int(m.group('size'))
            if size >= 1:
                for i in range(size):
                    name = '%s[%d]' % (m.group('name'),i)
                    uniforms.append((name, gtype))
            else:
                uniforms.append((m.group('name'), gtype))

        return uniforms
    uniforms = property(_get_uniforms,
                        doc = "Shader uniforms obtained from code")


    # ---------------------------------
    def _get_attributes(self):
        """
        Extract attributes (name and type) from code
        """

        attributes = []
        regex = re.compile("""\s*attribute\s+(?P<type>\w+)\s+"""
                           """(?P<name>\w+)\s*(\[(?P<size>\d+)\])?\s*;""")
        for m in re.finditer(regex,self._code):
            size = -1
            gtype = Shader._gtypes[m.group('type')]
            if m.group('size'):
                size = int(m.group('size'))
            if size >= 1:
                for i in range(size):
                    name = '%s[%d]' % (m.group('name'),i)
                    attributess.append((name, gtype))
            else:
                attributes.append((m.group('name'), gtype))
        return attributes
    attributes = property(_get_attributes,
                          doc = "Shader attributes obtained from code")





# ------------------------------------------------------ VertexShader class ---
class VertexShader(Shader):
    """ Vertex shader class """

    # ---------------------------------
    def __init__(self, code=None):
        Shader.__init__(self, code)
        self._type = gl.GL_VERTEX_SHADER

    # ---------------------------------
    def __repr__(self):
        return "Vertex Shader %d (%s)" % (self._id, self._source)





# ---------------------------------------------------- FragmentShader class ---
class FragmentShader(Shader):
    """ Fragment shader class """

    # ---------------------------------
    def __init__(self, code=None):
        Shader.__init__(self, code)
        self._type = gl.GL_FRAGMENT_SHADER

    # ---------------------------------
    def __repr__(self):
        return "Fragment Shader %d (%s)" % (self._id, self._source)
