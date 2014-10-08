// Require paths.
require.config({
  paths: {
    "jquery": "lib/jquery-2.1.1.min",
    "jquery-mousewheel": "lib/jquery.mousewheel.min"
  }
});

// Vispy library entry point.
define(["jquery", "jquery-mousewheel", "events"], function($, _, events) {
    var vispy = function() {
        // Constructor of the Vispy library.
        this.events = events;
    };

    vispy.prototype.init = function(canvas_id) {
        // Initialize the canvas.
        var canvas = $(canvas_id);
        $(canvas).css("background-color", "black");


        this.events.init(canvas);

        return canvas;
    };
    return new vispy();
});
