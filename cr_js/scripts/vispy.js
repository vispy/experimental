// Require paths.
require.config({
  paths: {
    "jquery": "lib/jquery-2.1.1.min"
  }
});

// Vispy library entry point.
define(["jquery", "events"], function($) {
    var vispy = function() {
        // Constructor of the Vispy library.
        
    };

    vispy.prototype.init = function(canvas) {
        // Initialize the canvas.
        canvas.css("background-color", "black");
    };
    return new vispy();
});
