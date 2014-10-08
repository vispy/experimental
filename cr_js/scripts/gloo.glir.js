/* WebGL utility functions */
function viewport(c) {
    c.gl.viewport(0, 0, c.width, c.height);
}

function clear(c, color) {
    c.gl.clearColor(color[0], color[1], color[2], color[3]);
    c.gl.clear(c.gl.COLOR_BUFFER_BIT);
}

function compile_shader(c, type, source) {
    source = "precision mediump float;\n" + source;
    source = source.replace(/\\n/g, "\n")
    
    var shader = c.gl.createShader(c.gl[type]);

    c.gl.shaderSource(shader, source);
    c.gl.compileShader(shader);

    if (!c.gl.getShaderParameter(shader, c.gl.COMPILE_STATUS))
    {
        console.log(c.gl.getShaderInfoLog(shader));
        return null;
    }

    return shader;
}

function attach_shaders(c, program, vertex, fragment) {
    c.gl.attachShader(program, vertex);
    c.gl.attachShader(program, fragment);
    c.gl.linkProgram(program);

    if (!c.gl.getProgramParameter(program, c.gl.LINK_STATUS))
    {
        console.warn("Could not initialise shaders on program '{0}'.".format(program));
    }
}


/* Creation of vispy.gloo.glir */
define(["jquery"], function($) {
    var glir = function() {
        // Constructor.

    };

    glir.prototype.init = function(c) {
        // Namespace with the table of all symbols used by GLIR.
        // For each id, it is a pair (object_type, webgl_handle)
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
        else if (cls == 'Program') {
            console.debug("Creating program '{0}'.".format(id));
            c._ns[id] = [cls, c.gl.createProgram()];
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
        else if (cls == 'Program') {
            console.debug("Deleting program '{0}'.".format(id));
            c.gl.deleteProgram(handle);
        }
    };

    glir.prototype.shaders = function(c, args) {
        var id = args[0];  // program id
        var vertex_code = args[1];
        var fragment_code = args[2];

        // Get the program handle.
        var handle = c._ns[id][1];

        // Compile shaders.
        console.debug("Compiling shaders for program '{0}'.".format(id));
        var vs = compile_shader(c, 'VERTEX_SHADER', vertex_code);
        var fs = compile_shader(c, 'FRAGMENT_SHADER', fragment_code);

        // Attach shaders.
        console.debug("Attaching shaders for program '{0}'".format(id));
        attach_shaders(c, handle, vs, fs);
    }

    glir.prototype.func = function(c, args) {
        var name = args[0];
        console.debug("Calling {0}.".format(name));

        // Replace strings by global GL variables.
        for (var i = 1; i < args.length; i++) {
            if (typeof args[i] === 'string') {
                args[i] = c.gl[args[i]];
            }
        }

        var func = c.gl[name];
        var func_args = args.slice(1)
        func.apply(c.gl, func_args);
    };

    return new glir();
});
