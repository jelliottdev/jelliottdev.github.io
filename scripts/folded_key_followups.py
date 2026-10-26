"""Detached browser replays of two exact historical folding variants.

Only full 184-rune synthetic Warning controls execute. Historical target
outputs/findings are neither recomputed nor imported as browser receipts.
"""
import copy
import hashlib
import json
from pathlib import Path

import authored_finite_followups as authored
import browser_followups as fixed
import build_repeating_key_banks as banks
import finite_control_storage as storage
import public_wordlist_followups as wordlist
from research_questions import validate_research_questions

ROOT = wordlist.ROOT
RECORD = 'rotating-folded-key-openings'
BASE = 'experiments/records/' + RECORD
VARIANTS = {'fold-repeat-endpoints': ('folded-repeat-endpoints-nine-openings', 618),
            'fold-skip-endpoints': ('folded-skip-endpoints-nine-openings', 532)}
PAGES = [pid for pid in wordlist.PAGES if pid != 'lp2-50']
SCRIPT_SHA256 = '82b697ab7938f17db8589f3c0b6f831fc80a770401f187a665d411e6b8435ba4'
CASE_DIGEST = '0c20c968a8c229abcbe817cd601fc640a74fd3a76b1ef699acea612125657878'


def folded_vectors(keys, variant):
    """Independent literal expansion; never call the historical source engine."""
    fixed.require(variant in VARIANTS, 'unknown folded historical variant')
    vectors, named = set(), 0
    for key in keys:
        key = tuple(key)
        back = tuple(reversed(key)) if variant == 'fold-repeat-endpoints' else tuple(reversed(key[1:-1]))
        whole = key + back
        period = next(n for n in range(1, len(whole) + 1)
                      if len(whole) % n == 0 and tuple(whole[i % n] for i in range(len(whole))) == whole)
        cycle = whole[:period]
        named += period
        vectors.update(cycle[i:] + cycle[:i] for i in range(period))
    return sorted(vectors), named


def source(root=ROOT):
    root = Path(root)
    declared = wordlist.source(root)
    record = json.loads((root / BASE / 'record.json').read_bytes())
    fixed.require(record['id'] == RECORD and record['status'] == 'published', 'folded source ownership changed')
    pins = {p['path']: p['sha256'] for p in declared['pins']}
    def pinned(path, digest):
        target = (root / path).resolve()
        fixed.require(target.is_relative_to(root.resolve()), 'folded source pin escapes root')
        raw = target.read_bytes()
        fixed.require(hashlib.sha256(raw).hexdigest() == digest, 'folded source pin changed: ' + path)
        fixed.require(path not in pins or pins[path] == digest, 'conflicting folded source pin')
        pins[path] = digest
        return raw
    script = record['reproduction']['script']
    fixed.require(script == BASE + '/run.py' and record['reproduction']['script_sha256'] == SCRIPT_SHA256, 'folded source script identity changed')
    pinned(script, SCRIPT_SHA256)
    for pin in record['reproduction']['inputs'] + record['reproduction']['outputs']:
        pinned(pin['path'], pin['sha256'])
    raw = {path: pinned(path, digest) for path, digest in banks.SCHEDULE_PINS.items()}
    manifest = json.loads(raw['experiments/suites/classical-key-schedules/manifest.json'])
    result = json.loads(raw[BASE + '/results.json'])
    fixed.require(result['schema'] == 'liberpedia-classical-key-schedules-results-v1'
                  and result['kind'] == RECORD and result['manifest_sha256'] == banks.SCHEDULE_PINS['experiments/suites/classical-key-schedules/manifest.json']
                  and result['key_plan_sha256'] == wordlist.PINS['plan.json']
                  and result['opening_plan_sha256'] == wordlist.OPENING_PLAN_SHA256
                  and result['case_digest_sha256'] == CASE_DIGEST, 'folded saved census identity changed')
    for key, value in {'key_count': 43, 'page_count': 55, 'opening_count': 9,
                       'configuration_count': 6272, 'comparison_count': 3104640}.items():
        fixed.require(type(result[key]) is int and result[key] == value, 'folded historical count changed: ' + key)
    fixed.require(manifest['source_keys_sha256'] == wordlist.PINS['plan.json']
                  and manifest['opening_vectors_sha256'] == wordlist.OPENING_PLAN_SHA256
                  and manifest['records'][RECORD]['variants'] == list(banks.VARIANTS), 'folded source rule domain changed')
    maintained = banks.prepare(root)
    selected = {}
    for variant, (_, count) in VARIANTS.items():
        bank = next(b for b in maintained['banks'] if b['id'] == 'public-wordlist-' + variant + '-v1')
        reference = dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=count)
        expected, named = folded_vectors([k['indices'] for k in declared['keys']], variant)
        actual = banks.resolve(reference)
        fixed.require(named == len(expected) == bank['total'] == count
                      and actual == [list(k) for k in expected], 'folded bank differs from the complete named variant')
        audit = bank['sourceAudit']
        fixed.require(audit['historicalSettings'] == audit['distinctFullVectors'] == 6272
                      and audit['overLimitVectors'] == 648 and audit['overLimitPeriods'] == [324]
                      and bank['historicalSettings'] == result['variants'][variant]['configurations'] == count,
                      'folded bank loses the historical domain boundary')
        fixed.require(all(pin in bank['sourcePins'] for pin in [{'path': p, 'sha256': h} for p, h in banks.SCHEDULE_PINS.items()]), 'folded bank lacks source pins')
        selected[variant] = dict(reference=reference, vectors=actual, audit=copy.deepcopy(audit))
    return {'record': record, 'criterion': copy.deepcopy(declared['criterion']), 'variants': selected,
            'pins': [{'path': p, 'sha256': h} for p, h in sorted(pins.items())],
            'audit': {'historicalSettings': 6272, 'browserVariantSettings': 1150,
                      'outsideBrowserSettings': 5122, 'unsupportedPeriod324Settings': 648,
                      'targetExecutions': 0, 'importedHistoricalReceipts': 0, 'caseDigest': CASE_DIGEST}}


def candidate(root=ROOT, variant='fold-repeat-endpoints', *, declared=None):
    fixed.require(variant in VARIANTS, 'unknown folded historical variant')
    declared = source(root) if declared is None else declared
    identifier, count = VARIANTS[variant]
    bank = next(b for b in banks.prepare(root)['banks'] if b['id'] == 'public-wordlist-' + variant + '-v1')
    complete = dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=count)
    fixed.require(declared['variants'][variant]['reference'] == complete
                  and declared['variants'][variant]['vectors'] == banks.resolve(complete),
                  'folded candidate must retain the complete audited named variant')
    opening_raw = (Path(root) / wordlist.OPENING_PLAN).read_bytes()
    fixed.require(hashlib.sha256(opening_raw).hexdigest() == wordlist.OPENING_PLAN_SHA256, 'folded opening source pin changed')
    expected_criterion = {'kind': 'exact-prefix-set', 'openings': [{'id': o['id'], 'values': o['indices']}
                          for o in json.loads(opening_raw)['openings']]}
    fixed.require(declared['criterion'] == expected_criterion, 'folded candidate changed the historical opening check')
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': copy.deepcopy(declared['criterion']),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'key', 'valuesFrom': copy.deepcopy(declared['variants'][variant]['reference'])}]}}.items():
        rules[name] = specified(value)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': specified({'operations': [{'id': 'repeating_key', 'direction': 'subtract', 'reset': 'page'}]}),
            'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    repeated = variant == 'fold-repeat-endpoints'
    title = 'Replay folded keys with ' + ('both end runes repeated' if repeated else 'the end runes used once')
    recipe = authored.construct_followup(root, card=card, identifier=identifier, title=title,
        question='Does a key read forward and backward ' + ('including both end runes' if repeated else 'without repeating its end runes') + ' recover one of nine known openings?',
        scope_change=f'Replay the historical {variant} variant: all {count} distinct full key cycles and starting places, subtraction, page restarts, 55 rune-bearing pages and nine fixed 12-rune openings. This is {count * 55:,} page-and-key cases.',
        limitation=f'This browser replay has no saved results yet. It repeats one named variant within the historical 6,272-setting test and does not import its output receipts or change its negative finding. The other folding variant and both rotating schedules are outside this recipe. It does not test general readability, new keys, later text positions, other arithmetic signs or other restart rules.',
        motivation='Read a key forward, then back, and repeat that sequence. ' + ('For a small ABC key, repeating the two end runes gives ABCCBA.' if repeated else 'For a small ABC key, using the end runes once gives ABCB.') + ' Try every starting place in that exact cycle and compare page beginnings with nine already-decoded passages.')
    recipe['control'] = storage.compact_pooled(recipe['control'])
    # Both the packed wire and its full exact controls must satisfy existing
    # budgets. No split, dropped member or raised limit is an allowed fallback.
    storage.expand(recipe['control'])
    authored.validate_recipe(recipe, root)
    return recipe


def questions():
    return [{'id': identifier, 'state': 'open', 'note': f'Replay the complete historical {variant} variant in the browser. The original finding remains unchanged; historical outputs are not imported as browser results.',
             'records': [], 'followup': identifier, 'protocol': {'id': 'finite-settings-output', 'version': 1}}
            for variant, (identifier, _) in VARIANTS.items()]


def proposed(root=ROOT):
    declared = source(root)
    result = copy.deepcopy(declared['record'])
    def semantic(recipe):
        value = copy.deepcopy(recipe)
        value['control'] = storage.expand(value['control'])
        return value
    for variant in VARIANTS:
        recipe = candidate(root, variant, declared=declared)
        old = [r for r in result.get('browser_followups', []) if r['id'] == recipe['id']]
        fixed.require(len(old) <= 1 and (not old or semantic(old[0]) == semantic(recipe)), 'existing folded recipe changed')
        if not old:
            result.setdefault('browser_followups', []).append(recipe)
    for question in questions():
        old = [q for q in result.get('research_questions', []) if q['id'] == question['id']]
        fixed.require(not old or old == [question], 'existing folded question changed')
        if not old:
            result.setdefault('research_questions', []).append(question)
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    for indent in (None, 2):
        encoded = json.dumps(result, ensure_ascii=False, indent=indent, separators=(',', ':') if indent is None else None).encode()
        fixed.require(len(encoded) + 1 <= 2 * 1024 * 1024, 'complete folded proposal exceeds the unchanged source byte bound')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate a detached proposal; never install it')
    parser.parse_args()
    proposal = proposed()
    print(json.dumps({'recordId': RECORD, 'variants': {v: {'programs': n, 'pages': 55, 'cases': n * 55} for v, (_, n) in VARIANTS.items()},
                      'historicalSettings': 6272, 'browserSettings': 1150, 'targetExecutions': 0, 'importedHistoricalReceipts': 0,
                      'minifiedBytes': len(json.dumps(proposal, ensure_ascii=False, separators=(',', ':')).encode()),
                      'prettyBytes': len(json.dumps(proposal, ensure_ascii=False, indent=2).encode()) + 1, 'installed': False}))
