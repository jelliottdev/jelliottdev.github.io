"""Independently replay the manuscript calculations in a downloaded family batch.

python reproduce_family.py --batch deor-feedback-BATCH.json --out replay.json
Keep research_runner.py beside this file. No network or additional packages.
This checks the contained DEOR cases and complete returned manuscript results.
It does not authenticate the text against the website's current input snapshot,
verify saved coverage, or verify synthetic controls: their task inputs are not
included in this download. Control results are retained unchanged, not endorsed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import research_runner as runner

MAX_BYTES = 2 * 1024 * 1024
KEY = [23, 18, 3, 4]
WARNING = [24, 7, 24, 4, 9, 21, 17, 18, 20, 10, 18, 1]
TITLE = 'DEOR key: fixed Warning opening'


def same(actual, expected):
    """Match every field, permitting only engine-equivalent floating rounding."""
    if isinstance(expected, bool):
        return type(actual) is bool and actual == expected
    if isinstance(expected, (int, float)):
        if type(actual) not in (int, float) or not math.isfinite(actual):
            return False
        return actual == expected if float(expected).is_integer() else abs(actual - expected) <= 1e-12
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(same(a, b) for a, b in zip(actual, expected))
    return type(actual) is type(expected) and actual == expected


def scalar_strings(value):
    if isinstance(value, str):
        runner.require(not any(0xD800 <= ord(ch) <= 0xDFFF for ch in value), 'Invalid Unicode scalar')
    elif isinstance(value, dict):
        for key, item in value.items():
            scalar_strings(key)
            scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            scalar_strings(item)


def validate_plan(plan):
    runner.fields(plan, ('schema', 'familyId', 'revision', 'planId', 'cases'), 'Family plan')
    runner.require(plan['schema'] == 'liberpedia-family-plan-v1' and plan['familyId'] == 'deor-feedback-v1', 'Unsupported family')
    for name in ('revision', 'planId'):
        runner.require(isinstance(plan[name], str) and re.fullmatch('[a-f0-9]{64}', plan[name]), 'Invalid ' + name)
    cases = plan['cases']
    runner.require(isinstance(cases, list) and 1 <= len(cases) <= 12, 'A batch needs one to twelve cases')
    previous, alphabet = '', None
    for item in cases:
        runner.fields(item, ('id', 'configuration', 'pageId', 'task'), 'Family case')
        configuration, page = item['configuration'], item['pageId']
        runner.require(isinstance(configuration, str), 'Invalid configuration')
        parts = configuration.split('--')
        runner.require(len(parts) == 3 and parts[0] in ('repeat', 'plaintext-autokey', 'ciphertext-autokey')
                       and parts[1] in ('subtract', 'add') and parts[2] in ('page', 'line', 'word'), 'Unsupported configuration')
        runner.require(isinstance(page, str) and re.fullmatch(r'lp2-(?:[0-4][0-9]|5[1-5])', page), 'Unsupported family page')
        runner.require(isinstance(item['id'], str) and item['id'] == configuration + '--' + page and item['id'] > previous,
                       'Family cases must be distinct and ordered')
        previous = item['id']
        task = runner.validate(item['task'])
        runner.require(task['title'] == TITLE + ' · ' + configuration + ' · ' + page
                       and len(task['pages']) == 1 and task['pages'][0]['id'] == page, 'Task does not match its case')
        expected_step = {'op': 'keyed-shift', 'key': KEY, 'mode': parts[0], 'direction': parts[1], 'reset': parts[2]}
        runner.require(task['steps'] == [expected_step] and task['criterion'] == {'kind': 'exact-prefix', 'values': WARNING},
                       'Task does not use the fixed DEOR key and Warning opening')
        runner.require(alphabet is None or alphabet == task['alphabet'], 'Cases use different alphabets')
        alphabet = task['alphabet']
        runes = {entry['rune'] for entry in alphabet}
        runner.require(any(ch in runes for ch in task['pages'][0]['text']), 'Family page has no rune text')
    identity = hashlib.sha256(runner.canonical({k: v for k, v in plan.items() if k != 'planId'})).hexdigest()
    runner.require(plan['planId'] == identity, 'Family plan identity differs')
    return cases


def reproduce(batch):
    runner.fields(batch, ('plan', 'results', 'controls'), 'Family download')
    scalar_strings(batch)
    cases = validate_plan(batch['plan'])
    runner.require(isinstance(batch['results'], list) and isinstance(batch['controls'], list)
                   and len(batch['results']) == len(cases) and len(batch['controls']) == len(cases), 'Batch results are incomplete')
    # Controls lack task inputs in this format. Check identity/shape only, and
    # preserve them without claiming their calculations were reproduced.
    for case, item in zip(cases, batch['controls']):
        runner.fields(item, ('caseId', 'results'), 'Retained control results')
        runner.require(item['caseId'] == case['id'] and isinstance(item['results'], list)
                       and len(item['results']) == 2, 'Controls belong to another case')
        for name, control in zip(('layout-forward', 'layout-reversed'), item['results']):
            runner.fields(control, ('id', 'result'), 'Retained control')
            runner.require(control['id'] == name and isinstance(control['result'], dict), 'Malformed retained control')
    fresh = []
    for case, item in zip(cases, batch['results']):
        runner.fields(item, ('caseId', 'result'), 'Manuscript result')
        runner.require(item['caseId'] == case['id'], 'Result does not match its ordered case')
        result = runner.run(case['task'])
        runner.require(same(item['result'], result), 'Complete result differs for ' + case['id'])
        fresh.append({'caseId': case['id'], 'result': result})
    return {'plan': batch['plan'], 'results': fresh, 'controls': batch['controls']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        source, output = args.batch.resolve(), args.out.resolve()
        runner.require(output not in (source, Path(__file__).resolve(), Path(runner.__file__).resolve()),
                       'Output cannot overwrite inputs or either runner')
        runner.require(not args.out.exists() and not args.out.is_symlink(), 'Output already exists')
        with source.open('rb') as handle:
            raw = handle.read(MAX_BYTES + 1)
        runner.require(len(raw) <= MAX_BYTES, 'Family download exceeds the 2 MB byte limit')
        batch = json.loads(raw.decode('utf-8'), object_pairs_hook=runner.unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid JSON number')))
        result = reproduce(batch)
        payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
        print('Reproduced ' + str(len(result['results'])) + ' manuscript calculations. Controls retained, not verified. No website coverage changed.')
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        parser.exit(2, 'reproduce_family: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
