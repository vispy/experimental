
/******************************************************************************
/ Utility functions
/*****************************************************************************/

// Base64 decoder
var Base64Binary = {
    _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

    /* will return a  Uint8Array type */
    decodeArrayBuffer: function(input) {
        var bytes = (input.length/4) * 3;
        var ab = new ArrayBuffer(bytes);
        this.decode(input, ab);

        return ab;
    },

    decode: function(input, arrayBuffer) {
        //get last chars to see if are valid
        var lkey1 = this._keyStr.indexOf(input.charAt(input.length-1));		 
        var lkey2 = this._keyStr.indexOf(input.charAt(input.length-2));		 
        
        var bytes = (input.length/4) * 3;
        if (lkey1 == 64) bytes--; //padding chars, so skip
        if (lkey2 == 64) bytes--; //padding chars, so skip

        var uarray;
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;
        var j = 0;

        if (arrayBuffer)
            uarray = new Uint8Array(arrayBuffer);
        else
            uarray = new Uint8Array(bytes);

        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

        for (i=0; i<bytes; i+=3) {	
            //get the 3 octets in 4 ascii chars
            enc1 = this._keyStr.indexOf(input.charAt(j++));
            enc2 = this._keyStr.indexOf(input.charAt(j++));
            enc3 = this._keyStr.indexOf(input.charAt(j++));
            enc4 = this._keyStr.indexOf(input.charAt(j++));

            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;

            uarray[i] = chr1;			
            if (enc3 != 64) uarray[i+1] = chr2;
            if (enc4 != 64) uarray[i+2] = chr3;
        }

        return uarray;	
    }
}

// Convert a Base64-encoded array into a Javascript Array Buffer.
function get_array(s, vartype) {
    var data = Base64Binary.decodeArrayBuffer(s);
    var size = Math.floor(data.byteLength / 4);
    // TODO: accept 16 and 8 bit and 64 bit
    // 32 bits floats
    if (vartype.startsWith('GL_FLOAT')) {
        data = new Float32Array(data, 0, size);
    }
    // 32 bits int
    else if (vartype.startsWith('GL_INT')) {
        // HACK: we force int32 to be float32 for OpenGL ES
        data = new Float32Array(new Int32Array(data, 0, size));
    }
    return data;
}


// Provide string.startsWith function.
if (typeof String.prototype.startsWith != 'function') {
  // see below for better implementation!
  String.prototype.startsWith = function (str){
    return this.indexOf(str) == 0;
  };
}






/******************************************************************************
/ vispy.app.js
/*****************************************************************************/
function get_pos(c, e) {
    return [e.clientX - c.offsetLeft, e.clientY - c.offsetTop];
}

function get_modifiers(e) {
    var modifiers = [];
    if (e.altKey) modifiers.push('alt');
    if (e.ctrlKey) modifiers.push('ctrl');
    if (e.metaKey) modifiers.push('meta');
    if (e.shiftKey) modifiers.push('shift');
    return modifiers;
}

function get_key(e){
    var keynum = null;
    if(window.event){ // IE					
        keynum = e.keyCode;
    }
    else if(e.which){ // Netscape/Firefox/Opera					
            keynum = e.which;
         }
    return keynum;
    if (keynum != null)
        return String.fromCharCode(keynum).toLowerCase();
    else
        return null;
}

function gen_mouse_event(c, e, type) {
    if (c._eventinfo.is_button_pressed)
        var button = e.button;
    else
        button = null;
    var pos = get_pos(c, e);
    var modifiers = get_modifiers(e);
    var press_event = c._eventinfo.press_event;
    var last_event = c._eventinfo.last_event;
    var event = {
        'type': type,
        'pos': pos,
        'button': button,
        'is_dragging': press_event != null,
        'modifiers': modifiers,
        'delta': null,
        'press_event': press_event,
        
        //'last_event': last_event,  // WARNING: recursion problems?
    }
    return event;
}

function gen_key_event(c, e, type) {
    var modifiers = get_modifiers(e);
    var last_event = c._eventinfo.last_event;
    var event = {
        'type': type,
        'modifiers': modifiers,
        'key': get_key(e),
        
        //'last_event': last_event,  // WARNING: recursion problems?
    }
    return event;
}

function init_app(c) {
    c.on_mouse_press = function(e) { };
    c.on_mouse_release = function(e) { };
    c.on_mouse_move = function(e) { };
    c.on_mouse_wheel = function(e) { };
    c.on_mouse_click = function(e) { };
    c.on_mouse_dblclick = function(e) { };
    
    c.on_key_press = function(e) { };
    c.on_key_release = function(e) { };
    
    // This object stores some state necessary to generate the appropriate
    // events.
    c._eventinfo = {
        'type': null,
        'pos': null,
        'button': null,
        'is_dragging': null,
        'key': null,
        'modifiers': [],
        'press_event': null,
        'last_event': null,
        'delta': null,
    }
    
    // HACK: boolean stating whether a mouse button is pressed.
    // This is necessary because e.button==0 in two cases: no
    // button is pressed, or the left button is pressed.
    c._eventinfo.is_button_pressed = 0;
    
    c.onmousemove = function(e) {
        var event = gen_mouse_event(c, e, 'mouse_move');
        
        // Vispy callbacks.
        c.on_mouse_move(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    c.onmousedown = function(e) {
        ++c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_release');
        
        // Vispy callbacks.
        c.on_mouse_press(event);
        
        // Save the last press event.
        c._eventinfo.press_event = event;
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    c.onmouseup = function(e) {
        --c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_press');
        
        // Vispy callbacks.
        c.on_mouse_release(event);
        
        // Reset the last press event.
        c._eventinfo.press_event = null;
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    c.onclick = function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    }
    c.ondblclick = function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    }
    c.onmousewheel = function(e) {
        var event = gen_mouse_event(c, e, 'mouse_wheel');
        event.delta = [e.wheelDeltaX / 100., e.wheelDeltaY / 100.];
        
        // Vispy callbacks.
        c.on_mouse_wheel(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    
    
    c.onkeypress = function(e) {
        var event = gen_key_event(c, e, 'key_press');
        
        // Vispy callbacks.
        c.on_key_press(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    c.onkeyup = function(e) {
        var event = gen_key_event(c, e, 'key_release');
        
        // Vispy callbacks.
        c.on_key_release(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    }
    c.onkeydown = function(e) {
        //c._eventinfo.modifiers = get_modifiers(e);
    }
}







/******************************************************************************
/ vispy.gloo.js
/*****************************************************************************/


function viewport(c) {
    c.gl.viewport(0, 0, c.width, c.height);
}

function clear(c, color) {
    c.gl.clearColor(color[0], color[1], color[2], color[3]);
    c.gl.clear(c.gl.COLOR_BUFFER_BIT);
}

function init_gl(c) {
    c.gl = c.getContext("webgl") || c.getContext("experimental-webgl");
    viewport(c);
    clear(c, [0,0,0,1]);
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



function GLObject() {
    this._handle = -1;
    this._need_create = true;
    this._need_update = true;
    this._need_delete = false;
}
GLObject.prototype._activate = function() { }
GLObject.prototype._deactivate = function() { }
GLObject.prototype._create = function() { }
GLObject.prototype._update = function() { }
GLObject.prototype.activate = function() {

    if (this._need_create) {
        this._create();
        this._need_create = false;
    }
    
    this._activate();
    
    if (this._need_update) {
        this._update();
        this._need_update = false;
        this._activate();
    }
}
GLObject.prototype.deactivate = function() {
    this._deactivate();
}




function Buffer(c, data, type) {
    if (typeof(type) == 'undefined')
        type = 'ARRAY_BUFFER'
    this.c = c;
    this.type = type;
    this.set_data(data);
}
Buffer.prototype = new GLObject();
Buffer.prototype.set_data = function(data) {
    this.data = data;
    this.nbytes = data.length;
}
Buffer.prototype._create = function() {
    this._handle = this.c.gl.createBuffer();
}
Buffer.prototype._delete = function() {
    this.c.gl.deleteBuffer(this._handle);
}
Buffer.prototype._activate = function() {
    this.c.gl.bindBuffer(this.c.gl[this.type], this._handle);
}
Buffer.prototype._deactivate = function() {
    //this.c.gl.bindBuffer(this.c.gl[this.type], 0);
}
Buffer.prototype._update = function() {
    this.c.gl.bufferData(this.c.gl[this.type], this.data, this.c.gl.STATIC_DRAW);
}



var gl_typeinfo = {
    'GL_FLOAT':         [1, 'FLOAT', 'float32'],
    'GL_FLOAT_VEC2':    [2, 'FLOAT', 'float32'],
    'GL_FLOAT_VEC3':    [3, 'FLOAT', 'float32'],
    'GL_FLOAT_VEC4':    [4, 'FLOAT', 'float32'],
    'GL_INT':           [1, 'INT', 'int32'],
    'GL_INT_VEC2':      [2, 'INT', 'int32'],
    'GL_INT_VEC3':      [3, 'INT', 'int32'],
    'GL_INT_VEC4':      [4, 'INT', 'int32'],
    'GL_BOOL':          [1, 'BOOL', 'bool'],
    'GL_BOOL_VEC2':     [2, 'BOOL', 'bool'],
    'GL_BOOL_VEC3':     [3, 'BOOL', 'bool'],
    'GL_BOOL_VEC4':     [4, 'BOOL', 'bool']
}

function Attribute(c, program, name, gtype) {
    this.c = c;
    this.program = program;
    this.name = name;
    this.gtype = gtype;
}
Attribute.prototype = new GLObject();
Attribute.prototype.set_data = function(data) {
    this.data = data;
}
Attribute.prototype._create = function() {
    this._handle = this.c.gl.getAttribLocation(this.program._handle, this.name);
}
Attribute.prototype._activate = function() {
    this.data.activate();
    r = gl_typeinfo[this.gtype];
    ndim = r[0];
    gtype = r[1];
    dtype = r[2];
    stride = this.data.stride;
    this.size = this.data.nbytes / ndim;
    
    this.c.gl.enableVertexAttribArray(this._handle);
    this.c.gl.vertexAttribPointer(this._handle, ndim, this.c.gl[gtype],
                                false, 0, this.data.offset);
}
Attribute.prototype._deactivate = function() {
    this.data.deactivate();
}
Attribute.prototype._update = function() {
    // TODO
}




var _ufunctions = {
    'GL_FLOAT':        'uniform1fv',
    'GL_FLOAT_VEC2':   'uniform2fv',
    'GL_FLOAT_VEC3':   'uniform3fv',
    'GL_FLOAT_VEC4':   'uniform4fv',
    'GL_INT':          'uniform1iv',
    'GL_BOOL':         'uniform1iv',
    'GL_FLOAT_MAT2':   'uniformMatrix2fv',
    'GL_FLOAT_MAT3':   'uniformMatrix3fv',
    'GL_FLOAT_MAT4':   'uniformMatrix4fv',
    'GL_SAMPLER_2D':   'uniform1i',
}

function Uniform(c, program, name, gtype) {
    this.c = c;
    this.program = program;
    this.name = name;
    this.gtype = gtype;
    this._ufunction = _ufunctions[gtype];
}
Uniform.prototype = new GLObject();
Uniform.prototype.set_data = function(data) {
    this.data = data;
    this._need_update = true;
}
Uniform.prototype._create = function() {
    this._handle = this.c.gl.getUniformLocation(this.program._handle, this.name);
}
Uniform.prototype._activate = function() {
    // TODO texture
}
Uniform.prototype._deactivate = function() {
    // TODO texture
}
Uniform.prototype._update = function() {
    if (this.data == undefined)
        return;
    this.c.gl[this._ufunction](this._handle, this.data);
}





function Program(c, vertex, fragment) {
    this.c = c;
    this.vertex = compile_shader(c, "VERTEX_SHADER", vertex);
    this.fragment = compile_shader(c, "FRAGMENT_SHADER", fragment);
    this._attributes = {};
    this._uniforms = {};
    this._create();
}
Program.prototype = new GLObject();
Program.prototype._create = function() {
    this._handle = this.c.gl.createProgram();
}
Program.prototype._update = function() {
    this.c.gl.attachShader(this._handle, this.vertex);
    this.c.gl.attachShader(this._handle, this.fragment);
    this.c.gl.linkProgram(this._handle);

    if (!this.c.gl.getProgramParameter(this._handle, this.c.gl.LINK_STATUS))
    {
        console.log("Could not initialise shaders");
    }
}
Program.prototype.add_attribute = function(name, gtype, data) {
    this._attributes[name] = new Attribute(this.c, this, name, gtype);
    if (typeof(data) != undefined)
        this.set_data(name, data);
}
Program.prototype.add_uniform = function(name, gtype, data) {
    this._uniforms[name] = new Uniform(this.c, this, name, gtype);
    if (typeof(data) != undefined)
        this.set_data(name, data);
}
Program.prototype._activate = function() {
    if (this._need_update) {
        return;
    }
    this.c.gl.useProgram(this._handle);
    for (var name in this._attributes) {
        this._attributes[name].activate();
    }
    for (var name in this._uniforms) {
        this._uniforms[name].activate();
    }
}
Program.prototype._deactivate = function() {
    for (var name in this._attributes) {
        this._attributes[name].deactivate();
    }
    for (var name in this._uniforms) {
        this._uniforms[name].deactivate();
    }
}
Program.prototype.set_data = function(name, data) {
    if (name in this._attributes)
        this._attributes[name].set_data(data);
    if (name in this._uniforms)
        this._uniforms[name].set_data(data);
}
Program.prototype.draw = function(count) {
    this.activate();
    first = 0;
    count = this._attributes[Object.keys(this._attributes)[0]].size;
    this.c.gl.drawArrays(this.c.gl[this.mode], first, count);
    this.deactivate();
}

function create_program(c, program_export) {
    var vertex = program_export['vertex_shader'];
    var fragment = program_export['fragment_shader'];
    
    var program = new Program(c, vertex, fragment);
    program.mode = program_export['mode'].toUpperCase();
    
    for (var name in program_export['attributes']) {
        attr = program_export['attributes'][name];
        var gtype = attr['gtype'];
        var data = get_array(attr['data']['buffer'], gtype)
        var vbo = new Buffer(c, data);
        program.add_attribute(name, gtype, vbo);
    }
    
    for (var name in program_export['uniforms']) {
        uniform = program_export['uniforms'][name];
        var gtype = uniform['gtype'];
        var data = get_array(uniform['data']['buffer'], gtype);
        program.add_uniform(name, gtype, data);
    }
    return program;
}

function show_program(c, program) {
    program.draw();
}

function create_scene(c, gloo_export) {
    _programs = {}
    for (var progname in gloo_export['programs']) {
        program = create_program(c, gloo_export['programs'][progname]);
        _programs[progname] = program;
    }
    scene = {'programs': _programs};
    return scene;
}

function show_scene(c, scene, color) {
    if (color == undefined)
        color = [0., 0., 0., 1.];
    clear(c, color);
    for (var name in scene['programs']) {
        show_program(c, scene['programs'][name]);
    }
}
