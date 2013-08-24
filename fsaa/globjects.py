"""
Some collected classes that wrap OpenGl objects.
These shoulde be put in vispy (properly redisigned) soon.
"""


import ctypes
import OpenGL.GL as gl
import numpy as np
import OpenGL.GL.framebufferobjects as glfbo

# Dict that maps numpy datatypes to openGL data types
dtypes = {  'uint8':gl.GL_UNSIGNED_BYTE,    'int8':gl.GL_BYTE,
            'uint16':gl.GL_UNSIGNED_SHORT,  'int16':gl.GL_SHORT, 
            'uint32':gl.GL_UNSIGNED_INT,    'int32':gl.GL_INT, 
            'float32':gl.GL_FLOAT }

# From visvis
class TextureObject(object):
    """ TextureObject(texType)
    
    Basic texture class that wraps an OpenGl texture. It manages the OpenGl
    class and exposes a rather high-level interface to it.
    
    texType is one of gl.GL_TEXTURE_1D, gl.GL_TEXTURE_2D, gl.GL_TEXTURE_3D
    and specifies whether this is a 1D, 2D or 3D texture.
    
    Exposed methods:
      * Enable() call be for using
      * Disable() call after using
      * SetData() update the data    
      * DestroyGl() remove only the texture from OpenGl memory.
      * Destroy() remove textures and reference to data.
        
    Note: this is not a Wobject nor a Wibject.
    
    """
    
    # One could argue to use polymorphism to implement 3 classes: one for 
    # each dimension. Yes you could, but the way to handle the data and
    # communicate with OpenGl is so similar I chose not to. I use the
    # texType to determine which function to call. 
    
    def __init__(self, ndim):
        
        # Check given texture type
        if ndim not in [1,2,3]:
            raise ValueError('Texture ndim should be 1, 2 or 3.')
        
        # Store the number of dimensions. This attribute is used to make the 
        # choices for which OpenGl functions to use etc.
        self._ndim = ndim
        
        # Store the texture type, as we can determine it easily.
        tmp = {1:gl.GL_TEXTURE_1D, 2:gl.GL_TEXTURE_2D, 3:gl.GL_TEXTURE_3D}
        self._texType = tmp[ndim]
        
        self._interpolate = False
        
        # Texture ID. This is an integer by which OpenGl identifies the 
        # texture.
        self._texId = 0
        
        # To store the used texture unit so we can disable it properly.
        self._texUnit = -1
        self._useTexUnit = False # set to True if OpenGl version high enough
        
        # A reference (not a weak one) to the original data as given with 
        # SetData. We need this in order to re-upload the texture if it is 
        # moved to another OpenGl context (other figure).
        # Note that the self._shape does not have to be self._dataRef.shape.
        self._dataRef = None
        
        # The shape of the data as uploaded to OpenGl. Is None if no
        # data was uploaded. Note that the self._shape does not have to 
        # be self._dataRef.shape; the data might be downsampled.
        self._shape = None
        
        # A flag to indicate that the data in self._dataRef should be uploaded.
        # 1 signifies an update is required.
        # 2 signifies an update is required, with padding zeros.
        # -1 signifies the current data uploaded ok.
        # -2 ignifies the current data uploaded ok with padding.
        # 0 signifies failure of uploading
        self._uploadFlag = 1
        
        # Flag to indicate whether we can use this
        self._canUse = False
    
    
    def Enable(self, texUnit=0):
        """ Enable(texUnit)
        
        Enable the texture, using the given texture unit (max 9).
        If necessary, will upload/update the texture in OpenGl memory now.
        
        If texUnit is -1, will not bind the texture.
        
        """ 
        
        # Did we fail uploading texture last time?
        troubleLastTime = (self._uploadFlag==0)
        
        # If texture invalid, tell to upload, but only if we have a chance
        if self._texId == 0 or not gl.glIsTexture(self._texId):
            if not troubleLastTime:
                # Only if not in failure mode
                self._uploadFlag = abs(self._uploadFlag)
        
        # Store texture-Unit-id, and activate. Do before calling _setDataNow!
        if texUnit >= 0:
            self._texUnit = texUnit
            self._useTexUnit = True#getOpenGlCapable('1.3')        
            if self._useTexUnit:
                gl.glActiveTexture( gl.GL_TEXTURE0 + texUnit )   # Opengl v1.3
        
        # If we should upload/update, do that now. (SetData also sets the flag)
        if self._uploadFlag > 0:
            self._SetDataNow()
        
        # check if ok now
        if not gl.glIsTexture(self._texId):
            if not troubleLastTime:
                print("Warning enabling texture, the texture is not valid. " + 
                        "(Hiding message for future draws.)")
            return
        
        # Enable texturing, and bind to texture
        if texUnit >= 0:
            gl.glEnable(self._texType)
            gl.glBindTexture(self._texType, self._texId)
    
    
    def Disable(self):
        """ Disable()
        
        Disable the texture. It's safe to call this, even if the texture
        was not enabled.
        
        """
        
        # No need to disable. Also, if disabled because system does not
        # know 3D textures, we can not call glDisable with that arg.
        if self._uploadFlag == 0:
            return
        
        # Select active texture if we can
        if self._texUnit >= 0 and self._useTexUnit:
            gl.glActiveTexture( gl.GL_TEXTURE0 + self._texUnit )            
            self._texUnit = -1
        
        # Disable
        gl.glDisable(self._texType)
        
        # Set active texture unit to default (0)
        if self._useTexUnit:
            gl.glActiveTexture( gl.GL_TEXTURE0 )
    
   
    def SetData(self, data):
        """ SetData(data)
        
        Set the data to display. If possible, will update the data in the
        existing texture (is possible if of the same shape).
        
        """
        
        # check data
        if not isinstance(data, np.ndarray):
            raise ValueError("Data should be a numpy array.")
        
        # check shape (raises ValueError if not ok)
        try:
            self._GetFormat(data.shape)
        except ValueError:
            raise # reraise from here
        
        # ok, store data and raise flag
        self._dataRef = data        
        self._uploadFlag = abs(self._uploadFlag)
    
    
    def _SetDataNow(self):
        """ Make sure the data in self._dataRef is uploaded to 
        OpenGl memory. If possible, update the data rather than 
        create a new texture object.
        """
        
        # Test whether padding to a factor of two is required
        needPadding = (abs(self._uploadFlag) == 2)
        needPadding = needPadding or not True#getOpenGlCapable('2.0')
        
        # Set flag in case of failure (set to success at the end)
        # If we tried without padding, we can still try with padding.
        # Note: In theory, getOpenGlCapable('2.0') should be enough to
        # determine if padding is required. However, bloody ATI drivers
        # sometimes need 2**n textures even if OpenGl > 2.0. (I've 
        # encountered this with someones PC and verified that the current
        # solution solves this.)
        if needPadding:
            self._uploadFlag = 0 # Give up
        else:
            self._uploadFlag = 2 # Try with padding next time
        
        # Get data. 
        if self._dataRef is None:
            return
        data = self._dataRef
        
        # older OpenGl versions do not know about 3D textures
        if self._ndim==3 and not getOpenGlCapable('1.2','3D textures'):
            return
        
        # Convert data type to one supported by OpenGL
        if data.dtype.name not in dtypes:
            # Long integers become floats; int32 would not have enough range
            if data.dtype in (np.int64, np.uint64):
                data = data.astype(np.float32)
            # Bools become bytes
            elif data.dtype == np.bool:
                data = data.astype(np.uint8)
            else:
                # Make singles in all other cases (e.g. np.float64, np.float128)
                # We cannot explicitly use float128, since its not always defined
                data = data.astype(np.float32)
        
        # Determine type
        thetype = data.dtype.name
        if not thetype in dtypes:
            # this should not happen, since we convert incompatible types
            raise ValueError("Cannot convert datatype %s." % thetype)
        gltype = dtypes[thetype]
        
        # Determine format
        internalformat, format = self._GetFormat(data.shape)
        
        # Can we update or should we upload?        
        
        if (    gl.glIsTexture(self._texId) and 
                self._shape and (data.shape == self._shape) ):
            # We can update.
            
            # Bind to texture
            gl.glBindTexture(self._texType, self._texId)
            
            # update            
            self._UpdateTexture(data, internalformat, format, gltype)
        
        else:
            # We should upload.
            
            # Remove any old data. 
            self.DestroyGl()
            
            # Create texture object
            self._texId = gl.glGenTextures(1)
            
            # Bind to texture
            gl.glBindTexture(self._texType, self._texId)
            
            # Should we make the image a power of two?
            if needPadding:
                data2 = makePowerOfTwo(data, self._ndim)
                if data2 is not data:
                    data = data2
                    print("Warning: the data was padded to make it a power of two.")
            
            # test whether it fits, downsample if necessary
            ok, count = False, 0
            while not ok and count<8:
                ok = self._TestUpload(data, internalformat,format,gltype)
                if not ok:
                #if count<2 and data.shape[0]<1000: # for testing
                    data = downSample(data, self._ndim)
                    count += 1
            
            # give warning or error
            if count and not ok:                
                raise MemoryError(  "Could not upload texture to OpenGL, " +
                                    "even after 8 times downsampling.")
            elif count:
                print(  "Warning: data was downscaled " + str(count) + 
                        " times to fit it in OpenGL memory." )
            
            # upload!
            self._UploadTexture(data, internalformat, format, gltype)
            
            # keep reference of data shape (as loaded to opengl)
            self._shape = data.shape
        
        # flag success
        if needPadding:
            self._uploadFlag = -2
        else:
            self._uploadFlag = -1
    
    
    def _UpdateTexture(self, data, internalformat, format, gltype):
        """ Update an existing texture object. It should have been 
        checked whether this is possible (same shape).
        """
        gl.glBindTexture(self._texType, self._texId)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP);
        filter = [gl.GL_NEAREST, gl.GL_LINEAR][self._interpolate]
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, filter);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, filter);
        
        # define dict
        D = {   1: (gl.glTexSubImage1D, gl.GL_TEXTURE_1D),
                2: (gl.glTexSubImage2D, gl.GL_TEXTURE_2D),
                3: (gl.glTexSubImage3D, gl.GL_TEXTURE_3D)}
        
        # determine function and target from texType
        uploadFun, target = D[self._ndim]
        
        # Build argument list
        shape = [i for i in reversed( list(data.shape[:self._ndim]) )]
        args = [target, 0] + [0 for i in shape] + shape + [format,gltype,data]
        
        # Upload!
        uploadFun(*tuple(args))
    
    
    def _TestUpload(self, data, internalformat, format, gltype):
        """ Test whether we can create a texture of the given shape.
        Returns True if we can, False if we can't.
        """
        
        # define dict
        D = {   1: (gl.glTexImage1D, gl.GL_PROXY_TEXTURE_1D),
                2: (gl.glTexImage2D, gl.GL_PROXY_TEXTURE_2D),
                3: (gl.glTexImage3D, gl.GL_PROXY_TEXTURE_3D)}
        
        # determine function and target from texType
        uploadFun, target = D[self._ndim]
        
        # build args list
        shape = [i for i in reversed( list(data.shape[:self._ndim]) )]
        args = [target, 0, internalformat] + shape + [0, format, gltype, None]
        
        # do fake upload
        uploadFun(*tuple(args))
        
        # test and return
        ok = gl.glGetTexLevelParameteriv(target, 0, gl.GL_TEXTURE_WIDTH)
        return bool(ok)
    
    
    def _UploadTexture(self, data, internalformat, format, gltype):
        """ Upload a texture to the current texture object. 
        It should have been verified that the texture will fit.
        """
        
        gl.glBindTexture(self._texType, self._texId)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP);
        filter = [gl.GL_NEAREST, gl.GL_LINEAR][self._interpolate]
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, filter);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, filter);
        
        # define dict
        D = {   1: (gl.glTexImage1D, gl.GL_TEXTURE_1D),
                2: (gl.glTexImage2D, gl.GL_TEXTURE_2D),
                3: (gl.glTexImage3D, gl.GL_TEXTURE_3D)}
        
        # determine function and target from texType
        uploadFun, target = D[self._ndim]
        
        # build args list
        shape = [i for i in reversed( list(data.shape[:self._ndim]) )]
        args = [target, 0, internalformat] + shape + [0, format, gltype, data]
        
        # call
        uploadFun(*tuple(args))
    
    
    def _GetFormat(self, shape):
        """ Get internalformat and format, based on the self._ndim
        and the shape. If the shape does not match with the texture
        type, an exception is raised.
        """
        
        if self._ndim == 1:
            if len(shape)==1:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE
            elif len(shape)==2 and shape[1] == 1:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE
            elif len(shape)==2 and shape[1] == 3:
                iformat, format = gl.GL_RGB, gl.GL_RGB
            elif len(shape)==2 and shape[1] == 4:
                iformat, format = gl.GL_RGBA, gl.GL_RGBA
            else:
                raise ValueError("Cannot create 1D texture, data of invalid shape.")
        
        elif self._ndim == 2:
        
            if len(shape)==2:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE                
            elif len(shape)==3 and shape[2]==1:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE
            elif len(shape)==3 and shape[2]==3:
                iformat, format = gl.GL_RGB, gl.GL_RGB
            elif len(shape)==3 and shape[2]==4:
                iformat, format = gl.GL_RGBA, gl.GL_RGBA
            else:
                raise ValueError("Cannot create 2D texture, data of invalid shape.")
        
        elif self._ndim == 3:
        
            if len(shape)==3:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE
            elif len(shape)==4 and shape[3]==1:
                iformat, format = gl.GL_LUMINANCE8, gl.GL_LUMINANCE
            elif len(shape)==4 and shape[3]==3:
                iformat, format = gl.GL_RGB, gl.GL_RGB
            elif len(shape)==4 and shape[3]==4:
                iformat, format = gl.GL_RGBA, gl.GL_RGBA
            else:
                raise ValueError("Cannot create 3D texture, data of invalid shape.")
        
        else:
            raise ValueError("Cannot create a texture with these dimensions.")
        
        return iformat, format
    
    
    def DestroyGl(self):
        """ DestroyGl()
        
        Removes the texture from OpenGl memory. The internal reference
        to the original data is kept though.
        
        """
        try:
            if self._texId > 0:
                gl.glDeleteTextures([self._texId])
        except Exception:
            pass
        self._texId = 0
    
    
    def Destroy(self):
        """ Destroy()
        
        Really destroy data. 
        
        """  
        # remove OpenGl bits      
        self.DestroyGl()
        # remove internal reference
        self._dataRef = None
        self._shape = None
    
    
    def __del__(self):
        self.Destroy()




class ShaderException(Exception):
    pass

# From Nicolas Rougier
class Shader:
    def __init__(self, vertex_code = None, fragment_code = None):
        self.uniforms = {}
        self.handle = gl.glCreateProgram()
        self.linked = False
        self._build_shader(vertex_code, gl.GL_VERTEX_SHADER)
        self._build_shader(fragment_code, gl.GL_FRAGMENT_SHADER)
        self._link()

    def _build_shader(self, strings, shader_type):
        if not strings:
            return
        count = len(strings)
        if count < 1: 
            return
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, strings)
        gl.glCompileShader(shader)
        status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if not status:
            if shader_type == gl.GL_VERTEX_SHADER:
                print(gl.glGetShaderInfoLog(shader))
                raise (ShaderException, 'Vertex compilation error')
            elif shader_type == gl.GL_FRAGMENT_SHADER:
                print(gl.glGetShaderInfoLog(shader))
                raise (ShaderException, 'Fragment compilation error')
            else:
                print(gl.glGetShaderInfoLog(shader))
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
            log = gl.glGetProgramInfoLog(self.handle)
            raise ShaderException('Linking: '+ log)
        else:
            self.linked = True

    def bind(self):
        gl.glUseProgram(self.handle)

    def unbind(self):
        gl.glUseProgram(0)

    def uniformf(self, name, *vals):
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name.encode('utf-8')))
        self.uniforms[name] = loc
        if len(vals) in range(1, 5):
            { 1 : gl.glUniform1f,
              2 : gl.glUniform2f,
              3 : gl.glUniform3f,
              4 : gl.glUniform4f
            }[len(vals)](loc, *vals)

    def uniformi(self, name, *vals):
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name.encode('utf-8')))
        self.uniforms[name] = loc
        if len(vals) in range(1, 5):
            { 1 : gl.glUniform1i,
              2 : gl.glUniform2i,
              3 : gl.glUniform3i,
              4 : gl.glUniform4i
            }[len(vals)](loc, *vals)

    def uniform_matrixf(self, name, mat):
        loc = self.uniforms.get(name, gl.glGetUniformLocation(self.handle,name))
        self.uniforms[name] = loc
        gl.glUniformMatrix4fv(loc, 1, False, mat)


class RenderTexture(TextureObject):
    """ Eventually we want just one do-it-all texture class... 
    Or perhaps one for each dimension.
    """
    def create_empty_texture(self, width, height, filter=gl.GL_LINEAR):
        self._texId = gl.glGenTextures(1)
        gl.glBindTexture(self._texType, self._texId)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, filter);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, filter);
        
        data = None
        gl.glTexImage2D(self._texType, 0, gl.GL_RGBA8, width, height, 0, gl.GL_BGRA, gl.GL_UNSIGNED_BYTE, data)


class FrameBuffer:
    """ http://www.songho.ca/opengl/gl_fbo.html
    
    The framebuffer is a structure that holds render targets.
    Switching between FBO's is slow. Switching its components (i.e. targets)
    is fast.
    Render buffer objects function as a render target, without having the
    functionality of a normal texture. Used for depth and stencil buffer.
    """
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._id = -1
        self._id = glfbo.glGenFramebuffers(1)
        self._depthbuffer = -1
    
    def attach_texture(self, texture):
        glfbo.glBindFramebuffer(glfbo.GL_FRAMEBUFFER, self._id)
        # Attach texture to this FBO
        glfbo.glFramebufferTexture2DEXT(glfbo.GL_FRAMEBUFFER, 
                glfbo.GL_COLOR_ATTACHMENT0_EXT, texture._texType, texture._texId, 0);
    
    def add_depth_buffer(self):
        # Create render buffer for depth
        id = glfbo.glGenRenderbuffers(1)
        glfbo.glBindRenderbuffer(glfbo.GL_RENDERBUFFER, id)
        glfbo.glRenderbufferStorage(glfbo.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, self._width, self._height)
        # Attach render buffer to this FBO
        glfbo.glFramebufferRenderbuffer(glfbo.GL_FRAMEBUFFER, 
                glfbo.GL_DEPTH_ATTACHMENT_EXT, glfbo.GL_RENDERBUFFER, id)
        self._depthbuffer = id
    
    def check(self):
        status = glfbo.glCheckFramebufferStatus(glfbo.GL_FRAMEBUFFER)
        if int(status) != int(glfbo.GL_FRAMEBUFFER_COMPLETE):
            # should probably be a FrameBufferError or something?
            raise RuntimeError('Current framebuffer configuration is not supported.')
    
    def enable(self):
        glfbo.glBindFramebuffer(glfbo.GL_FRAMEBUFFER, self._id);
    
    def disable(self):
        glfbo.glBindFramebuffer(glfbo.GL_FRAMEBUFFER, 0);