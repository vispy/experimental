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
import OpenGL.GL as gl

from globject import GLObject
from shader import VertexShader
from shader import FragmentShader
from shader import gl_typeinfo
from variable import Uniform
from variable import Attribute



# Patch: pythonize the glGetActiveAttrib
import ctypes
gl._glGetActiveAttrib = gl.glGetActiveAttrib
def glGetActiveAttrib(program, index):
    # Prepare
    bufsize = 32
    length = ctypes.c_int()
    size = ctypes.c_int()
    type = ctypes.c_int()
    name = ctypes.create_string_buffer(bufsize)
    # Call
    gl._glGetActiveAttrib(program, index, 
                          bufsize, ctypes.byref(length), ctypes.byref(size), 
                          ctypes.byref(type), name)
    # Return Python objects
    return name.value, size.value, type.value
gl.glGetActiveAttrib = glGetActiveAttrib




# -------------------------------------------------- ProgramException class ---
class ProgramException(Exception):
    """ Program exception class """
    pass



# ----------------------------------------------------------- Program class ---
class Program(GLObject):
    """
    A program is an object to which shaders can be attached and linked to create
    the program.
    """

    # ---------------------------------
    def __init__(self, verts=[], frags=[]):
        """Initialize the program and register shaders to be linked.

        Parameters
        ----------

        verts : list of vertex shaders
        frags : list of fragment shaders

        Note
        ----

        If several vertex shaders are specified, only one can contain the main
        function.

        If several fragment shaders are specified, only one can contain the main
        function.
        """

        GLObject.__init__(self)

        # Get all vertex shaders
        self._verts = []
        if type(verts) in [str, VertexShader]:
            verts = [verts]
        for shader in verts:
            if type(shader) is str:
                self._verts.append(VertexShader(shader))
            elif shader not in self._verts:
                self._verts.append(shader)

        # Get all fragment shaders
        self._frags = []
        if type(frags) in [str, FragmentShader]:
            frags = [frags]
        for shader in frags:
            if type(shader) is str:
                self._frags.append(FragmentShader(shader))
            elif shader not in self._frags:
                self._frags.append(shader)

        # Build uniforms and attributes
        self.build_uniforms()
        self.build_attributes()


    # ---------------------------------
    def attach(self, shaders):
        """ Attach one or several vertex/fragment shaders to the program. """

        if type(shaders) in [VertexShader, FragmentShader]:
            shaders = [shaders]
        for shader in shaders:
            if type(shader) is VertexShader:
                self._verts.append(shader)
            else:
                self._frags.append(shader)

        # Ensure uniqueness of shaders
        self._verts = list(set(self._verts))
        self._frags = list(set(self._frags))

        # Update dirty flag to induce a new build when necessary
        self._dirty  = True

        # Build uniforms and attributes
        self.build_uniforms()
        self.build_attributes()


    # ---------------------------------
    def detach(self, shaders):
        """Detach one or several vertex/fragment shaders from the program.

        Note
        ----

        We don't need to defer attach/detach shaders since shader deletion
        takes care of that.
        """

        if type(shaders) in [VertexShader, FragmentShader]:
            shaders = [shaders]
        for shader in shaders:
            if type(shader) is VertexShader:
                if shader in self._verts:
                    self._verts.remove(shader)
                else:
                    raise ShaderException("Shader is not attached to the program")
            if type(shader) is FragmentShader:
                if shader in self._frags:
                    self._frags.remove(shader)
                else:
                    raise ShaderException("Shader is not attached to the program")

        # Update dirty flag to induce a new build when necessary
        self._dirty = True

        # Build uniforms and attributes
        self.build_uniforms()
        self.build_attributes()


    # ---------------------------------
    def build(self):
        """
        Build (link) the program and checks everything's ok.

        A GL context must be available to be able to build (link)
        """

        # Check if linkage is needed
        if self.status and not self.dirty:
            return

        # Check if we have something to link
        if not self._verts:
            raise ProgramException("No vertex shader has been given")
        if not self._frags:
            raise ProgramException("No fragment shader has been given")

        # Check if program has been created
        if not self._handle:
            self._handle = gl.glCreateProgram()
            if not self._handle:
                raise ShaderException("Cannot create program object")

        # Detach any attached shaders
        attached = gl.glGetAttachedShaders(self._handle)
        for handle in attached:
            gl.glDetachShader(self._handle, handle)

        # Attach vertex and fragment shaders
        for shader in self._verts:
            gl.glAttachShader(self._handle, shader.handle)
        for shader in self._frags:
            gl.glAttachShader(self._handle, shader.handle)

        # Link the program
        gl.glLinkProgram(self._handle)
        if not gl.glGetProgramiv(self._handle, gl.GL_LINK_STATUS):
            print(gl.glGetProgramInfoLog(self._handle))
            raise ShaderException('Linking error')

        # Linkage ok
        self._status = True

        # Sane state
        self._dirty = False

        # Activate uniforms
        active_uniforms = [name for (name,gtype) in self.active_uniforms]
        for uniform in self._uniforms.values():
            if uniform.name in active_uniforms:
                uniform.active = True
            else:
                uniform.active = False

        # Activate attributes
        active_attributes = [name for (name,gtype) in self.active_attributes]
        for attribute in self._attributes.values():
            if attribute.name in active_attributes:
                attribute.active = True
            else:
                attribute.active = False



    # ---------------------------------
    def build_uniforms(self):
        """ Build the uniform objects """

        self._uniforms = {}
        texture_count = 1
        for (name,gtype) in self.all_uniforms:
            uniform = Uniform(self, name, gtype)
            if gtype in (gl.GL_SAMPLER_2D, gl.GL_SAMPLER_CUBE):
                uniform.texture_unit = texture_count
                texture_count += 1
            self._uniforms[name] = uniform


    # ---------------------------------
    def build_attributes(self):
        """ Build the attribute objects """

        self._attributes = {}
        for (name,gtype) in self.all_attributes:
            attribute = Attribute(self, name, gtype)
            self._attributes[name] = attribute


    # ---------------------------------
    def __setitem__(self, name, data):
        if name in self._uniforms.keys():
            self._uniforms[name].set_data(data)
            # If program is currently in use, we upload immediately the data
            # if self._bound:
            #    self._uniforms[name].upload_data(data)
        elif name in self._attributes.keys():
            self._attributes[name].set_data(data)
            # If program is currently in use, we upload immediately the data
            # if self._bound:
            #    self._attribute[name].upload_data(data)
        else:
            raise ProgramException("Unknown uniform or attribute")


    # ---------------------------------
    def activate(self):
        """Activate the program as part of current rendering state."""

        gl.glUseProgram(self.handle)


    # ---------------------------------
    def deactivate(self):
        """Deactivate the program."""

        gl.glUseProgram(0)


    # ---------------------------------
    def _get_all_uniforms(self):
        """Extract uniforms from shaders code """

        v_uniforms, f_uniforms = [], []
        for shader in self._verts:
            v_uniforms = shader.uniforms
        for shader in self._frags:
            f_uniforms = shader.uniforms
        uniforms = list(set(v_uniforms + f_uniforms))
        return uniforms
    all_uniforms = property(_get_all_uniforms,
        doc = """ Program uniforms obtained from shaders code """)


    # ---------------------------------
    def _get_active_uniforms(self):
        """ Extract active uniforms from GPU """

        count = gl.glGetProgramiv(self.handle, gl.GL_ACTIVE_UNIFORMS)
        # This match a name of the form "name[size]" (= array)
        regex = re.compile("""(?P<name>\w+)\s*(\[(?P<size>\d+)\])\s*""")
        uniforms = []
        for i in range(count):
            name, size, gtype = gl.glGetActiveUniform(self.handle, i)
            # This checks if the uniform is an array
            # Name will be something like xxx[0] instead of xxx
            m = regex.match(name)
            # When uniform is an array, size corresponds to the highest used index
            if m:
                name = m.group('name')
                if size >= 1:
                    for i in range(size):
                        name = '%s[%d]' % (m.group('name'),i)
                        uniforms.append((name, gtype))
            else:
                uniforms.append((name, gtype))

        return uniforms
    active_uniforms = property(_get_active_uniforms,
        doc = "Program active uniforms obtained from GPU")


    # ---------------------------------
    def _get_inactive_uniforms(self):
        """ Extract inactive uniforms from GPU """

        active_uniforms = self.active_uniforms
        inactive_uniforms = self.all_uniforms
        for uniform in active_uniforms:
            if uniform in inactive_uniforms:
                inactive_uniforms.remove(uniform)
        return inactive_uniforms
    inactive_uniforms = property(_get_inactive_uniforms,
        doc = "Program inactive uniforms obtained from GPU")


    # ---------------------------------
    def _get_all_attributes(self):
        """ Extract attributes from shaders code """

        v_attributes, f_attributes = [], []
        for shader in self._verts:
            v_attributes = shader.attributes
        # No attribute in fragment shaders
        # for shader in self._frags:
        #    f_attributes = shader.attributes
        attributes = list(set(v_attributes + f_attributes))
        return attributes
    all_attributes = property(_get_all_attributes,
        doc = "Program attributes obtained from shaders code")


    # ---------------------------------
    def _get_active_attributes(self):
        """ Extract active attributes from GPU """

        count = gl.glGetProgramiv(self.handle, gl.GL_ACTIVE_ATTRIBUTES)
        attributes = []

        # This match a name of the form "name[size]" (= array)
        regex = re.compile("""(?P<name>\w+)\s*(\[(?P<size>\d+)\])""")

        for i in range(count):
            name, size, gtype = gl.glGetActiveAttrib(self.handle, i)

            # This checks if the attribute is an array
            # Name will be something like xxx[0] instead of xxx
            m = regex.match(name)
            # When attribute is an array, size corresponds to the highest used index
            if m:
                name = m.group('name')
                if size >= 1:
                    for i in range(size):
                        name = '%s[%d]' % (m.group('name'),i)
                        attributes.append((name, gtype))
            else:
                attributes.append((name, gtype))
        return attributes
    active_attributes = property(_get_active_attributes,
        doc = "Program active attributes obtained from GPU")


    # ---------------------------------
    def _get_inactive_attributes(self):
        """ Extract inactive attributes from GPU """

        active_attributes = self.active_attributes
        inactive_attributes = self.all_attributes
        for attribute in active_attributes:
            if attribute in inactive_attributes:
                inacative_attributes.remove(attribute)
        return inactive_attributes
    inactive_attributes = property(_get_inactive_attributes,
        doc = "Program inactive attributes obtained from GPU")


    # ---------------------------------
    def _get_shaders(self):
        """ Get shaders list """

        shaders = []
        shaders.extend(self._verts)
        shaders.extend(self._frags)
        return shaders
    shaders = property(_get_shaders,
        doc = "List of shaders currently attached to this program")


    # ---------------------------------
    def draw(self, mode = gl.GL_TRIANGLES, first=0, count=None):
        """ Draw the attribute arrays in the specified mode.
        
        Parameters
        ----------
        mode : GL_ENUM
            GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP, 
            GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN

        first : int
            The starting vertex index in the vertex array. Default 0.

        count : int
            The number of vertices to draw. Default all.
        """

        self.activate()

        # Upload uniform
        uniforms = self._uniforms.values()
        for uniform in uniforms:
            uniform.upload_data()

        # Upload attributes
        attributes = self._attributes.values()
        for attribute in attributes:
            attribute.upload_data()

        # Get element count from first attribute
        # We need more tests here
        #  - do we have at least 1 attribute ?
        #  - does all attributes report same count ?
        count = (count or attributes[0].size) - first

        # Draw
        gl.glDrawArrays(mode, first, count)
        gl.glBindBuffer( gl.GL_ARRAY_BUFFER, 0 )

        self.deactivate()
