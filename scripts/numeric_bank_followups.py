"""Propose four source-owned number-stream restart searches; synthetic runs only.

This detached authoring tool never installs records or runs manuscript targets.
It independently audits every archived output before constructing new language
comparisons. The earlier nine-opening decisions remain historical findings.
"""
import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path

import authored_finite_followups as authored
import browser_boundary_variations as boundary
import browser_followups as fixed
import finite_control_storage as storage
import finite_sequence_banks as banks
from research_questions import validate_research_questions

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['lp2-%02d' % n for n in range(56)]
FAMILIES = {
    'lp2-prime-minus-one-openings': {
        'bankId': 'prime-minus-one-v1', 'bankSha256': '61add0f42e87c8d2b71a32e54d1b005ac4ca77c5b818bf52d97600da248988dc',
        'label': 'prime-minus-one', 'explanation': 'prime numbers with one subtracted from each',
        'pins': {'plan.json': '61013e70fe327294168831fc53889c4cbad54e5bd22e801b6b8b06296973917a', 'results.json': 'c2e1572cb2a10ac53cdb8bc3c0f9ffd46a494278c5cd97fcf8f23a6d86aa836b', 'run.py': '72175c2a653105f325e22d28be3458646ae7ed3dd5f868cfe80870ef27ef4f79', 'check.py': '58a9311e6a622374b5d087dcf185525d19703a8d70c15140913f031d4fc8ce8f'}},
    'lp2-prime-openings': {
        'bankId': 'prime-v1', 'bankSha256': '3e0668ec3551b8dce1245a918c614b6861b80d210fe492d29c9b261439b21bcc',
        'label': 'prime-number', 'explanation': 'successive prime numbers',
        'pins': {'plan.json': '7348fa88c1300e504d099c1027fa5ef8c03ed28f686fe1df29bee77cd6512274', 'results.json': '3f7ebb3f7e5f2ee2cf2ddf518a5546b76d11056d96b3a6dcbb3c8930e61240f3', 'run.py': '4f45a282ea5137ee6da3323357ecaa3698ee765b716e8dfcac930d3afe205635', 'check.py': 'b3c1a37cd3fe2a52cfcbbce26d748188536dbadeab7de38e49751ce99a96405a'}},
    'lp2-fibonacci-openings': {
        'bankId': 'fibonacci-v1', 'bankSha256': '6e3475d825d2da7975e139407b1af1c7f2d908deb0c5ab0c91db39ac2b4c31b8',
        'label': 'Fibonacci', 'explanation': 'Fibonacci numbers, starting with zero and one and adding the previous two numbers',
        'pins': {'plan.json': '260b0040349ce426064d87c5d0b51481b25f29cbb7fd43560d55c2e7dec9812b', 'results.json': 'f29635492567ea137d6d9b45a2079dd5f33b9a9ea98262dde9a1b97a66c7af26', 'run.py': '09caa98d544adea0c3cd79f736d114295ec798e3be4f249fbbad8ea03ed075b5', 'check.py': '0121421c0fbd1c2aa31f75c6e2e1e72e28c21057a7b26a066054b24b7082279a'}},
    'lp2-totient-openings': {
        'bankId': 'totient-v1', 'bankSha256': '822e947c36fd3ebf492ab5e8e2d86f287e2348968b99ccccb1aa4b4edf9dc75d',
        'label': 'totient', 'explanation': 'totients: count the positive integers up to each number that have no common factor with it greater than one',
        'pins': {'plan.json': 'cb09778b854deedfa473486798b968d9315b60f0e8a13fd697b84f34ca890324', 'results.json': '15e2a0e36e139d8cdcd0652225566b9071f81e79ba0efc72606f697730b225ae', 'run.py': 'c3ec24c0961e29b34f6c2592eea5c5b18a72f5ff77dd1df759af3fcd1408661f', 'check.py': '7fe64c64833d775d10c43d6796a89c6381d2d8d5d73253e9b916e000b05baaac'}}}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(record_id):
    fixed.require(record_id in FAMILIES, 'unknown numerical source record')
    return FAMILIES[record_id]['bankId'].removesuffix('-v1') + '-stream-reset-language'


def independent_terms(bank_id, count):
    """Arithmetic oracle independent of the maintained finite bank/compiler."""
    if bank_id in ('prime-v1', 'prime-minus-one-v1'):
        terms, n = [], 2
        while len(terms) < count:
            if all(n % d for d in range(2, math.isqrt(n) + 1)):
                terms.append(n - (bank_id == 'prime-minus-one-v1'))
            n += 1
        return terms
    if bank_id == 'fibonacci-v1':
        terms, a, b = [], 0, 1
        for _ in range(count):
            terms.append(a)
            a, b = b, a + b
        return terms
    fixed.require(bank_id == 'totient-v1', 'unknown independent sequence')
    return [sum(math.gcd(k, n) == 1 for k in range(1, n + 1)) for n in range(1, count + 1)]


def source(record_id, root=ROOT):
    """Pin source files, official inputs and all 3,190 complete saved arrays."""
    root, family = Path(root), FAMILIES[record_id]
    base = 'experiments/records/' + record_id
    pins = {}
    def read_pin(path, expected):
        target = (root / path).resolve()
        fixed.require(target.is_relative_to(root.resolve()), 'source pin escapes root')
        raw = target.read_bytes()
        fixed.require(digest(raw) == expected, 'source pin changed: ' + path)
        pins[path] = expected
        return raw
    frozen = {name: read_pin(base + '/' + name, sha) for name, sha in family['pins'].items()}
    plan, result = json.loads(frozen['plan.json']), json.loads(frozen['results.json'])
    record = json.loads((root / base / 'record.json').read_bytes())
    fixed.require(record['id'] == record_id and record['status'] == 'published', 'source ownership changed')
    fixed.require(plan['pages'] == PAGES and plan['offsets'] == list(range(29)) and plan['signs'] == [-1, 1]
                  and plan['prefix_length'] == 12 and len(plan['openings']) == 9, 'historical search bounds changed')
    fixed.require(result['plan_sha256'] == family['pins']['plan.json'], 'historical plan link changed')
    for pin in plan['inputs']:
        read_pin(pin['path'], pin['sha256'])
    for pin in record['reproduction']['inputs']:
        read_pin(pin['path'], pin['sha256'])
    alphabet = fixed.alphabet(root)
    bundle = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    fixed.require(bundle['alphabet'] == alphabet, 'official alphabet differs')
    lookup = {row['rune']: n for n, row in enumerate(alphabet)}
    streams = {}
    for page_id in PAGES:
        raw = (root / 'text' / (page_id + '.txt')).read_bytes()
        text = raw.decode('utf-8')
        page = json.loads((root / 'data/pages' / (page_id + '.json')).read_bytes())
        fixed.require(text == page['raw'] == next(p['raw'] for p in bundle['pages'] if p['id'] == page_id),
                      'official raw input differs: ' + page_id)
        streams[page_id] = [lookup[ch] for ch in text if ch in lookup]
        pins['text/' + page_id + '.txt'] = digest(raw)
    terms = independent_terms(family['bankId'], max(map(len, streams.values())) + 28)
    fixed.require(len(terms) == 305 and result['shifts'] == terms, 'archived numerical sequence differs')
    bank = banks.get(family['bankId'], family['bankSha256'])
    fixed.require(bank['values'] == [n % 29 for n in terms], 'maintained bank differs from the independent historical vector')
    fixed.require(result['page_lengths'] == {p: len(v) for p, v in streams.items()}
                  and result['empty_pages'] == ['lp2-50'], 'archived input lengths differ')
    openings = []
    for opening in plan['openings']:
        raw = read_pin(opening['source'], opening['sha256'])
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        values = [int(row['output_index']) for row in rows[:12]]
        fixed.require(values == opening['indices'], 'source opening differs: ' + opening['id'])
        openings.append((opening['id'], values))
    fixed.require(len({name for name, _ in openings}) == 9, 'source opening identities repeat')
    expected = {(p, offset, sign) for p, stream in streams.items() if stream for offset in range(29) for sign in (-1, 1)}
    seen, matching, distinct = set(), 0, set()
    for case in result['cases']:
        identity = (case['page'], case['offset'], case['sign'])
        fixed.require(identity in expected and identity not in seen, 'archived case missing, duplicated or outside scope')
        seen.add(identity)
        output, stream = case['output_indices'], streams[case['page']]
        fixed.require(len(output) == len(stream), 'archived output length differs')
        for n, value in enumerate(output):
            fixed.require(type(value) is int and 0 <= value < 29
                          and (value - case['sign'] * terms[n + case['offset']]) % 29 == stream[n],
                          'archived output fails independent inverse arithmetic')
        matches = [name for name, values in openings if output[:12] == values]
        fixed.require(case['matching_openings'] == matches, 'archived opening decision differs')
        matching += bool(matches)
        distinct.add((case['page'], tuple(output)))
    fixed.require(seen == expected and result['case_count'] == len(seen) == 3190
                  and result['comparison_count'] == 28710 and result['matching_case_count'] == matching == 0,
                  'archived comparison totals differ')
    if 'distinct_page_outputs' in result:
        fixed.require(result['distinct_page_outputs'] == len(distinct), 'archived distinct-output count differs')
    if family['bankId'] == 'fibonacci-v1':
        cycle = [v % 29 for v in terms[:14]]
        fixed.require(result['residue_period'] == 14 and result['residue_cycle'] == cycle
                      and all(terms[n] % 29 == cycle[n % 14] for n in range(len(terms)))
                      and all((cycle[n], cycle[(n + 1) % 14]) != (0, 1) for n in range(1, 14)),
                      'Fibonacci residue cycle changed')
    return {'record': record, 'bank': bank, 'pins': [{'path': p, 'sha256': sha} for p, sha in sorted(pins.items())],
            'audit': {'historicalCases': len(seen), 'historicalComparisons': 28710, 'historicalMatchingCases': matching,
                      'historicalOutputIndices': sum(len(c['output_indices']) for c in result['cases'])}}


def candidate(record_id, root=ROOT, *, declared=None):
    declared = source(record_id, root) if declared is None else declared
    family, specified = FAMILIES[record_id], lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': copy.deepcopy(fixed.LANGUAGE_CRITERION),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'offset', 'values': list(range(29))},
                            {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}.items():
        rules[name] = specified(value)
    baseline = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
                'method': specified({'operations': [{'id': 'finite_key_bank', 'bankId': family['bankId'],
                    'bankSha256': family['bankSha256'], 'reset': 'page'}]}),
                'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    card = boundary.family(baseline, operation_index=0, allowed_resets=['page', 'line', 'word'])['card']
    fixed.require(len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode()) <= 12 * 1024,
                  'canonical bank card exceeds 12 KiB')
    fibonacci_note = ' Fibonacci residues repeat after 14 terms; the 29 named starting places include duplicates, not independent trials.' if family['bankId'] == 'fibonacci-v1' else ''
    return authored.construct_followup(root, card=card, identifier=identifier(record_id),
        title='Try the ' + family['label'] + ' stream with three restart rules',
        question='Do outputs from the fixed ' + family['label'] + ' stream resemble the maintained language samples across 29 starting places, both arithmetic directions and page, line or word restarts?',
        scope_change='Keep the original 29 starting places, addition and subtraction, and LP2-00-55. Include page restarts and add line and word restarts. Compare language samples instead of the nine fixed historical openings.' + fibonacci_note,
        limitation='Use the stored 305-term sequence once per restart, without wrapping, skipped runes or carry between pages. These new comparisons have no results yet.' + fibonacci_note,
        motivation='Change successive rune numbers using ' + family['explanation'] + '. Try 29 starting places, adding or subtracting, and restart at each page, line or word. The earlier test checked nine fixed openings; this new comparison asks about language similarity, not a proved reading.')


def questions(record_id):
    return [{'id': identifier(record_id), 'state': 'open', 'note': 'A new language comparison with three restart rules. Earlier nine-opening findings are unchanged; no output or reading is asserted.',
             'records': [], 'followup': identifier(record_id), 'protocol': {'id': 'finite-settings-output', 'version': 1}}]


def semantic_recipe(recipe):
    value = copy.deepcopy(recipe)
    value['control'] = storage.expand(value['control'])
    return value


def proposed(record_id, root=ROOT):
    declared = source(record_id, root)
    result = copy.deepcopy(declared['record'])
    recipe, wanted = candidate(record_id, root, declared=declared), identifier(record_id)
    prior = [r for r in result.get('browser_followups', []) if r['id'] == wanted]
    fixed.require(len(prior) <= 1 and (not prior or semantic_recipe(prior[0]) == semantic_recipe(recipe)), 'existing numerical-bank recipe changed')
    result['browser_followups'] = [r for r in result.get('browser_followups', []) if r['id'] != wanted] + [recipe]
    prior_questions = [q for q in result.get('research_questions', []) if q['id'] == wanted]
    fixed.require(not prior_questions or prior_questions == questions(record_id), 'existing numerical-bank question changed')
    result['research_questions'] = [q for q in result.get('research_questions', []) if q['id'] != wanted] + questions(record_id)
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    fixed.require(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()) < 2 * 1024 * 1024,
                  'proposed source exceeds 2 MiB')
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare installed declarations to the deterministic proposal; never install it')
    parser.add_argument('--output', type=Path, help='Write detached proposed records as files only inside outer qa-temp')
    args = parser.parse_args()
    values = {record_id: proposed(record_id) for record_id in FAMILIES}
    if args.check:
        for record_id, value in values.items():
            installed = json.loads((ROOT / 'experiments/records' / record_id / 'record.json').read_bytes())
            fixed.require(installed == value, 'installed numerical-bank declarations differ: ' + record_id)
    if args.output:
        destination = args.output.resolve()
        fixed.require(destination.is_relative_to((ROOT.parent.parent / 'qa-temp').resolve()), 'private output must stay inside outer qa-temp')
        destination.mkdir(parents=True, exist_ok=True)
        for record_id, value in values.items():
            (destination / (record_id + '.json')).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps({'records': list(values), 'programsPerRecord': 174, 'pagesPerRecord': 56,
                      'casesPerRecord': 9744, 'targetExecutions': 0, 'installed': bool(args.check)}))


if __name__ == '__main__':
    main()
