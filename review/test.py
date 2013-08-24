import sys
import numpy as np
import OpenGL.GLUT as glut
from program import Program
from shader import VertexShader
from shader import FragmentShader



if __name__ == '__main__':

    def display():
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        glut.glutSwapBuffers()

    def reshape(width,height):
        gl.glViewport(0, 0, width, height)

    def keyboard( key, x, y ):
        if key == '\033': sys.exit( )

    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    glut.glutCreateWindow('Shader test')
    glut.glutReshapeWindow(512,512)
    glut.glutDisplayFunc(display)
    glut.glutReshapeFunc(reshape)
    glut.glutKeyboardFunc(keyboard )

    vertex = """
    #version 120

    attribute vec3 position;
    uniform vec4 color;
    void main()
    {
        gl_Position = color;
    }
    """

    fragment = """
    #version 120

    uniform vec4 color;
    void main()
    {
        gl_FragColor = color;
    }
    """

    # No GL context required
    # ----------------------
    program = Program(vertex,fragment)
    frag = FragmentShader("uniform int dummy;")
    print("Attaching shader")
    program.attach(frag)
    print("Dettaching shader")
    program.detach(frag)

    print("Uniforms:   %s" % program.all_uniforms)
    print("Attributes: %s" % program.all_attributes)
    print("Shaders: %s" % program.shaders)
    print("Program status: %s" % (
          "dirty (needs new build) " if program.dirty else "clean"))

    print("Setting color")
    program['color'] = 1,1,1,1

    # This should raise a ProgramException
    # print("Setting unknown variable")
    # program['position'] = 1,1,1,1

    # GL context required
    # -------------------
    print
    print("Active uniforms:     %s" % program.active_uniforms)
    print("Active attributes:   %s" % program.active_attributes)
    print("Inactive uniforms:   %s" % program.inactive_uniforms)
    print("Inactive attributes: %s" % program.inactive_attributes)

    print
    print('Program name: %d' % program.handle)
    print("Program status: %s" % (
          "dirty (needs new build) " if program.dirty else "clean"))

    print
    print("Attaching shader")
    program.attach(frag)
    print("Detaching shader")
    program.detach(frag)
    print("Program status: %s" % (
          "dirty (needs new build) " if program.dirty else "clean"))
    program.build()
    print("Building program")
    print("Program status: %s" % (
          "dirty (needs new build) " if program.dirty else "clean"))
    print


    # Error reporting
    # ---------------
    program = Program("void main() { gl_Position = color; }",
                      "void main() { }")
    program.build()
