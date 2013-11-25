from vispy_experimental import ak_visuals as visuals

from vispy import app
from vispy.util import transforms


fig = visuals.Figure()
fig.show()

camcontainer = visuals.PixelCamera(fig.viewport.world)
transforms.translate(camcontainer.transform, 50, 50)
#         transforms.scale(self._camcontainer.transform, 2, 2, )
        
camera = visuals.TwoDCamera(camcontainer)#(self._viewport.world)
camera.xlim = -100, 500
camera.ylim = -100, 500
fig.viewport.camera = camera


points = visuals.PointsVisual(fig.viewport.world)
#         transforms.scale(points.transform, 0.5, 0.5)
#         transforms.translate(points.transform, 100, -100, 0)

app.run()

