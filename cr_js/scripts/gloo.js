/* Creation of vispy.gloo */
define(["jquery", "gloo.glir"], function($, glir) {
    var gloo = function() {
        this.glir = glir;
        // Constructor.
        console.log(glir);
    };

    return new gloo();
});
