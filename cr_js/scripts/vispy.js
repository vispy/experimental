require.config({
  paths: {
    "jquery": "lib/jquery-2.1.1.min"
  }
});

define(["jquery", "events"], function($) {
    var vispy = function() {
        // Constructor.
        
    };

    vispy.prototype.init = function(canvas) {
        console.log(canvas);
    };
    return new vispy();
});
