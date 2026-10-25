"""Compile explicitly declared archived counts into reproducible browser receipts.

This verifies a fixed published measurement; it does not rerun the exploratory
shuffle search, alter its findings, or create a community task/submission.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'word-internal-affine-lags'
BASE = f'experiments/records/{RECORD}'
PAGES = [f'lp2-{i:02d}' for i in range(56)]
CRITERION = {'kind': 'word-affine-count', 'lag': 6, 'a': 27, 'b': 24, 'boundaries': 'hyphen-period'}
REQUIRED = [f'text/{page}.txt' for page in PAGES] + ['data/index.json', f'{BASE}/results.json', f'{BASE}/run.py', f'{BASE}/check.py']


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def measure(text, alphabet):
    """Independent Python count and exact finite-word permutation expectation."""
    lookup = {row['rune']: i for i, row in enumerate(alphabet)}
    matches = opportunities = 0
    expected = Fraction(0)
    for segment in re.split(r'[-.]', text):
        word = [lookup[c] for c in segment if c in lookup]
        n = len(word)
        if n <= 6:
            continue
        opportunities += n - 6
        matches += sum(word[i + 6] == (24 - 2 * word[i]) % 29 for i in range(n - 6))
        counts = Counter(word)
        possible = sum(counts[c] * (counts[(24 - 2 * c) % 29] - int((24 - 2 * c) % 29 == c)) for c in range(29))
        expected += Fraction((n - 6) * possible, n * (n - 1))
    return {'opportunities': opportunities, 'matches': matches, 'expected': {'numerator': str(expected.numerator), 'denominator': str(expected.denominator)}}


def build(root=ROOT, write=True):
    record = json.loads((root / BASE / 'record.json').read_text(encoding='utf-8'))
    declaration = record.get('published_count_evidence')
    keys = {'schema', 'id', 'input_version', 'pages', 'criterion', 'alphabet_sha256', 'checked_at', 'source_sha256'}
    if not isinstance(declaration, dict) or set(declaration) != keys or record['id'] != RECORD or record['status'] != 'published':
        raise ValueError('Missing explicit published count declaration')
    if declaration['schema'] != 'liberpedia-published-count-declaration-v1' or declaration['id'] != 'lag-six-hyphen-period' or declaration['input_version'] != 'raw' or declaration['pages'] != PAGES or declaration['criterion'] != CRITERION:
        raise ValueError('Unsupported published count projection')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T00:00:00\.000Z', declaration['checked_at']):
        raise ValueError('Projection check date must be explicit and reproducible')
    pins = declaration['source_sha256']
    if not isinstance(pins, dict) or set(pins) != set(REQUIRED):
        raise ValueError('The complete original source pins are required')
    for name in REQUIRED:
        if sha((root / name).read_bytes()) != pins[name]:
            raise ValueError('Published source pin changed: ' + name)
    original = json.loads((root / BASE / 'results.json').read_text(encoding='utf-8'))
    if original['schema'] != 'liberpedia-word-internal-affine-lags-v1' or original['claim'] != {'lag': 6, 'a': 27, 'b': 24, 'equation': "c' = 24 - 2c (mod 29)"}:
        raise ValueError('The original report does not declare this rule')
    if original['input_sha256'] != {name: pins[name] for name in REQUIRED if name == 'data/index.json' or name.startswith('text/')}:
        raise ValueError('Original report input pins differ from the declaration')
    alphabet = [{key: row[key] for key in ('rune', 'latin', 'prime')} for row in json.loads((root / 'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    if sha(stable(alphabet)) != declaration['alphabet_sha256']:
        raise ValueError('Ordered alphabet differs from the declared alphabet')
    texts = [{'id': page, 'text': (root / f'text/{page}.txt').read_bytes().decode('utf-8')} for page in PAGES]
    official = json.loads((root / 'data/local-run-inputs.json').read_text(encoding='utf-8'))
    if official['alphabet'] != alphabet or any(next(p['raw'] for p in official['pages'] if p['id'] == page['id']) != page['text'] for page in texts):
        raise ValueError('Current raw browser inputs differ from the pinned archived text')
    measured = [dict(page=page['id'], **measure(page['text'], alphabet)) for page in texts]
    if original['page_counts'] != [{key: page[key] for key in ('page', 'opportunities', 'matches')} for page in measured]:
        raise ValueError('Original per-page statistics disagree with the independent count')
    expected = sum((Fraction(int(page['expected']['numerator']), int(page['expected']['denominator'])) for page in measured), Fraction())
    total = {'opportunities': sum(p['opportunities'] for p in measured), 'matches': sum(p['matches'] for p in measured), 'expected': {'numerator': str(expected.numerator), 'denominator': str(expected.denominator)}, 'pages': measured}
    if any(original['target'][key] != total[key] for key in ('opportunities', 'matches')) or not math.isclose(original['target']['exact_word_shuffle_expected'], float(expected), rel_tol=0, abs_tol=1e-10):
        raise ValueError('Original totals disagree with freshly recomputed values')
    # Execute the pinned independent original scan, not its costly exploratory
    # shuffle search. The adapter also checks its per-page statements above.
    subprocess.run(['python', str(root / BASE / 'check.py')], cwd=root, check=True, capture_output=True, text=True)
    payload = {'title': 'Published lag-six count · LP2-00–55', 'pages': texts, 'alphabet': alphabet, 'steps': [], 'criterion': CRITERION}
    node_code = """const fs=require('node:fs'),crypto=require('node:crypto'),E=require(process.argv[1]);
(async()=>{const task=await E.prepare(JSON.parse(fs.readFileSync(0,'utf8'))),result=await E.verify(task,E.run(task));console.log(JSON.stringify({task,result,id:crypto.createHash('sha256').update(E.stable(result)).digest('hex')}));})().catch(e=>{console.error(e);process.exitCode=1;});"""
    completed = subprocess.run(['node', '-e', node_code, str(root / 'local-experiment.js')], input=json.dumps(payload, ensure_ascii=False), cwd=root, check=True, capture_output=True, text=True, encoding='utf-8')
    browser = json.loads(completed.stdout)
    if browser['result']['wordPairs'] != total:
        raise ValueError('Browser engine and independent Python count disagree')
    source_pins = [{'path': name, 'sha256': pins[name]} for name in REQUIRED]
    # These maintained code files are published with repository LF endings.
    # Windows checkout conversion must not change their published identity.
    # Archived manuscript/report/checker pins above remain exact raw bytes.
    source_pins += [{'path': name, 'sha256': sha((root / name).read_bytes().replace(b'\r\n', b'\n'))} for name in ['local-experiment.js', 'scripts/build_published_count_evidence.py']]
    provenance = {'schema': 'liberpedia-published-count-projection-v1', 'recordId': RECORD, 'projection': {'id': declaration['id'], 'criterion': CRITERION, 'pages': PAGES, 'alphabetSha256': declaration['alphabet_sha256'], 'taskId': browser['task']['taskId'], 'resultId': browser['id']}, 'sourcePins': sorted(source_pins, key=lambda pin: pin['path']), 'checkedAt': declaration['checked_at'], 'dateMeaning': 'Count projection independently checked; not a historical browser submission.', 'expectationMeaning': 'Exact rational shuffle averages freshly recomputed; archived floating-point means are not reinterpreted as exact.'}
    revision = sha(stable(provenance))
    manifest = {'schema': 'liberpedia-published-count-evidence-v1', 'records': [{'recordId': RECORD, 'revision': revision, 'provenance': provenance}], 'entries': [{'recordId': RECORD, 'revision': revision, 'caseId': 'lag-six-hyphen-period--all-pages', 'task': browser['task'], 'inputVersion': 'raw', 'run': {'id': browser['id'], 'createdAt': declaration['checked_at'], 'result': browser['result']}}]}
    content = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
    javascript = "/* Generated by scripts/build_published_count_evidence.py. */\n(function(root){'use strict';const data=" + content + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedCountEvidenceData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"
    artifacts = {'data/published-count-evidence.json': content + '\n', 'published-count-evidence-data.js': javascript}
    for name, value in artifacts.items():
        if write:
            (root / name).write_text(value, encoding='utf-8', newline='\n')
        elif not (root / name).exists() or (root / name).read_text(encoding='utf-8') != value:
            raise ValueError('Stale published count evidence: ' + name)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    value = build(write=not options.check)
    print('Published count evidence: verified ' + str(len(value['entries'])) + ' immutable projection receipt.')
