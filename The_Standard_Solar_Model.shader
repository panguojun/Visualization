/*
 * Physically Accurate Solar Model Visualization
 * Renders the Sun's interior with correct temperature layers
 * Uses blackbody radiation for accurate color representation
 */

// Physical constants
#define kB 1.380649e-23        // Boltzmann constant (J/K)
#define h 6.62607015e-34       // Planck constant (J·s)
#define c 299792458.0           // Speed of light (m/s)
#define sigma 5.670374419e-8    // Stefan-Boltzmann constant (W/m²K⁴)
#define G 6.67430e-11           // Gravitational constant (m³/kg/s²)
#define M_sun 1.989e30          // Solar mass (kg)
#define R_sun 6.957e8           // Solar radius (m)
#define m_p 1.6726219e-27       // Proton mass (kg)

// Solar structure parameters
#define CORE_RADIUS 0.25        // Fractional radius of core
#define RADIATIVE_ZONE 0.7       // End of radiative zone
#define CONVECTION_ZONE 0.98     // End of convection zone

// Temperature profile function (returns temperature in Kelvin)
float solarTemperature(float r) {
    r *= R_sun; // Convert to physical radius
    
    // Core (0-0.25R☉) - polynomial fit to standard solar model
    if (r < 0.25*R_sun) {
        float x = r/(0.25*R_sun);
        return 15.7e6 * (1.0 - 0.72*x*x + 0.18*x*x*x*x);
    }
    // Radiative zone (0.25-0.7R☉)
    else if (r < 0.7*R_sun) {
        float T0 = 7.2e6;
        float alpha = 0.9;
        return T0 * pow(0.25*R_sun/r, alpha);
    }
    // Convective zone (0.7-0.98R☉)
    else if (r < 0.98*R_sun) {
        return mix(2.0e6, 1.8e4, (r-0.7*R_sun)/(0.28*R_sun));
    }
    // Photosphere (surface)
    else {
        return 5778.0; // Effective temperature
    }
}

// Blackbody radiation spectrum (approximate)
vec3 blackbodyColor(float T) {
    // Normalized temperature
    float t = T/10000.0;
    
    // Red channel
    float r = 1.0;
    if (T > 6500.0) {
        r = 0.85 + 0.15 * (9000.0-T)/2500.0;
    } else {
        r = 1.0;
    }
    
    // Green channel
    float g = 0.0;
    if (T < 4000.0) {
        g = 0.4 + 0.6 * T/4000.0;
    } else if (T < 7000.0) {
        g = 1.0;
    } else if (T < 20000.0) {
        g = 1.0 - 0.3 * (T-7000.0)/13000.0;
    } else {
        g = 0.7;
    }
    
    // Blue channel
    float b = 0.0;
    if (T < 2000.0) {
        b = 0.0;
    } else if (T < 4000.0) {
        b = 0.3 * (T-2000.0)/2000.0;
    } else if (T < 12000.0) {
        b = 0.3 + 0.7 * (T-4000.0)/8000.0;
    } else {
        b = 1.0;
    }
    
    // Intensity scaling (Stefan-Boltzmann law)
    float intensity = pow(T/5778.0, 4.0);
    
    // Combine and normalize
    vec3 color = vec3(r, g, b) * intensity;
    return normalize(color) * min(1.0, intensity);
}

// Main rendering function
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalized pixel coordinates (0 to 1) with aspect ratio correction
    vec2 uv = (2.0*fragCoord.xy - iResolution.xy) / min(iResolution.x, iResolution.y);
    float r = length(uv);
    
    // Only render within solar radius
    if (r > 1.0) {
        fragColor = vec4(0.0);
        return;
    }
    
    // Calculate temperature at this radius
    float T = solarTemperature(r);
    
    // Get blackbody color
    vec3 color = blackbodyColor(T);
    
    // Enhance core visibility with extra glow
    if (r < CORE_RADIUS) {
        float coreGlow = smoothstep(0.0, CORE_RADIUS, r);
        color = mix(vec3(1.0, 0.7, 0.3), color, coreGlow);
        color *= 1.0 + 2.0 * (1.0-coreGlow);
    }
    
    // Add radiative/convective zone boundary effect
    if (abs(r - RADIATIVE_ZONE) < 0.02) {
        color = mix(color, vec3(0.9, 0.9, 1.0), 0.7);
    }
    
    // Add granulation pattern in outer layers
    if (r > 0.7) {
        vec2 seed = uv*100.0 + vec2(iTime*0.1);
        float noise = fract(sin(dot(seed, vec2(12.9898, 78.233)))) * 0.15;
        color += noise * vec3(1.0, 0.9, 0.8);
    }
    
    // Add corona effect at edge
    if (r > 0.95) {
        float corona = smoothstep(0.95, 1.0, r);
        color = mix(color, vec3(1.0, 0.9, 0.5), corona * 0.8);
    }
    
    // Gamma correction
    color = pow(color, vec3(1.0/2.2));
    
    fragColor = vec4(color, 1.0);
}
