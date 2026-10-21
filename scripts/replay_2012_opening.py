"""Inspect the archived 2012 opening JPEG; optionally repeat OutGuess extraction."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'exports/sources/cicada-2012'
sha = lambda b: hashlib.sha256(b).hexdigest()


def audit(executable=None):
    manifest = json.loads((SOURCE/'manifest.json').read_bytes())
    for item in manifest['files']:
        assert sha((SOURCE/item['file']).read_bytes()) == item['sha256'], item['file']
    raw = (SOURCE/'final.jpg').read_bytes()
    assert raw[:2] == b'\xff\xd8'
    pos, width, height = 2, None, None
    while pos < len(raw):
        assert raw[pos] == 255
        marker = raw[pos+1]
        if marker == 0xda:
            break
        size = int.from_bytes(raw[pos+2:pos+4], 'big')
        assert size >= 2
        if marker in (0xc0, 0xc1, 0xc2):
            height = int.from_bytes(raw[pos+5:pos+7], 'big')
            width = int.from_bytes(raw[pos+7:pos+9], 'big')
        pos += 2+size
    end = raw.rfind(b'\xff\xd9')
    assert end >= pos
    tail = raw[end+2:].decode('ascii')
    cipher = re.fullmatch(r'TIBERIVS CLAVDIVS CAESAR says "([^"]+)"\n', tail)[1]
    decoded = ''.join(chr(ord(c)-4) for c in cipher)
    assert decoded == 'http://i.imgur.com/m9sYK.jpg'
    assert ''.join(chr(ord(c)+4) for c in decoded) == cipher
    assert (width, height) == (509, 503)
    primes = [width, height, 3301]
    assert all(n > 1 and all(n % d for d in range(2, int(n**0.5)+1)) for n in primes)
    payload = (SOURCE/'retrieved-payload.bin').read_bytes()
    assert payload == (SOURCE/'archived-payload.txt').read_bytes()
    coordinates = [list(map(int, m)) for m in re.findall(rb'(?m)^(\d+):(\d+)$', payload)]
    assert len(coordinates) == 76 and [x[0] for x in coordinates] == list(range(1,77))
    retrieval = {'performed_this_run': False, 'comparison': 'stored retrieved bytes equal archived payload'}
    if executable:
        executable = Path(executable).resolve()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'payload.bin'
            proc = subprocess.run([str(executable), '-r', str(SOURCE/'final.jpg'), str(output)], capture_output=True, timeout=30)
            assert proc.returncode == 0, proc.stderr
            assert output.read_bytes() == payload
            retrieval = {'performed_this_run': True, 'tool_sha256': sha(executable.read_bytes()),
                         'returncode': proc.returncode, 'output_sha256': sha(output.read_bytes()),
                         'diagnostic': proc.stderr.decode('utf-8').replace(str(SOURCE/'final.jpg'),'final.jpg').replace(str(output),'payload.bin')}
    return {'image_sha256': sha(raw), 'image_bytes': len(raw), 'width': width, 'height': height,
            'jpeg_end_marker_offset_zero_based': end, 'appended_text': tail,
            'shift': -4, 'decoded_historical_url': decoded, 'primes': primes,
            'later_phone_stage_product': width*height*3301,
            'payload_bytes': len(payload), 'payload_sha256': sha(payload),
            'coordinates': coordinates, 'retrieval': retrieval,
            'limits': 'File replay, not proof of original posting date. No historic domain contacted, signatures checked or subsequent book code solved.',
            'script_sha256': sha(Path(__file__).read_bytes())}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--outguess', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args=p.parse_args()
    report=audit(args.outguess)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,indent=2)
        stream.write('\n')
    print('JPEG trailer, dimensions, inverse shift and 76 coordinates checked.')
    print('Fresh extraction matched.' if args.outguess else 'Stored payload comparison only; no extraction run.')
