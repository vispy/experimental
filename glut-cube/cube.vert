// Uniforms
// ------------------------------------
uniform   vec4 u_color;
uniform   mat4 u_model;
uniform   mat4 u_view;
uniform   mat4 u_projection;

// Attributes
// ------------------------------------
attribute vec3 position;
attribute vec4 color;

// Varying
// ------------------------------------
varying vec4 v_color;

void main()
{
    v_color = color*u_color;
    gl_Position = u_projection * u_view * u_model * vec4(position,1.0);
}
