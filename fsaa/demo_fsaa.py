#!/usr/bin/env python
# Copyright (C) 2013 Almar Klein

""" Demo code for FSAA (full screen anti-alisaing)

Demoing a variety of FSAA techniques. There are two demos, one on which
a selected technique is applied to a test image. Another where it
is applied to a set of rotating stars. See the bottom of the file for
the user settings.

It seems like the two most familiar techniques, FXAA and SMAA dont
perform so well on the kind of data that we're interested in.

It seems we need to look at techniques that blur in the direction of
edges. DDAA seems the best candidate so far. And of course SSAA 
creates beautiful results.

Note: DDAA suffers some artifacts (undersmoothing) at near-horizontal
and near-vertical edges. I expect that we can do something about this.
Perhaps it would make a nice student assignment to improve, tweak, and
validate the algorithm, bases on a range of different input data.

Note: Most of the code in this file is terribly inefficient, with shaders
being created on every draw and stuff like that ... sorry.

"""

import os
import sys
import time

import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu

import OpenGL.GL.framebufferobjects as glfbo

from globjects import TextureObject, Shader, RenderTexture, FrameBuffer

import vispy.app
vispy.app.use('pyglet')


def orthographic( left, right, bottom, top, znear, zfar ):
    assert( right  != left )
    assert( bottom != top  )
    assert( znear  != zfar )
    
    M = np.zeros((4,4), dtype=np.float32)
    M[0,0] = +2.0/(right-left)
    M[3,0] = -(right+left)/float(right-left)
    M[1,1] = +2.0/(top-bottom)
    M[3,1] = -(top+bottom)/float(top-bottom)
    M[2,2] = -2.0/(zfar-znear)
    M[3,2] = -(zfar+znear)/float(zfar-znear)
    M[3,3] = 1.0
    return M


def render_scene(smooth=False, scale=1.0):
    """ OpenGL calls to render a test scene.
    """
    if smooth:
        gl.glEnable(gl.GL_LINE_SMOOTH)
    #
    gl.glLineWidth(3.0*scale)
    gl.glColor(0.2, 0.8, 0.5)
    gl.glBegin(gl.GL_LINE_STRIP)
    gl.glVertex2f(0.2, 0.6)
    gl.glVertex2f(0.7, 0.8)
    gl.glVertex2f(0.3, 0.1)
    gl.glVertex2f(0.2, 0.4)
    gl.glEnd()
    # Big circle
    gl.glLineWidth(1.0*scale)
    gl.glColor(0, 0, 0)
    gl.glBegin(gl.GL_LINE_STRIP)
    for r in np.linspace(0, 2*np.pi, 100):
        gl.glVertex2f(np.sin(r)*0.4+0.5, np.cos(r)*0.4+0.5)
    gl.glEnd()
    # Stripes
    gl.glLineWidth(1.0*scale)
    gl.glColor(0, 0, 0)
    gl.glBegin(gl.GL_LINE_STRIP)
    for r in np.linspace(0, 0.5*np.pi, 16):
        gl.glVertex2f(0.3, 0.3)
        gl.glVertex2f(np.sin(r)*0.5+0.3, np.cos(r)*0.5+0.3)
    gl.glEnd()
    # Filled square
    gl.glColor(0, 0, 0.5)
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(0.1, 0.1); gl.glVertex2f(0.1, 0.2); 
    gl.glVertex2f(0.2, 0.2); gl.glVertex2f(0.2, 0.1); 
    gl.glEnd()
    # empty square
    gl.glLineWidth(1.0*scale)
    gl.glColor(0, 0, 0.5)
    gl.glBegin(gl.GL_LINE_STRIP)
    gl.glVertex2f(0.8, 0.8); gl.glVertex2f(0.8, 0.9); 
    gl.glVertex2f(0.9, 0.9); gl.glVertex2f(0.9, 0.8);  gl.glVertex2f(0.8, 0.8);
    gl.glEnd()
    # Small filled circle
    gl.glColor(0.5, 0, 0)
    gl.glBegin(gl.GL_POLYGON)
    for r in np.linspace(0, 2*np.pi, 100):
        gl.glVertex2f(np.sin(r)*0.05+0.85, np.cos(r)*0.05+0.15)
    gl.glEnd()
    # Small circle
    gl.glLineWidth(1.0*scale)
    gl.glColor(0.5, 0, 0)
    gl.glBegin(gl.GL_LINE_STRIP)
    for r in np.linspace(0, 2*np.pi, 100):
        gl.glVertex2f(np.sin(r)*0.05+0.15, np.cos(r)*0.05+0.85)
    gl.glEnd()
    #
    gl.glColor(1,1,1,1)
    gl.glDisable(gl.GL_LINE_SMOOTH)



class CircleDemo(vispy.app.Canvas):
    
    def __init__(self, technique, preaa=False):
        vispy.app.Canvas.__init__(self)
        
        self._npasses = 1
        if technique[-1] in '0123456789':
            self._npasses = int(technique[-1])
            technique = technique[:-1]
        self._technique = technique
        self._preaa = preaa
        # Load different parts of shader code.
        self._shader_code = self.load_shader_code(technique)
        
    
    def load_shader_code(self, technique):
        fname = os.path.join(os.path.dirname(__file__), technique+'.glsl')
        SHADER = open(fname , 'rb').read().decode('ascii', 'ignore')
        return SHADER.split('='*80)
    
    def initialize_event(self, event):
        pass
    
    def on_paint(self, event):
        
        w,h = W, H
        scale = 1
        aakernel = None
        if self._technique == 'ssaa':
            scale = 3  # Make this 2, 3, 4 ... for 4x, 9x, 16x aa
            w, h = W*scale, H*scale
        
        # Set up FBO
        fb = FrameBuffer(w, h)
        tex = RenderTexture(2)
        tex.create_empty_texture(w, h) # Must match depth buffer!
        fb.attach_texture(tex)
        fb.add_depth_buffer()
        fb.check()
        
        # Draw scene off-screen
        fb.enable()
        gl.glClearColor(1,1,1,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.setup_scene(0, 0, w, h)
        if self._preaa:
            render_scene(True, scale)
        else:
            render_scene(False, scale)
        fb.disable()
        
        # Pergorm aa
        if self._technique == 'ssaa':
            self._pass_ssaa(tex, w, h, scale)
        elif self._technique == 'smaa':
            self._pass_smaa(tex)
        else:
            self._pass_aa(tex)
        
        # Draw original to screen too
        self.setup_scene(W, 0, W, H)
        render_scene()
        
        # And original but smoothed
        self.setup_scene(2*W, 0, W, H)
        render_scene(smooth=True)
        
        # Now blit texture to backbuffer
        self._backend._vispy_swap_buffers() # todo: private attr!
    
    
    def setup_scene(self, *args):
        """ Set viewport (with args) and projection matrices.
        """
        gl.glViewport(*args);
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity();
        glu.gluOrtho2D(0.0, 1.0, 0.0, 1.0);
        gl.glMatrixMode(gl.GL_MODELVIEW);
        gl.glLoadIdentity();
        
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_BLEND)
    
    
    def _pass_aa(self, tex):
        if self._npasses == 1:
            # Prepare for drawing texture to screen
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H)
            tex.Enable(0)
            shader = Shader(None, self._shader_code[0])
            shader.bind()
            shader.uniformf('shape', W, H)
            shader.uniformi('texture', 0)
            # Draw texture to screen
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            shader.unbind()
            tex.Disable()
            return
        
        # We get here only if npasses != 1
        
        for i in range(self._npasses):
            # Create frame buffer to render to
            fb = fb_edges = FrameBuffer(W, H)
            resultTex = RenderTexture(2)
            resultTex.create_empty_texture(W, H) # Must match depth buffer!
            fb.attach_texture(resultTex)
            fb.add_depth_buffer()
            fb.enable()
            # Prepare for drawing texture to screen
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H)
            tex.Enable(0)
            shader = Shader(None, self._shader_code[0])
            shader.bind()
            shader.uniformf('shape', W, H)
            shader.uniformi('texture', 0)
            # Draw texture to screen
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            shader.unbind()
            tex.Disable()
            fb.disable()
            # Prepare for next round
            tex = resultTex
        
        # Prepare for drawing texture to screen
        gl.glClearColor(1,1,1,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.setup_scene(0, 0, W, H)
        tex.Enable(0)
        # Draw texture to screen
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord(0,0); gl.glVertex(0,0); 
        gl.glTexCoord(0,1); gl.glVertex(0,1); 
        gl.glTexCoord(1,1); gl.glVertex(1,1); 
        gl.glTexCoord(1,0); gl.glVertex(1,0); 
        gl.glEnd()
        tex.Disable()
        
    
    
    def _pass_ssaa(self, tex, w, h, scale):
        # Select Lanczos kernel based on scale.
        aakernel = [None, None,
                    [0.44031130485056913, 0.29880437751590694, 0.04535643028360444, -0.06431646022479595],
                    [0.2797564513818748, 0.2310717037833796, 0.11797652759318597, 0.01107354293249700],
                ][scale]
        
        # Prepare for drawing texture to screen
        gl.glClearColor(1,1,1,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.setup_scene(0, 0, W, H)
        tex.Enable(0)
        shader = Shader(None, self._shader_code[0])
        shader.bind()
        shader.uniformf('shape', w, h) # resolution of previous pass
        shader.uniformi('texture', 0)
        if aakernel:
            shader.uniformf('aakernel', *aakernel)
        
        # Draw texture to screen
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord(0,0); gl.glVertex(0,0); 
        gl.glTexCoord(0,1); gl.glVertex(0,1); 
        gl.glTexCoord(1,1); gl.glVertex(1,1); 
        gl.glTexCoord(1,0); gl.glVertex(1,0); 
        gl.glEnd()
        shader.unbind()
        tex.Disable()
    
    
    def _pass_smaa(self, tex):
        # Get precomputed textures
        from smaa_tex import getSearchTex, getAreaTex
        searchTex = RenderTexture(2)
        searchTex.SetData(getSearchTex())
        areaTex = RenderTexture(2)
        areaTex._interpolate = True # Enforce GL_LINEAR
        areaTex.SetData(getAreaTex())
        
        # Compose shader code
        bigOne = self._shader_code[-1]
        edgeVertex = bigOne + self._shader_code[0]
        edgeFragment = bigOne + self._shader_code[1]
        blendVertex = bigOne + self._shader_code[2]
        blendFragment = bigOne + self._shader_code[3]
        neighborhoodVertex = bigOne + self._shader_code[4]
        neighborhoodFragment = bigOne + self._shader_code[5]
        
        
        if True: # Pass 1
            fb = fb_edges = FrameBuffer(W, H)
            edgesTex = RenderTexture(2)
            edgesTex.create_empty_texture(W, H) # Must match depth buffer!
            fb.attach_texture(edgesTex)
            fb.add_depth_buffer()
            #
            fb.enable()
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H); gl.glDisable(gl.GL_BLEND)
            #
            shader = Shader(edgeVertex, edgeFragment)
            shader.bind()
            tex.Enable(0)
            shader.uniformi('texture', 0)
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            fb.disable()
            tex.Disable()
            shader.unbind()
        
        if True: # Pass 2
            fb = FrameBuffer(W, H)
            blendTex = RenderTexture(2)
            blendTex.create_empty_texture(W, H) # Must match depth buffer!
            fb.attach_texture(blendTex)
            fb.add_depth_buffer()
            #
            fb.enable()
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H); gl.glDisable(gl.GL_BLEND)
            #
            shader = Shader(blendVertex, blendFragment)
            shader.bind()
            edgesTex.Enable(0)
            areaTex.Enable(1)
            searchTex.Enable(2)
            shader.uniformi('edge_tex', 0)
            shader.uniformi('area_tex', 1)
            shader.uniformi('search_tex', 2)
            #
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            fb.disable()
            edgesTex.Disable()
            areaTex.Disable()
            searchTex.Disable()
            shader.unbind()
        
        if True: # Pass 3
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H); gl.glDisable(gl.GL_BLEND)
            #
            shader = Shader(neighborhoodVertex, neighborhoodFragment)
            shader.bind()
            tex.Enable(0)
            blendTex.Enable(1)
            shader.uniformi('texture', 0)
            shader.uniformi('blend_tex', 1)
            #
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            tex.Disable()
            blendTex.Disable()
            shader.unbind()
    



class StarDemo(CircleDemo):
    def __init__(self, *args):
        CircleDemo.__init__(self, *args)
        
        self._raw = False
        self._play = True
        
        # Calculate loads of stars
        self._N = N = 100
        self._x = np.random.uniform(size=N)
        self._y = np.random.uniform(size=N)
        self._s = np.random.uniform(0.02, 0.1, size=N)
        self._a = np.random.uniform(0.0, np.pi, size=N)
        self._w = np.random.uniform(1, 4, size=N)
        # Color!
        self._r = np.random.uniform(size=N)
        self._g = np.random.uniform(size=N)
        self._b = np.random.uniform(size=N)
    
    def on_key_press(self, event):
        if event.type == 'key_press':
            if event.key == 'Space':
                self._raw = not self._raw
            elif event.text == 's':
                self._play = not self._play
    
    def on_paint(self, event):
        
        w,h = W, H
        scale = 1
        aakernel = None
        if self._technique == 'ssaa':
            scale = 3  # Make this 2, 3, 4 ... for 4x, 9x, 16x aa
            w, h = W*scale, H*scale
        
        # Set up FBO
        if hasattr(self, '_fb'):
            fb = self._fb
            tex = self._tex
        else:
            fb = FrameBuffer(w, h)
            tex = RenderTexture(2)
            tex.create_empty_texture(w, h) # Must match depth buffer!
            fb.attach_texture(tex)
            fb.add_depth_buffer()
            fb.check()
            #
            self._fb = fb
            self._tex = tex
        
        # Draw scene off-screen
        fb.enable()
        gl.glClearColor(1,1,1,1);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.setup_scene(0, 0, w, h)
        if self._preaa:
            self._draw_stars(True, scale)
        else:
            self._draw_stars(False, scale)
        fb.disable()
        
        # Pergorm aa
        if self._raw:
            # Prepare for drawing texture to screen
            gl.glClearColor(1,1,1,1);
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.setup_scene(0, 0, W, H)
            tex.Enable(0)
            # Draw texture to screen
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord(0,0); gl.glVertex(0,0); 
            gl.glTexCoord(0,1); gl.glVertex(0,1); 
            gl.glTexCoord(1,1); gl.glVertex(1,1); 
            gl.glTexCoord(1,0); gl.glVertex(1,0); 
            gl.glEnd()
            tex.Disable()
        elif self._technique == 'ssaa':
            self._pass_ssaa(tex, w, h, scale)
        elif self._technique == 'smaa':
            self._pass_smaa(tex)
        else:
            self._pass_aa(tex)
        
        # Now blit texture to backbuffer
        self._backend._vispy_swap_buffers()
        
        # Prepare for next round
        self._a += 0.005
        self.update()
    
    
    def _draw_stars(self, smooth, scale):
        # Initialize
        n = 10
        if smooth:
            gl.glEnable(gl.GL_LINE_SMOOTH)
        
        for i in range(self._N):
            
            gl.glLineWidth(int(self._w[i]*scale))
            gl.glColor(self._r[i], self._g[i], self._b[i])
            gl.glBegin(gl.GL_LINE_STRIP)
            #
            r1 = self._s[i]
            r2 = r1 *0.4
            for j in np.arange(n+1):
                if j%2: r = r1
                else:   r = r2
                theta = np.pi/12 + 2*np.pi * j/float(n)
                theta += self._a[i]
                x = r*np.cos(theta)
                y = r*np.sin(theta)
                gl.glVertex(self._x[i] + x, self._y[i] + y) 
            gl.glEnd()
        
        # Clean up
        gl.glDisable(gl.GL_LINE_SMOOTH)
        gl.glColor(1,1,1,1)


if __name__ == '__main__':
    
    # Choices ...
    W, H = 300, 300
    DemoClass = StarDemo
    PREAA = 0 # Using GL_LINE_SMOOTH to create the image
    
    #NAME = 'ssaa - super sampling, real antialiasing at the cost of performance'
    #NAME = 'smooth_aa - simply smooth everything'
    NAME = 'ddaa - directional diffusing. blur in direction of edges'
    #NAME = 'mcaa - reconstruct original shape similar to marching squares'
    #NAME = 'fxaa - fast approximate aa, a popular technique in modern games (probably not implemented correctly)'
    #NAME = 'dlaa - directionally localized aa (by Andreev)'
    #NAME = 'nfaa - normal filter aa (by Styves)'
    #NAME = 'smaa - enhanced subpixel morphological aa by Jorge Jimenez (not implemented correctly?)'
    
    # Create demo canvas object
    if DemoClass is StarDemo:
        demo = DemoClass(NAME.split('-')[0].strip(), PREAA)
        demo.geometry = None, None, W, H  #demo.resize(W, H)
        
    else:
        demo = DemoClass(NAME.split('-')[0].strip(), PREAA)
        demo.geometry = None, None, 3*W, H  #demo.resize(3*W, H)
    
#     # Init glut
#     if DemoClass is StarDemo:
#         glut.glutCreateWindow("FSAA star demo: %s" % NAME)
#         glut.glutReshapeWindow(W, H)
#         demo = DemoClass(NAME.split('-')[0].strip(), PREAA)
#         glut.glutDisplayFunc(demo.on_display)
#         glut.glutIdleFunc(demo.on_idle)
#         glut.glutKeyboardFunc(demo.on_key)
#     else:
#         glut.glutCreateWindow("FSAA demo: %s" % NAME)
#         glut.glutReshapeWindow(3*W, H)
#         demo = DemoClass(NAME.split('-')[0].strip(), PREAA)
#         glut.glutDisplayFunc(demo.on_display)
    
    demo.show()
    
    demo.title = 'FSAA demo'
    vispy.app.run() # todo: should be vispy.app.run()
    
    