/* WebGL utility functions */
function viewport(c) {
    c.gl.viewport(0, 0, c.width(), c.height());
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
        console.error(c.gl.getShaderInfoLog(shader));
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

function create_attribute(c, program, vbo_id, name, type, stride, offset) {
    // program: program handle
    // vbo_id
    // name: attribute name
    // type: float, vec3, etc.
    // stride: 0 by default
    // offset: 0 by default

    var _attribute_info = get_attribute_info(type);
    var attribute_type = _attribute_info[0];  // FLOAT, INT or BOOL
    var ndim = _attribute_info[1]; // 1, 2, 3 or 4

    _vbo_info = c._ns[vbo_id];
    var vbo_handle = _vbo_info.handle;

    var attribute_handle = c.gl.getAttribLocation(program, name);
    c.gl.bindBuffer(c.gl.ARRAY_BUFFER, vbo_handle);

    c.gl.enableVertexAttribArray(attribute_handle);
    c.gl.vertexAttribPointer(attribute_handle, ndim, 
                             c.gl[attribute_type],
                             false, stride, offset);
    return attribute_handle;
}

function set_uniform(c, uniform_handle, uniform_function, value) {
    // Get a TypedArray.
    array = to_typed_array(value);

    if (uniform_function.indexOf('Matrix') > 0) {
        // Matrix uniforms.
        c.gl[uniform_function](uniform_handle, false, array);
    }
    else {
        // Scalar uniforms.
        c.gl[uniform_function](uniform_handle, array);
    }
}

function get_attribute_info(type) {
    // type: vec2, ivec3, float, etc.
    
    // Find OpenGL attribute type.
    var gl_type = 'FLOAT';
    if (type[0] == 'i' || type == 'int') {
        gl_type = 'INT';
    }
    
    // Find ndim.
    var ndim;
    if (type == 'int' || type == 'float') {
        ndim = 1;
    }
    else {
        ndim = parseInt(type.slice(-1));
    }

    return [gl_type, ndim];
}

function get_uniform_function(type) {
    // Find OpenGL attribute type.
    var type_char;
    var ndim;
    if (type[0] == 'i' || type == 'int') {
        type_char = 'i';
    }
    else {
        type_char = 'f';
    }
    
    // Find ndim.
    var ndim;
    if (type == 'int' || type == 'float') {
        ndim = 1;
    }
    else {
        ndim = parseInt(type.slice(-1));
    }

    return 'uniform{0}{1}v'.format(ndim, type_char);
}


/* Creation of vispy.gloo.glir */
define(["jquery"], function($) {
    var glir = function() {
        var that = this;
        // Constructor.
        VispyCanvas.prototype.call = function(command) {
            that.call(this, command);
        };
    };

    glir.prototype.init = function(c) {
        // Namespace with the table of all symbols used by GLIR.

        // The key is user-specified and is named the **id**.
        // The WebGL internal handle is called the **handle**.

        // For each id key, the value is an object with the following properties:
        // * object_type ('VertexBuffer', 'Program', etc.)
        // * handle (the WebGL internal handle, for all objects)
        // * data_type (for Buffers)
        // * offset (for Buffers)
        // * attributes (for Programs)
        // * uniforms (for Programs)
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
            c._ns[id] = {
                object_type: cls, 
                handle: c.gl.createBuffer(),
                size: 0,  // current size of the buffer
            };
        }
        else if (cls == 'Program') {
            console.debug("Creating program '{0}'.".format(id));
            c._ns[id] = {
                object_type: cls,
                handle: c.gl.createProgram(),
                attributes: {},
                uniforms: {},
            };
        }
    };

    glir.prototype.delete = function(c, args) {
        var id = args[0];
        var cls = c._ns[id].object_type;
        var handle = c._ns[id].handle;
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
        var handle = c._ns[id].handle;

        // Compile shaders.
        console.debug("Compiling shaders for program '{0}'.".format(id));
        var vs = compile_shader(c, 'VERTEX_SHADER', vertex_code);
        var fs = compile_shader(c, 'FRAGMENT_SHADER', fragment_code);

        // Attach shaders.
        console.debug("Attaching shaders for program '{0}'".format(id));
        attach_shaders(c, handle, vs, fs);
    }

    glir.prototype.data = function(c, args) {
        var buffer_id = args[0];
        var offset = args[1];
        var data = args[2];
        var size = data.length;

        var buffer_type = c._ns[buffer_id].object_type; // VertexBuffer or IndexBuffer
        var buffer_handle = c._ns[buffer_id].handle;
        var gl_type;
        if (buffer_type == 'VertexBuffer') {
            gl_type = c.gl.ARRAY_BUFFER;
        }
        else if (buffer_type == 'IndexBuffer') {
            gl_type = c.gl.ELEMENT_ARRAY_BUFFER;
        }

        // Get a TypedArray.
        var array = to_typed_array(data);

        c.gl.bindBuffer(gl_type, buffer_handle);

        // Allocate buffer or reallocate buffer
        if (c._ns[buffer_id].size == 0) {
            // The existing buffer was empty: we create it.
            console.debug("Allocating {0} elements in buffer '{1}'.".format(
                size, buffer_id));
            c.gl.bufferData(gl_type, array, c.gl.STATIC_DRAW);
            c._ns[buffer_id].size = size;
        }
        else {
            // We reuse the existing buffer.
            console.debug("Updating {0} elements in buffer '{1}', offset={2}.".format(
                size, buffer_id, offset));
            c.gl.bufferSubData(gl_type, offset, array);
        }
    }

    glir.prototype.attribute = function(c, args) {
        var program_id = args[0];  // program id
        var name = args[1];
        var type = args[2];
        var vbo_id = args[3];
        var stride = args[4];
        var offset = args[5];

        var program_handle = c._ns[program_id].handle;

        console.debug("Creating attribute '{0}' for program '{1}'.".format(
                name, program_id
            ));
        var attribute_handle = create_attribute(c, program_handle, vbo_id,
            name, type, stride, offset);

        // Store the attribute handle in the attributes array of the program.
        c._ns[program_id].attributes[name] = attribute_handle;
    }

    glir.prototype.uniform = function(c, args) {
        var program_id = args[0];  // program id
        var name = args[1];
        var type = args[2];
        var value = args[3];
        
        var program_handle = c._ns[program_id].handle;

        c.gl.useProgram(program_handle);

        // Check the cache.
        if (c._ns[program_id].uniforms[name] == undefined) {
            // If necessary, we create the uniform and cache both its handle and
            // GL function.
            console.debug("Creating uniform '{0}' for program '{1}'.".format(
                    name, program_id
                ));
            var uniform_handle = c.gl.getUniformLocation(program_handle, name);
            var uniform_function = get_uniform_function(type);
            // We cache the uniform handle and the uniform function name as well.
            c._ns[program_id].uniforms[name] = [uniform_handle, uniform_function];
        }
        console.debug("Setting uniform '{0}' to '{1}' with {2} elements.".format(
                name, value, value.length
            ));
        var uniform_info = c._ns[program_id].uniforms[name];
        var uniform_handle = uniform_info[0];
        var uniform_function = uniform_info[1];
        set_uniform(c, uniform_handle, uniform_function, value);
    }

    glir.prototype.draw = function(c, args) {
        var program_id = args[0];
        var mode = args[1];
        var selection = args[2];

        var program_handle = c._ns[program_id].handle;

        if (selection.length == 2) {
            var start = selection[0];
            var count = selection[1];
            c.gl.useProgram(program_handle);
            console.debug("Rendering program '{0}' with {1}.".format(
                program_id, mode));
            c.gl.drawArrays(c.gl[mode], start, count);
        }     
        else if (selection.length == 3) {
            var index_buffer_handle = selection[0];
            var index_buffer_type = selection[1];
            var count = selection[2];
            // TODO: index buffer
        }
    }

    glir.prototype.func = function(c, args) {
        var name = args[0];
        console.debug("Calling {0}({1}).".format(name, args.slice(1)));

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
