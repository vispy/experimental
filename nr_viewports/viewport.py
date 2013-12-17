# -*- coding: utf-8 -*-
# Copyright (c) 2013, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.



class Viewport(object):
    # Internal id counter to keep track of created objects
    _idcount = 1


    def __init__(self, size=(800,600), position=(0,0), aspect=None, color=(1,1,1,1)):
        self._parent = None
        self._children = []
        self._color = color
        self._size_request = size
        self._position_request = position
        self._aspect = aspect
        self._id = Viewport._idcount
        Viewport._idcount += 1


    def add(self, child):
        """ Add a new child to the viewport """
        child.parent = self
        self._children.append(child)


    def __getitem__(self, index):
        """Get children using index"""
        return self._children[index]


    def get_root(self):
        if not parent:
            return self
        return self._parent
    root = property(get_root,
                    doc = "Root viewport")


    def get_parent(self):
        return self._parent
    def set_parent(self, parent):
        self._parent = parent
    parent = property(get_parent, set_parent,
                    doc = "Parent viewport")



    def get_dirty(self):
        return self._dirty
    def set_dirty(self, dirty):
        self._dirty = dirty
        for child in self._children:
            child.dirty = dirty
    dirty = property(get_dirty, set_dirty,
                     doc = "Set dirty flag for self and any children")


    
    def compute_viewport(self):
        """ Compute actual viewport in absolute coordinates """

        if self.parent is None:
            self._position = 0,0
            self._size = self._size_request
        else:
            X,Y = self.parent.position
            W,H = self.parent.size
        
            # Relative width
            if self._size_request[0] <= 1.0:
                w = min(self._size_request[0]*W,W)
            # Absolute width
            else:
                w = self._size_request[0]
            w = int(round(w))

            # Relative height
            if self._aspect:
                h = self._aspect*w
            else:
                if self._size_request[1] <= 1.0:
                    h = min(self._size_request[1]*H, H)
                # Absolute height
                else:
                    h = self._size_request[1]
            h = int(round(h))

            # Relative x
            if -1.0 < self._position_request[0] < 1.0:
                x = self._position_request[0]*W
            # Absolute x
            else:
                x = self._position_request[0]
            x = int(round(x))

            # Relative y
            if -1.0 < self._position_request[1] < 1.0:
                y = self._position_request[1]*H
            # Absolute y
            else:
                y = self._position_request[1]
            y = int(round(y))

            if x > 0 and (w+x) > W:
                w = W-x
            elif x < 0 and (w-x) > W:
                w = W+x
                x = 0

            if y > 0 and (h+y) > H:
                h = H-y
            elif y < 0 and (h-y) > H:
                h = H+y
                y = 0

            if x < 0:
                x = W-w+x
            if y < 0:
                y = H-h+y

            self._size = (w,h)
            self._position = (X+x,Y+y)

        for child in self._children:
            child.compute_viewport()


    def get_size(self):
        return self._size
    def set_size(self, size):
        self._size_request = size
        self.root.compute_viewport()

    size = property(get_size, set_size,
                    doc = "Actual size of the viewport")



    def get_position(self):
        return self._position
    def set_position(self):
        self._position_request = position
        self.root.compute_viewport()
    position = property(get_position, set_position,
                    doc = "Actual position of the viewport")



    def clear(self):
        x,y = self._position
        w,h = self._size
        gl.glPushAttrib( gl.GL_VIEWPORT_BIT | gl.GL_SCISSOR_BIT )
        gl.glViewport( x, y, w, h )
        gl.glEnable( gl.GL_SCISSOR_TEST )
        gl.glScissor( x, y, w, h )
        gl.glClearColor(*self._color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for child in self._children:
            child.clear()
        gl.glPopAttrib( )


    # ---------------------------------------------------------------- repr ---
    def __str__(self):
        return '\n'.join(self.__replines__())

    def __replines__(self):
        """ ASCII Display of Trees by andrew cooke """
        yield "VP%d (%dx%d%+d%+d)" % (self._id,
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
    import sys
    import OpenGL.GL as gl
    import OpenGL.GLUT as glut

    root = Viewport( size=(1000,1000), color=(1,0,0,1))
    root.add( Viewport(size=(.5,.5), position=(-1,-1), aspect=1, color=(0,1,0,1)) )
    root[0].add( Viewport(size=(.5,.5), position=(1,1), aspect=1, color=(0,0,1,1)) )
    root[0][0].add( Viewport(size=(.5,.5), position=(-1,-1), aspect=1, color=(1,1,0,1)) )
    root.compute_viewport()
    print root


    def on_display():
        root.clear()
        glut.glutSwapBuffers()
    def on_keyboard(key, x, y):
        if key == '\033': sys.exit()
    def on_reshape(width, height):
        root._size_request = (width,height)
        root.compute_viewport()
    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
    glut.glutCreateWindow("Viewports")
    glut.glutReshapeWindow(1000, 1000)
    glut.glutDisplayFunc(on_display)
    glut.glutReshapeFunc(on_reshape)
    glut.glutKeyboardFunc(on_keyboard)
    glut.glutMainLoop()

