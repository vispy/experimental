""" 
Example that illustrates using multiple subplots.
Also to test performance of the glViewport and Program enabling overhead.

On my 3 year old laptop, I find it takes 0.6 ms per subplot. Leading
to 50 FPS on a 6x6 array of plots. Showing 36 plots with 10.000 points each
runs at 30 FPS. For comparison, a single plot with 360.000 points runs
at the same frame rate. 

This shows that as the visualization itself becomes harder, the overhead
becomes negligible compared to the time required for the drawing itself.
For easy visualizations the overhead is small enough to render massive
arrays of subplots in realtime.
"""

import time
from vispy_experimental import ak_visuals as visuals

from vispy import app
from vispy.util import transforms

RES = 600
NCOLS = 5
NROWS = 5

# Create a figure
fig = visuals.Figure()
fig.size = RES, RES
fig.show()

# Add a simple normal pixelcamera. This camera looks at the many
# subplots. Each subplot has its own world with a visual and a camera.
visuals.PixelCamera(fig.world)

for col in range(NCOLS):
    for row in range(NROWS):
        # Create viewport
        viewport = visuals.Viewport(fig.world)
        viewport.transform[-1, 0] = col * RES / NCOLS
        viewport.transform[-1, 1] = row * RES / NROWS
        viewport.transform[0,0] = RES/NCOLS
        viewport.transform[1,1] = RES/NROWS
        # Create a camera in the viewport
        camera = visuals.TwoDCamera(viewport.world)
        camera.xlim = -100, 500
        camera.ylim = -100, 500
        # Create a points visual in the viewport
        points = visuals.PointsVisual(viewport.world, 1000)


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


if False:
    ## Evaluate measurements 
    # Measured
    ncolrow = [6,  7,   8,  9, 10, 11, 12]
    fpss    = [48, 37, 28, 23, 18, 15, 12]
    # Process
    xx = [x**2 for x in ncolrow]
    yy = [1.0 / fps for fps in fpss]
    timepersubplot = [1000*y/x for x, y in zip(xx, yy)]
    # Show
    import visvis as vv
    vv.figure(1); vv.clf()
    vv.plot(xx, yy)
    vv.xlabel('number of subplots')
    vv.ylabel('timer per frame')
    #
    vv.figure(2); vv.clf()
    vv.plot(timepersubplot)
    vv.gca().SetLimits(rangeY=(0, 1.1*max(timepersubplot)))
    
    