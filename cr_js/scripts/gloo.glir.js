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

function create_attribute(c, program, vbo_handle, vbo_type,
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

    var attribute_handle = c.gl.getAttribLocation(program, name);
    c.gl.bindBuffer(c.gl[vbo_type], vbo_handle);

    c.gl.enableVertexAttribArray(attribute_handle);
    c.gl.vertexAttribPointer(attribute_handle, ndim, 
                             c.gl[attribute_type],
                             false, stride, offset);
    return attribute_handle;
}

// REFACTOR: put these two functions in glir
function create_uniform(c, program_handle, name) {
    uniform_handle = c.gl.getUniformLocation(program_handle, name)
    return uniform_handle;
}

function set_uniform(c, uniform_handle, uniform_function, value) {

    // Get a TypedArray.
    array = to_typed_array(value);

    c.gl[uniform_function](uniform_handle, array);
    // TODO: matrix
    // this.c.gl[this._ufunction](this._handle, false, this.data);
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


/* Data functions */
var _typed_array_map = {
    'float32': Float32Array,
    'int16': Int16Array,
    'int32': Int32Array,
    // TODO
};



function to_typed_array(data) {


    // Return a TypedArray from a JSON object describing a data buffer.
    // storage_type is one of 'javascript_array', 'javascript_typed_array', 
    // 'base64', 'png'
    var storage_type = data["storage_type"];

    // data can also be just a normal typed array, in which case we just return
    // the argument value.
    if (storage_type == undefined) {
        return data;
    }

    var data_type = data["data_type"];
    var contents = data["buffer"];

    if (storage_type == "javascript_array") {
        // A regular JavaScript array, the type must be specified in 'data_type'.
        return _typed_array_map[data_type](contents);
    }
    else if (storage_type == "javascript_typed_array") {
        // A JavaScript Typedarray.
        return contents;
    }
    if (storage_type == "base64") {
        // A base64-encoded buffer.
        // TODO
    }
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

        // The key is user-specified and is name the **id**.
        // The WebGL internal handle is called the **handle**. It is always the
        // second element in each item of the symbol table.

        // For each id, it is a pair (object_type, webgl_handle)
        // 0: type ('VertexBuffer', 'Program', etc.)
        // 1: handle
        //
        // Buffers:
        // 2: type
        // 3: offset
        //
        // Programs:
        // 2: attributes
        // 3: uniforms
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
            c._ns[id] = [cls, c.gl.createProgram(), {}, {}]; // attributes, uniforms
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
        var buffer_id = args[0];
        var offset = args[1];
        var data = args[2];

        var buffer_type = c._ns[buffer_id][0]; // VertexBuffer or IndexBuffer
        var buffer_handle = c._ns[buffer_id][1];
        var gl_type;
        if (buffer_type == 'VertexBuffer') {
            gl_type = c.gl['ARRAY_BUFFER'];
        }
        else if (buffer_type == 'IndexBuffer') {
            gl_type = c.gl['ELEMENT_ARRAY_BUFFER'];
        }

        // Get a TypedArray.
        var array = to_typed_array(data);

        c.gl.bindBuffer(gl_type, buffer_handle);

        c.gl.bufferData(gl_type, array, c.gl.STATIC_DRAW);
    }

    glir.prototype.attribute = function(c, args) {
        var program_id = args[0];  // program id
        var name = args[1];
        var type = args[2];
        var vbo_id = args[3];
        var stride = args[4];
        var offset = args[5];

        var program_handle = c._ns[program_id][1];


        // REFACTOR: integrate this into `create_attribute`
        var _attribute_info = get_attribute_info(type);
        var attribute_type = _attribute_info[0];
        var ndim = _attribute_info[1];

        _vbo_info = c._ns[vbo_id];
        var vbo_type = _vbo_info[0];
        var vbo_handle = _vbo_info[1];

        console.debug("Creating attribute '{0}' for program '{1}'.".format(
                name, program_id
            ));
        var attribute_handle = create_attribute(c, program_handle, 
            vbo_handle, 'ARRAY_BUFFER',
            name, attribute_type, ndim, stride, offset);

        // Store the attribute handle in the attributes array of the program.
        c._ns[program_id][2][name] = attribute_handle;
    }

    glir.prototype.uniform = function(c, args) {
        var program_id = args[0];  // program id
        var name = args[1];
        var type = args[2];
        var value = args[3];
        
        var program_handle = c._ns[program_id][1];

        c.gl.useProgram(program_handle);

        // Check the cache.
        if (c._ns[program_id][3][name] == undefined) {
            // If necessary, we create the uniform and cache both its handle and
            // GL function.
            console.debug("Creating uniform '{0}' for program '{1}'.".format(
                    name, program_id
                ));
            var uniform_handle = create_uniform(c, program_handle, name);
            var uniform_function = get_uniform_function(type);
            // We cache the uniform handle and the uniform function name as well.
            c._ns[program_id][3][name] = [uniform_handle, uniform_function];
        }
        console.debug("Setting uniform '{0}' to value '{1}'.".format(
                name, value
            ));
        var uniform_info = c._ns[program_id][3][name];
        var uniform_handle = uniform_info[0];
        var uniform_function = uniform_info[1];
        set_uniform(c, uniform_handle, uniform_function, value);
    }

    glir.prototype.draw = function(c, args) {
        var program_id = args[0];
        var mode = args[1];
        var selection = args[2];

        var program_handle = c._ns[program_id][1];

        if (selection.length == 2) {
            var start = selection[0];
            var count = selection[1];
            c.gl.useProgram(program_handle);
            c.gl.drawArrays(c.gl[mode], start, count);
        }     
        else if (selection.length == 3) {
            var index_buffer_handle = selection[0];
            var index_buffer_type = selection[1];
            var count = selection[2];
            // TODO
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
