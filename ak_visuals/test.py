from vispy_experimental import ak_visuals as visuals

from vispy import app
from vispy.util import transforms

# Create a figure
fig = visuals.Figure()
fig.size = 600, 600
fig.show()

# Create a camera inside a container
camcontainer = visuals.PixelCamera(fig.world)
camera = visuals.TwoDCamera(camcontainer)#(self._viewport.world)
camera.xlim = -100, 500
camera.ylim = -100, 500
fig.camera = camera

# Create a points visual inside a container
pointscontainer = visuals.Visual(fig.world)
points = visuals.PointsVisual(pointscontainer)
# transforms.scale(points.transform, 0.5, 0.5)
# transforms.translate(points.transform, 100, -100, 0)


# Transform either the camera container or the point container.
# Their effects should be mutually reversed.
#
# transforms.translate(camcontainer.transform, 50, 50)
# transforms.rotate(camcontainer.transform, 10, 0,0,1)
#
# transforms.translate(pointscontainer.transform, 50, 50)
# transforms.rotate(pointscontainer.transform, 10, 0,0,1)

# Run!
app.run()

