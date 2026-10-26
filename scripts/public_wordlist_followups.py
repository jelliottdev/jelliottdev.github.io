"""Detached 43-key opening replay; audit saved prefixes, execute synthetic controls only.

The pinned certificate records an earlier 58-page ZIP comparison. This adapter
has not inspected that ZIP and never promotes its certificate to output receipts.
"""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path

import build_repeating_key_banks as banks
import authored_finite_followups as authored
import browser_followups as fixed
import finite_control_storage as storage
from research_questions import validate_research_questions

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'public-wordlist-vigenere'
BASE = 'experiments/records/' + RECORD
IDENTIFIER = 'public-wordlist-nine-openings'
PAGES = ['lp2-%02d' % n for n in range(56)]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
REVISION = 'd219a8099f8d24e52496e9ee3456ed9980893884'
ARCHIVE_SHA256 = '531db6fe93ae89e3dce5e4fa3a4d16647181c1b4bc0218bc8c3a59ef80541837'
OPENING_PLAN = 'experiments/records/lp2-known-vigenere-keys/plan.json'
OPENING_PLAN_SHA256 = '3636812c3a3666956a6d71aae5bda236d42a5371a60814d5fb1bc5a2762e634a'
RULE = 'P_j=(C_j-K_(j mod |K|)) mod 29, per page, punctuation and numbers do not advance the key'
PINS = {
    'plan.json': 'f988c9d2ec1b0040a59025253b23752721627edc081c6cc4659e6e8cb417107c',
    'results.json': '282804f80e5e31ee5e6982264935e4ceef031432ec626c4090bb6aa937820d0c',
    'run.py': '8dc8211ac0553c319922f176acef9110256e6c57f4d29c81247f0d6656d72cd3',
    'check.py': '422adf01a9253f373974b26e08610213ccb37818333179411b539941e650e3a0',
    'source-output-certificate.json': 'f9a6e3c6d9e78188ec3af224eea6f61a848f4c63b22d82f349c4776cc7ee7e2b',
}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def source(root=ROOT):
    """Verify every saved nine-rune prefix by inverse arithmetic, never decode a target."""
    root, pins = Path(root), {}
    def pinned(path, expected):
        target = (root / path).resolve()
        fixed.require(target.is_relative_to(root.resolve()), 'source pin escapes root')
        raw = target.read_bytes()
        fixed.require(sha(raw) == expected, 'source pin changed: ' + path)
        pins[path] = expected
        return raw
    raw = {name: pinned(BASE + '/' + name, digest) for name, digest in PINS.items()}
    plan, result, certificate = [json.loads(raw[name]) for name in ('plan.json', 'results.json', 'source-output-certificate.json')]
    record = json.loads((root / BASE / 'record.json').read_bytes())
    fixed.require(record['id'] == RECORD and record['status'] == 'published', 'source ownership changed')
    fixed.require(plan['schema'] == 'liberpedia-public-wordlist-vigenere-plan-v1'
                  and plan['source_repository'] == 'https://github.com/LiberPrimus/Failed-Attempts'
                  and plan['source_commit'] == REVISION and plan['source_archive_sha256'] == ARCHIVE_SHA256
                  and plan['source_archive'] == 'bruteforce/vigenere/vigenere-bruteforce-results.zip'
                  and plan['rule'] == RULE, 'source rule or archive identity changed')
    fixed.require(result['schema'] == 'liberpedia-public-wordlist-vigenere-results-v1'
                  and result['plan_sha256'] == PINS['plan.json'] and result['source_archive_sha256'] == ARCHIVE_SHA256
                  and result['opening_plan_sha256'] == OPENING_PLAN_SHA256, 'saved report links changed')
    for pin in record['reproduction']['inputs']:
        pinned(pin['path'], pin['sha256'])
    alphabet = fixed.alphabet(root)
    fixed.require(''.join(row['rune'] for row in alphabet) == RUNES, 'canonical alphabet changed')
    lookup = {rune: n for n, rune in enumerate(RUNES)}
    keys = plan['keys']
    fixed.require(type(keys) is list and len(keys) == 43
                  and [item['id'] for item in keys] == ['key-%02d' % n for n in range(1, 44)], 'complete ordered key identities changed')
    for key in keys:
        fixed.fields(key, ('id', 'runes'), 'source key')
        fixed.require(type(key['runes']) is str and 1 <= len(key['runes']) <= 256
                      and all(ch in lookup for ch in key['runes']), 'source key spelling is not canonical GP runes')
    vectors = {key['id']: [lookup[ch] for ch in key['runes']] for key in keys}
    fixed.require(len({tuple(v) for v in vectors.values()}) == 43, 'duplicate source keys')
    opening_plan = json.loads(pinned(OPENING_PLAN, OPENING_PLAN_SHA256))
    openings = []
    for opening in opening_plan['openings']:
        rows = list(csv.DictReader(io.StringIO(pinned(opening['source'], opening['sha256']).decode('utf-8-sig'))))
        values = [int(row['output_index']) for row in rows[:12]]
        fixed.require(values == opening['indices'] and len(values) == 12, 'opening source trace changed')
        openings.append({'id': opening['id'], 'values': values})
    fixed.require(len(openings) == 9, 'complete nine-opening set required')
    fixed.validate_prefix_set({'kind': 'exact-prefix-set', 'openings': openings})
    bundle = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    fixed.require(bundle['alphabet'] == alphabet, 'official alphabet differs')
    fixed.require([row['path'] for row in result['sources']] == ['text/' + pid + '.txt' for pid in PAGES], 'complete ordered source pages changed')
    streams = {}
    for pid, pin in zip(PAGES, result['sources']):
        text = pinned(pin['path'], pin['sha256']).decode('utf-8')
        current = json.loads((root / 'data/pages' / (pid + '.json')).read_bytes())
        fixed.require(current['id'] == pid and current['raw'] == text == next(p['raw'] for p in bundle['pages'] if p['id'] == pid), 'official input changed: ' + pid)
        streams[pid] = [lookup[ch] for ch in text if ch in lookup]
        fixed.require(type(pin['runes']) is int and pin['runes'] == len(streams[pid]), 'stored input length changed')
    fixed.require([pid for pid, values in streams.items() if not values] == ['lp2-50'], 'rune-empty scope changed')
    # The saved first nine runes suffice to rule out every full twelve-rune
    # opening here. Never invent the absent final three or a complete output.
    expected = [(pid, key['id']) for pid in PAGES for key in keys]
    fixed.require(len(result['cases']) == 2408 and [(c['page'], c['key']) for c in result['cases']] == expected, 'complete ordered case domain changed')
    prefix_runes = 0
    for case in result['cases']:
        pid, key_id = case['page'], case['key']
        text = case['first_nine_runes']
        fixed.require(type(text) is str and all(ch in lookup for ch in text), 'stored prefix spelling changed')
        saved = [lookup[ch] for ch in text]
        fixed.require(len(saved) == min(9, len(streams[pid])) and type(case['has_runes']) is bool
                      and case['has_runes'] == bool(streams[pid]), 'stored prefix length or empty marker changed')
        key = vectors[key_id]
        fixed.require(all((value + key[i % len(key)]) % 29 == streams[pid][i] for i, value in enumerate(saved)), 'stored prefix inverse arithmetic failed')
        fixed.require(not any(saved == o['values'][:9] for o in openings), 'saved nine-rune prefix cannot exclude the full opening')
        fixed.require(case['opening_matches'] == [], 'stored opening decision changed')
        prefix_runes += len(saved)
    fixed.require(plan['source_output_anchor'] == {'page': 'lp2-15', 'key_index': 0,
                  'first_nine_runes': next(c['first_nine_runes'] for c in result['cases'] if c['page'] == 'lp2-15' and c['key'] == 'key-01')}, 'public output anchor changed')
    for name, value in {'key_count': 43, 'page_count': 56, 'case_count': 2408, 'rune_bearing_cases': 2365, 'opening_comparisons': 21285, 'matched_cases': 0}.items():
        fixed.require(type(result[name]) is int and result[name] == value, 'stored coverage total changed: ' + name)
    fixed.require(certificate['schema'] == 'liberpedia-public-complete-output-certificate-v1'
                  and certificate['source_revision'] == REVISION and certificate['source_zip_sha256'] == ARCHIVE_SHA256
                  and certificate['page_files'] == 58 and certificate['keys_per_page'] == 43
                  and certificate['complete_matches'] == 2494 and certificate['published_lp2_00_55_matches'] == 2408
                  and list(certificate['page_sha256']) == ['lp2-%02d' % n for n in range(58)], 'historical certificate limits changed')
    for pid, digest in certificate['page_sha256'].items():
        pinned('text/' + pid + '.txt', digest)
    return {'record': record, 'keys': [{'id': key['id'], 'runes': key['runes'], 'indices': vectors[key['id']]} for key in keys],
            'criterion': {'kind': 'exact-prefix-set', 'openings': openings},
            'pins': [{'path': p, 'sha256': digest} for p, digest in sorted(pins.items())],
            'audit': {'declaredCases': 2408, 'runeBearingCases': 2365, 'emptyCases': 43,
                      'openingComparisons': 21285, 'savedPrefixRunesVerified': prefix_runes,
                      'completeSourceOutputsVerifiedHere': 0, 'sourceArchiveInspectedHere': False,
                      'certificateMeaning': 'Pinned record of an earlier 58-page ZIP comparison; not complete outputs or a newly verified ZIP comparison.'}}


def candidate(root=ROOT, *, declared=None):
    declared = source(root) if declared is None else declared
    bank = next(b for b in banks.prepare(root)['banks'] if b['id'] == 'public-wordlist-keys-v1')
    reference = {'bankId': bank['id'], 'bankSha256': bank['sha256'], 'start': 0, 'count': bank['total']}
    fixed.require({tuple(k) for k in banks.resolve(reference)} == {tuple(k['indices']) for k in declared['keys']}, 'bank differs from audited source keys')
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': copy.deepcopy(declared['criterion']),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'key', 'valuesFrom': reference}]}}.items():
        rules[name] = specified(value)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': specified({'operations': [{'id': 'repeating_key', 'direction': 'subtract', 'reset': 'page'}]}),
            'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    return authored.construct_followup(root, card=card, identifier=IDENTIFIER,
        title='Check nine known openings with 43 archived rune keys',
        question='Does any of the 43 archived rune keys recover one of nine complete 12-rune openings at a page start?',
        scope_change='Repeat the same 43 literal keys, subtraction, phase zero, page restarts and nine named openings on LP2-00-55. Retain rune-empty LP2-50 as 43 no-rune cases, excluded from opening comparisons.',
        limitation='Check all 2,408 page-and-key cases: 2,365 rune-bearing cases and 43 empty cases. The earlier negative finding covers 21,285 opening comparisons. This new browser replay has no results yet. It does not verify the separate 58-page ZIP comparison or test new keys, later starts, other restarts or language scores.',
        motivation='A public attempt tried these 43 rune sequences as repeating keys. Repeat its exact opening check in your browser, comparing complete 12-rune beginnings with nine known passages.')


def questions():
    return [{'id': IDENTIFIER, 'state': 'open', 'note': 'Replay the exact 43-key, nine-opening comparison in the browser. Historical findings remain unchanged; the separate source ZIP certificate is not imported as saved output.',
             'records': [], 'followup': IDENTIFIER, 'protocol': {'id': 'finite-settings-output', 'version': 1}}]


def proposed(root=ROOT):
    declared = source(root)
    result = copy.deepcopy(declared['record'])
    recipe = candidate(root, declared=declared)
    prior = [r for r in result.get('browser_followups', []) if r['id'] == IDENTIFIER]
    def semantic(value):
        value = copy.deepcopy(value)
        value['control'] = storage.expand(value['control'])
        return value
    fixed.require(len(prior) <= 1 and (not prior or semantic(prior[0]) == semantic(recipe)), 'existing wordlist recipe changed')
    if not prior:
        result.setdefault('browser_followups', []).append(recipe)
    owned = [q for q in result.get('research_questions', []) if q['id'] == IDENTIFIER]
    fixed.require(not owned or owned == questions(), 'existing wordlist question changed')
    if not owned:
        result.setdefault('research_questions', []).extend(questions())
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    fixed.require(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) < 2 * 1024 * 1024, 'wordlist proposal exceeds source bound')
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Audit sources and validate a detached proposal; never install it')
    parser.add_argument('--output', type=Path, help='Write detached proposal inside outer qa-temp only')
    args = parser.parse_args()
    if args.output:
        fixed.require(args.output.resolve().is_relative_to((ROOT.parent.parent / 'qa-temp').resolve()), 'private output must stay inside outer qa-temp')
    value = proposed()
    if args.output:
        destination = args.output.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        (destination / (RECORD + '.json')).write_bytes((json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
    print(json.dumps({'recordId': RECORD, 'followupId': IDENTIFIER, 'programs': 43, 'declaredCases': 2408,
                      'runeBearingCases': 2365, 'emptyCases': 43, 'openingComparisons': 21285,
                      'targetExecutions': 0, 'installed': False, 'detachedOutputWritten': bool(args.output)}))

if __name__ == '__main__':
    main()
