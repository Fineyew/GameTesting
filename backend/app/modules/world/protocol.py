"""Protocol2 binds the client to immutable, millimetre-normalized geometry."""
import hashlib
import json

PROTOCOL = 2


def geometry_digest(geometry):
    def normalized(value):
        if isinstance(value, dict):
            return {k:normalized(v) for k,v in value.items()}
        if isinstance(value, list):
            return [normalized(v) for v in value]
        if type(value) in (int,float):
            return round(value*1000)
        return value
    return hashlib.sha256(json.dumps(normalized(geometry),sort_keys=True,separators=(",",":")).encode()).hexdigest()
