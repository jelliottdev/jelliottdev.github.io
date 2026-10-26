"""Reproduce a declared remaining-page check after both maintained control suites.

python verify_subset_controls.py --task task.json --origins origins.json --controls runner-controls.json --out results.json
Only fixed sibling modules and the Python standard library are used. No network.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

import research_runner as runner
import verify_controls as authored
import verify_plan_controls as generic

PAGE = re.compile(r'(?:lp1-(?:0[0-9]|1[0-6])|lp2-(?:[0-4][0-9]|5[0-7]))')
FINITE_AUDIT_SHA256 = 'b7d76511d4dbc464468131382303944c1c7f88e8287d9df80024514ddb123de7'


def finite_relation(task, relation):
    # This fixed sibling is bundled only for authored finite-member packages.
    source = (Path(__file__).resolve().parent / 'verify_finite_search.py').read_bytes()
    runner.require(len(source) <= 100000 and hashlib.sha256(source).hexdigest() == FINITE_AUDIT_SHA256,
                   'The fixed finite member guard changed')
    import verify_finite_search as finite
    runner.fields(relation, ('kind', 'card', 'settings', 'declaredPages', 'remainingPages'), 'Finite source relation')
    card, settings = relation['card'], relation['settings']
    operations, axes, _ = finite.declaration(card, max_cases=76800, check_expanded_budget=False)
    declared, current = card['scope']['value']['pages'], [page['id'] for page in task['pages']]
    runner.require(relation['declaredPages'] == declared and relation['remainingPages'] == current
                   and current == [page for page in declared if page in current], 'Finite source pages changed')
    runner.require(isinstance(settings, list) and len(settings) == len(axes), 'Incomplete finite member settings')
    selected = copy.deepcopy(operations)
    for setting, axis in zip(settings, axes):
        runner.fields(setting, ('operation', 'name', 'value'), 'Finite member setting')
        runner.require(setting['operation'] == axis['operation'] and setting['name'] == axis['name']
                       and any(finite.stable(setting['value']) == finite.stable(v) for v in axis['values']),
                       'Settings are outside the original finite declaration')
        selected[axis['operation']][axis['name']] = setting['value']
    rules = copy.deepcopy(card['rules'])
    rules['searchBounds'] = {'status': 'not_applicable'}
    runner.require(rules['inputVersion']['status'] == 'specified'
                   and rules['inputVersion']['value'] in ('raw', 'reviewed')
                   and rules['evaluation']['status'] == 'specified', 'Finite source needs exact input and evaluation')
    criterion = rules['evaluation']['value']
    if criterion == 'measurement':
        criterion = {'kind': 'measurement'}
    runner.require(finite.stable(finite.compile_steps(selected, rules)) == finite.stable(task['steps'])
                   and finite.stable(criterion) == finite.stable(task['criterion']), 'Finite member program changed')


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
            runner.require(isinstance(relation, dict), 'Invalid scope relation')
            if relation.get('kind') == 'finite-settings-member':
                finite_relation(task, relation)
                subsets += 1
                original = {key: value for key, value in item.items() if key != 'scopeRelation'}
                authored.validate_origin(original)
                result.append(original)
                continue
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


def verified_authored_controls(task, document, folder):
    """A validated finite relation admits its own full known-answer witness.

    The target's acceptance prefix stays unchanged. Fixed recipes continue to
    require their original matching criterion through the existing guard.
    """
    original = origins_without_relations(task, document)
    checked = 0
    for entry, clean in zip(document['origins'], original['origins']):
        if entry.get('scopeRelation', {}).get('kind') != 'finite-settings-member':
            checked += authored.verified_controls(task, {'version': 1, 'origins': [clean]}, folder)
            continue
        control = authored.validate_origin(clean)
        fixture = control['task']
        runner.validate(fixture)
        runes = {row['rune'] for row in fixture['alphabet']}
        count = sum(ch in runes for page in fixture['pages'] for ch in page['text'])
        runner.require('synthetic' in fixture['title'].lower() and len(fixture['pages']) == 1
                       and 1 <= count <= 256 and fixture['steps'] == task['steps']
                       and fixture['alphabet'] == task['alphabet']
                       and fixture['criterion']['kind'] == 'exact-prefix'
                       and len(fixture['criterion']['values']) == count,
                       'Finite control must check its complete synthetic output')
        saved = authored.read_json(folder / 'controls' / (fixture['taskId'] + '.json'))
        runner.require(saved == fixture, 'Control file differs from finite origin snapshot')
        result = runner.run(fixture)
        runner.require(authored.positive_control(fixture, result)
                       and hashlib.sha256(authored.stable(result).encode('utf-8')).hexdigest()
                       == control['expected_result_sha256'], 'Finite full-output control failed')
        checked += 1
    return checked


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
        verified_authored_controls(task, authored.read_json(origins), target.parent)
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
