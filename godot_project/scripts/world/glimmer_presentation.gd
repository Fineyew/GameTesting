class_name GlimmerPresentation
extends TidebeatEffect
## Stable benchmark entry point backed by the shared bounded spell renderer.
const DURATION = 1.15

func begin(from: Vector3, to: Vector3) -> void:
    configure("glimmer_spark",from,to)
