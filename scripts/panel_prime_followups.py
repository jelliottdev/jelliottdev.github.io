"""Prepare source-owned spiral-prime declarations; execute synthetic controls only."""
import copy
import hashlib
import json
from pathlib import Path

import authored_finite_followups as authored
import browser_followups as fixed
import browser_boundary_variations as boundary
from research_questions import validate_research_questions

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'lp2-panel-prime-openings'
PLAN_SHA256 = '7fafa7f3d121f3a55fbd2c5069722566bf5465b93f438fa9a1bc2b5b9ee74975'
PAGES = ['lp2-%02d' % n for n in range(56)]


def source(root=ROOT):
    """Fail closed on the original plan, printed spiral, and official raw text."""
    root = Path(root)
    raw = (root / 'experiments/records' / RECORD / 'plan.json').read_bytes()
    fixed.require(hashlib.sha256(raw).hexdigest() == PLAN_SHA256, 'source plan pin changed')
    plan = json.loads(raw)
    for item in plan['inputs']:
        actual = (root / item['path']).read_bytes()
        fixed.require(hashlib.sha256(actual).hexdigest() == item['sha256'], 'source input pin changed: ' + item['path'])
    fixed.require(plan['pages'] == PAGES and plan['offsets'] == list(range(16))
                  and plan['signs'] == [-1, 1] and plan['prefix_length'] == 12,
                  'source bounds changed')
    panel = json.loads((root / 'data/pages/lp2-15.json').read_bytes())['numbers']
    ledger = json.loads((root / 'exports/fibonacci-prime-panel.json').read_bytes())['rows']
    key = [row['prime'] for row in ledger]
    fixed.require(len(key) == 16 and key == plan['key'], 'source spiral key changed')
    for row in ledger:
        fixed.require(panel[row['row'] - 1][row['column'] - 1] == row['printed']
                      == abs(3301 - row['prime']), 'printed spiral does not reproduce key')
    bundle = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    fixed.require(bundle['alphabet'] == fixed.alphabet(root), 'official alphabet differs')
    official = {page['id']: page for page in bundle['pages']}
    for page in PAGES:
        text = (root / 'text' / (page + '.txt')).read_text(encoding='utf-8')
        current = json.loads((root / 'data/pages' / (page + '.json')).read_bytes())['raw']
        fixed.require(current == text == official[page]['raw'], 'official raw input differs: ' + page)
    return plan


def candidate(reset, root=ROOT):
    if reset == 'line':
        card = boundary.variants(candidate('page', root)['card'], operation_index=0,
                                 allowed_resets=['line'])[0]['card']
        return authored.construct_followup(root, card=card,
            identifier='panel-primes-line-reset-language',
            title='Restart the spiral-prime pattern at every written line',
            question='Does restarting the spiral-prime pattern at every written line produce outputs resembling the maintained language samples?',
            scope_change='Keep all 16 starting places, both directions and LP2-00–55 pages. Change only the repeating-key restart from each page to each written line.',
            limitation='A higher language score is a lead to inspect, not a reading. The pattern restarts at line breaks, but not at spaces or punctuation. No result for this extension is asserted.',
            motivation='Try the same spiral-derived pattern from its chosen starting place at each written line. This differs from restarting at every word or continuing through the whole page; repeating the spiral remains an assumption.')
    fixed.require(reset in ('page', 'word'), 'unknown restart rule')
    plan = source(root)
    key = [n % 29 for n in plan['key']]
    keys = [key[phase:] + key[:phase] for phase in plan['offsets']]
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve',
                        'unmapped': 'preserve', 'inputVersion': 'raw',
                        'evaluation': copy.deepcopy(fixed.LANGUAGE_CRITERION),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'key', 'values': keys},
                            {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}.items():
        rules[name] = specified(value)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': specified({'operations': [{'id': 'repeating_key', 'reset': reset}]}),
            'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    if reset == 'page':
        metadata = dict(identifier='panel-primes-language-comparison',
            title='Compare existing spiral-prime output with language samples',
            question='Do the existing spiral-prime outputs resemble the maintained language samples?',
            scope_change='Keep the original 16 starting places, both directions and LP2-00–55 pages. Compare complete output with language samples instead of checking nine fixed openings.',
            limitation='Language similarity is not a recovered reading. This is a new evaluation of existing outputs, not a new test of the spiral order or a result for other uses of the panel.',
            motivation='The sixteen numbers derived from the printed spiral have already been tried as a repeating key. Compare that saved output with language samples beyond its first twelve runes.')
    else:
        metadata = dict(identifier='panel-primes-word-reset-language',
            title='Restart the spiral-prime pattern at every word',
            question='Does restarting the spiral-prime pattern at every visible word produce outputs resembling the maintained language samples?',
            scope_change='Keep all 16 starting places, both directions and LP2-00–55 pages. Change only the repeating-key restart from each page to each visible word.',
            limitation='A higher language score is a lead to inspect, not a translation. Each non-rune mark ends a word. Repeating the spiral numbers is an assumption, not an instruction printed on the page.',
            motivation='Try the same spiral-derived number pattern with a different restart rule: begin again at every word instead of continuing through the page. No result for this extension is asserted.')
    return authored.construct_followup(root, card=card, **metadata)


def recipes(root=ROOT):
    return [candidate(reset, root) for reset in ('page', 'word', 'line')]


def questions():
    return [{'id': identifier, 'state': 'open', 'note': note, 'records': [],
             'followup': identifier, 'protocol': {'id': 'finite-settings-output', 'version': 1}}
            for identifier, note in [
                ('panel-primes-language-comparison', 'A new language comparison of complete existing outputs. The historical nine-opening result is unchanged; language similarity is not a reading.'),
                ('panel-primes-word-reset-language', 'Change only the key restart to every visible word. This bounded extension has no asserted result.'),
                ('panel-primes-line-reset-language', 'Keep the same spiral, starting places, directions and pages. Restart only at written line breaks instead of each page. This bounded extension has no asserted result.')]]


def build(root=ROOT):
    """Return a proposed record; never write the published source."""
    root = Path(root)
    record = json.loads((root / 'experiments/records' / RECORD / 'record.json').read_bytes())
    generated = recipes(root)
    installed = {recipe['id']: recipe for recipe in record.get('browser_followups', [])}
    for recipe in generated[:2]:
        fixed.require(recipe['id'] not in installed or installed[recipe['id']] == recipe,
                      'existing panel recipe changed: ' + recipe['id'])
    identifiers = {recipe['id'] for recipe in generated}
    result = copy.deepcopy(record)
    result['browser_followups'] = [r for r in record.get('browser_followups', []) if r['id'] not in identifiers] + generated
    result['research_questions'] = [q for q in record.get('research_questions', []) if q['id'] not in identifiers] + questions()
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    fixed.require(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) < 512 * 1024,
                  'proposed record exceeds runtime source bound')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check installed declarations against the source-owned generator')
    parser.add_argument('--output', type=Path, help='Write a private proposed record for review; never the source record')
    args = parser.parse_args()
    value = build()
    if args.check:
        installed = json.loads((ROOT / 'experiments/records' / RECORD / 'record.json').read_bytes())
        fixed.require(installed == value, 'installed panel follow-ups are stale')
    if args.output:
        destination = args.output.resolve()
        private = (ROOT.parent.parent / 'qa-temp').resolve()
        fixed.require(destination.is_relative_to(private), 'candidate output must be inside outer qa-temp')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps({'recordId': RECORD, 'finiteFollowups': 3, 'programsPerFollowup': 32, 'pages': 56,
                      'casesPerFollowup': 1792, 'emptyRuneCases': 32, 'targetExecutions': 0}))
