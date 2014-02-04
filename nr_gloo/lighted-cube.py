#! /usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All rights reserved.
# Distributed under the terms of the new BSD License.
# -----------------------------------------------------------------------------
import sys
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut

from cube import cube
from gloo import Program, VertexBuffer, IndexBuffer
from transforms import perspective, translate, rotate

vertex = """
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

attribute vec3 a_position;
attribute vec3 a_normal;

varying vec3 v_position;
varying vec3 v_normal;

void main()
{
    v_normal = a_normal;
    v_position = a_position;
    gl_Position = u_projection * u_view * u_model * vec4(a_position,1.0);
}
"""

fragment = """
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_normal;

uniform vec3 light_intensity;
uniform vec3 light_position;

varying vec3 v_position;
varying vec3 v_normal;

void main()
{
    // Calculate normal in world coordinates
    vec3 normal = normalize(u_normal * vec4(v_normal,1.0)).xyz;

    // Calculate the location of this fragment (pixel) in world coordinates
    vec3 position = vec3(u_view*u_model * vec4(v_position, 1));

    // Calculate the vector from this pixels surface to the light source
    vec3 surfaceToLight = light_position - position;

    // Calculate the cosine of the angle of incidence (brightness)
    float brightness = dot(normal, surfaceToLight) /
                      (length(surfaceToLight) * length(normal));
    brightness = max(min(brightness,1.0),0.0);

    // Calculate final color of the pixel, based on:
    // 1. The angle of incidence: brightness
    // 2. The color/intensities of the light: light.intensities
    // 3. The texture and texture coord: texture(tex, fragTexCoord)

    gl_FragColor = brightness * vec4(light_intensity, 1);
}
"""


def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLES, indices)
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)
    projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
    program['u_projection'] = projection

def keyboard(key, x, y):
    if key == '\033': sys.exit( )

def timer(fps):
    global theta, phi
    theta += .5
    phi += .5
    model = np.eye(4, dtype=np.float32)
    rotate(model, theta, 0,0,1)
    rotate(model, phi, 0,1,0)
    normal = np.array(np.matrix(np.dot(view,model)).I.T)
    program['u_model'] = model
    program['u_normal'] = normal
    glut.glutTimerFunc(1000/fps, timer, fps)
    glut.glutPostRedisplay()


# Glut init
# --------------------------------------
glut.glutInit(sys.argv)
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutCreateWindow('Lighted Cube')
glut.glutReshapeWindow(512,512)
glut.glutReshapeFunc(reshape)
glut.glutKeyboardFunc(keyboard )
glut.glutDisplayFunc(display)
glut.glutTimerFunc(1000/60, timer, 60)

# Build cube data
# --------------------------------------
vertices, indices, _ = cube()
vertices = VertexBuffer(vertices)
indices = IndexBuffer(indices)

# Build view, model, projection & normal
# --------------------------------------
view = np.eye(4,dtype=np.float32)
model = np.eye(4,dtype=np.float32)
projection = np.eye(4,dtype=np.float32)
translate(view, 0,0,-5)
normal = np.array(np.matrix(np.dot(view,model)).I.T)

# Build program
# --------------------------------------
program = Program(vertex, fragment)
program.bind(vertices)
program["light_position"] = 2,2,2
program["light_intensity"] = 1,1,1
program["u_model"] = model
program["u_view"] = view
program["u_normal"] = normal
phi, theta = 0,0

# OpenGL initalization
# --------------------------------------
gl.glClearColor( .3, .3, .35, 1 )
gl.glEnable(gl.GL_DEPTH_TEST)

# Start
# --------------------------------------
glut.glutMainLoop()
