"""
Simple test showing one visual.
It also illustrates using a hierarchy of visuals to easily transform
objects. Similarly, the camera can be positioned by transforming a parent
object. Further, this example runs an FPS counter.
"""

import time
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

# Explicitly set the second camera, or the Viewport will pick the second
fig.camera = camera

# Create a points visual inside a container
pointscontainer = visuals.Visual(fig.world)
points = visuals.PointsVisual(pointscontainer, 1000)

# Transform either the camera container or the point container.
# Their effects should be mutually reversed. 
# UNCOMMENT TO ACTIVATE
#
#transforms.translate(camcontainer.transform, 50, 50)
#transforms.rotate(camcontainer.transform, 10, 0,0,1)
#
#transforms.translate(pointscontainer.transform, 50, 50)
#transforms.rotate(pointscontainer.transform, 10, 0,0,1)


# Count FPS
t0, frames, t = time.time(), 0, 0
@fig.connect
def on_paint(event):
    global t, t0, frames
    t = time.time()
    frames = frames + 1
    elapsed = (t-t0) # seconds
    if elapsed > 2.5:
        print( "FPS : %.2f (%d frames in %.2f second)"
               % (frames/elapsed, frames, elapsed))
        t0, frames = t,0
    event.source.update()

# Run!
app.run()

