"""Check both archived cicada carriers; optionally repeat OutGuess extraction."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'exports/sources/countdown-2012'
REPORT = ROOT / 'exports/cicada-2012-countdown.json'
sha = lambda data: hashlib.sha256(data).hexdigest()


def audit(executable=None):
    manifest = json.loads((SOURCE/'manifest.json').read_bytes())
    for entry in manifest['files']:
        assert sha((SOURCE/entry['file']).read_bytes()) == entry['sha256'], entry['file']
    rows = []
    for stage in ('countdown', 'locations'):
        image = (SOURCE/(stage+'.jpg')).read_bytes()
        payload = (SOURCE/(stage+'.retrieved.bin')).read_bytes()
        assert payload == (SOURCE/(stage+'.asc')).read_bytes()
        receipt = next(r for r in manifest['extraction']['receipts'] if r['stage']==stage)
        assert sha(payload) == receipt['extracted_sha256']
        text = payload.decode('ascii')
        body = text.split('\n\n',1)[1].split('-----BEGIN PGP SIGNATURE-----')[0]
        rows.append(dict(stage=stage,image_bytes=len(image),image_sha256=sha(image),
                         payload_bytes=len(payload),payload_sha256=sha(payload),body=body))
        if executable:
            with tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary)/'message.bin'
                proc=subprocess.run([str(Path(executable).resolve()),'-r',str(SOURCE/(stage+'.jpg')),str(output)],capture_output=True,timeout=30)
                assert proc.returncode==0,proc.stderr
                assert output.read_bytes()==payload
    assert rows[0]['image_sha256'] != rows[1]['image_sha256']
    assert '17:00 on Monday, 9 January 2012 UTC' in rows[0]['body']
    coordinates=[]
    for raw in rows[1]['body'].splitlines():
        # OpenPGP cleartext dash escaping adds '- ' before a line beginning '-'.
        unescaped=raw[2:] if raw.startswith('- ') else raw
        if not unescaped.strip() or unescaped.strip()=='3301':
            continue
        match=re.fullmatch(r'\s*(-?\d+\.\d+)\s*,?\s+(-?\d+\.\d+)\s*',unescaped)
        # One preserved coordinate has a comma with no following space.
        if not match:
            match=re.fullmatch(r'\s*(-?\d+\.\d+),(-?\d+\.\d+)\s*',unescaped)
        assert match,repr(raw)
        lat,lon=map(float,match.groups())
        assert -90<=lat<=90 and -180<=lon<=180
        coordinates.append(dict(raw_line=raw,unescaped_line=unescaped,latitude=match[1],longitude=match[2]))
    assert len(coordinates)==12 and coordinates[-1]['latitude']=='-33.90281'
    return dict(carriers=rows,coordinates=coordinates,
                fresh_extraction_this_run=bool(executable),
                extraction_tool_sha256=sha(Path(executable).read_bytes()) if executable else None,
                limits='Stored-byte checks do not run OutGuess unless --outguess is supplied. Cleartext dash unescaping is not signature verification. No domain, coordinate site or phone number was contacted; coordinate count describes this payload only.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outguess',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=audit(args.outguess)
    if args.check:
        saved=json.loads(REPORT.read_bytes())
        for key in ('carriers','coordinates','limits'):
            assert saved[key]==result[key],key
        print('PASS: both carriers, payload hashes, 12 coordinates; fresh extraction:',bool(args.outguess))
    else:
        print(json.dumps(result,indent=2))
