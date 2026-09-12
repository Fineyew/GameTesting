shader_type spatial;
render_mode diffuse_burley, specular_disabled;
uniform vec4 ground_color : source_color = vec4(0.44,0.60,0.51,1.0);
uniform vec4 path_color : source_color = vec4(.83,.76,.58,1.0);
uniform vec4 rise_bounds = vec4(0.0);
uniform bool rise_enabled = false;
varying vec2 ground_position;
varying float ground_up;
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
void vertex() { ground_position = (MODEL_MATRIX*vec4(VERTEX,1.0)).xz; ground_up = abs((MODEL_NORMAL_MATRIX*NORMAL).y); }
void fragment() {
    // Two low-frequency washes keep a readable surface without texture memory.
    float broad = grain(ground_position*.65);
    float wash = broad*.17 + grain(ground_position*3.0)*.045;
    float verge = (broad-.5)*.28;
    float north_path = 1.0-smoothstep(2.08,2.48,abs(ground_position.x)+verge);
    float west_path = 1.0-smoothstep(1.33,1.73,abs(ground_position.y+4.0)+verge);
    float well_plaza = 1.0-smoothstep(2.5,3.05,length(ground_position-vec2(0,-5))+verge);
    float rise_path = 0.0;
    if (rise_enabled) {
        vec2 edge = min(ground_position-rise_bounds.xy,rise_bounds.zw-ground_position);
        rise_path = smoothstep(.15,.65,min(edge.x,edge.y));
    }
    vec3 top_color = mix(ground_color.rgb,path_color.rgb,max(rise_path,max(well_plaza,max(north_path,west_path))));
    ALBEDO = mix(vec3(.56,.53,.44),top_color,smoothstep(.1,.8,ground_up))*(.80+wash);
    ROUGHNESS = 1.0;
}
