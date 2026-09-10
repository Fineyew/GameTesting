shader_type spatial;
render_mode diffuse_burley, specular_disabled;
uniform vec4 ground_color : source_color = vec4(0.44,0.60,0.51,1.0);
varying vec2 ground_position;
float grain(vec2 p) {
    vec2 cell = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a = fract(sin(dot(cell,vec2(127.1,311.7)))*43758.5453);
    float b = fract(sin(dot(cell+vec2(1,0),vec2(127.1,311.7)))*43758.5453);
    float c = fract(sin(dot(cell+vec2(0,1),vec2(127.1,311.7)))*43758.5453);
    float d = fract(sin(dot(cell+vec2(1,1),vec2(127.1,311.7)))*43758.5453);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
void vertex() { ground_position = (MODEL_MATRIX*vec4(VERTEX,1.0)).xz; }
void fragment() {
    // Two low-frequency washes keep a readable surface without texture memory.
    float wash = grain(ground_position*.65)*.17 + grain(ground_position*3.0)*.045;
    ALBEDO = ground_color.rgb*(.80+wash);
    ROUGHNESS = 1.0;
}
