"""Audit archived panel-prime outputs and format separate indexed receipts.

The builder never calls a target runner. Its only newly supplied outputs are
empty arrays for the declared rune-empty page omitted by the original checker.
"""
import csv
import io
import json
from pathlib import Path

import published_known_key_projection as known

ROOT = Path(__file__).resolve().parents[1]
BASE = 'experiments/records/lp2-panel-prime-openings'
RECORD = 'lp2-panel-prime-openings'
CHECKED_AT = '2026-10-25T00:00:00.000Z'
PINS = {
    'plan.json': '7fafa7f3d121f3a55fbd2c5069722566bf5465b93f438fa9a1bc2b5b9ee74975',
    'results.json': 'd78bc73a0fabe0a70937ae3ab787b6160c9481935b1627a8281e5e6147787d50',
    'run.py': '700aa4ec788d9d07d0e9febd4f6bb4f8c9fe501ce63458fadff3e031ad307d6d',
    'check.py': '004e1de1f29cde08d8911a803e3259c3444324a05e9dc62df0c5e78e4a7e6fee',
}
KEY = [2, 3, 5, 7, 13, 23, 43, 79, 149, 263, 463, 829, 1481, 2593, 4507, 7817]
AUDIT_PATH = 'published-evidence/programs/panel-prime-historical-audit.json'
INDEX_PATH = 'data/published-panel-program-source-index.json'
MODULE_PATH = 'data/published-panel-program-source-index-data.js'
sha, stable, require = known.sha, known.stable, known.require


def audit(root=ROOT):
    root = Path(root)
    pins = {}
    for name, expected in PINS.items():
        path = BASE + '/' + name
        require(sha((root / path).read_bytes()) == expected, 'Archived panel source pin changed: ' + path)
        pins[path] = expected
    plan = json.loads((root / BASE / 'plan.json').read_bytes())
    report = json.loads((root / BASE / 'results.json').read_bytes())
    pages = [f'lp2-{n:02d}' for n in range(56)]
    require(plan['pages'] == pages and plan['key'] == KEY and plan['offsets'] == list(range(16)) and plan['signs'] == [-1, 1] and plan['prefix_length'] == 12, 'Historical panel domain changed')
    require(report['schema'] == 'liberpedia-panel-prime-openings-v1' and report['plan_sha256'] == PINS['plan.json'], 'Historical panel report identity changed')
    for entry in plan['inputs']:
        path = entry['path']
        require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'Unsafe historical input path')
        require(sha((root / path).read_bytes()) == entry['sha256'], 'Historical panel input pin changed: ' + path)
        pins[path] = entry['sha256']
    source_page = json.loads((root / 'data/pages/lp2-15.json').read_bytes())
    ledger = json.loads((root / 'exports/fibonacci-prime-panel.json').read_bytes())
    require(ledger['page'] == 'lp2-15' and ledger['source_sha256'] == pins['data/pages/lp2-15.json'] and ledger['original_image_sha256'] == source_page['image_sha256'], 'Panel ledger source changed')
    reconstructed = []
    for position, step in enumerate(ledger['rows'], 1):
        printed = source_page['numbers'][step['row'] - 1][step['column'] - 1]
        require(step['step'] == position and abs(3301 - step['prime']) == printed == step['printed'], 'Printed panel spiral differs from ledger')
        reconstructed.append(step['prime'])
    require(reconstructed == KEY == report['key'] and [n % 29 for n in KEY] == report['key_mod_29'], 'Panel prime order changed')
    baseline = json.loads((root / 'experiments/records/lp2-fibonacci-openings/plan.json').read_bytes())
    for field in ('pages', 'signs', 'prefix_length', 'openings', 'representation', 'advancement', 'decision', 'stopping_rule'):
        require(plan[field] == baseline[field], 'Historical opening convention changed: ' + field)
    index = json.loads((root / 'data/index.json').read_bytes())
    alphabet = [{k: row[k] for k in ('rune', 'latin', 'prime')} for row in index['alphabet']]
    require(len(alphabet) == 29 and len({a['rune'] for a in alphabet}) == 29, 'Historical alphabet changed')
    lookup = {a['rune']: i for i, a in enumerate(alphabet)}
    texts = {pid: (root / 'text' / (pid + '.txt')).read_bytes().decode('utf-8') for pid in pages}
    vectors = {pid: [lookup[c] for c in text if c in lookup] for pid, text in texts.items()}
    official = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    require(official['alphabet'] == alphabet and all(next(p['raw'] for p in official['pages'] if p['id'] == pid) == text for pid, text in texts.items()), 'Browser panel inputs differ from archived inputs')
    require(report['page_lengths'] == {p: len(v) for p, v in vectors.items()} and report['empty_pages'] == [p for p, v in vectors.items() if not v] == ['lp2-50'], 'Historical rune-empty scope changed')
    require(len(plan['openings']) == 9 and len({o['id'] for o in plan['openings']}) == 9, 'Historical opening domain changed')
    for opening in plan['openings']:
        data = (root / opening['source']).read_bytes()
        require(sha(data) == opening['sha256'], 'Opening source pin changed')
        values = [int(row['output_index']) for row in csv.DictReader(io.StringIO(data.decode('utf-8-sig')))][:12]
        require(values == opening['indices'] and len(values) == 12, 'Historical opening source differs')
        pins[opening['source']] = opening['sha256']
    expected = {(pid, offset, sign) for pid, values in vectors.items() if values for offset in range(16) for sign in (-1, 1)}
    cases = {}
    for row in report['cases']:
        require(type(row['offset']) is int and type(row['sign']) is int, 'Panel setting must use exact integers')
        identity = row['page'], row['offset'], row['sign']
        require(identity in expected and identity not in cases, 'Unexpected or duplicate panel output')
        pid, offset, sign = identity
        output, original = row['output_indices'], vectors[pid]
        require(len(output) == len(original) and all(type(n) is int and 0 <= n < 29 for n in output), 'Incomplete panel output')
        require(all((n - sign * KEY[(i + offset) % 16]) % 29 == original[i] for i, n in enumerate(output)), 'Panel output violates its inverse equation')
        matches = [o['id'] for o in plan['openings'] if output[:12] == o['indices']]
        require(row['matching_openings'] == matches, 'Historical panel opening decisions changed')
        cases[identity] = row
    require(set(cases) == expected and report['case_count'] == len(cases) == 1760 and report['comparison_count'] == 15840 and report['matching_case_count'] == sum(bool(r['matching_openings']) for r in cases.values()) == 0, 'Historical panel totals changed')
    require(report['distinct_page_outputs'] == sum(len({tuple(r['output_indices']) for (page, _, _), r in cases.items() if page == pid}) for pid in pages) == 1760, 'Historical distinct-output total changed')
    return plan, alphabet, texts, cases, pins


def prepare(root=ROOT):
    root = Path(root)
    plan, alphabet, texts, cases, pins = audit(root)
    files = {}
    sidecar = {'schema': 'liberpedia-historical-opening-audit-v1', 'recordId': RECORD, 'auditedAt': CHECKED_AT,
               'dateMeaning': 'Audit/import date; the panel archive records no historical browser receipt or execution timestamp.',
               'openings': plan['openings'], 'caseCount': 1760, 'comparisonCount': 15840, 'matchingCaseCount': 0,
               'historicalNonemptyCaseCount': 1760, 'historicalRuneIndexCount': sum(len(r['output_indices']) for r in cases.values()),
               'projectedCaseCount': 1792, 'structuralEmptyInputCaseCount': 32, 'emptyPages': ['lp2-50'],
               'emptyInputMeaning': 'The original run/check explicitly omitted LP2-50 because its archived text contains no recognized runes. Thirty-two empty arrays are supplied only to format complete current page scopes; they are not historical runs or archived candidate arrays.',
               'projectedCriterion': 'warning', 'otherOpeningEvaluations': 'The other eight original 12-rune opening decisions remain archived source evidence; projected receipts evaluate Warning only.'}
    files[AUDIT_PATH] = stable(sidecar) + '\n'
    pins[AUDIT_PATH] = sha(files[AUDIT_PATH])
    for path in ('scripts/published_panel_prime_projection.py', 'scripts/published_known_key_projection.py', 'tools/research_runner.py', 'local-experiment.js'):
        pins[path] = sha((root / path).read_bytes().replace(b'\r\n', b'\n'))
    criterion = {'kind': 'exact-prefix', 'values': next(o['indices'] for o in plan['openings'] if o['id'] == 'warning')}
    entries = []
    for offset in range(16):
        for sign in (-1, 1):
            direction = 'subtract' if sign == -1 else 'add'
            identifier = f'panel-primes-phase-{offset}-{direction}'
            key = [n % 29 for n in KEY]
            steps = [{'op': 'keyed-shift', 'key': key[offset:] + key[:offset], 'mode': 'repeat', 'direction': direction, 'reset': 'page'}]
            task = {'schema': known.runner.TASK_SCHEMA, 'engine': known.runner.ENGINE, 'title': 'Audited archived output · ' + identifier,
                    'pages': [{'id': pid, 'text': text} for pid, text in texts.items()], 'alphabet': alphabet, 'steps': steps, 'criterion': criterion}
            task['taskId'] = known.runner.task_identity(task)
            known.runner.validate(task)
            rows = [cases[(pid, offset, sign)]['output_indices'] if pid != 'lp2-50' else [] for pid in texts]
            result = known.receipt_result(task, rows)
            result_id = sha(stable(result))
            projection = {'id': identifier, 'ownerRecordId': RECORD, 'sourceProgramId': identifier, 'inputVersion': 'raw', 'steps': steps,
                          'criterion': criterion, 'pages': list(texts), 'alphabetSha256': sha(stable(alphabet)), 'taskId': task['taskId'], 'resultId': result_id}
            provenance = {'schema': 'liberpedia-published-program-projection-v1', 'recordId': RECORD, 'projection': projection,
                          'sourcePins': [{'path': p, 'sha256': v} for p, v in sorted(pins.items())], 'checkedAt': CHECKED_AT,
                          'dateMeaning': sidecar['dateMeaning'],
                          'verificationMeaning': 'All 1,760 complete archived nonempty outputs and 15,840 original opening decisions were independently audited against pinned sources. This receipt formats one of 32 fixed programs with 55 archived arrays and one explicitly structural rune-empty LP2-50 output, evaluating Warning only. No target transformation was rerun to construct it.'}
            revision = sha(stable(provenance))
            case_id = identifier + '--all-pages'
            receipt = {'schema': 'liberpedia-published-program-evidence-v1', 'records': [{'recordId': RECORD, 'revision': revision, 'provenance': provenance}],
                       'entries': [{'recordId': RECORD, 'revision': revision, 'caseId': case_id, 'task': task, 'inputVersion': 'raw', 'run': {'id': result_id, 'createdAt': CHECKED_AT, 'result': result}}]}
            path = 'published-evidence/programs/' + identifier + '.json'
            content = stable(receipt) + '\n'
            files[path] = content
            entries.append({'recordId': RECORD, 'revision': revision, 'caseId': case_id, 'inputVersion': 'raw', 'taskId': task['taskId'], 'resultId': result_id,
                            'createdAt': CHECKED_AT, 'steps': steps, 'criterion': criterion, 'alphabetSha256': projection['alphabetSha256'],
                            'pages': [{'id': pid, 'textSha256': sha(text)} for pid, text in texts.items()], 'path': path, 'sha256': sha(content), 'bytes': len(content.encode('utf-8'))})
    index = {'schema': 'liberpedia-published-program-source-index-v1', 'entries': entries}
    files[INDEX_PATH] = stable(index) + '\n'
    files[MODULE_PATH] = "/* Generated audited panel program index; separate from known-key sources. */\n(function(root){'use strict';const data=" + stable(index) + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedPanelProgramSourceIndexData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"
    return files


def build(root=ROOT, write=False):
    root = Path(root)
    files = prepare(root)
    for name, content in files.items():
        path = root / name
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
        else:
            require(path.exists() and path.read_bytes() == content.encode('utf-8'), 'Stale panel projection: ' + name)
    return json.loads(files[INDEX_PATH])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    index = build(write=args.write)
    print(f"PASS: {len(index['entries'])} panel programs; 1,760 archived nonempty outputs plus 32 structural empty-input projections.")
