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
const float PI = 3.141592653589793;


float
cap( float type, float dx, float dy, float t )
{
    float d = 0.0;

    // None
    if                 ( type < 0.5 )  discard;
    // Round
    else if ( abs(type - 1.0) < 0.5 ) return sqrt(dx*dx+dy*dy);
    // Triangle out
    else if ( abs(type - 2.0) < 0.5 ) return max(abs(dy),(t+dx-abs(dy)));
    // Triangle in
    else if ( abs(type - 3.0) < 0.5 ) return (dx+abs(dy));
    // Square
    else if ( abs(type - 4.0) < 0.5 ) return max(dx,dy);
    // Butt
    else if ( abs(type - 5.0) < 0.5 ) return max(dx+t,dy);

    discard;
}


// Uniforms
// ------------------------------------
uniform mat4      u_view;
uniform mat4      u_projection;
uniform mat4      u_model;
uniform vec2      u_viewport;
uniform sampler2D u_dash_atlas;


// Varying
// ------------------------------------
varying vec2  v_texcoord;
varying vec4  v_color;
varying float v_length;
varying float v_linewidth;
varying float v_localwidth;
varying float v_antialias;
varying float v_dash_phase;
varying float v_dash_period;
varying float v_dash_index;
varying vec2  v_dash_caps;


void main()
{
    float dx = v_texcoord.x;
    float dy = abs(v_texcoord.y);
    float dash_width = v_linewidth;
    float freq = v_dash_period * dash_width;
    float u = mod( dx + v_dash_phase*dash_width, freq );
    vec4 v = texture2D(u_dash_atlas, vec2(u/freq, v_dash_index));
    float dash_center= v.x * dash_width;
    float dash_type  = v.y;
    float _start = v.z * dash_width;
    float _stop  = v.a * dash_width;
    float dash_start = dx - u + _start;
    float dash_stop  = dx - u + _stop;
    float line_start = 0.0;
    float line_stop = v_length;

    vec4 color = vec4(v_color.rgb, v_color.a * (dx/v_length));
    float t = v_localwidth/2. - 1.5*v_antialias;
    float d = dy;
    

    // Check is dash stop is before line start
    if( dash_stop <= line_start )
    {
        discard;
    }
    // Check is dash start is beyond line stop
    if( dash_start >= line_stop )
    {
        discard;
    }

    // Line cap start
    if( (dx <= line_start) && (dash_start <= line_start) && (dash_stop >= line_start) )
    {
        float u = v_localwidth * abs(dx) / dash_width;
        d = cap( v_dash_caps.x, u, abs(dy), t);
    }
    // Line stop cap
    else if( (dx >= line_stop) && (dash_stop >= line_stop) && (dash_start <= line_stop) )
    {
        float u = v_localwidth * (dx-line_stop) / dash_width;
        d = cap( v_dash_caps.y, u, abs(dy), t);
    }
    // Dash body (plain)
    else if( dash_type == 0.0 )
    {
        // This is only to save last two tests
    }
    // Dash cap start
    else if( dash_type < 0.0 )
    {
        //float u = v_localwidth * max(u-dash_center, 0.0) / dash_width;
        float u = v_localwidth * max(u-dash_center, 0.0) / dash_width;
        d = cap( v_dash_caps.y, u , abs(dy), t);
    }
    // Dash cap end
    else if( dash_type > 0.0 )
    {
        float u = v_localwidth * max( dash_center-u, 0.0 ) / dash_width;
        d = cap( v_dash_caps.x, u, abs(dy), t);
    }
    

    // Distance to border
    // ------------------------------------------------------------------------
    d = d - t;
    if( d < 0.0 )
    {
        gl_FragColor = color;
    }
    else
    {
        d /= v_antialias;
        float a = exp(-d*d)*color.a;
        if( a < 0.001 )
            discard;
            //gl_FragColor = vec4(1.0,1.0,0.0,1.0);
        else
            gl_FragColor = vec4(color.xyz, a);
    }
}
