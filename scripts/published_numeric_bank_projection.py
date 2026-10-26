"""Detached compact proof of numeric archives as complete nine-opening receipts.

This does not install evidence, register catalogs, execute target programs or
claim that the archived arrays were produced by a historical browser run.
"""
from collections import Counter
from dataclasses import dataclass
import copy
import json
from pathlib import Path

import browser_followups as fixed
import numeric_bank_followups as numeric
import numeric_opening_set_followups as openings

ROOT = numeric.ROOT
CHECKED_AT = '2026-10-26T00:00:00.000Z'
SCHEMA = 'liberpedia-published-numeric-bank-matrix-v1'
DATE_MEANING = 'Verification/import date only; no historical browser execution date or new target execution is asserted.'


def stable(value):
    return fixed.stable(value)


def digest(value):
    return numeric.digest(stable(value).encode('utf8'))


@dataclass(frozen=True)
class Projection:
    """Source-audited immutable bytes; detached views cannot rewrite evidence."""
    _bytes: bytes

    def __init__(self, manifest):
        fixed.require(manifest['schema'] == SCHEMA and manifest['sha256'] == digest(manifest['payload']), 'Detached numeric matrix changed')
        object.__setattr__(self, '_bytes', (stable(manifest) + '\n').encode('utf8'))

    def manifest(self):
        return json.loads(self._bytes)

    def bytes(self):
        return self._bytes

    def receipt(self, program_id):
        manifest = self.manifest()
        payload = manifest['payload']
        matches = [program for program in payload['programs'] if program['id'] == program_id]
        fixed.require(len(matches) == 1, 'Unknown or ambiguous numeric source program')
        program = matches[0]
        family = numeric.FAMILIES[payload['recordId']]
        bank = payload['bank']
        fixed.require(bank['id'] == family['bankId'] and bank['sha256'] == family['bankSha256']
                      and digest({'schema': 'liberpedia-finite-sequence-bank-v1', 'id': bank['id'], 'values': bank['values']}) == bank['sha256'],
                      'Stored numeric bank changed')
        tail = numeric.banks.resolve(family['bankId'], family['bankSha256'], program['offset'])
        fixed.require(tail == bank['values'][program['offset']:], 'Resolved numeric bank tail changed')
        task = {'schema': fixed.runner.TASK_SCHEMA, 'engine': fixed.runner.ENGINE,
                'title': 'Audited archived output · ' + program_id,
                'pages': copy.deepcopy(payload['pages']), 'alphabet': copy.deepcopy(payload['alphabet']),
                'steps': [{'op': 'finite-shift', 'key': tail, 'direction': program['direction'], 'reset': 'page'}],
                'criterion': copy.deepcopy(payload['criterion'])}
        task['taskId'] = fixed.runner.task_identity(task)
        fixed.runner.validate(task)
        rows = [payload['outputs'][index] for index in program['outputRefs']]
        fixed.require([row['page'] for row in rows] == [page['id'] for page in task['pages']], 'Program output page order changed')
        result = format_result(task, rows)
        projection = {'id': program_id, 'sourceProgramId': program_id, 'ownerRecordId': payload['recordId'],
                      'inputVersion': 'raw', 'steps': task['steps'], 'criterion': task['criterion'],
                      'pages': [p['id'] for p in task['pages']], 'alphabetSha256': digest(task['alphabet']),
                      'taskId': task['taskId'], 'resultId': digest(result)}
        provenance = {'schema': 'liberpedia-published-program-projection-v1', 'recordId': payload['recordId'],
                      'projection': projection, 'sourcePins': payload['sourcePins'], 'checkedAt': CHECKED_AT,
                      'dateMeaning': DATE_MEANING,
                      'verificationMeaning': 'All 3,190 complete archived rune-bearing arrays and 28,710 nine-opening decisions were independently audited. This receipt formats one fixed program with 55 archived arrays and one structural rune-empty LP2-50 output. No target transformation was run to construct it; the empty output is not a historical run.'}
        revision = digest(provenance)
        return {'schema': 'liberpedia-published-program-evidence-v1',
                'records': [{'recordId': payload['recordId'], 'revision': revision, 'provenance': provenance}],
                'entries': [{'recordId': payload['recordId'], 'revision': revision,
                    'caseId': program_id + '--all-pages', 'task': task, 'inputVersion': 'raw',
                    'run': {'id': projection['resultId'], 'createdAt': CHECKED_AT, 'result': result}}]}


def format_result(task, rows):
    """Reinsert archived indices; check inverse arithmetic, never compute outputs."""
    fixed.require(len(rows) == len(task['pages']) and [row['page'] for row in rows] == [page['id'] for page in task['pages']], 'Incomplete or duplicate output page scope')
    alphabet = task['alphabet']
    indices = {row['rune']: n for n, row in enumerate(alphabet)}
    frequencies, transformed, matches = Counter(), [], []
    pairs = equal = count = 0
    step = task['steps'][0]
    sign = 1 if step['direction'] == 'add' else -1
    for page, row in zip(task['pages'], rows):
        values = row['values']
        original = [indices[ch] for ch in page['text'] if ch in indices]
        fixed.require(len(values) == len(original) and all(type(v) is int and 0 <= v <= 28 for v in values), 'Incomplete archived output')
        fixed.require(all((v - sign * step['key'][n]) % 29 == original[n] for n, v in enumerate(values)), 'Archived output fails inverse arithmetic')
        expected = [opening['id'] for opening in task['criterion']['openings'] if values[:len(opening['values'])] == opening['values']]
        fixed.require(expected == row['matchingOpenings'], 'Archived ordered opening decisions changed')
        fixed.require(row['origin'] == ('archived' if original else 'structural-empty-input')
                      and (original or page['id'] == 'lp2-50'), 'Structural empty provenance changed')
        iterator = iter(values)
        transformed.append({'page': page['id'], 'text': ''.join(alphabet[next(iterator)]['rune'] if ch in indices else ch for ch in page['text'])})
        matches.append({'page': page['id'], 'matched': bool(expected), 'matchingOpenings': expected})
        frequencies.update(values)
        count += len(values)
        pairs += max(0, len(values)-1)
        equal += sum(a == b for a, b in zip(values, values[1:]))
    return {'schema': fixed.runner.RESULT_SCHEMA, 'taskId': task['taskId'], 'engine': fixed.runner.ENGINE,
            'runnerVersion': '1', 'metrics': {'pages': len(task['pages']), 'runes': count, 'adjacentPairs': pairs,
                'equalAdjacentPairs': equal, 'ioc': sum(n*(n-1) for n in frequencies.values())/(count*(count-1)) if count > 1 else 0},
            'matches': matches, 'transformed': transformed}


def prepare(record_id, root=ROOT):
    root = Path(root)
    declared = numeric.source(record_id, root)
    family = numeric.FAMILIES[record_id]
    criterion = openings.criterion(record_id, root, declared=declared)
    base = 'experiments/records/' + record_id
    report_raw = (root / base / 'results.json').read_bytes()
    fixed.require(numeric.digest(report_raw) == family['pins']['results.json'], 'Archived numeric report changed after audit')
    report = json.loads(report_raw)
    cases = {(row['page'], row['offset'], row['sign']): row for row in report['cases']}
    fixed.require(len(cases) == 3190, 'Duplicate or missing archived numeric case')
    alphabet = fixed.alphabet(root)
    pages = [{'id': page, 'text': (root / 'text' / (page + '.txt')).read_bytes().decode('utf8')} for page in numeric.PAGES]
    pins = {pin['path']: pin['sha256'] for pin in declared['pins']}
    fixed.require(all(numeric.digest(page['text'].encode('utf8')) == pins['text/' + page['id'] + '.txt'] for page in pages), 'Page changed after source audit')
    outputs, unique, programs = [], {}, []
    for offset in range(29):
        for sign in (-1, 1):
            direction = 'subtract' if sign == -1 else 'add'
            program_id = family['bankId'].removesuffix('-v1') + '-offset-' + str(offset) + '-' + direction + '-nine-openings'
            refs = []
            for page in pages:
                original = cases.get((page['id'], offset, sign))
                fixed.require(original is not None or page['id'] == 'lp2-50', 'An archived output is missing')
                row = {'page': page['id'], 'values': original['output_indices'] if original else [],
                       'matchingOpenings': original['matching_openings'] if original else [],
                       'origin': 'archived' if original else 'structural-empty-input'}
                key = stable(row)
                if key not in unique:
                    unique[key] = len(outputs)
                    outputs.append(copy.deepcopy(row))
                refs.append(unique[key])
            programs.append({'id': program_id, 'offset': offset, 'direction': direction, 'outputRefs': refs})
    payload = {'recordId': record_id, 'sourcePins': declared['pins'], 'alphabet': alphabet, 'pages': pages,
               'criterion': criterion, 'bank': copy.deepcopy(declared['bank']),
               'programs': programs, 'outputs': outputs, 'audit': declared['audit'],
               'declaredCases': 3248, 'structuralEmptyCases': 58, 'checkedAt': CHECKED_AT, 'dateMeaning': DATE_MEANING}
    return Projection({'schema': SCHEMA, 'payload': payload, 'sha256': digest(payload)})


def publication_files(root=ROOT):
    """Return exact provider bytes only; installing belongs to the caller."""
    files, pointers = {}, []
    for record_id, family in numeric.FAMILIES.items():
        projection = prepare(record_id, root)
        path = 'published-evidence/programs/numeric-bank-' + family['bankId'] + '-nine-openings.json'
        raw = projection.bytes()
        files[path] = raw
        payload = projection.manifest()['payload']
        input_pins = {pin['path']: pin['sha256'] for pin in payload['sourcePins']}
        for program in payload['programs']:
            receipt = projection.receipt(program['id'])
            entry, record = receipt['entries'][0], receipt['records'][0]
            task, result = entry['task'], entry['run']
            pointers.append({'recordId': record_id, 'revision': record['revision'], 'caseId': entry['caseId'],
                'inputVersion': entry['inputVersion'], 'taskId': task['taskId'], 'resultId': result['id'],
                'createdAt': result['createdAt'], 'steps': task['steps'], 'criterion': task['criterion'],
                'alphabetSha256': record['provenance']['projection']['alphabetSha256'],
                'pages': [{'id': page['id'], 'textSha256': input_pins['text/' + page['id'] + '.txt']} for page in task['pages']],
                'path': path, 'sha256': numeric.digest(raw), 'bytes': len(raw),
                'sourceFormat': 'numeric-bank-matrix-v1', 'programId': program['id']})
    index = {'schema': 'liberpedia-published-program-source-index-v1', 'entries': pointers}
    files['data/published-numeric-program-source-index.json'] = (stable(index) + '\n').encode('utf8')
    return files


def statistics(projection):
    manifest = projection.manifest()
    receipt_bytes = sum(len((stable(projection.receipt(program['id']))+'\n').encode('utf8')) for program in manifest['payload']['programs'])
    return {'recordId': manifest['payload']['recordId'], 'programs': 58, 'declaredCases': 3248,
            'historicalRuneBearingCases': 3190, 'structuralEmptyCases': 58,
            'uniqueOutputRows': len(manifest['payload']['outputs']), 'compactMatrixBytes': len(projection.bytes()),
            'duplicatedFullReceiptBytes': receipt_bytes, 'targetExecutions': 0}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Detached matrix output inside outer qa-temp only')
    parser.add_argument('--check-installed', action='store_true', help='Read-only comparison of all five installed provider artifacts')
    args = parser.parse_args()
    if args.output:
        destination = args.output.resolve()
        fixed.require(destination.is_relative_to((ROOT.parent.parent / 'qa-temp').resolve()), 'Output must stay inside outer qa-temp')
        destination.mkdir(parents=True, exist_ok=True)
    if args.check_installed:
        for path, expected in publication_files().items():
            fixed.require((ROOT / path).is_file() and (ROOT / path).read_bytes() == expected, 'Installed numeric provider differs: ' + path)
        print('PASS: four numeric matrices and all 232 provider headers match; no files changed.')
        raise SystemExit(0)
    for record_id in numeric.FAMILIES:
        value = prepare(record_id)
        if args.output:
            (destination / (record_id + '.json')).write_bytes(value.bytes())
        print(json.dumps(statistics(value)))
