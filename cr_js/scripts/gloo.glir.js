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

function create_attribute(c, program, vbo, vbo_type,
                          name, attribute_type,
                          ndim, stride, offset) {
    // program: program handle
    // name: attribute name
    // vbo: vbo handle
    // vbo_type
    // attribute_type: FLOAT, INT or BOOL
    // ndim: 2, 3 or 4
    // stride: 0 by default
    // offset: 0 by default

    // c.gl.useProgram(program);
    var attribute_handle = c.gl.getAttribLocation(program, name);

    c.gl.bindBuffer(c.gl[vbo_type], vbo);

    c.gl.enableVertexAttribArray(attribute_handle);
    c.gl.vertexAttribPointer(attribute_handle, ndim, 
                             c.gl[attribute_type],
                             false, stride, offset);
    return attribute_handle;
}

function get_attribute_info(type) {
    // type: vec2, ivec3, float, etc.
    
    // Find OpenGL attribute type.
    var gl_type = 'FLOAT';
    if (type[0] == 'i' || type == 'int') {
        gl_type = 'INT';
    }
    
    // Find ndim.
    if (type == 'int' || type == 'float') {
        var ndim = 1;
    }
    else {
        ndim = parseInt(type.slice(-1));
    }

    return [gl_type, ndim];
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
            c._ns[id] = [cls, c.gl.createBuffer(), null, null];  // type, offset
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

    glir.prototype.data = function(c, args) {
        var vbo_id = args[0];
        var offset = args[1];
        var data = args[2];
        
        // TODO: set the data for VertexBuffer
        // TODO: find the type

        c._ns[vbo_id][2] = type;
        c._ns[vbo_id][3] = offset;
    }

    glir.prototype.attribute = function(c, args) {
        var program_id = args[0];  // program id
        var name = args[1];
        var type = args[2];
        var vbo_id = args[3];
        var stride = args[4];
        var offset = args[5];

        var program_handle = c._ns[program_id][1];

        _attribute_info = get_attribute_info(type);
        var attribute_type = _attribute_info[0];
        var ndim = _attribute_info[1];

        _vbo_info = c._ns[vbo_id];
        var vbo_handle = _vbo_info[0];
        var vbo_type = _vbo_info[1];

        console.debug("Creating attribute '{0}' for program '{1}'.".format(
                name, program_id
            ));
        var attribute_id = create_attribute(c, program_handle, 
            vbo_handle, vbo_type,
            name, attribute_type, ndim, stride, offset);

        // QUESTION: attributes don't have a user-specified id?
        // c._ns[] = ['Attribute', attribute_id];
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
