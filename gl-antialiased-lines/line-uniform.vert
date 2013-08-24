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

/* Cross product of v1 and v2 */
float cross(in vec2 v1, in vec2 v2)
{
    return v1.x*v2.y - v1.y*v2.x;
}

/* Computes intersection of line v1-v2 and v3-v4 */
bool intersection(in vec2 v1, in vec2 v2, in vec2 v3, in vec2 v4, out vec2 p)
{
    float num = -cross(v1-v3, v4-v3);
    if( abs(num) < 1e-10)
    {
        p = (v2+v3)/2.0;
        return true;
    }
    float den = cross(v2-v1, v4-v3);
    if( abs(den) < 1e-10 )
    {
        return false;
    }
    p = v1+(num/den)*(v2-v1);
    return true;
}

/* Returns the coordinate of the projection of v3 onto line segment v1-v2
   0 <= u <= 1 if v3 projects itself within segment */
float projection(in vec2 v1, in vec2 v2, in vec2 v3)
{
    return dot(v3-v1,v2-v1) / dot(v2-v1,v2-v1);
}

/* Returns distance of v3 to line v1-v2 */
float signed_distance(in vec2 v1, in vec2 v2, in vec2 v3)
{
    return cross(v2-v1,v1-v3) / length(v2-v1);
}

/* Compute the join betwen v0-v1 and v1-v2 according to vertex id vid */
void calc_join(in vec2 v0, in vec2 v1, in vec2 v2, in float width, in float vid,
               out vec2 pos, out vec2 dist, out float length)
{
    float len1 = length(v1-v0);
    float len2 = length(v2-v1);
    vec2 t1, t2, n1, n2;

    if( len1 != 0.0 ) {
        t1 = (v1-v0)/len1;
        n1 = vec2(-t1.y, t1.x) * width;
    }
    if( len2 != 0.0 ) {
        t2 = (v2-v1)/len2;
        n2 = vec2(-t2.y, t2.x) * width;
    }

    // v0 != v1 & v != v2
    // Colinear case will be handled by intersection
    // ------------------------------------------------------------------------
    if( (len1 > 0.0) && (len2 > 0.0) ) {
        if (vid == 0.0) {
            intersection(v0+n1, v1+n1, v1+n2, v2+n2, pos);
            float u = projection( v1, v2, pos );
            dist = vec2( u*len2, +width );
            length = len2;
        } else if( vid == 1.0 ) {
            intersection(v0-n1, v1-n1, v1-n2, v2-n2, pos);
            float u = projection( v1, v2, pos );
            dist = vec2( u*len2, -width );
            length = len2;
        } else if( vid == 2.0 ) {
            intersection(v0-n1, v1-n1, v1-n2, v2-n2, pos);
            float u = projection( v0, v1, pos );
            dist = vec2( u*len1, -width );
            length = len1;
        } else if( vid == 3.0 ) {
            intersection(v0+n1, v1+n1, v1+n2, v2+n2, pos);
            float u = projection( v0, v1, pos );
            dist = vec2( u*len1, +width );
            length = len1;
        }
    // v0 == v1 (line start)
    // ------------------------------------------------------------------------
    } else if( len1 == 0.0 ) {
        if (vid == 0.0) {
            pos  = v1 + n2;
            dist = vec2( 0.0, +width);
            length = len2;
        } else if( vid == 1.0 ) {
            pos  = v1 - n2;
            dist = vec2( 0.0, -width );
            length = len2;
        } else if( vid == 2.0 ) {
            pos  = v1 + n2;
            dist = vec2( len2, +width );
            length = len1;
        } else if( vid == 3.0 ) {
            pos  = v1 - n2;
            dist = vec2( len2, -width );
            length = len1;
        }
    // v1 == v2 (line end)
    // ------------------------------------------------------------------------
    } else if( len2 == 0.0 ) {
        if (vid == 0.0) {
            pos  = v1 - n1;
            dist = vec2( 0.0, -width );
            length = len2;
        } else if( vid == 1.0 ) {
            pos  = v1 + n1;
            dist = vec2( 0.0, +width );
            length = len2;
        } else if( vid == 2.0 ) {
            pos  = v1 - n1;
            dist = vec2( len1, -width );
            length = len1;
        } else if( vid == 3.0 ) {
            pos  = v1 + n1;
            dist = vec2( len1, +width );
            length = len1;
        }
    // v0 == v1 == v2
    // ------------------------------------------------------------------------
    } else {
        pos = v1;
        dist = vec2( 0.0 );
        length = 0.0;
    }
}


/* Compute the miter distance */
void calc_miter(in vec2 prev2, in vec2 prev, // previous vertices (-2,-1)
                in vec2 curr,                // current vertex (0)
                in vec2 next, in vec2 next2, // following vertices (+1,+2)
                in vec2 position,            // actual position (after calc_join)
                in float vid, out vec2 miter)
{
    vec2 t, t1, t2, t3;
    float len1, len2, len3;
    miter = vec2(0.0);

    // ------------------------------------------------------------------------
    if( vid < 2.0 ) {
        t1 = normalize(curr - prev);
        t2 = normalize(next - curr);
        t3 = normalize(next2 - next);
        t = normalize(t1+t2);
        miter.x = signed_distance(curr, curr+t, position);
        t = normalize(t2+t3);
        miter.y = signed_distance(next, next+t, position);
    // ------------------------------------------------------------------------
    } else {
        t1 = normalize(prev - prev2);
        t2 = normalize(curr - prev);
        t3 = normalize(next - curr);
        t = normalize(t1+t2);
        miter.x = signed_distance(prev, prev+t, position);
        t = normalize(t2+t3);
        miter.y = signed_distance(curr, curr+t, position);
    }
}


// M : Model matrix, V : View matrix, P : Projection matrix, N : Normal matrix
// ----------------------------------------------------------------------------
uniform mat4 M, V, P, N;
uniform float width;
uniform float blur;
uniform vec4  color;
uniform float miter_limit;

attribute vec2 prev2;  // previous-previous vertex (-2)
attribute vec2 prev;   // previous vertex          (-1)
attribute vec2 curr;   // current vertex           ( 0)
attribute vec2 next;   // next vertex              (+1)
attribute vec2 next2;  // next-next vertex         (+2)
attribute float vid;   // vertex id (0,1,2 or 3)

varying vec2 dist;     
varying vec2 miter;
varying float length;

void main()
{
    vec2 position;
    float w = ceil(2.5*blur+width)/2.0;

    // Compute actual vertex position
    calc_join(prev, curr, next, w, vid, position, dist, length);

    // Compute distance to miter join
    calc_miter(prev2, prev, curr, next, next2, position, vid, miter);
   
    gl_Position = (P*(V*M))*vec4(position,0.0,1.0);
}
