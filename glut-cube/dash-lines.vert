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
//
// See http://codeflow.org/entries/2012/aug/05/webgl-rendering-of-solid-trails/
//
// -----------------------------------------------------------------------------
const float PI = 3.141592653589793;


// Uniforms
// ------------------------------------
uniform mat4      u_view;
uniform mat4      u_projection;
uniform mat4      u_model;
uniform vec4      u_viewport;
uniform sampler2D u_uniforms;
uniform vec3      u_uniforms_shape;
uniform sampler2D u_dash_atlas;


// Attributes
// ------------------------------------
attribute vec3 a_prev;
attribute vec3 a_curr;
attribute vec3 a_next;
attribute vec2 a_texcoord;
attribute float a_index;

// Varying
// ------------------------------------
varying vec4 v_color;
varying vec2 v_texcoord;
varying float v_length;
varying float v_linewidth;
varying float v_localwidth;
varying float v_antialias;
varying float v_dash_phase;
varying float v_dash_period;
varying float v_dash_index;
varying vec2  v_dash_caps;


// Project from the world space to the screen space
vec2 project(vec4 P)
{
    vec2 p = 0.5 + (P.xyz/P.w).xy * 0.5;
    return p * u_viewport.zw;
}

// Project from the screen space to the world space
vec4 unproject(vec2 p, float z, float w)
{
    vec4 P = vec4( w*((p/u_viewport.zw)*2.0 - 1.0), z, w);
    return P;
}

// Estimate the linewidth
// WARNING: wrong if position == sPosition
float estimate_width(vec3 position, vec2 sPosition, float width)
{
    vec4 view_pos = u_view * u_model * vec4(position, 1.0);
    vec4 scale_pos = view_pos - vec4(normalize(view_pos.xy)*width, 0.0, 1.0);
    vec2 screen_scale_pos = project(u_projection * scale_pos);
    return distance(sPosition, screen_scale_pos);
}

void main() 
{
    // ------------------------------------------------------- Get uniforms ---
    float rows = u_uniforms_shape.x;
    float cols = u_uniforms_shape.y;
    float count= u_uniforms_shape.z;
    float index = a_index;
    int index_x = int(mod(index, (floor(cols/(count/4.0))))) * int(count/4.0);
    int index_y = int(floor(index / (floor(cols/(count/4.0)))));
    float size_x = cols - 1.0;
    float size_y = rows - 1.0;
    float ty = 0.0; 
    if (size_y > 0.0)
        ty = float(index_y)/size_y;

    int i = index_x;
    vec4 _uniform;

    // Get fg_color(4)
    v_color = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));

    // Get v_length(1), v_linewidth(1), v_antialias(1), v_dash_phase(1)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    v_length    = _uniform.x;
    v_linewidth = _uniform.y;
    v_antialias = _uniform.z;
    v_dash_phase= _uniform.w;

    // Get dash_period(1), dash_index(1), dash_caps(2)
    _uniform = texture2D(u_uniforms, vec2(float(i++)/size_x,ty));
    v_dash_period = _uniform.x;
    v_dash_index  = _uniform.y;
    v_dash_caps.x = _uniform.z;
    v_dash_caps.y = _uniform.w;
    // ------------------------------------------------------------------------

    mat4 T = u_projection * u_view * u_model;

    vec2 prev = project( T * vec4(a_prev.xyz,1.0));
    vec2 next = project( T * vec4(a_next.xyz,1.0));
    vec4 tcurr =         T * vec4(a_curr.xyz,1.0);
    vec2 curr = project(tcurr);

    vec2 tangent1 = normalize(prev - curr);
    vec2 tangent2 = normalize(curr - next);
    vec2 tangent = normalize(tangent1 + tangent2);
    vec2 ortho = vec2(-tangent.y, tangent.x)*a_texcoord.y;
    v_localwidth = estimate_width(a_curr.xyz, curr, v_linewidth);
    float w = v_localwidth/2. + 1.25*v_antialias;

    vec2 pos = curr + w*ortho;
    v_texcoord.x = a_texcoord.x;
    v_texcoord.y = a_texcoord.y * w;

    if( v_texcoord.x <= 0.0 )
    {
        pos += w*tangent; 
        v_texcoord.x -= v_linewidth/2.;
    }
    else if( v_texcoord.x >= v_length )
    {
        pos -= w*tangent;
        v_texcoord.x += v_linewidth/2.;
    }

    gl_Position = unproject(pos, tcurr.z, tcurr.w);
    //gl_Position = unproject(pos, v_position.z, v_position.w);
}
