// Antialiasing by simple Gaussian smoothing. Included for comparison.
// Copyright (C) 2013 Almar Klein

uniform sampler2D texture; // The 2D texture
uniform vec2 shape;

void main()
{    
    
    // Get centre location
    vec2 pos = gl_TexCoord[0].xy;
    
    // Init value
    vec4 color1 = vec4(0.0, 0.0, 0.0, 0.0); 
    vec4 color2; // to set color later
    
    // Init kernel and number of steps
    //vec4 kernel = vec4(0.399, 0.242, 0.054, 0.004); // Gaussian sigma 1.0
    vec4 kernel = vec4(0.53, 0.22, 0.015, 0.00018); // Gaussian sigma 0.75
    //vec4 kernel = vec4(0.79, 0.11, 0.0026, 0.000001); // Gaussian sigma 0.5
    int sze = 3; 
    
    // Init step size in tex coords
    float dx = 1.0/shape.x;
    float dy = 1.0/shape.y;
    
    // Convolve
    for (int y=-sze; y<sze+1; y++)
    {
        for (int x=-sze; x<sze+1; x++)
        {   
            float k = kernel[int(abs(float(x)))] * kernel[int(abs(float(y)))];
            vec2 dpos = vec2(float(x)*dx, float(y)*dy);
            color1 += texture2D(texture, pos+dpos) * k;
        }
    }
    gl_FragColor = color1;
    gl_FragColor.a = 1.0;
    
}
