"""Reproduce a declared remaining-page check after both maintained control suites.

python verify_subset_controls.py --task task.json --origins origins.json --controls runner-controls.json --out results.json
Only fixed sibling modules and the Python standard library are used. No network.
"""
import argparse
import json
from pathlib import Path
import re

import research_runner as runner
import verify_controls as authored
import verify_plan_controls as generic

PAGE = re.compile(r'(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))')


def origins_without_relations(task, document):
    runner.fields(document, ('version', 'origins'), 'Origins document')
    runner.require(type(document['version']) is int and document['version'] == 1
                   and isinstance(document['origins'], list) and 1 <= len(document['origins']) <= 10,
                   'Invalid origins document')
    current = [page['id'] for page in task['pages']]
    result, subsets = [], 0
    for item in document['origins']:
        runner.require(isinstance(item, dict), 'Invalid origin entry')
        if 'scopeRelation' in item:
            relation = item['scopeRelation']
            runner.fields(relation, ('kind', 'declaredPages', 'remainingPages'), 'Scope relation')
            declared, remaining = relation['declaredPages'], relation['remainingPages']
            runner.require(relation['kind'] == 'remaining-pages'
                           and isinstance(declared, list) and isinstance(remaining, list)
                           and 1 <= len(remaining) < len(declared) <= 75,
                           'Invalid remaining-page scope')
            for values in (declared, remaining):
                runner.require(all(isinstance(v, str) and PAGE.fullmatch(v) for v in values),
                               'Invalid declared page identity')
                runner.require(len(set(values)) == len(values) and values == sorted(values),
                               'Repeated or reordered declared pages')
            runner.require(remaining == current and all(page in declared for page in remaining),
                           'Scope relation changed the actual target pages')
            subsets += 1
        original = {key: value for key, value in item.items() if key != 'scopeRelation'}
        authored.validate_origin(original)
        result.append(original)
    runner.require(subsets > 0, 'A remaining-page relation is required')
    return {'version': 1, 'origins': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--origins', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        target, origins, controls, output = (p.resolve() for p in
                                             (args.task, args.origins, args.controls, args.out))
        runner.require(target.parent == origins.parent == controls.parent,
                       'Task, origins and runner controls must share one extracted folder')
        runner.require(not output.exists() and not args.out.is_symlink(), 'Output already exists')
        inputs = (target, origins, controls, Path(__file__).resolve(), Path(runner.__file__).resolve(),
                  Path(authored.__file__).resolve(), Path(generic.__file__).resolve())
        runner.require(output not in inputs, 'Output cannot overwrite packaged inputs or guards')
        task = authored.read_json(target)
        runner.validate(task)
        original = origins_without_relations(task, authored.read_json(origins))
        authored.verified_controls(task, original, target.parent)
        generic.verified_controls(task, authored.read_json(controls))
        # Neither suite executes the target; all controls must finish first.
        result = runner.run(task)
        payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
        print('Verified authored and task-bound controls; saved results to ' + str(args.out))
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, 'verify_subset_controls: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
