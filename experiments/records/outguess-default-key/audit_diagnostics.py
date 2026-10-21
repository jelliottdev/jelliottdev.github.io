"""Audit saved OutGuess diagnostics without running OutGuess or interpreting payloads."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def measure():
    raw = (HERE / 'results/report.json').read_bytes()
    records = json.loads(raw)['records']
    assert len(records) == 77 and len({r['image'] for r in records}) == 77
    rows = []
    for record in records:
        match = re.search(r'Steg retrieve: seed: (\d+), len: (\d+)', record['diagnostic'])
        if match is None:
            raise ValueError('Missing diagnostic header: ' + record['image'])
        seed, length = map(int, match.groups())
        code = record['returncode']
        rows.append({'image': record['image'], 'seed_reported': seed,
                     'length_reported': length, 'returncode': code,
                     'returncode_u32_hex': f'0x{code & 0xffffffff:08X}',
                     'output_bytes': record['bytes'], 'recorded_status': record['status']})
    shared = [r for r in rows if (r['seed_reported'], r['length_reported']) == (41408, 58152)]
    counts = Counter(r['returncode'] for r in shared)
    assert counts == {0: 19, 1: 5, 3221225620: 41}
    assert 3221225620 == int('C0000094', 16)
    return {'schema': 'liberpedia-outguess-diagnostic-audit-v1',
            'report_sha256': hashlib.sha256(raw).hexdigest(),
            'method': 'Parse the saved diagnostic seed/length and cross-tabulate recorded process return codes. No extraction rerun.',
            'shared_header': {'seed': 41408, 'length': 58152, 'records': len(shared),
                              'returncode_counts': {str(k): v for k, v in sorted(counts.items())}},
            'windows_code_reference': 'https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55',
            'windows_code_name': 'STATUS_INTEGER_DIVIDE_BY_ZERO',
            'limits': 'The logs do not locate the failing instruction or establish why headers repeat. Reported length is not validated payload length. No image is shown free of hidden data.',
            'records': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = measure()
    path = HERE / 'results/diagnostic-audit.json'
    if args.write:
        path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    else:
        assert json.loads(path.read_bytes()) == report, 'Diagnostic audit differs'
    print('PASS: all 77 diagnostic headers; shared header split 19/5/41; Windows code conversion')
