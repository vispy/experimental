/* WebGL utility functions */
function viewport(c) {
    c.gl.viewport(0, 0, c.width, c.height);
}

function clear(c, color) {
    c.gl.clearColor(color[0], color[1], color[2], color[3]);
    c.gl.clear(c.gl.COLOR_BUFFER_BIT);
}

function init_webgl(c) {
    // Get the DOM object, not the jQuery one.
    var canvas = c.get(0);
    c.gl = canvas.getContext("webgl") || 
            canvas.getContext("experimental-webgl");
    viewport(c);
    clear(c, [0, 0, 0, 1]);
}


/* Creation of vispy.gloo */
define(["jquery", "gloo.glir"], function($, glir) {
    var gloo = function() {
        this.glir = glir;
        // Constructor.

    };

    gloo.prototype.init = function(c) {
        init_webgl(c);
    };

    return new gloo();
});
