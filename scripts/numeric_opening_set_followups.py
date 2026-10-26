"""Detached historical nine-opening browser replays; synthetic controls only.

All archived source arrays and decisions are audited by the shared numerical
source checker. No source record is installed and no manuscript task is run.
"""
import copy
import json
from pathlib import Path

import authored_finite_followups as authored
import browser_followups as fixed
import numeric_bank_followups as numeric
from research_questions import validate_research_questions

ROOT = numeric.ROOT
FAMILIES = numeric.FAMILIES
PAGES = numeric.PAGES


def identifier(record_id):
    fixed.require(record_id in FAMILIES, 'unknown numerical source record')
    return FAMILIES[record_id]['bankId'].removesuffix('-v1') + '-stream-nine-openings'


def criterion(record_id, root=ROOT, *, declared=None):
    declared = numeric.source(record_id, root) if declared is None else declared
    path = 'experiments/records/' + record_id + '/plan.json'
    raw = (Path(root) / path).read_bytes()
    fixed.require(numeric.digest(raw) == FAMILIES[record_id]['pins']['plan.json']
                  and any(pin['path'] == path and pin['sha256'] == numeric.digest(raw) for pin in declared['pins']),
                  'audited opening plan changed')
    plan = json.loads(raw)
    return {'kind': 'exact-prefix-set', 'openings': [
        {'id': opening['id'], 'values': opening['indices'][:]} for opening in plan['openings']]}


def candidate(record_id, root=ROOT, *, declared=None):
    declared = numeric.source(record_id, root) if declared is None else declared
    family = FAMILIES[record_id]
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': criterion(record_id, root, declared=declared),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'offset', 'values': list(range(29))},
                            {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}.items():
        rules[name] = specified(value)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': specified({'operations': [{'id': 'finite_key_bank', 'bankId': family['bankId'],
                'bankSha256': family['bankSha256'], 'reset': 'page'}]}),
            'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    fixed.require(len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode()) <= 12 * 1024,
                  'canonical opening-set card exceeds 12 KiB')
    fibonacci = ' Fibonacci residues repeat after 14 terms; the 29 named starting places include duplicates, not independent trials.' if family['bankId'] == 'fibonacci-v1' else ''
    return authored.construct_followup(root, card=card, identifier=identifier(record_id),
        title='Check nine known openings with the ' + family['label'] + ' stream',
        question='Does the fixed ' + family['label'] + ' stream recover any of nine named 12-rune openings at a page start?',
        scope_change='Replay the same nine ordered 12-rune openings, 29 starting offsets, subtraction and addition, and page restarts from the historical test. Include all 56 pages, recording rune-empty LP2-50 as no runes.' + fibonacci,
        limitation='Use the complete remaining tail of the stored 305-term sequence, with no wrap, skips or cross-page carry. There are 58 settings and 3,248 declared page cases, including 58 rune-empty cases; the historical test had 3,190 rune-bearing cases and 28,710 opening comparisons. The original historical finding is unchanged; this new browser replay has no results yet.' + fibonacci,
        motivation='Change rune numbers using ' + family['explanation'] + ', then compare each page opening with nine known passages. Only a complete 12-rune match counts. This repeats the earlier opening test; it does not compare language scores or add line and word restarts.')


def questions(record_id):
    return [{'id': identifier(record_id), 'state': 'open',
             'note': 'Replay the original nine-opening comparison in the browser. The historical result is unchanged; no new browser result is asserted.',
             'records': [], 'followup': identifier(record_id),
             'protocol': {'id': 'finite-settings-output', 'version': 1}}]


def proposed(record_id, root=ROOT):
    declared = numeric.source(record_id, root)
    result = copy.deepcopy(declared['record'])
    recipe, wanted = candidate(record_id, root, declared=declared), identifier(record_id)
    prior = [item for item in result.get('browser_followups', []) if item['id'] == wanted]
    fixed.require(len(prior) <= 1 and (not prior or numeric.semantic_recipe(prior[0]) == numeric.semantic_recipe(recipe)),
                  'existing numerical opening-set recipe changed')
    if not prior:
        result.setdefault('browser_followups', []).append(recipe)
    existing = [item for item in result.get('research_questions', []) if item['id'] == wanted]
    fixed.require(not existing or existing == questions(record_id), 'existing numerical opening-set question changed')
    if not existing:
        result.setdefault('research_questions', []).extend(questions(record_id))
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    fixed.require(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()) < 2 * 1024 * 1024,
                  'proposed source exceeds 2 MiB')
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare installed declarations without changing them')
    parser.add_argument('--output', type=Path, help='Write detached proposals inside outer qa-temp only')
    parser.add_argument('--no-directwrite', action='store_true', help='Explicitly retain the always-detached authoring mode')
    args = parser.parse_args()
    if args.output:
        destination = args.output.resolve()
        fixed.require(destination.is_relative_to((ROOT.parent.parent / 'qa-temp').resolve()),
                      'private output must stay inside outer qa-temp')
    values = {record_id: proposed(record_id) for record_id in FAMILIES}
    if args.check:
        for record_id, value in values.items():
            installed = json.loads((ROOT / 'experiments/records' / record_id / 'record.json').read_bytes())
            fixed.require(installed == value, 'installed numerical opening-set declarations differ: ' + record_id)
    if args.output:
        destination.mkdir(parents=True, exist_ok=True)
        for record_id, value in values.items():
            (destination / (record_id + '.json')).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps({'records': list(values), 'programsPerRecord': 58, 'pagesPerRecord': 56,
                      'casesPerRecord': 3248, 'runeBearingCasesPerRecord': 3190,
                      'historicalComparisonsPerRecord': 28710, 'targetExecutions': 0, 'installed': bool(args.check)}))


if __name__ == '__main__':
    main()
