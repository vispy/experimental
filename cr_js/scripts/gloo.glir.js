/* Creation of vispy.gloo.glir */
define(["jquery"], function($) {
    var glir = function() {
        // Constructor.

    };

    glir.prototype.init = function(c) {

    }

    glir.prototype.call = function(c, command) {
        console.log("calling: " + command);
    }

    return new glir();
});
