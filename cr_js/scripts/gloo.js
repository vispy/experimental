function init_webgl(c) {
    // Get the DOM object, not the jQuery one.
    var canvas = c.$el.get(0);
    c.gl = canvas.getContext("webgl") || 
            canvas.getContext("experimental-webgl");
}


/* Creation of vispy.gloo */
define(["jquery", "gloo.glir"], function($, glir) {
    var gloo = function() {
        this.glir = glir;
        // Constructor.

    };

    gloo.prototype.init = function(c) {
        init_webgl(c);
        this.glir.init(c);
    };

    return new gloo();
});
