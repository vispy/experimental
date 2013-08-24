import sys
import ctypes
import numpy as np
import OpenGL.GL as gl

ALL_OFF = '\033[0m'
BOLD = '\033[1m'
BLACK = '\033[30m'
RED = '\033[31m'


def print_shader_error(error, line_no, code):
    lines = code.split('\n')
    start = max(0,line_no-2)
    end = min(len(lines),line_no+0)
    print '...' 
    for i, line in enumerate(lines[start-1:end]):
        if (i+start) == line_no:
            print '%03d %s' % (i+start, BOLD+RED+line+ALL_OFF)
        else:
            if len(line):
                print '%03d %s' % (i+start,line)
    print '--> ERROR:',error
    print


def parse_shader_error( error ):
    """Parses a single GLSL error and extracts the line number and error
    description.

    Line number and description are returned as a tuple.

    GLSL errors are not defined by the standard, as such,
    each driver provider prints their own error format.

    Nvidia print using the following format::

        0(7): error C1008: undefined variable "MV"

    Nouveau Linux driver using the following format::

        0:28(16): error: syntax error, unexpected ')', expecting '('

    ATi and Intel print using the following format::

        ERROR: 0:131: '{' : syntax error parse error

    """
    import re

    # Nvidia
    # 0(7): error C1008: undefined variable "MV"
    match = re.match( r'(\d+)\((\d+)\):\s(.*)', error )
    if match:
        return (
            int(match.group( 2 )),   # line number
            match.group( 3 )    # description
            )

    # ATI
    # Intel
    # ERROR: 0:131: '{' : syntax error parse error
    match = re.match( r'ERROR:\s(\d+):(\d+):\s(.*)', error )
    if match:
        return (
            int(match.group( 2 )),   # line number
            match.group( 3 )    # description
            )

    # Nouveau
    # 0:28(16): error: syntax error, unexpected ')', expecting '('
    match = re.match( r'(\d+):(\d+)\((\d+)\):\s(.*)', error )
    if match:
        return (
            int(match.group( 2 )),   # line number
            match.group( 4 )    # description
            )

    raise ValueError( 'Unknown GLSL error format' )




class ShaderException(Exception):
    pass

class Shader:
    def __init__(self, vertex_code = None, fragment_code = None):
        self.uniforms = {}
        self.handle = 0
        self.vertex_code   = vertex_code
        self.fragment_code = fragment_code

    def build(self):
        self.handle = gl.glCreateProgram()
        self.linked = False
        self._build_shader(self.vertex_code, gl.GL_VERTEX_SHADER)
        self._build_shader(self.fragment_code, gl.GL_FRAGMENT_SHADER)
        self._link()

    def _build_shader(self, strings, shader_type):
        count = len(strings)
        if count < 1: 
            return
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, strings)
        gl.glCompileShader(shader)
        status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if not status:
            error = gl.glGetShaderInfoLog(shader)
            if shader_type == gl.GL_VERTEX_SHADER:
                err_line, err_desc = parse_shader_error(error)
                print_shader_error(err_desc, err_line, self.vertex_code)
                sys.exit()
                raise (ShaderException, 'Vertex compilation error')
            elif shader_type == gl.GL_FRAGMENT_SHADER:
                print error
                sys.exit()
                raise (ShaderException, 'Fragment compilation error')
            else:
                print error
                sys.exit()
                raise (ShaderException)
        else:
            gl.glAttachShader(self.handle, shader)

    def _link(self):
        gl.glLinkProgram(self.handle)
        temp = ctypes.c_int(0)
        gl.glGetProgramiv(self.handle, gl.GL_LINK_STATUS, ctypes.byref(temp))
        if not temp:
            gl.glGetProgramiv(self.handle,
                              gl.GL_INFO_LOG_LENGTH, ctypes.byref(temp))
            print gl.glGetProgramInfoLog(self.handle)
            raise(ShaderException, 'Linking error' )
        else:
            self.linked = True

    def bind(self):
        if not self.handle: self.build()
        gl.glUseProgram(self.handle)

    def unbind(self):
        if not self.handle: self.build()
        gl.glUseProgram(0)

    def uniform(self, name, value):
        if not self.handle: self.build()
        loc = self.uniforms.get(name,
                                gl.glGetUniformLocation(self.handle,name))
        self.uniforms[name] = loc
        value = np.array(value)
        count = value.size
        dtype = value.dtype
        if dtype in [np.uint8, np.uint16, np.uint32, np.uint64]:
            if count in [1,2,3,4]:
                { 1 : gl.glUniform1u,
                  2 : gl.glUniform2u,
                  3 : gl.glUniform3u,
                  4 : gl.glUniform4u}[count](loc, *value)
            else:
                raise RuntimeError("Unknown uniform format")
        elif dtype in [np.int8, np.int16, np.int32, np.int64]:
            if count in range(1,5):
                { 1 : gl.glUniform1i,
                  2 : gl.glUniform2i,
                  3 : gl.glUniform3i,
                  4 : gl.glUniform4i}[count](loc, *value)
            else:
                raise RuntimeError("Unknown uniform format")
        elif dtype in [np.float32, np.float64]:
            if count in range(1,5):
                { 1 : gl.glUniform1f,
                  2 : gl.glUniform2f,
                  3 : gl.glUniform3f,
                  4 : gl.glUniform4f}[count](loc, *value)
            elif count == 16:
                gl.glUniformMatrix4fv(loc, 1, False, value)
        else:
            raise RuntimeError("Unknown uniform format")
            

    def uniformf(self, name, *vals):
        if not self.handle: self.build()
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name))
        self.uniforms[name] = loc
        if len(vals) in range(1, 5):
            { 1 : gl.glUniform1f,
              2 : gl.glUniform2f,
              3 : gl.glUniform3f,
              4 : gl.glUniform4f
            }[len(vals)](loc, *vals)

    def uniformi(self, name, *vals):
        if not self.handle: self.build()
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name))
        self.uniforms[name] = loc
        if len(vals) in range(1, 5):
            { 1 : gl.glUniform1i,
              2 : gl.glUniform2i,
              3 : gl.glUniform3i,
              4 : gl.glUniform4i
            }[len(vals)](loc, *vals)

    def uniform_matrixf(self, name, mat):
        if not self.handle: self.build()
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name))
        self.uniforms[name] = loc
        gl.glUniformMatrix4fv(loc, 1, False, mat)
