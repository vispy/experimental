// TODO: how to handle heterogeneous data types, structured arrays.
// Probably with DataViews.

// Mapping between user-friendly data type string, and typed array classes.
var _typed_array_map = {
    'float32': Float32Array,
    'int8': Int8Array,
    'int16': Int16Array,
    'int32': Int32Array,
    'uint8': Uint8Array,
    'uint16': Uint16Array,
    'uint32': Uint32Array,
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
        // TODO: base64-encoded buffer. Need to decode and convert to a typed array
    }
}
