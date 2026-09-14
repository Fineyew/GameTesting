"""Shared validation for the versioned single-floor geometry descriptor."""
import re


def _integer(value, limit):
    return type(value) in (int, float) and abs(value) <= limit and value == int(value)


def validate_surface(definition):
    if not isinstance(definition, dict) or set(definition) != {"bounds", "cells"}:
        raise ValueError("terrain requires only bounds and cells")
    bounds, cells = definition["bounds"], definition["cells"]
    if not isinstance(bounds, list) or len(bounds) != 4 or any(
        not _integer(v, 4096) for v in bounds
    ):
        raise ValueError("terrain bounds must be four bounded integers")
    bounds = [int(v) for v in bounds]

    width, depth = bounds[2] - bounds[0], bounds[3] - bounds[1]
    if not (1 <= width <= 128 and 1 <= depth <= 128):
        raise ValueError("terrain extent must be 1..128 metres per axis")
    if not isinstance(cells, dict) or len(cells) > width * depth:
        raise ValueError("invalid terrain cell map")
    normalized = {}
    for key, heights in cells.items():
        if not isinstance(key, str) or not re.fullmatch(r"(0|[1-9][0-9]*):(0|[1-9][0-9]*)", key):
            raise ValueError("noncanonical terrain cell key")
        x, z = map(int, key.split(":"))
        if x >= width or z >= depth:
            raise ValueError("terrain cell outside bounds")
        if not isinstance(heights, list) or len(heights) != 4 or any(
            not _integer(v, 8000) for v in heights
        ):
            raise ValueError("terrain corners must be four integer millimetres within +/-8000")
        normalized[(x, z)] = tuple(v / 1000 for v in heights)
    return tuple(bounds), normalized
