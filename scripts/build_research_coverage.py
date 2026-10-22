"""Keep the research-coverage summary synchronized with the published registry."""
from collections import Counter
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
article = ROOT / 'articles/research-coverage.html'
records = json.loads((ROOT / 'data/experiments.json').read_text(encoding='utf-8'))['records']
families = json.loads((ROOT / 'data/method-families.json').read_text(encoding='utf-8'))['families']
intake = json.loads((ROOT / 'data/reported-attempts.json').read_text(encoding='utf-8'))
screening = json.loads((ROOT / 'data/source-screening.json').read_text(encoding='utf-8'))
screened = len(screening['sources'])
followups = sum(item['disposition'] == 'followup' for item in screening['sources'])
unscreened = len(intake['screening_queue']) - screened
assert unscreened >= 0
counts = Counter(record['record_type']['id'] for record in records)
intake_counts = Counter(entry['status'] for entry in intake['entries'])
assert sum(counts.values()) == len(records)
assert set(counts) == {'method', 'replay', 'measurement', 'control', 'audit', 'alphabet', 'historical'}
unlinked = sum(not family['related'] for family in families)

summary = (f'<p>The research archive currently contains <strong>{len(records)} published reproducible records</strong>: '
           f'{counts["method"]} bounded solving or extraction tests, {counts["replay"]} proposed-method replay, '
           f'{counts["measurement"]} manuscript measurements, {counts["control"]} controls, '
           f'{counts["audit"]} source or input audits, {counts["alphabet"]} alphabet-wide analyses, '
           f'and {counts["historical"]} historical reproduction. '
           f'The <a href="#/wiki/solving-methods">method map</a> has {len(families)} families; '
           f'{unlinked} have no linked completed record. A missing link means <strong>not documented here</strong>, '
           'not “never tried”; a linked record covers only its stated inputs and bounds.</p>\n'
           '<p>Record type matters as much as outcome. The '
           '<a href="#/experiments/lp2-prime-openings">prime-shift test</a> applies a specified rule to unsolved pages. '
           'The <a href="#/experiments/doublet-lag-profile">doublet measurement</a> describes a ciphertext feature. '
           'The <a href="#/experiments/dead-tree-alignment">tree-source audit</a> checks artwork provenance. '
           'Only the first is a bounded attempt to use a candidate solving operation; none is a complete LP2 solve. '
           '<a href="#/experiments">Have we tried it?</a> separates these roles when searching.</p>\n'
           f'<p><strong>What remains in the supplied-source intake:</strong> {intake_counts["not-replayed"]} reported ideas are not replayed, '
           f'{intake_counts["partial"]} are partly replayed, and {intake_counts["related-only"]} have related work but no exact replay. '
           f'Of {len(intake["screening_queue"])} additional supplied source files, {screened} have been screened: '
           f'{followups} retain specific follow-ups, {screened - followups} yielded no further distinct claim in the supplied file, '
           f'and {unscreened} remain unscreened. Screening classifies the supplied extracts; it does not complete their replays. '
           'These groups count reports and files, not additional experiments: equivalent claims can share a test, '
           'while one report may need several fixed variants. The <a href="#/wiki/reported-attempts">source-specific intake</a> '
           'names the exact missing work.</p>')

start = '<!-- research-summary:start -->'
end = '<!-- research-summary:end -->'
source = article.read_text(encoding='utf-8')
assert source.count(start) == source.count(end) == 1
left, rest = source.split(start, 1)
_, right = rest.split(end, 1)
updated = left + start + '\n' + summary + '\n' + end + right
article.write_text(updated, encoding='utf-8', newline='\n')
print(f'Updated research coverage: {len(records)} records, {len(families)} families, {unlinked} without a linked record.')
