"""Verify packaged synthetic controls before running a bounded local task.

Usage: python verify_controls.py --task task.json --origins origins.json --out results.json
Only the bundled fixed runner and Python standard library are used. No network.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import research_runner as runner

HEX = re.compile(r'[a-f0-9]{64}')
IDENTIFIER = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def stable(value):
    """Match LocalExperiment.stable for the bounded runner's JSON result."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + stable(value[k])
                              for k in sorted(value)) + '}'
    if isinstance(value, list):
        return '[' + ','.join(stable(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def read_json(path):
    with path.open('rb') as handle:
        data = handle.read(runner.MAX_FILE_BYTES + 1)
    runner.require(len(data) <= runner.MAX_FILE_BYTES, 'Packaged JSON exceeds its byte limit')
    return json.loads(data.decode('utf-8'), object_pairs_hook=runner.unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid JSON number')))


def validate_origin(value):
    runner.fields(value, ('origin', 'control', 'question', 'scopeChange', 'limitation'), 'Origin entry')
    origin = value['origin']
    runner.fields(origin, ('recordId', 'followupId', 'recordSha256', 'protocolSha256'), 'Origin')
    for key in ('recordId', 'followupId'):
        runner.require(isinstance(origin[key], str) and len(origin[key]) <= 100
                       and IDENTIFIER.fullmatch(origin[key]), 'Invalid origin identifier')
    for key in ('recordSha256', 'protocolSha256'):
        runner.require(isinstance(origin[key], str) and HEX.fullmatch(origin[key]), 'Invalid origin hash')
    for key in ('question', 'scopeChange', 'limitation'):
        runner.require(isinstance(value[key], str) and value[key].strip()
                       and len(value[key]) <= 1200, 'Invalid origin text')
    control = value['control']
    runner.fields(control, ('label', 'task', 'expected_result_sha256'), 'Control')
    runner.require(isinstance(control['label'], str) and control['label'].strip()
                   and len(control['label']) <= 300 and 'synthetic' in control['label'].lower(),
                   'Control must be labeled synthetic')
    runner.require(isinstance(control['expected_result_sha256'], str)
                   and HEX.fullmatch(control['expected_result_sha256']), 'Invalid control result hash')
    return control


def positive_control(task, result):
    if task['criterion']['kind'] == 'exact-prefix':
        return bool(result['matches']) and all(m['matched'] for m in result['matches'])
    if task['criterion']['kind'] == 'word-prime-sums':
        sums = result['wordSums']
        return (type(sums['words']) is int and 0 < sums['words'] <= 9007199254740991
                and type(sums['total']) is int and 0 < sums['total'] <= 9007199254740991)
    if task['criterion']['kind'] == 'word-affine-count':
        pairs = result['wordPairs']
        return (pairs['opportunities'] > 0 and pairs['matches'] == pairs['opportunities']
                and int(pairs['expected']['numerator']) < pairs['opportunities'] * int(pairs['expected']['denominator']))
    return False


def verified_controls(task, document, folder):
    runner.validate(task)
    runner.fields(document, ('version', 'origins'), 'Origins document')
    runner.require(type(document['version']) is int and document['version'] == 1
                   and isinstance(document['origins'], list) and 1 <= len(document['origins']) <= 10,
                   'Unsupported or empty origins document')
    runner.require(task['criterion']['kind'] in ('measurement', 'exact-prefix', 'word-affine-count', 'word-prime-sums', 'language-score'), 'Controls require supported evaluation')
    checked = set()
    for value in document['origins']:
        control = validate_origin(value)
        fixture = control['task']
        runner.validate(fixture)
        runner.require('synthetic' in fixture['title'].lower(), 'Control task must be labeled synthetic')
        control_runes = {entry['rune'] for entry in fixture['alphabet']}
        runner.require(len(fixture['pages']) == 1
                       and sum(ch in control_runes for ch in fixture['pages'][0]['text']) <= 4096,
                       'Synthetic control exceeds its bound')
        for key in ('steps', 'alphabet'):
            runner.require(fixture[key] == task[key], 'Control uses a different ' + key)
        if task['criterion']['kind'] in ('measurement', 'language-score'):
            runner.require(fixture['criterion']['kind'] == 'exact-prefix'
                           and bool(fixture['criterion']['values'])
                           and len(fixture['criterion']['values']) == sum(
                               ch in control_runes for ch in fixture['pages'][0]['text']),
                           'Output comparison requires a complete synthetic exact-prefix control')
        else:
            runner.require(fixture['criterion'] == task['criterion'], 'Control uses a different criterion')
        saved = read_json(folder / 'controls' / (fixture['taskId'] + '.json'))
        runner.require(saved == fixture, 'Control file differs from the origin snapshot')
        identity = (fixture['taskId'], control['expected_result_sha256'])
        if identity not in checked:
            result = runner.run(fixture)
            runner.require(positive_control(fixture, result),
                           'Synthetic control failed its recovery property; target not run')
            digest = hashlib.sha256(stable(result).encode('utf-8')).hexdigest()
            runner.require(digest == control['expected_result_sha256'],
                           'Synthetic control result hash differs; target not run')
            checked.add(identity)
    return len(checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--origins', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        target, origins, output = args.task.resolve(), args.origins.resolve(), args.out.resolve()
        runner.require(target.parent == origins.parent, 'Task and origins must be in the same extracted folder')
        runner.require(not output.exists() and not args.out.is_symlink(), 'Output already exists')
        runner.require(output not in (target, origins, Path(__file__).resolve(), Path(runner.__file__).resolve()),
                       'Output cannot overwrite packaged inputs or runner')
        task = read_json(target)
        runner.require(task['criterion']['kind'] != 'language-score',
                       'Use verify_authored_language.py or verify_subset_controls.py so both control suites run')
        count = verified_controls(task, read_json(origins), target.parent)
        # No target transformation occurs before every control has passed.
        result = runner.run(task)
        payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
        print('Verified ' + str(count) + ' synthetic control(s); saved results to ' + str(args.out))
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, 'verify_controls: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
