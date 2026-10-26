"""Replay packaged runner checks before a manuscript computation. No network.

python verify_plan_controls.py --task task.json --controls runner-controls.json --out results.json
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import research_runner as runner


def stable(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + stable(value[k])
                              for k in sorted(value)) + '}'
    if isinstance(value, list):
        return '[' + ','.join(stable(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def read_json(path):
    with path.open('rb') as source:
        content = source.read(runner.MAX_FILE_BYTES + 1)
    runner.require(len(content) <= runner.MAX_FILE_BYTES, 'Packaged JSON exceeds its byte limit')
    return json.loads(content.decode('utf-8'), object_pairs_hook=runner.unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid JSON number')))


def verified_controls(target, suite):
    runner.validate(target)
    runner.fields(suite, ('version', 'targetId', 'cases'), 'Runner checks')
    runner.require(type(suite['version']) is int and suite['version'] == 1
                   and suite['targetId'] == target['taskId'], 'Runner checks belong to another task')
    cases = suite['cases']
    runner.require(isinstance(cases, list) and len(cases) == 2, 'Two runner checks are required')
    identifiers, task_ids = set(), set()
    prefix_states = []
    for case in cases:
        runner.fields(case, ('id', 'task', 'expectedResultSha256'), 'Runner check')
        runner.require(isinstance(case['id'], str) and re.fullmatch(r'[a-z][a-z0-9-]{0,63}', case['id'])
                       and case['id'] not in identifiers, 'Invalid or repeated check identifier')
        identifiers.add(case['id'])
        control = case['task']
        runner.validate(control)
        runner.require(control['taskId'] not in task_ids, 'Runner checks must be distinct')
        task_ids.add(control['taskId'])
        runner.require('synthetic' in control['title'].lower(), 'Runner check must be labeled synthetic')
        for key in ('steps', 'alphabet'):
            runner.require(control[key] == target[key], 'Runner check uses a different ' + key)
        runes = {entry['rune'] for entry in control['alphabet']}
        runner.require(len(control['pages']) == 2 and all(
            1 <= sum(ch in runes for ch in page['text']) <= 320 for page in control['pages']),
            'Runner check exceeds its synthetic input bounds')
        if target['criterion']['kind'] in ('exact-prefix', 'exact-prefix-set'):
            runner.require(control['criterion']['kind'] == target['criterion']['kind'],
                           'Runner check uses a different evaluation')
        else:
            runner.require(control['criterion'] == target['criterion'],
                           'Runner check uses a different evaluation')
        expected = case['expectedResultSha256']
        runner.require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected),
                       'Invalid runner check result hash')
        result = runner.run(control)
        actual = hashlib.sha256(stable(result).encode('utf-8')).hexdigest()
        runner.require(actual == expected, 'Runner check result differs; manuscript task not run')
        if target['criterion']['kind'] in ('exact-prefix', 'exact-prefix-set'):
            runner.require(bool(result['matches']), 'Runner prefix check has no comparisons')
            prefix_states.append(result['matches'][0]['matched'])
    if target['criterion']['kind'] in ('exact-prefix', 'exact-prefix-set'):
        runner.require(prefix_states == [True, False], 'Prefix checks must exercise a match and a mismatch')
    return len(cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        target, controls, output = args.task.resolve(), args.controls.resolve(), args.out.resolve()
        runner.require(target.parent == controls.parent, 'Task and runner checks must share one extracted folder')
        runner.require(not output.exists() and not args.out.is_symlink(), 'Output already exists')
        runner.require(output not in (target, controls, Path(__file__).resolve(), Path(runner.__file__).resolve()),
                       'Output cannot overwrite packaged inputs or runner')
        task = read_json(target)
        count = verified_controls(task, read_json(controls))
        result = runner.run(task)
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n')
        print('Verified ' + str(count) + ' runner checks; saved results to ' + str(args.out))
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, 'verify_plan_controls: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
