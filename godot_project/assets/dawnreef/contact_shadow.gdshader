shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never;
void fragment() {
    ALBEDO = vec3(.06,.075,.065);
    ALPHA = (1.0-smoothstep(.08,.5,length(UV-vec2(.5))))*.24;
}
