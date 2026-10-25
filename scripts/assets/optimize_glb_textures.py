"""Derive web GLBs with bounded textures; retain source assets and geometry.

Requires the existing Pillow installation. Run from the repository root.
"""
import io
import json
from pathlib import Path
import struct
from PIL import Image


def optimize(source: Path, target: Path, size=1024):
    data = source.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert magic == 0x46546C67 and version == 2 and length == len(data)
    json_size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    document = json.loads(data[20:20 + json_size])
    offset = 20 + json_size
    bin_size, kind = struct.unpack_from('<II', data, offset)
    assert kind == 0x004E4942
    binary = data[offset + 8:offset + 8 + bin_size]
    images = {im['bufferView']: im for im in document.get('images', [])}
    rebuilt = bytearray()
    old_pixels = new_pixels = 0
    for index, view in enumerate(document.get('bufferViews', [])):
        assert view.get('buffer', 0) == 0
        start = view.get('byteOffset', 0)
        payload = binary[start:start + view['byteLength']]
        if index in images:
            with Image.open(io.BytesIO(payload)) as original:
                old_pixels += original.width * original.height
                image = original.copy()
                image.thumbnail((size, size), Image.Resampling.LANCZOS)
                new_pixels += image.width * image.height
                output = io.BytesIO()
                # Preserve color/normal/metallic channel conventions and alpha.
                fmt = 'PNG' if images[index].get('mimeType') == 'image/png' else 'JPEG'
                image.save(output, format=fmt, **({'quality': 88} if fmt == 'JPEG' else {}))
                payload = output.getvalue()
        rebuilt.extend(b'\0' * (-len(rebuilt) % 4))
        view['byteOffset'] = len(rebuilt)
        view['byteLength'] = len(payload)
        rebuilt.extend(payload)
    document['buffers'][0]['byteLength'] = len(rebuilt)
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    rebuilt.extend(b'\0' * (-len(rebuilt) % 4))
    result = (struct.pack('<III', magic, version, 12 + 8 + len(encoded) + 8 + len(rebuilt))
              + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
              + struct.pack('<II', len(rebuilt), 0x004E4942) + rebuilt)
    # All non-image views must still contain precisely the source geometry bytes.
    original_doc = json.loads(data[20:20 + json_size])
    for i, (old, new) in enumerate(zip(original_doc.get('bufferViews', []), document.get('bufferViews', []))):
        if i not in images:
            start = old.get('byteOffset', 0)
            assert binary[start:start + old['byteLength']] == rebuilt[new['byteOffset']:new['byteOffset'] + new['byteLength']]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    return {'file': str(source), 'original_bytes': len(data), 'web_bytes': len(result),
            'original_rgba_bytes': old_pixels * 4, 'web_rgba_bytes': new_pixels * 4,
            'geometry_unchanged': True}


if __name__ == '__main__':
    root = Path('frontend/public/models')
    reports = [optimize(p, root / 'optimized' / p.relative_to(root))
               for folder in ('mesas', 'instrumentos') for p in sorted((root / folder).glob('*.glb'))]
    Path('/tmp/insoft-web-models.json').write_text(json.dumps(reports, indent=2) + '\n')
    print(json.dumps({'models': len(reports), 'original_bytes': sum(r['original_bytes'] for r in reports),
                      'web_bytes': sum(r['web_bytes'] for r in reports), 'geometry_unchanged': True}))
