""" Proof of concept for instant zebra.
If you don't get this, don't worry :)
"""

from vispy_experimental import ak_entities as entities

import numpy as np
from vispy import app
from vispy.util import transforms


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
transforms.scale(vp1.transform, 400, 400)
transforms.scale(vp2.transform, 400, 400)
transforms.translate(vp1.transform, 0)
transforms.translate(vp2.transform, 400, 0, 0)

# Create two cameras
cam0 = entities.FirstPersonCamera(vp1.world)  # Placeholder camera
cam1 = entities.FirstPersonCamera(cam0)
cam2 = entities.FirstPersonCamera(cam0)

# Set limits of cam0, this is only to set position right, its fov is not used
cam0._pos = 0, 0, 0
cam1._pos = -0.05
cam2._pos = +0.05

# Set fov of cam1 and cam2
cam1.fov = cam2.fov = 45.0

# Apply cameras
vp1.camera = cam1
vp2.camera = cam2
vp1.bgcolor = (0,0,0.2)
vp2.bgcolor = (0,0.2,0)

# Create an entity
# Note that we now put the floor at 1.80 and camera at 0.0, because our
# cameras are still upside down :D
data = np.random.uniform(-2, 2, (1000,3)).astype('float32')
data[:,2] = 1.80
points = entities.PointsEntity(vp1.world, data)

app.run()

