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
        
        'last_event': last_event,  // WARNING: recursion problems?
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


/* Canvas initialization */
function init_app(c) {

    /* Registering handlers */
    c.on_mouse_press = function(f) { c.mouse_press = f; };
    c.on_mouse_release = function(f) { c.mouse_release = f; };
    c.on_mouse_move = function(f) { c.mouse_move = f; };
    c.on_mouse_wheel = function(f) { c.mouse_wheel = f; };
    c.on_mouse_dblclick = function(f) { c.mouse_dblclick = f; };
    c.on_key_press = function(f) { c.key_press = f; };
    c.on_key_release = function(f) { c.key_release = f; };

    /* Callback functions */
    c.mouse_press = function(e) { };
    c.mouse_release = function(e) { };
    c.mouse_move = function(e) { };
    c.mouse_wheel = function(e) { };
    c.mouse_click = function(e) { };
    c.mouse_dblclick = function(e) { };
    
    c.key_press = function(e) { };
    c.key_release = function(e) { };
    
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
    
    c.mousemove(function(e) {
        var event = gen_mouse_event(c, e, 'mouse_move');
        
        // Vispy callbacks.
        c.mouse_move(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.mousedown(function(e) {
        ++c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_release');
        
        // Vispy callbacks.
        c.mouse_press(event);
        
        // Save the last press event.
        c._eventinfo.press_event = event;
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.mouseup(function(e) {
        --c._eventinfo.is_button_pressed;
        var event = gen_mouse_event(c, e, 'mouse_press');
        
        // Vispy callbacks.
        c.mouse_release(event);
        
        // Reset the last press event.
        c._eventinfo.press_event = null;
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.click(function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    });
    c.dblclick(function(e) {
    
        // Reset the last press event.
        c._eventinfo.press_event = null;
    });
    c.mousewheel(function(e) {
        var event = gen_mouse_event(c, e, 'mouse_wheel');
        event.delta = [e.wheelDeltaX / 100., e.wheelDeltaY / 100.];
        
        // Vispy callbacks.
        c.mouse_wheel(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    
    // document.onmousemove = c.onmousemove;
    // document.onmousedown = c.onmousedown;
    // document.onmouseup = c.onmouseup;
    
    c.keypress(function(e) {
        var event = gen_key_event(c, e, 'key_press');
        
        // Vispy callbacks.
        c.key_press(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.keyup(function(e) {
        var event = gen_key_event(c, e, 'key_release');
        
        // Vispy callbacks.
        c.key_release(event);
        
        // Save the last event.
        c._eventinfo.last_event = event;
    });
    c.keydown(function(e) {
        //c._eventinfo.modifiers = get_modifiers(e);
    });
    
    c.mouseout(function(e) {
    });
}


/* Creation of vispy.events */
define(['jquery'], function($) {
    var events = function() {
        // Constructor.

    };

    events.prototype.init = function(c) {
        init_app(c);
    };

    return new events();
});
