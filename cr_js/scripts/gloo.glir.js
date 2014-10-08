


/* Creation of vispy.gloo.glir */
define(["jquery"], function($) {
    var glir = function() {
        // Constructor.

    };

    glir.prototype.init = function(c) {
        // Namespace with the table of all symbols used by GLIR.
        c._ns = {};
    }

    glir.prototype.call = function(c, command) {
        var method = command[0].toLowerCase();
        this[method](c, command.slice(1));
    }

    glir.prototype.create = function(c, args) {
        var id = args[0];
        var cls = args[1];
        if (cls == 'VertexBuffer') {
            console.debug("Creating vertex buffer '{0}'.".format(id));
            c._ns[id] = [cls, c.gl.createBuffer()];
        }
    };

    glir.prototype.delete = function(c, args) {
        var id = args[0];
        var cls = c._ns[id][0];
        var handle = c._ns[id][1];
        if (cls == 'VertexBuffer') {
            console.debug("Deleting vertex buffer '{0}'.".format(id));
            c.gl.deleteBuffer(handle);
        }
    };

    return new glir();
});
