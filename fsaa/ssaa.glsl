// Super sampling antialiasing. Provides diffusion with a kernel that
// is passed as a uniform. You probably want it to be a Lanczos kernel!
// Copyright (C) 2013 Almar Klein

// Uniforms obtained from OpenGL
uniform sampler2D texture; // The 2D texture
uniform vec2 shape; // And its shape (as in OpenGl)
uniform vec4 aakernel; // The smoothing kernel for anti-aliasing


void main()
{    
    // Get centre location
    vec2 pos = gl_TexCoord[0].xy;
    
    // Init value
    vec4 color1 = vec4(0.0, 0.0, 0.0, 0.0); 
    
    // Init kernel and number of steps
    vec4 kernel = aakernel;
    
    // Init step size in tex coords
    float dx = 1.0/shape.x;
    float dy = 1.0/shape.y;
    
    // Convolve
    int sze = 3;
    for (int y=-sze; y<sze+1; y++)
    {
        for (int x=-sze; x<sze+1; x++)
        {   
            float k = kernel[int(abs(float(x)))] * kernel[int(abs(float(y)))];
            vec2 dpos = vec2(float(x)*dx, float(y)*dy);
            color1 += texture2D(texture, pos+dpos) * k;
        }
    }
    
    // Determine final color
    gl_FragColor = color1;
    gl_FragColor.a = 1.0;
    
}
