"""Recheck pinned R18-L1 JPEG fingerprints on Liberpedia's hosted LP2 originals."""

import collections
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SOURCE = REPO / 'research/source-intake/vendor/dukotah-r18-l1'
sys.path.insert(0, str(SOURCE))
from jpeg_fingerprint import fingerprint  # noqa: E402

PAGES = [REPO / f'images/lp2-{i:02d}.jpg' for i in range(58)]
SOURCE_SUMMARY = SOURCE / 'pages_summary.json'
PARSER = SOURCE / 'jpeg_fingerprint.py'
RECOVERY = REPO / 'research/source-intake/dukotah-image-input-recovery-2026-10-23.json'
OUT = REPO / 'research/source-intake/r18-jpeg-fingerprint-replay-2026-10-23.json'
vector_fields = ('ncomp', 'subsampling', 'progressive', 'dqt_sha1', 'ijg_q',
                 'dht_class', 'ndht', 'dri', 'apps', 'icc_sha256', 'marker_order', 'jfif')

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PARSER) == '18b33e4dba7822cbcd29eb67a4aa230de8f28ca604179485987552d1f1b9ce64'
assert sha(SOURCE_SUMMARY) == '9a8cc7fb4ccfc4fa3dd23733eb5063714014312e69c1b58dd278b74d62a15268'
source = json.loads(SOURCE_SUMMARY.read_text(encoding='utf-8'))
recovery = json.loads(RECOVERY.read_text(encoding='utf-8'))
expected = {int(r['source_page'][1:-4]): r['source_expected_sha256']
            for r in recovery['lp2_source_images']}
rows = []
classes = collections.OrderedDict()
for page, path in enumerate(PAGES):
    digest = sha(path)
    fp = fingerprint(str(path))
    vector = {key: fp['fingerprint_vector'][key] for key in vector_fields}
    key = json.dumps(vector, sort_keys=True)
    classes.setdefault(key, []).append(page)
    rows.append({'page': page, 'sha256': digest, 'bytes': path.stat().st_size,
                 'source_manifest_exact': digest == expected[page] if page in expected else None,
                 'geometry': fp['fingerprint_vector']['geometry'], 'ncomp': vector['ncomp'],
                 'ijg_quality_candidates': vector['ijg_q'], 'icc_sha256': vector['icc_sha256'],
                 'dht_class': vector['dht_class']})
replay_classes = [{'members': members, 'n': len(members), 'vector': json.loads(key)}
                  for key, members in classes.items()]
assert len(rows) == source['n_files'] == 58
assert replay_classes == source['classes'], 'fingerprint class mismatch'
assert all(row['source_manifest_exact'] for row in rows[:56])
assert source['icc_all_identical'] is True

result = {
    'schema': 'liberpedia-r18-jpeg-fingerprint-audit-v1',
    'source_revision': 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1',
    'source_parser_sha256': sha(PARSER), 'source_summary_sha256': sha(SOURCE_SUMMARY),
    'input_recovery_sha256': sha(RECOVERY),
    'scope': 'Source parser replay on 58 hosted LP2 JPEGs. This verifies metadata classes, not an encoder, document workflow, cipher, or authorship.',
    'source_manifest_byte_matches': sum(row['source_manifest_exact'] is True for row in rows),
    'source_manifest_pages': len(expected),
    'class_partition_exact': True,
    'classes': replay_classes,
    'icc_all_identical': True,
    'icc_description': source['icc']['icc_desc']['text'],
    'rows': rows,
}
encoded = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
if sys.argv[1:] == ['--check']:
    assert OUT.read_text(encoding='utf-8') == encoded, 'Published JPEG fingerprint audit differs'
elif not sys.argv[1:]:
    OUT.write_text(encoded, encoding='utf-8', newline='\n')
else:
    raise SystemExit('Usage: audit-r18-jpeg-fingerprints.py [--check]')
print(json.dumps({'pages': len(rows), 'manifest_byte_matches': result['source_manifest_byte_matches'],
                  'classes': [(x['n'], x['members'][:3]) for x in replay_classes],
                  'source_partition_exact': True, 'icc_all_identical': True}))
