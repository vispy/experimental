// -----------------------------------------------------------------------------
// Copyright (c) 2013 Nicolas P. Rougier. All rights reserved.
// 
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
// 
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
// 
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
// 
// THIS SOFTWARE IS PROVIDED BY NICOLAS P. ROUGIER ''AS IS'' AND ANY EXPRESS OR
// IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
// EVENT SHALL NICOLAS P. ROUGIER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
// INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
// THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
// 
// The views and conclusions contained in the software and documentation are
// those of the authors and should not be interpreted as representing official
// policies, either expressed or implied, of Nicolas P. Rougier.
// -----------------------------------------------------------------------------
const float PI = 3.14159265358979323846264;
const float THETA = 15.0 * 3.14159265358979323846264/180.0;


// Uniforms
// ------------------------------------
uniform mat4      u_view;
uniform mat4      u_projection;
uniform mat4      u_model;
uniform vec4      u_viewport;
uniform sampler2D u_uniforms;
uniform vec3      u_uniforms_shape;

// Attributes
// ------------------------------------
attribute vec3  a_center;
attribute vec2  a_texcoord;
attribute float a_index;

// Varying
// ------------------------------------
varying vec4  v_fg_color;
varying vec4  v_bg_color;
varying float v_radius;
varying vec2  v_position;
varying float v_linewidth;
varying float v_antialias;

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
    vec4 _uniform;

    // Get fg_color(4)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    v_fg_color = _uniform;

    // Get bg_color(4)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    v_bg_color = _uniform;
    //v_bg_color.rgb = (a_center+1.5)/3.0;
    //v_bg_color.a = 1.0;


    // Get translate(2), scale(1), rotate(1)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty)); 
    vec3  translate = _uniform.xyz;
    float scale     = _uniform.w;

    // Get linewidth(1), antialias(1)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    v_radius     = _uniform.x;
    v_linewidth  = _uniform.y;
    v_antialias  = _uniform.z;

    // Thickness below 1 pixel are represented using a 1 pixel thickness
    // and a modified alpha
    v_fg_color.a = min(v_linewidth, v_fg_color.a);
    v_linewidth = max(v_linewidth, 1.0);

    // If color is fully transparent we just will discard the fragment anyway
    if( (v_fg_color.a <= 0.0) && (v_bg_color.a <= 0.0))
    {
        gl_Position = vec4(0.0,0.0,0.0,1.0);
        return;
    }

    // This is the actual half width of the line
    float w = ceil(1.25*v_antialias+v_linewidth)/2.0;

    // Move vertex position into place
    v_radius *= scale;
    v_position = a_texcoord*(v_radius+w);

    vec4 center = ((u_view*u_model)*vec4(a_center,1.0));
    center.xyz += translate.xyz;

    gl_Position = u_projection*center;
    gl_Position.xy += (v_position* gl_Position.w)/u_viewport.zw;
}
