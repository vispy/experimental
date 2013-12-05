""" Proof of concept for instant zebra.
If you don't get this, don't worry :)  this file does not really belong here
but it was the easest place to put it for now...
"""

import time
import numpy as np

from vispy import app, gloo
from vispy.util import transforms

from vispy_experimental import ak_entities as entities


class ZebraVisual:
    
    VERT_SHADER = """
        // Stuff that each visual must have ...
        uniform   mat4 transform_model;
        uniform   mat4 transform_view;
        uniform   mat4 transform_projection;
        
        uniform float t;

        attribute vec3 a_position1;
        attribute vec3 a_position2;
        
        varying vec4 v_color;
        void main (void) {
            vec3 a_position = a_position1*(1.0-t) + a_position2*t;
            gl_Position = vec4(a_position, 1.0);
            gl_Position = transform_projection * transform_view 
                        * transform_model * gl_Position;
            v_color = vec4(0.0, 1.0, 1.0, 1.0);
        }
    """
    
    FRAG_SHADER = """
        varying vec4 v_color;
        void main()
        {    
            gl_FragColor = v_color;
        }
    """
    
    def __init__(self,):
        
        
        vertices = []
        dr = 0.15
        
        for r in range(-1,4):
            r *= dr*2
            r1, r2 = r, r+dr
            r1, r2 = max(r1, 0), max(r2, 0)
            
            N = 64
            for i in range(N):
                x1 = np.cos(np.pi*2 * i/N)
                y1 = np.sin(np.pi*2 * i/N)
                x2 = np.cos(np.pi*2 * (i+1)/N)
                y2 = np.sin(np.pi*2 * (i+1)/N)
                
                vertices.append( (x1*r1, y1*r1, 0))
                vertices.append( (x1*r2, y1*r2, 0))
                vertices.append( (x2*r2, y2*r2, 0))
                #
                vertices.append( (x1*r1, y1*r1, 0))
                vertices.append( (x2*r2, y2*r2, 0))
                vertices.append( (x2*r1, y2*r1, 0))
        
        vertices2 = vertices
        vertices = []
        
        for r in range(5):
            r *= dr*2
            r1, r2 = r, r+dr
            
            N = 64
            for i in range(N):
                x1 = np.cos(np.pi*2 * i/N)
                y1 = np.sin(np.pi*2 * i/N)
                x2 = np.cos(np.pi*2 * (i+1)/N)
                y2 = np.sin(np.pi*2 * (i+1)/N)
                
                vertices.append( (x1*r1, y1*r1, 0))
                vertices.append( (x1*r2, y1*r2, 0))
                vertices.append( (x2*r2, y2*r2, 0))
                #
                vertices.append( (x1*r1, y1*r1, 0))
                vertices.append( (x2*r2, y2*r2, 0))
                vertices.append( (x2*r1, y2*r1, 0))
        
        
        data1 = np.array(vertices2, dtype='float32' )
        data2 = np.array(vertices, dtype='float32' )
        
        # Create program and vertex buffer
        self.program = gloo.Program(self.VERT_SHADER, self.FRAG_SHADER)
        self.program['a_position1'] = gloo.VertexBuffer(data1)
        self.program['a_position2'] = gloo.VertexBuffer(data2)
    
    
    def draw(self):
        self.program['t'] = time.time() % 1
        self.program.draw('TRIANGLES')
        



class ZebraEntity(entities.Entity):
    def __init__(self, parent, *args):
        entities.Entity.__init__(self, parent)
        self._visual = ZebraVisual(*args)


class MyFigure(entities.Figure):
    def on_mouse_move(self, event):
        cam0.on_mouse_move(event)
#         cam2.on_mouse_move(event)

fig = MyFigure()#entities.Figure()
fig.size = 800, 400
fig.show()

#camera = entities.NDCCamera(fig.world)
camera = entities.PixelCamera(fig.world)

# Create two viewports, use the same world
vp1 = entities.Viewport(fig.world)
vp2 = entities.Viewport(fig.world)
vp1.world = vp2.world

# Put them next to each-other
# transforms.scale(vp1.transform, 400, 400)
# transforms.scale(vp2.transform, 400, 400)
# transforms.translate(vp1.transform, 0)
# transforms.translate(vp2.transform, 400, 0, 0)
#
transforms.scale(vp1.transform, 1280, 1024)
transforms.scale(vp2.transform, 1280, 1024)
transforms.translate(vp2.transform, 1280, 0, 0)

# Create two cameras
cam0 = entities.FirstPersonCamera(vp1.world)  # Placeholder camera
cam1 = entities.FirstPersonCamera(cam0)
cam2 = entities.FirstPersonCamera(cam0)

# Set limits of cam0, this is only to set position right, its fov is not used
cam0._pos = 0, 0, 0
cam1._pos = 0, 0, -0.05
cam2._pos = 0, 0, +0.05

# Set fov of cam1 and cam2
cam1.fov = cam2.fov = 100.0  # fov of display

# Apply cameras
vp1.camera = cam1
vp2.camera = cam2
# vp1.bgcolor = (0,0,0.2)
# vp2.bgcolor = (0,0.2,0)

# Create an entity
# Note that we now put the floor at eye-height and camera at 0.0, because our
# cameras are still upside down :D
data = np.random.uniform(-2, 2, (1000,3)).astype('float32')
data[:,2] = 1.80
# points = entities.PointsEntity(vp1.world, data)
zebra = ZebraEntity(vp1.world)


# Create tracker
from cybertools.trackers import IntersenseUdpTracker
tracker = IntersenseUdpTracker()
if not tracker.units:
    raise RuntimeError('No units found, perhaps the server is not running or UDP is off?')
wand = tracker.units[-1]
# wand.reset()


def idle_func(event=None):
    cam0._view_az = -wand.euler[0] # yaw
    cam0._view_el = wand.euler[1] # pitch
    cam0._view_ro = wand.euler[2] # roll
    for c in (cam0, cam1, cam2):
        c.update_angles()
    fig.update()
    

timer = app.Timer(0.01, idle_func)
timer.start()


# Set to HDM
from cybertools.desktop import DesktopManager
dm = DesktopManager()
dm.applyGeometry(fig.native, dm.displayGeometry)
    
app.run()

