# Veilbound Tides — first Fal asset evaluation

These are experimental generated assets, not approved or integrated game content. No repository, gameplay, backend, deployment or APK changes were made.

## Generation
One Tripo H3.1 standard textured text-to-3D lantern and two ElevenLabs V2 sounds. Estimated generation cost $0.246; this is not a verified billing receipt. Exact prompts, settings and request IDs are in generation-record.json. No paid regeneration was requested.

## Audio checks
Both MP3 files decode at 44.1 kHz stereo, exactly 3 and 20 seconds of decoded samples. The spell source has 7 floating-point samples at or above full scale (maximum 1.0905); a separate WAV with 3 dB attenuation preserves headroom. Original files are retained. Ambience has no full-scale samples; waveform endpoint continuity alone does not prove a perceptually seamless loop. Listening quality, loop quality, speaker mix and Android integration are not yet verified. No claim is made that either sound contains every requested element.

## Acceptance still required
Visual and audio art-direction review, source/license records before shipping, scale/material/collision/LOD cleanup as needed, Godot import, on-device memory and draw-call measurements, and in-game listening. Generated output is source material, not automatically a final production asset.

## Lantern result
Preview shows a readable handcrafted wood-and-brass lantern, turquoise core and orange bindings. It is taller and slimmer than the squat silhouette requested. GLB header validates: 2,421 triangles, 1,883 vertices, one mesh primitive/material, 658,944 bytes. Three embedded 2048x2048 textures are excessive for this small mobile prop; a later import pass should evaluate 512/1024px textures and material simplification. Material has no emissive property; the turquoise core is not yet an actual glowing light. Raw mesh bounds are 1 unit tall; scene transform, Godot size and pivot still need validation. No runtime render or physical-device test performed.

## Recommendation
Promising as art source for a narrow Dawnreef visual pass. Review in the actual scene before ordering a batch. Preserve originals, create optimized derivatives, implement glow through the existing material/lighting architecture, and measure the result on Android. Do not treat the supplier preview as in-game evidence.
