"""Audit archived known-key arrays and project them into bounded, indexed receipts.

No target transformation is executed. Every stored index is checked against the
declared modular equation before constructing a current-format import receipt.
"""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import research_runner as runner

BASE = 'experiments/records/lp2-known-vigenere-keys'
RECORD = 'lp2-known-vigenere-keys'
CHECKED_AT = '2026-10-25T00:00:00.000Z'
PINS = {
    'plan.json': '3636812c3a3666956a6d71aae5bda236d42a5371a60814d5fb1bc5a2762e634a',
    'results.json': '7df0a8a0a7d9214aafac7034d12ac61e83d088e6815240559f2cf17106ffe323',
    'run.py': '8a76a9610ec49765b563e9222e288f523c7ebd4d6dce9a7377d286f085a3c762',
    'check.py': '7f74a57591b3928228bde4d04ec3b2ff9be26741c97a1d61bb3ea8fcf82c12d0',
}
KEYS = {'welcome': [23,10,1,10,9,10,16,26], 'second-koan': [0,10,4,0,1,19,0,18,4,18,9,0,18]}
AUDIT_PATH = 'published-evidence/programs/known-key-historical-audit.json'
# Frozen code used by the original import. Runtime upgrades must not rewrite
# old receipt provenance, revisions, dates or task/result identities.
HISTORICAL_CODE_PINS = {'scripts/published_known_key_projection.py': '824029e9b72d0eeaf84890ad5f966c101472c47d5ff47e9d0cf7f0eba1b95aea', 'tools/research_runner.py': 'be73adac90d9b7cf7ee8a7b2f11bdd1d7a61974e84b21a5566ca97f37a1d0c61', 'local-experiment.js': 'b2f38df4184a36f1462cfea120c1d121dde05babdb29e30f97442d8528b762c2'}


def historical_code_pins(root=ROOT):
    root = Path(root)
    for source, digest in HISTORICAL_CODE_PINS.items():
        retained = root / 'published-sources/runtime' / (digest + Path(source).suffix)
        require(retained.is_file() and sha(retained.read_bytes()) == digest,
                'Historical projection code is missing or changed: ' + source)
    return dict(HISTORICAL_CODE_PINS)



def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(root=ROOT):
    root = Path(root)
    pins = {}
    for name, expected in PINS.items():
        path = BASE + '/' + name
        require(sha((root / path).read_bytes()) == expected, 'Archived source pin changed: ' + path)
        pins[path] = expected
    plan = json.loads((root / BASE / 'plan.json').read_bytes())
    report = json.loads((root / BASE / 'results.json').read_bytes())
    pages = [f'lp2-{n:02d}' for n in range(56)]
    require(plan['pages'] == pages and plan['keys'] == [{'id': k, 'indices': v} for k, v in KEYS.items()] and plan['signs'] == [-1, 1], 'Historical program domain changed')
    require(report['schema'] == 'liberpedia-known-key-opening-v1' and report['plan_sha256'] == PINS['plan.json'], 'Historical report identity changed')
    alphabet = [{k: row[k] for k in ('rune', 'latin', 'prime')} for row in json.loads((root / 'data/index.json').read_bytes())['alphabet']]
    require(report['alphabet'] == [a['rune'] for a in alphabet], 'Historical alphabet changed')
    indices = {a['rune']: i for i, a in enumerate(alphabet)}
    texts, vectors = {}, {}
    require([p['path'] for p in report['inputs']] == ['text/' + p + '.txt' for p in pages], 'Historical input domain changed')
    for source in report['inputs']:
        raw = (root / source['path']).read_bytes()
        require(sha(raw) == source['sha256'], 'Historical input pin changed: ' + source['path'])
        pins[source['path']] = source['sha256']
        pid = Path(source['path']).stem
        texts[pid] = raw.decode('utf-8')
        vectors[pid] = [indices[c] for c in texts[pid] if c in indices]
    official = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    require(official['alphabet'] == alphabet and all(next(p['raw'] for p in official['pages'] if p['id'] == pid) == text for pid, text in texts.items()), 'Browser inputs differ from archived inputs')
    require(len(plan['openings']) == 9 and len({o['id'] for o in plan['openings']}) == 9, 'Historical opening domain changed')
    for opening in plan['openings']:
        raw = (root / opening['source']).read_bytes()
        require(sha(raw) == opening['sha256'], 'Historical opening pin changed')
        values = [int(r['output_index']) for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))][:12]
        require(values == opening['indices'] and len(values) == 12, 'Historical opening differs from source trace')
        pins[opening['source']] = opening['sha256']
    expected = {(pid, key, phase, sign) for pid in pages for key, key_values in KEYS.items() for phase in range(len(key_values)) for sign in (-1, 1)}
    cases = {}
    for row in report['cases']:
        identity = (row['page'], row['key'], row['phase'], row['sign'])
        require(identity in expected and identity not in cases, 'Unexpected or duplicate historical case')
        pid, key, phase, sign = identity
        out, original, key_values = row['output_indices'], vectors[pid], KEYS[key]
        require(len(out) == len(original) and all(type(n) is int and 0 <= n < 29 for n in out), 'Incomplete historical output')
        # Independently check the inverse equation; never call the target runner.
        require(all((n - sign * key_values[(i + phase) % len(key_values)]) % 29 == original[i] for i, n in enumerate(out)), 'Historical output violates declared key equation')
        matches = [o['id'] for o in plan['openings'] if out[:12] == o['indices']]
        require(row['matching_openings'] == matches, 'Historical opening evaluations changed')
        cases[identity] = row
    require(set(cases) == expected and report['case_count'] == 2352 and report['comparison_count'] == 21168 and report['matching_case_count'] == sum(bool(r['matching_openings']) for r in cases.values()) == 0, 'Historical coverage or result totals changed')
    return plan, alphabet, texts, cases, pins


def receipt_result(task, rows):
    runes = [a['rune'] for a in task['alphabet']]
    rune_set, counts, transformed, matches = set(runes), Counter(), [], []
    total = pairs = equal = 0
    for page, values in zip(task['pages'], rows):
        counts.update(values)
        total += len(values)
        pairs += max(0, len(values) - 1)
        equal += sum(a == b for a, b in zip(values, values[1:]))
        out = iter(values)
        transformed.append({'page': page['id'], 'text': ''.join(runes[next(out)] if c in rune_set else c for c in page['text'])})
        matches.append({'page': page['id'], 'matched': values[:12] == task['criterion']['values']})
    return {'schema': runner.RESULT_SCHEMA, 'taskId': task['taskId'], 'engine': runner.ENGINE,
            'metrics': {'pages': len(rows), 'runes': total, 'adjacentPairs': pairs, 'equalAdjacentPairs': equal,
                        'ioc': sum(n * (n - 1) for n in counts.values()) / (total * (total - 1)) if total > 1 else 0},
            'matches': matches, 'transformed': transformed, 'runnerVersion': '1'}


def prepare(root=ROOT):
    root = Path(root)
    plan, alphabet, texts, cases, pins = audit(root)
    files = {}
    sidecar = {'schema': 'liberpedia-historical-opening-audit-v1', 'recordId': RECORD,
               'historicalDeclaredBeforeRun': plan['declared_before_run'], 'auditedAt': CHECKED_AT,
               'dateMeaning': 'Audit/import date; the archive contains no historical browser receipt or execution timestamp.',
               'openings': plan['openings'], 'caseCount': 2352, 'comparisonCount': 21168, 'matchingCaseCount': 0,
               'projectedCriterion': 'warning', 'otherOpeningEvaluations': 'The other eight original opening checks remain archived source evidence; these receipts evaluate Warning only.'}
    files[AUDIT_PATH] = stable(sidecar) + '\n'
    pins[AUDIT_PATH] = sha(files[AUDIT_PATH])
    pins.update(historical_code_pins(root))
    criterion = {'kind': 'exact-prefix', 'values': next(o['indices'] for o in plan['openings'] if o['id'] == 'warning')}
    alphabet_hash = sha(stable(alphabet))
    entries = []
    for key, key_values in KEYS.items():
        for phase in range(len(key_values)):
            for sign in (-1, 1):
                direction = 'subtract' if sign == -1 else 'add'
                identifier = f'known-keys-{key}-phase-{phase}-{direction}'
                steps = [{'op': 'keyed-shift', 'key': key_values[phase:] + key_values[:phase], 'mode': 'repeat', 'direction': direction, 'reset': 'page'}]
                task = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE, 'title': 'Audited archived output · ' + identifier,
                        'pages': [{'id': pid, 'text': text} for pid, text in texts.items()], 'alphabet': alphabet, 'steps': steps, 'criterion': criterion}
                task['taskId'] = runner.task_identity(task)
                runner.validate(task)
                result = receipt_result(task, [cases[(pid, key, phase, sign)]['output_indices'] for pid in texts])
                result_id = sha(stable(result))
                projection = {'id': identifier, 'ownerRecordId': RECORD, 'sourceProgramId': identifier, 'inputVersion': 'raw', 'steps': steps,
                              'criterion': criterion, 'pages': list(texts), 'alphabetSha256': alphabet_hash, 'taskId': task['taskId'], 'resultId': result_id}
                provenance = {'schema': 'liberpedia-published-program-projection-v1', 'recordId': RECORD, 'projection': projection,
                              'sourcePins': [{'path': p, 'sha256': value} for p, value in sorted(pins.items())], 'checkedAt': CHECKED_AT,
                              'dateMeaning': 'Audit/import date of archived arrays; not a historical browser submission or historical execution timestamp.',
                              'verificationMeaning': 'All 2,352 complete archived outputs and all nine original 12-rune opening checks were independently audited against pinned sources. This receipt formats one of 42 fixed programs and evaluates only the original Warning opening. No target transformation was rerun to construct it.'}
                revision = sha(stable(provenance))
                case_id = identifier + '--all-pages'
                receipt = {'schema': 'liberpedia-published-program-evidence-v1', 'records': [{'recordId': RECORD, 'revision': revision, 'provenance': provenance}],
                           'entries': [{'recordId': RECORD, 'revision': revision, 'caseId': case_id, 'task': task, 'inputVersion': 'raw', 'run': {'id': result_id, 'createdAt': CHECKED_AT, 'result': result}}]}
                path = 'published-evidence/programs/' + identifier + '.json'
                content = stable(receipt) + '\n'
                files[path] = content
                entries.append({'recordId': RECORD, 'revision': revision, 'caseId': case_id, 'inputVersion': 'raw', 'taskId': task['taskId'], 'resultId': result_id,
                                'createdAt': CHECKED_AT, 'steps': steps, 'criterion': criterion, 'alphabetSha256': alphabet_hash,
                                'pages': [{'id': pid, 'textSha256': sha(text)} for pid, text in texts.items()], 'path': path, 'sha256': sha(content), 'bytes': len(content.encode('utf-8'))})
    index = {'schema': 'liberpedia-published-program-source-index-v1', 'entries': entries}
    files['data/published-program-source-index.json'] = stable(index) + '\n'
    files['published-program-source-index-data.js'] = "/* Generated audited program source index. */\n(function(root){'use strict';const data=" + stable(index) + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedProgramSourceIndexData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"
    return files


def build(root=ROOT, write=True):
    root = Path(root)
    files = prepare(root)
    for name, content in files.items():
        path = root / name
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
        else:
            require(path.exists() and path.read_bytes() == content.encode('utf-8'), 'Stale indexed program evidence: ' + name)
    return json.loads(files['data/published-program-source-index.json'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write reviewed indexed projections; otherwise check generated bytes')
    args = parser.parse_args()
    index = build(write=args.write)
    print(f"PASS: {len(index['entries'])} audited program receipts; 2,352 complete archived cases retained.")
