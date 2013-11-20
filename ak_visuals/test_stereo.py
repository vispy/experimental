from vispy_experimental import ak_visuals as visuals
from vispy_experimental.ak_visuals.somevisuals import PointsVisual

from vispy import app
from vispy.util import transforms


class MyFigure(visuals.Figure):
    def on_mouse_move(self, event):
        cam1.on_mouse_move(event)
        cam2.on_mouse_move(event)
        
fig = MyFigure()#visuals.Figure()
fig.show()

#camera = visuals.NDCCamera(fig.viewport.world)
camera = visuals.PixelCamera(fig.viewport.world)

# Create two viewports, use the same world
vp1 = visuals.Viewport(fig.viewport.world)
vp2 = visuals.Viewport(fig.viewport.world)
vp1.world = vp2.world

# Put them next to each-other
transforms.scale(vp1.transform, 200, 200)
transforms.scale(vp2.transform, 200, 200)
transforms.translate(vp1.transform, 0)
transforms.translate(vp2.transform, 200, 0, 0)

# Create two cameras
cam0 = visuals.TwoDCamera(vp1.world)  # Placeholder camera
cam1 = visuals.TwoDCamera(cam0)
cam2 = visuals.TwoDCamera(cam0)
transforms.translate(cam1.transform, +50, 0)
transforms.translate(cam2.transform, -50, 0)
#
for cam in (cam0, cam1, cam2):
    cam.xlim = -100, 500
    cam.ylim = -100, 500
#
vp1.camera = cam1
vp2.camera = cam2
vp1.bgcolor = (0,0,0.2)
vp2.bgcolor = (0,0.2,0)

# Create a visual
points = PointsVisual(vp1.world)

app.run()

