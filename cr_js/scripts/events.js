/* Internal functions */
function get_pos(c, e) {
    return [e.clientX - c.offsetLeft, e.clientY - c.offsetTop];
}

function normalize_pos(c, pos) {
    return [2*pos[0]/c.width-1, 1-2*pos[1]/c.height];
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


/* Event generation */
function gen_mouse_event(c, e, type) {
    if (c._eventinfo.is_button_pressed)
        var button = e.button;
    else
        button = null;
    var pos = get_pos(c.$el.get(0), e);
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
        
        'last_event': last_event,  // WARNING: recursion problems?
    }
    return event;
}

function gen_resize_event(c, size) {
    // var canvas = c.$el.get(0);
    // console.log(c);
    var event = {
        'type': 'resize',
        'size': size,//[c.clientWidth, c.clientHeight]
    }
    return event;
}

function gen_paint_event(c) {
    var event = {
        'type': 'paint',
    }
    return event;
}

function gen_initialize_event(c) {
    var event = {
        'type': 'initialize',
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
        
        'last_event': last_event,  // WARNING: recursion problems?
    }
    return event;
}



/* Internal callback functions */
VispyCanvas.prototype._mouse_press = function(e) { };
VispyCanvas.prototype._mouse_release = function(e) { };
VispyCanvas.prototype._mouse_move = function(e) { };
VispyCanvas.prototype._mouse_wheel = function(e) { };
VispyCanvas.prototype._mouse_click = function(e) { };
VispyCanvas.prototype._mouse_dblclick = function(e) { };

VispyCanvas.prototype._key_press = function(e) { };
VispyCanvas.prototype._key_release = function(e) { };

VispyCanvas.prototype._initialize = function(e) { };
VispyCanvas.prototype._resize = function(e) { };
VispyCanvas.prototype._paint = function(e) { };



/* Registering handlers */
VispyCanvas.prototype.on_mouse_press = function(f) { 
    this._mouse_press = f; 
};
VispyCanvas.prototype.on_mouse_release = function(f) { 
    this._mouse_release = f; 
};
VispyCanvas.prototype.on_mouse_move = function(f) { 
    this._mouse_move = f; 
};
VispyCanvas.prototype.on_mouse_wheel = function(f) { 
    this._mouse_wheel = f; 
};
VispyCanvas.prototype.on_mouse_dblclick = function(f) { 
    this._mouse_dblclick = f; 
};
VispyCanvas.prototype.on_key_press = function(f) { 
    this._key_press = f; 
};
VispyCanvas.prototype.on_key_release = function(f) { 
    this._key_release = f; 
};
VispyCanvas.prototype.on_initialize = function(f) {
    this._initialize = f;
};
VispyCanvas.prototype.on_resize = function(f) { 
    this._resize = f; 
};
VispyCanvas.prototype.on_paint = function(f) { 
    this._paint = f; 
};


VispyCanvas.prototype.initialize = function() {
    var event = gen_initialize_event(this);
    this._initialize(event);
};
VispyCanvas.prototype.paint = function() {
    var event = gen_paint_event(this);
    this._paint(event);
};
VispyCanvas.prototype.update = VispyCanvas.prototype.paint;
VispyCanvas.prototype.resize = function(size) {
    if (size == undefined) {
        var size = [this.$el.width(), this.$el.height()];
    }
    var event = gen_resize_event(this, size);
    this.gl.canvas.width = size[0];
    this.gl.canvas.height = size[1];
    this.size = size;
    this.width = size[0];
    this.height = size[1];
    this._resize(event);
};

VispyCanvas.prototype.toggle_fullscreen = function() {
    if (screenfull.enabled) {
        if(screenfull.isFullscreen) {
            screenfull.exit();
            this.resize(this._size);
        }
        else {
            this._size = [this.$el.width(), this.$el.height()];
            screenfull.request(this.$el[0]);
            this.resize([screen.width, screen.height]);
        }
    }
}

VispyCanvas.prototype.resizable = function() {
    var that = this;
    this.$el.resizable({
        resize: function(event, ui) {
            that.resize([ui.size.width, ui.size.height]);
        }
    });
}

/* Canvas initialization */
function init_app(c) {

    c.$el.resize(function(e) {
            c.resize([e.width(), e.height()]);
        }
    );

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
    
    c.$el.mousemove(function(e) {
        var event = gen_mouse_event(c, e, 'mouse_move');
        
        // Vispy callbacks.
        c._mouse_move(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.$el.mousedown(function(e) {
        ++c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_release');
        
        // Vispy callbacks.
        c._mouse_press(event);
        
        // Save the last press event.
        c._eventinfo.press_event = event;
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.$el.mouseup(function(e) {
        --c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_press');
        
        // Vispy callbacks.
        c._mouse_release(event);
        
        // Reset the last press event.
        c._eventinfo.press_event = null;
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.$el.click(function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    });
    c.$el.dblclick(function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    });
    c.$el.mousewheel(function(e) {
        var event = gen_mouse_event(c, e, 'mouse_wheel');
        event.delta = [e.wheelDeltaX / 100., e.wheelDeltaY / 100.];
        
        // Vispy callbacks.
        c._mouse_wheel(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    
    // HACK: this is to extend the mouse events outside the canvas
    // document.onmousemove = c.onmousemove;
    // document.onmousedown = c.onmousedown;
    // document.onmouseup = c.onmouseup;
    
    c.$el.keypress(function(e) {
        var event = gen_key_event(c, e, 'key_press');
        
        // Vispy callbacks.
        c._key_press(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.$el.keyup(function(e) {
        var event = gen_key_event(c, e, 'key_release');
        
        // Vispy callbacks.
        c._key_release(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.$el.keydown(function(e) {
        //c._eventinfo.modifiers = get_modifiers(e);
    });
    
    c.$el.mouseout(function(e) {
    });
}


/* Creation of vispy.events */
define(["jquery", "jquery-mousewheel", "jquery-ui", "screenfull"], function($) {
    var events = function() {
        // Constructor.

    };

    events.prototype.init = function(c) {
        init_app(c);
    };

    return new events();
});
