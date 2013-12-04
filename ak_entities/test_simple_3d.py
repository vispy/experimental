"""
Simple test showing one entity using a 3D camera with interaction.
You need to move the mouse to initialize the view for now.
"""

import time
from vispy_experimental import ak_entities as entities

from vispy import app
from vispy.util import transforms

# Create a figure
fig = entities.Figure()
fig.size = 600, 600
fig.show()

# Create a camera inside a container
camcontainer = entities.PixelCamera()
camera = entities.ThreeDCamera(camcontainer)#(self._viewport.world)
camera._fov = 90  # or other between 0 and 179


# Explicitly set the second camera, or the Viewport will pick the second
fig.viewport.camera = camera

# Create a points entity inside a container
pointscontainer = entities.Entity(fig.world)
points = entities.PointsEntity(pointscontainer, 1000)


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

