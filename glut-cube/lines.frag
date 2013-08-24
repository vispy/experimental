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
uniform sampler2D u_dash_atlas;

// Varying
// ------------------------------------
varying vec2  v_texcoord;
varying vec4  v_color;
varying float v_length;
varying float v_linewidth;
varying float v_localwidth;
varying float v_antialias;
varying vec2  v_caps;

void main()
{
    //gl_FragColor = vec4(v_color.rgb, v_color.a); //* v_texcoord.x/v_length);
    // if( gl_FragCoord.z > .75 ) gl_FragColor.a *= .25;
    //return;

    float dx = v_texcoord.x;
    float dy = abs(v_texcoord.y);
    float line_start = 0.0;
    float line_stop = v_length;

    vec4 color = vec4(v_color.rgb, v_color.a * (dx/v_length));
    float t = v_localwidth/2. - 1.5*v_antialias;
    float d = dy;
    
    // Line cap start
    if( dx <= line_start )
    {
        float u = v_localwidth * abs(dx) / v_linewidth;
        d = cap( v_caps.x, u, abs(dy), t);
    }
    // Line stop cap
    else if( dx >= line_stop )
    {
        float u = v_localwidth * (dx-line_stop) / v_linewidth;
        d = cap( v_caps.y, u, abs(dy), t);
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
        else
            gl_FragColor = vec4(color.xyz, a);
    }
}
