// Directionally localized antialiasing.
// See http://blenderartists.org/forum/showthread.php?209574-Full-Screen-Anti-Aliasing-(NFAA-DLAA-SSAA)
// Copyright Martinsh


uniform sampler2D texture;
uniform vec2 shape;

float width = shape.x; //texture width
float height = shape.y; //texture height

vec2 texCoord = gl_TexCoord[0].st;

#define PIXEL_SIZE vec2(1.0/width, 1.0/height)

vec4 sampleOffseted(const in sampler2D tex, const in vec2 texCoord, const vec2 pixelOffset )
{
   return texture2D(tex, texCoord + pixelOffset * PIXEL_SIZE);
}

vec3 avg(const in vec3 value)
{
   static const float oneThird = 1.0 / 3.0;
   return dot(value.xyz, vec3(oneThird, oneThird, oneThird) );
}


vec4 firsPassEdgeDetect( vec2 texCoord )
{
   vec4 sCenter    = sampleOffseted(texture, texCoord, vec2( 0.0,  0.0) );
   vec4 sUpLeft    = sampleOffseted(texture, texCoord, vec2(-0.5, -0.5) );
   vec4 sUpRight   = sampleOffseted(texture, texCoord, vec2( 0.5, -0.5) );
   vec4 sDownLeft  = sampleOffseted(texture, texCoord, vec2(-0.5,  0.5) );
   vec4 sDownRight = sampleOffseted(texture, texCoord, vec2( 0.5,  0.5) );
 
   vec4 diff          = abs( ((sUpLeft + sUpRight + sDownLeft + sDownRight) * 4.0) - (sCenter * 16.0) );
   float edgeMask       = avg(diff.xyz);

   return vec4(sCenter.rgb, edgeMask);
}


void	main()
{
        // short edges
        vec4 sampleCenter     = sampleOffseted(texture, texCoord.xy, vec2( 0.0,  0.0) );   
        vec4 sampleHorizNeg0   = sampleOffseted(texture, texCoord.xy, vec2(-1.5,  0.0) );
        vec4 sampleHorizPos0   = sampleOffseted(texture, texCoord.xy, vec2( 1.5,  0.0) ); 
        vec4 sampleVertNeg0   = sampleOffseted(texture, texCoord.xy, vec2( 0.0, -1.5) ); 
        vec4 sampleVertPos0   = sampleOffseted(texture, texCoord.xy, vec2( 0.0,  1.5) );

        vec4 sumHoriz         = sampleHorizNeg0 + sampleHorizPos0;
        vec4 sumVert          = sampleVertNeg0  + sampleVertPos0;

        vec4 diffToCenterHoriz = abs( sumHoriz - (2.0 * sampleCenter) ) / 2.0;  
        vec4 diffToCenterVert  = abs( sumHoriz - (2.0 * sampleCenter) ) / 2.0;

        float valueEdgeHoriz    = avg( diffToCenterHoriz.xyz );
        float valueEdgeVert     = avg( diffToCenterVert.xyz );
        
        float edgeDetectHoriz   = clamp( (3.0 * valueEdgeHoriz) - 0.1,0.0,1.0);
        float edgeDetectVert    = clamp( (3.0 * valueEdgeVert)  - 0.1,0.0,1.0);

        vec4 avgHoriz         	= ( sumHoriz + sampleCenter) / 3.0;
        vec4 avgVert            = ( sumVert  + sampleCenter) / 3.0;

        float valueHoriz        = avg( avgHoriz.xyz );
        float valueVert         = avg( avgVert.xyz );

        float blurAmountHoriz   = clamp( edgeDetectHoriz / valueHoriz ,0.0,1.0);
        float blurAmountVert    = clamp( edgeDetectVert  / valueVert ,0.0,1.0);

        vec4 aaResult         	= mix( sampleCenter,  avgHoriz, blurAmountHoriz );
        aaResult                = mix( aaResult,       avgVert,  blurAmountVert );
  
        // long edges
        vec4 sampleVertNeg1   = sampleOffseted(texture, texCoord.xy, vec2(0.0, -3.5) ); 
        vec4 sampleVertNeg2   = sampleOffseted(texture, texCoord.xy, vec2(0.0, -7.5) );
        vec4 sampleVertPos1   = sampleOffseted(texture, texCoord.xy, vec2(0.0,  3.5) ); 
        vec4 sampleVertPos2   = sampleOffseted(texture, texCoord.xy, vec2(0.0,  7.5) ); 

        vec4 sampleHorizNeg1   = sampleOffseted(texture, texCoord.xy, vec2(-3.5, 0.0) ); 
        vec4 sampleHorizNeg2   = sampleOffseted(texture, texCoord.xy, vec2(-7.5, 0.0) );
        vec4 sampleHorizPos1   = sampleOffseted(texture, texCoord.xy, vec2( 3.5, 0.0) ); 
        vec4 sampleHorizPos2   = sampleOffseted(texture, texCoord.xy, vec2( 7.5, 0.0) ); 

        float pass1EdgeAvgHoriz  = ( sampleHorizNeg2.a + sampleHorizNeg1.a + sampleCenter.a + sampleHorizPos1.a + sampleHorizPos2.a ) / 5.0;
        float pass1EdgeAvgVert   = ( sampleVertNeg2.a  + sampleVertNeg1.a  + sampleCenter.a + sampleVertPos1.a  + sampleVertPos2.a  ) / 5.0;
        pass1EdgeAvgHoriz        = clamp( pass1EdgeAvgHoriz * 2.0 - 1.0 ,0.0,1.0);
        pass1EdgeAvgVert         = clamp( pass1EdgeAvgVert  * 2.0 - 1.0 ,0.0,1.0);
        float longEdge           = max( pass1EdgeAvgHoriz, pass1EdgeAvgVert);

        if ( longEdge > 1.0 )
        {
        vec4 avgHorizLong  		= ( sampleHorizNeg2 + sampleHorizNeg1 + sampleCenter + sampleHorizPos1 + sampleHorizPos2 ) / 5.0;
        vec4 avgVertLong   		= ( sampleVertNeg2  + sampleVertNeg1  + sampleCenter + sampleVertPos1  + sampleVertPos2  ) / 5.0;
        float valueHorizLong   	= avg(avgHorizLong.xyz);
        float valueVertLong     = avg(avgVertLong.xyz);

        vec4 sampleLeft       = sampleOffseted(texture, texCoord.xy, vec2(-1.0,  0.0) );
        vec4 sampleRight   	  = sampleOffseted(texture, texCoord.xy, vec2( 1.0,  0.0) );
        vec4 sampleUp         = sampleOffseted(texture, texCoord.xy, vec2( 0.0, -1.0) );
        vec4 sampleDown       = sampleOffseted(texture, texCoord.xy, vec2( 0.0,  1.0) );

        float valueCenter       = avg(sampleCenter.xyz);
        float valueLeft         = avg(sampleLeft.xyz);
        float valueRight        = avg(sampleRight.xyz);
        float valueTop          = avg(sampleUp.xyz);
        float valueBottom       = avg(sampleDown.xyz);

        vec4 diffToCenter  		= valueCenter - vec4(valueLeft, valueTop, valueRight, valueBottom);      
        float blurAmountLeft 	= clamp( 0.0 + ( valueVertLong  - valueLeft   ) / diffToCenter.x ,0.0,1.0);
        float blurAmountUp   	= clamp( 0.0 + ( valueHorizLong - valueTop      ) / diffToCenter.y ,0.0,1.0);
        float blurAmountRight	= clamp( 1.0 + ( valueVertLong  - valueCenter ) / diffToCenter.z ,0.0,1.0);
        float blurAmountDown 	= clamp( 1.0 + ( valueHorizLong - valueCenter ) / diffToCenter.w ,0.0,1.0);     

        vec4 blurAmounts   		= vec4( blurAmountLeft, blurAmountRight, blurAmountUp, blurAmountDown );
        blurAmounts             = (blurAmounts == vec4(0.0, 0.0, 0.0, 0.0)) ? vec4(1.0, 1.0, 1.0, 1.0) : blurAmounts;

        vec4 longBlurHoriz 		= mix( sampleLeft,  sampleCenter,  blurAmounts.x );
        longBlurHoriz           = mix( sampleRight, longBlurHoriz, blurAmounts.y );
        vec4 longBlurVert  		= mix( sampleUp,  sampleCenter,  blurAmounts.z );
        longBlurVert            = mix( sampleDown,  longBlurVert,  blurAmounts.w );

        aaResult                = mix( aaResult,       longBlurHoriz, pass1EdgeAvgVert);
        aaResult                = mix( aaResult,       longBlurVert,  pass1EdgeAvgHoriz);
   }

   gl_FragColor = vec4(aaResult.rgb, 1.0);
    //gl_FragColor = firsPassEdgeDetect( texCoord );
}
