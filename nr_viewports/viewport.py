# -*- coding: utf-8 -*-
# Copyright (c) 2013, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.



class Viewport(object):
    """A Viewport represents a rectangular area on a canvas. It can has children
    whose size can be defined in absolute coordinates or in relative
    coordinates relatively to the parent viewport. Let's consider a root
    viewport of size 400x400 and a child viewport:

    child.size = 100,100
    -> Final size will be 100,100
    
    child.size = -100,-100
    -> Final size will be (400-100),(400-100) = 300,300

    child.size = 0.5,0.5
    -> Final size will be (.5*400),(.5*400) = 200,200
    
    child.size = -0.5,-0.5
    -> Final size will be (400*(1-0.5)),(400*(1-0.5)) = 200,200

    Note that it is also possible to define an aspect (=height/width) that can
    be enforced. Positioning the viewport inside the parent viewport is also
    made using absolute or relative coordinates. Let's consider again the root
    viewport whose default coordinates are always +0+0:

    child.position = +10,+10
    -> Final position will be +10+10

    child.position = -10,-10
    -> Final position will be (400-10,400-10) = 390,390

    child.position = 0.25,0.25
    -> Final position will be (400*0.25,400*0.25) = 100,100
    
    child.position = -0.25,-0.25
    -> Final position will be (400*(1-0.25),400*(1-0.25) = 300,300

    Note that the final position of the viewport relates to the anchor point
    which can be also set in absolute or relative coordinates.

    The order of rendering is done accordingly to the depth variable. If not set
    when defining viewports, viewports are rendered in the order of the viewport
    hierarchy, starting from the root viewport.

    Any child viewport is guaranteed to be clipped against the parent viewport.
    """

    # Internal id counter to keep track of created objects
    _idcount = 0

    def __init__(self, size=(800,600), position=(0,0), anchor=(0,0),
                 depth=0, aspect=None, color=(1,1,1,1)):
        """
        Create a new viewport with requested size and position.

        Parameters
        ----------
        size: tuple as ([int,float], [int,float])
            Requested size.
            May be absolute (pixel) or relative to the parent (percent).
            Positive or negative values are accepted.

        position: tuple as ([int,float], [int,float])
            Requested position. 
            May be absolute (pixel) or relative to the parent (percent).
            Positive or negative values are accepted.

        anchor: tuple as ([int,float], [int,float]) or string
            Anchor point for positioning.
            May be absolute (pixel) or relative (percent).
            Positive or negative values are accepted.

        aspect: float 
            Aspect (width/height) to be enforced.

        depth: float or None
            Depth of the viewport (relative to others).

        color: 4-floats tuple
            Clear color.
        """

        self._parent = None
        self._children = []

        # Aspect ratio (width/height)
        self._aspect = aspect

        # Anchor point for placement
        self._anchor = anchor

        # Clear color
        self._color = color

        # Relative depth
        self._depth = depth

        # Requested size & position (may be honored or not, depending on parent)
        # (relative or absolute coordinates)
        self._requested_size     = size
        self._requested_position = position

        # Clipped size & position (used for glScissor)
        # (absolute coordinates)
        self._scissor_size     = size
        self._scissor_position = position

        # Viewport size & position (used for glViewport)
        # (absolute coordinates)
        self._viewport_size     = size
        self._viewport_position = position

        # Viewport id
        self._id = Viewport._idcount
        Viewport._idcount += 1
        

    def add(self, child):
        """ Add a new child to the viewport """
        
        child.parent = self
        self._children.append(child)


    def __getitem__(self, index):
        """Get children using index"""
        
        return self._children[index]



    # ---------------------------------------------------------------- root ---
    def get_root(self):
        if not self._parent:
            return self
        return self._parent
    root = property(get_root,
                    doc = "Root viewport")


    # -------------------------------------------------------------- parent ---
    def get_parent(self):
        return self._parent
    def set_parent(self, parent):
        self._parent = parent
    parent = property(get_parent, set_parent,
                    doc = "Parent viewport")


    
    # ---------------------------------------------------- compute_viewport ---
    def compute_viewport(self):
        """ Compute actual viewport in absolute coordinates """

        # Root requests are always honored
        if self.parent is None:
            self._position          = 0,0
            self._size              = self._requested_size
            self._viewport_position = 0,0
            self._viewport_size     = self._requested_size
            self._scissor_position  = 0,0
            self._scissor_size      = self._requested_size
            for child in self._children:
                child.compute_viewport()
            return

        # Children viewport request depends on parent viewport
        pvx, pvy = self.parent._viewport_position
        pvw, pvh = self.parent._viewport_size
        psx, psy = self.parent._scissor_position
        psw, psh = self.parent._scissor_size

        # Relative width (to actual parent viewport)
        # ------------------------------------------
        if self._requested_size[0] <= -1.0:
            vw = max(pvw + self._requested_size[0],0)
        elif self._requested_size[0] < 0.0:
            vw = max(pvw + self._requested_size[0]*pvw,0)
        elif self._requested_size[0] <= 1.0:
            vw = self._requested_size[0]*pvw
        # Absolute width
        else:
            vw = self._requested_size[0]
        vw = int(round(vw))

        # Enforce aspect first
        if self._aspect:
            vh = self._aspect*vw
        # Relative height (to actual parent viewport)
        # -------------------------------------------
        else:
            if self._requested_size[1] <= -1.0:
                vh = max(pvh + self._requested_size[1],0)
            elif self._requested_size[1] < 0.0:
                vh = max(pvh + self._requested_size[1]*pvh,0)
            elif self._requested_size[1] <= 1.0:
                vh = self._requested_size[1]*pvh
            # Absolute height
            else:
                vh = self._requested_size[1]
        vh = int(round(vh))

        # X anchor
        # ---------------------------------------
        if self._anchor[0] <= -1.0:
            ax = vw + self._anchor[0]
        elif self._anchor[0] < 0.0:
            ax = vw + self._anchor[0]*vw
        elif self._anchor[0] < 1.0:
            ax = self._anchor[0]*vw
        else:
            ax = self._anchor[0]
        ax = int(round(ax))

        # X positioning
        # ---------------------------------------
        if self._requested_position[0] <= -1.0:
            vx = pvw + self._requested_position[0]
        elif -1.0 < self._requested_position[0] < 0.0:
            vx = pvw + self._requested_position[0]*pvw
        elif 0.0 <= self._requested_position[0] < 1.0:
            vx = self._requested_position[0]*pvw
        else:
            vx = self._requested_position[0]
        vx = int(round(vx)) + pvx - ax

        # Y anchor
        # ---------------------------------------
        if self._anchor[1] <= -1.0:
            ay = vh + self._anchor[1]
        elif -1.0 < self._anchor[1] < 0.0:
            ay = vh + self._anchor[1]*vh
        elif 0.0 <= self._anchor[1] < 1.0:
            ay = self._anchor[1]*vh
        else:
            ay = self._anchor[1]
        ay = int(round(ay))

        # Y positioning
        # ---------------------------------------
        if self._requested_position[1] <= -1.0:
            vy = pvh + self._requested_position[1] #- vh
        elif -1.0 < self._requested_position[1] < 0.0:
            vy = pvh + self._requested_position[1]*pvh

        elif 0.0 <= self._requested_position[1] < 1.0:
            vy = self._requested_position[1]*pvh
        else:
            vy = self._requested_position[1]
        vy = int(round(vy)) + pvy - ay


        # Compute scissor size & position
        sx = max(pvx,vx)
        sy = max(pvy,vy)
        sw = max(min(psw-(sx-pvx)-1,vw), 0)
        sh = max(min(psh-(sy-pvy)-1,vh), 0)

        # Update internal information
        self._viewport_size     = vw, vh
        self._viewport_position = vx, vy
        self._scissor_size      = sw, sh
        self._scissor_position  = sx, sy

        # Update children
        for child in self._children:
            child.compute_viewport()



    # ---------------------------------------------------------------- size ---
    def get_size(self):
        return self._viewport_size
    def set_size(self, size):
        self._requested_size = size
        self.root.compute_viewport()

    size = property(get_size, set_size,
                    doc = "Actual size of the viewport")



    # ------------------------------------------------------------ position ---
    def get_position(self):
        return self._viewport_position
    def set_position(self):
        self._requested_position = position
        self.root.compute_viewport()
    position = property(get_position, set_position,
                    doc = "Actual position of the viewport")



    # ----------------------------------------------------------- rendering ---
    def lock(self):
        vx, vy = self._viewport_position
        vw, vh = self._viewport_size
        sx, sy = self._scissor_position
        sw, sh = self._scissor_size
        gl.glPushAttrib( gl.GL_VIEWPORT_BIT | gl.GL_SCISSOR_BIT )
        gl.glViewport( vx, vy, vw, vh )
        gl.glEnable( gl.GL_SCISSOR_TEST )
        gl.glScissor( sx, sy, sw, sh )
        
    def unlock(self):
        gl.glPopAttrib( )

    def clear(self):
        self.lock()
        gl.glClearColor(*self._color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for child in self._children:
            child.clear()
        self.unlock()


    # ---------------------------------------------------------------- name ---
    def get_name(self):
        if not self.parent:
            return "root"
        else:
            return "VP%d" % (self._id)
    name = property(get_name)
            

    # ---------------------------------------------------------------- repr ---
    def __str__(self):
        return '\n'.join(self.__replines__()) + '\n'
    def __replines__(self):
        """ ASCII Display of Trees by andrew cooke """
        yield "%s (%dx%d%+d%+d)" % (self.name,
                                self.size[0], self.size[1],
                                self.position[0], self.position[1])
        last = self._children[-1] if self._children else None
        for child in self._children:
            prefix = '└── ' if child is last else '├── '
            for line in child.__replines__():
                yield prefix + line
                prefix = '    ' if child is last else '│   '





# -------------------------------------------------------------------- main ---
if __name__ == '__main__':
    import sys, ctypes
    from OpenGL import platform
    import OpenGL.GL as gl
    import OpenGL.GLUT as glut

    root = Viewport( size=(800,800), color=(1,0,0,1))
#    root.add( Viewport(size=(100,1.0), position=(-100,0), anchor=(0,0), color=(0,1,0,1)) )
#    root.add( Viewport(size=(-101,1.0), position=(0,0), anchor=(0,0), color=(0,0,1,1)) )
    aspect = 1
    root.add( Viewport(size=(0.5,0.5), position=(0.5,0.5), anchor=(0.5,0.5),
                       aspect=aspect, color=(0,1,0,1)) )
    root[0].add( Viewport(size=(0.5,0.5), position=(1.0,1.0),
                          aspect=aspect, color=(0,0,1,1)) )
    root[0][0].add( Viewport(size=(0.5,0.5), position=(-1,-1), anchor=(-1,-1),
                             aspect=aspect, color=(1,1,0,1)) )


    def on_display():
        root.clear()
        glut.glutSwapBuffers()

    def on_keyboard(key, x, y):
        if key == '\033': sys.exit()

    def on_reshape(width, height):
        root.size = width, height

    def on_idle():
        global t, t0, frames
        t = glut.glutGet( glut.GLUT_ELAPSED_TIME )
        frames = frames + 1
        if t-t0 > 2500:
            print( "FPS : %.2f (%d frames in %.2f second)"
                   % (frames*1000.0/(t-t0), frames, (t-t0)/1000.0))
            t0, frames = t,0
        glut.glutPostRedisplay()

    glut.glutInit(sys.argv)
    # HiDPI support for retina display
    # This requires glut from http://iihm.imag.fr/blanch/software/glut-macosx/
    if sys.platform == 'darwin':
        try:
            glutInitDisplayString = platform.createBaseFunction( 
                'glutInitDisplayString', dll=platform.GLUT, resultType=None, 
                argTypes=[ctypes.c_char_p],
                doc='glutInitDisplayString(  ) -> None', 
                argNames=() )
            text = ctypes.c_char_p("rgba stencil double samples=8 hidpi")
            glutInitDisplayString(text)
        except:
            pass
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    glut.glutCreateWindow("Viewports")
    glut.glutReshapeWindow(*root.size)
    glut.glutDisplayFunc(on_display)
    glut.glutReshapeFunc(on_reshape)
    glut.glutKeyboardFunc(on_keyboard)
    glut.glutKeyboardFunc(on_keyboard)

    t0, frames, t = glut.glutGet(glut.GLUT_ELAPSED_TIME),0,0
    glut.glutIdleFunc(on_idle)

    glut.glutMainLoop()

