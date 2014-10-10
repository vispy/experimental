// Require paths.
require.config({
  paths: {
    "jquery": "lib/jquery-ui/external/jquery/jquery",
    "jquery-mousewheel": "lib/jquery.mousewheel.min",
    "jquery-ui": "lib/jquery-ui/jquery-ui.min",
    "screenfull": "lib/screenfull.min",
  }
});

function VispyCanvas($el) {
    this.$el = $el;
}

// Vispy library entry point.
define(["jquery", "events", "gloo", "util", "data"], 
    function($, events, gloo) {
        var vispy = function() {
            // Constructor of the Vispy library.
            this.events = events;
            this.gloo = gloo;
        };

        vispy.prototype.init = function(canvas_id) {
            // Initialize the canvas.
            var canvas = new VispyCanvas($(canvas_id));

            // Initialize events.
            this.events.init(canvas);

            // Initialize WebGL.
            this.gloo.init(canvas);

            return canvas;
        };
        return new vispy();
});
