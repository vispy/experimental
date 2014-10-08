// Require paths.
require.config({
  paths: {
    "jquery": "lib/jquery-2.1.1.min",
    "jquery-mousewheel": "lib/jquery.mousewheel.min"
  }
});

// Vispy library entry point.
define(["jquery", "events", "gloo", "util"], function($, events, gloo) {
    var vispy = function() {
        // Constructor of the Vispy library.
        this.events = events;
        this.gloo = gloo;
    };

    vispy.prototype.init = function(canvas_id) {
        // Initialize the canvas.
        var canvas = $(canvas_id);

        // Initialize events.
        this.events.init(canvas);

        // Initialize WebGL.
        this.gloo.init(canvas);

        return canvas;
    };
    return new vispy();
});
