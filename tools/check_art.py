"""Validate the small authored glTF kit and mobile geometry/import contract, without Blender."""
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def check():
    manifest = json.loads((ROOT / 'art_sources/dawnreef/manifest.json').read_text())
    total_bytes = 0
    for asset in manifest['assets']:
        path = ROOT / 'godot_project/assets/dawnreef' / asset['file']
        data = path.read_bytes()
        assert struct.unpack_from('<III',data) == (0x46546c67,2,len(data)), path
        length,kind = struct.unpack_from('<II',data,12)
        assert kind == 0x4e4f534a
        document = json.loads(data[20:20+length])
        assert not document.get('images'), 'Benchmark uses vertex colors, not hidden texture costs'
        assert all('uri' not in buffer for buffer in document['buffers']), 'GLB must be self-contained'
        triangles = 0
        for mesh in document['meshes']:
            for primitive in mesh['primitives']:
                assert primitive.get('mode',4) == 4, 'Only triangle geometry is budgeted'
                assert {'POSITION','NORMAL','COLOR_0'} <= primitive['attributes'].keys()
                count = document['accessors'][primitive['indices']]['count']
                assert count % 3 == 0
                triangles += count//3
        assert triangles <= asset['max_triangles'], (path,triangles)
        assert len(document['materials']) <= asset['max_materials'], path
        assert set(asset.get('nodes',[])) <= {n.get('name') for n in document['nodes']}
        if asset.get('bones'):
            assert len(document['skins']) == 1
            assert len(document['skins'][0]['joints']) == asset['bones']
            assert set(asset['animations']) == {a['name'] for a in document['animations']}
            assert all(a['channels'] and a['samplers'] for a in document['animations'])
        assert (ROOT/asset['source']).is_file() and (ROOT/asset['recipe']).is_file()
        assert 'meshes/generate_lods=true' in Path(str(path)+'.import').read_text()
        total_bytes += len(data)
        print(f"{path.name}: {triangles} triangles, {len(document['materials'])} materials, {len(data)} bytes")
    assert total_bytes < 5*1024*1024, 'Benchmark GLBs exceed the 5 MiB source-export allowance'
    print('ART_CATALOG_PASS')


if __name__ == '__main__':
    check()
