const float PI = 3.14159265358979323846264;
const float THETA = 15.0 * 3.14159265358979323846264/180.0;

// Cross product of v1 and v2
float cross(in vec2 v1, in vec2 v2)
{
    return v1.x*v2.y - v1.y*v2.x;
}

// Returns distance of v3 to line v1-v2
float signed_distance(in vec2 v1, in vec2 v2, in vec2 v3)
{
    return cross(v2-v1,v1-v3) / length(v2-v1);
}

// Rotate v around origin
void rotate( in vec2 v, in float alpha, out vec2 result )
{
    float c = cos(alpha);
    float s = sin(alpha);
    result = vec2( c*v.x - s*v.y,
                   s*v.x + c*v.y );
}


// Uniforms
uniform mat4 u_matrix;
uniform mat4 u_view;
uniform mat4 u_proj;

uniform vec4 color;
uniform vec2 translate;
uniform float scale;
uniform float theta;
uniform float linewidth;
uniform float antialias;
uniform vec2 linecaps;
uniform float linejoin;
uniform float miter_limit;
uniform float length;
uniform float dash_phase;
uniform float dash_period;
uniform float dash_index;
uniform vec2 dash_caps;
uniform float closed;


// Attributes
attribute vec2 a_position;
attribute vec4 a_tangents;
attribute vec2 a_segment;
attribute vec2 a_angles;
attribute vec2 a_texcoord;

// Varying
varying vec4  v_color;
varying vec2  v_segment;
varying vec2  v_angles;
varying vec2  v_linecaps;
varying vec2  v_texcoord;
varying vec2  v_miter;
varying float v_miter_limit;
varying float v_length;
varying float v_linejoin;
varying float v_linewidth;
varying float v_antialias;
varying float v_dash_phase;
varying float v_dash_period;
varying float v_dash_index;
varying vec2  v_dash_caps;
varying float v_closed;
void main()
{
    // Extract uniforms from uniform texture
    //float size = u_uniforms_shape.x - 1.0;
    //float index = a_index/(u_uniforms_shape.y-1.0);
    //int i = 0;
    //vec4 _uniform;

    // Get color(4)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    v_color = color;

    // Get translate(2), scale(1), theta(1)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    //vec2  translate = _uniform.xy;
    //float scale     = _uniform.z;
    //float theta     = _uniform.w;

    // Get linewidth(1), antialias(1), linecaps(2)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    v_linewidth = linewidth;
    v_antialias = antialias;
    v_linecaps  = linecaps;

    // Get linejoin(1), miterlimit(1), length(1), dash_phase(1)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    v_linejoin    = linejoin;
    v_miter_limit = miter_limit;
    v_length      = length;
    v_dash_phase  = dash_phase;

    // Get dash_period(1), dash_index(1), dash_caps(2)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    v_dash_period = dash_period;
    v_dash_index  = dash_index;
    v_dash_caps   = dash_caps;

    // Get closed(1)
    //_uniform = texture2D(u_uniforms, vec2(float(i++)/size,index));
    v_closed = closed;
    bool closed = (v_closed > 0.0);


    // Attributes to varyings
    v_angles  = a_angles;
    v_segment = a_segment * scale;
    v_length  = v_length * scale;

    // Thickness below 1 pixel are represented using a 1 pixel thickness
    // and a modified alpha
    v_color.a = min(v_linewidth, v_color.a);
    v_linewidth = max(v_linewidth, 1.0);


    // If color is fully transparent we just will discard the fragment anyway
    if( v_color.a <= 0.0 )
    {
        gl_Position = vec4(0.0,0.0,0.0,1.0);
        return;
    }

    // This is the actual half width of the line
    float w = ceil(1.25*v_antialias+v_linewidth)/2.0;

    vec2 position = a_position*scale;
    vec2 t1 = normalize(a_tangents.xy);
    vec2 t2 = normalize(a_tangents.zw);
    float u = a_texcoord.x;
    float v = a_texcoord.y;
    vec2 o1 = vec2( +t1.y, -t1.x);
    vec2 o2 = vec2( +t2.y, -t2.x);


    // This is a join
    // ----------------------------------------------------------------
    if( t1 != t2 ) {
        float angle  = atan (t1.x*t2.y-t1.y*t2.x, t1.x*t2.x+t1.y*t2.y);
        vec2 t  = normalize(t1+t2);
        vec2 o  = vec2( + t.y, - t.x);

        if ( v_dash_index > 0.0 )
        {
            // Broken angle
            // ----------------------------------------------------------------
            if( (abs(angle) > THETA) ) {
                position += v * w * o / cos(angle/2.0);
                float s = sign(angle);
                if( angle < 0.0 ) {
                    if( u == +1.0 ) {
                        u = v_segment.y + v * w * tan(angle/2.0);
                        if( v == 1.0 ) {
                            position -= 2.0 * w * t1 / sin(angle);
                            u -= 2.0 * w / sin(angle);
                        }
                    } else {
                        u = v_segment.x - v * w * tan(angle/2.0);
                        if( v == 1.0 ) {
                            position += 2.0 * w * t2 / sin(angle);
                            u += 2.0*w / sin(angle);
                        }
                    }
                } else {
                    if( u == +1.0 ) {
                        u = v_segment.y + v * w * tan(angle/2.0);
                        if( v == -1.0 ) {
                            position += 2.0 * w * t1 / sin(angle);
                            u += 2.0 * w / sin(angle);
                        }
                    } else {
                        u = v_segment.x - v * w * tan(angle/2.0);
                        if( v == -1.0 ) {
                            position -= 2.0 * w * t2 / sin(angle);
                            u -= 2.0*w / sin(angle);
                        }
                    }
                }
                // Continuous angle
                // ------------------------------------------------------------
            } else {
                position += v * w * o / cos(angle/2.0);
                if( u == +1.0 ) u = v_segment.y;
                else            u = v_segment.x;
            }
        }

        // Solid line
        // --------------------------------------------------------------------
        else
        {
            position.xy += v * w * o / cos(angle/2.0);
            if( angle < 0.0 ) {
                if( u == +1.0 ) {
                    u = v_segment.y + v * w * tan(angle/2.0);
                } else {
                    u = v_segment.x - v * w * tan(angle/2.0);
                }
            } else {
                if( u == +1.0 ) {
                    u = v_segment.y + v * w * tan(angle/2.0);
                } else {
                    u = v_segment.x - v * w * tan(angle/2.0);
                }
            }
        }

    // This is a line start or end (t1 == t2)
    // ------------------------------------------------------------------------
    } else {
        position += v * w * o1;
        if( u == -1.0 ) {
            u = v_segment.x - w;
            position -=  w * t1;
        } else {
            u = v_segment.y + w;
            position +=  w * t2;
        }
    }

    // Miter distance
    // ------------------------------------------------------------------------
    vec2 t;
    vec2 curr = a_position*scale;
    if( a_texcoord.x < 0.0 ) {
        vec2 next = curr + t2*(v_segment.y-v_segment.x);

        rotate( t1, +a_angles.x/2.0, t);
        v_miter.x = signed_distance(curr, curr+t, position);

        rotate( t2, +a_angles.y/2.0, t);
        v_miter.y = signed_distance(next, next+t, position);
    } else {
        vec2 prev = curr - t1*(v_segment.y-v_segment.x);

        rotate( t1, -a_angles.x/2.0,t);
        v_miter.x = signed_distance(prev, prev+t, position);

        rotate( t2, -a_angles.y/2.0,t);
        v_miter.y = signed_distance(curr, curr+t, position);
    }

    if (!closed && v_segment.x <= 0.0) {
        v_miter.x = 1e10;
    }
    if (!closed && v_segment.y >= v_length)
    {
        v_miter.y = 1e10;
    }

    v_texcoord = vec2( u, v*w );

    // Rotation
    float c = cos(theta);
    float s = sin(theta);
    position.xy = vec2( c*position.x - s*position.y,
                        s*position.x + c*position.y );
    // Translation
    position +=  translate;

    gl_Position = (u_proj*(u_view*u_matrix))*vec4(position,0.0,1.0);
}
