""" Test stereoscopic display.

This example illustrates:
  * Having two viewports that show the same scene
  * Using a different camera for each viewport
  * Controlling both cameras simultaneously
  
"""

from vispy_experimental import ak_entities as entities

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
cam0 = entities.TwoDCamera(vp1.world)  # Placeholder camera
cam1 = entities.TwoDCamera(cam0)
cam2 = entities.TwoDCamera(cam0)

# Set limits of cam0, this is only to set position right, its fov is not used
cam0.xlim = -100, 500
cam0.ylim = -100, 500

# Set fov of cam1 and cam2, and translate both cameras a bit
cam1.fov = cam2.fov = 600, 600
transforms.translate(cam1.transform, -50, 0)
transforms.translate(cam2.transform, +50, 0)

# Apply cameras
vp1.camera = cam1
vp2.camera = cam2
vp1.bgcolor = (0,0,0.2)
vp2.bgcolor = (0,0.2,0)

# Create a entity
points = entities.PointsEntity(vp1.world)

app.run()

