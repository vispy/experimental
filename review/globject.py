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
import numpy as np
import OpenGL.GL as gl


# ------------------------------------------------------------- gl_typeinfo ---
gl_typeinfo = {
    gl.GL_FLOAT        : ( 1, gl.GL_FLOAT,        np.float32),      
    gl.GL_FLOAT_VEC2   : ( 2, gl.GL_FLOAT,        np.float32),      
    gl.GL_FLOAT_VEC3   : ( 3, gl.GL_FLOAT,        np.float32),      
    gl.GL_FLOAT_VEC4   : ( 4, gl.GL_FLOAT,        np.float32),      
    gl.GL_INT          : ( 1, gl.GL_INT,          np.int32),        
    gl.GL_INT_VEC2     : ( 2, gl.GL_INT,          np.int32),        
    gl.GL_INT_VEC3     : ( 3, gl.GL_INT,          np.int32),        
    gl.GL_INT_VEC4     : ( 4, gl.GL_INT,          np.int32),        
    gl.GL_BOOL         : ( 1, gl.GL_BOOL,         np.bool),         
    gl.GL_BOOL_VEC2    : ( 2, gl.GL_BOOL,         np.bool),         
    gl.GL_BOOL_VEC3    : ( 3, gl.GL_BOOL,         np.bool),         
    gl.GL_BOOL_VEC4    : ( 4, gl.GL_BOOL,         np.bool),         
    gl.GL_FLOAT_MAT2   : ( 4, gl.GL_FLOAT,        np.float32),      
    gl.GL_FLOAT_MAT3   : ( 9, gl.GL_FLOAT,        np.float32),      
    gl.GL_FLOAT_MAT4   : (16, gl.GL_FLOAT,        np.float32),      
    gl.GL_SAMPLER_2D   : ( 1, gl.GL_UNSIGNED_INT, np.uint32),
    gl.GL_SAMPLER_CUBE : ( 1, gl.GL_UNSIGNED_INT, np.uint32) }



# ------------------------------------------------- GLObjectException class ---
class GLObjectException(Exception):
    """ GLObject exception class """
    pass



# ----------------------------------------------------------- Program class ---
class GLObject(object):
    """
    A GLObject is an object that is present in GPU memory (once build).

    All GPU operations are deferred until the object is actually used in a
    rendering process.
    """

    # Internal id counter to keep track of created objects
    _idcount = 0

    # ---------------------------------
    def __init__(self):
        """ Initialize the object """

        # Name of this object in GPU
        self._handle = 0

        # Whether object needs update
        self._dirty = True

        # Build status
        self._status = False

        # Object type
        self._type = 0

        # Object internal id
        self._id = GLObject._idcount+1
        GLObject._idcount += 1


    # ---------------------------------
    def __enter__(self):
        """ Entering context  """

        self.activate()
        return self

    
    # ---------------------------------
    def __exit__(self, type, value, traceback):
        """ Exiting context """

        self.deactivate()
        return True


    # ---------------------------------
    def delete(self):
        """ Delete the object from GPU (if it was present) """

        pass


    # ---------------------------------
    def build(self):
        """ Build the object into GPU (a GL context must be available)  """

        pass


    # ---------------------------------
    def update(self):
        """ Synchronize CPU and GPU (a GL context must be available) """

        pass


    # ---------------------------------
    def activate(self):
        """ Activate the object  (a GL context must be available) """

        pass


    # ---------------------------------
    def deactivate(self):
        """ Deactivate the object """

        pass


    # ---------------------------------
    def _get_dirty(self):
        """ Get dirty flag (indicating if object needs updated) """
        return self._dirty
    dirty = property(_get_dirty, doc = "Whether object needs update")


    # ---------------------------------
    def _get_status(self):
        """ Get object build status """
        return self._status
    status = property(_get_status, doc = "Object build status ")


    # ---------------------------------
    def _get_handle(self):
        """ Get object name (and build the object if necessary) """
        if not self._handle:
            self.build()
        return self._handle
    handle = property(_get_handle, doc = "Object name in GPU")


    # ---------------------------------
    def _get_type(self):
        """ Get object type """
        return self._type
    type = property(_get_type, doc = "Object type")


    # ---------------------------------
    def _get_id(self):
        """ Get object internal identity """
        return self._id
    id = property(_get_id, doc = "Object internal id")
