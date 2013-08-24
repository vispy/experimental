// Uniforms
// ------------------------------------
uniform mat4      u_view;
uniform mat4      u_projection;
uniform sampler2D u_uniforms;
uniform vec3      u_uniforms_shape;
uniform vec4      u_color;

// Attributes (in)
// ------------------------------------
attribute vec3    a_position;
attribute vec4    a_color;
attribute vec3    a_normal;
attribute float   a_index;


// Varying (out)
// ------------------------------------
varying vec4      v_color;

void main()
{
    float rows = u_uniforms_shape.x;
    float cols = u_uniforms_shape.y;
    float count= u_uniforms_shape.z;
    float index = a_index;
    int index_x = int(mod(index, (floor(cols/(count/4.0))))) * int(count/4.0);
    int index_y = int(floor(index / (floor(cols/(count/4.0)))));

    float size_x = cols - 1.0;
    float size_y = rows - 1.0;
    float ty = float(index_y)/size_y;
    int i = index_x;

    // Extract uniforms from uniform texture
    vec4 translate = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    vec4 rotate    = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    vec4 scale     = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));

    // Get position
    vec3 position = a_position;
    vec4 q;
    vec3 axis, temp;
    float angle;


    // Y axis rotation
    axis = vec3(0.0,1.0,0.0);
    angle = rotate.y / 2.0;
    q = vec4(axis * sin(angle), cos(angle));
    temp = cross(q.xyz, position) + q.w * position;
    position = vec3(cross(temp, -q.xyz) + dot(q.xyz,position) * q.xyz + q.w * temp);

    // Z axis rotation
    axis = vec3(0.0,0.0,1.0);
    angle = rotate.z / 2.0;
    q = vec4(axis * sin(angle), cos(angle));
    temp = cross(q.xyz, position) + q.w * position;
    position = vec3(cross(temp, -q.xyz) + dot(q.xyz,position) * q.xyz + q.w * temp);

    // Translation
    position += translate.xyz;

    // Scaling
    position *= scale.xyz;

    // Color
    v_color = a_color * u_color;

    
    gl_Position = u_projection * u_view * vec4(position,1.0);
}
