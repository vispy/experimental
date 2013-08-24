"""
Basic demonstration of timers
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vispy.app.timer import Timer

t = Timer(interval=1.0, iterations=7, start=True)

@t.connect
def fn(event):
    print event.__dict__
    if event.iteration > 3:
        event.source.app.quit()

t.app.run()
