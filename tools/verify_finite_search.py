"""Offline audit of a finite-search-snapshot-v1. Never runs a missing case.

python tools/verify_finite_search.py snapshot.json
The snapshot pins supplied inputs and receipts, not their public authenticity or
the completeness of today's public archive. No network or third-party packages.
"""
import argparse
import copy
from datetime import datetime
from decimal import Decimal
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

import research_runner as runner

MAX_BYTES = 8 * 1024 * 1024
HEX = re.compile(r'^[a-f0-9]{64}$')
RULES = ('representation', 'wordBoundaries', 'boundaryMode', 'unmapped',
         'inputVersion', 'evaluation', 'reset', 'initialState', 'searchBounds',
         'searchProtocol', 'exceptionalCases')
CLASSIFIED_ALIASES = set(('decipher|decipher the text|decipher lp2|decrypt|decrypt the text|decrypt lp2|solve lp2|solving lp2|solving|solve liber primus|find readable text|find plaintext|recover plaintext|produce readable text|find readable plaintext|measure|test a pattern|test a statistical effect|test statistical effect|measure a pattern|test a statistical pattern|reproduce|reproduce a result|reproduce an existing result|replicate a result|rerun a result|explain|explain a feature|explain a manuscript feature|verify source material|verify the source|check source material|verify a transcription|check a transcription').split('|'))
PROVENANCE = ('Supplied source identities and dates are retained unchanged. Replay verifies the computation, '
              'not authorship, publication, public availability or historical timing.')
LOOKUP = ('The lookup status recorded when this snapshot was assembled. '
          'It is not an offline proof that no other public work exists.')
LIMIT = ('Only these declared programs, the exact prefix and these pinned texts are covered. '
         'Missing cases are not covered by the packaged receipts; they are not established as new work. '
         'A matching opening is not a complete reading.')
require, fields, integer = runner.require, runner.fields, runner.integer


def stable(value):
    """The existing JS stable serializer: sorted UTF-16 keys + JSON numbers.

    Scientific receipts contain a floating-point IoC. Python's default JSON
    spelling (0.0, e-07) differs from JavaScript's (0, e-7).
    """
    if value is None:
        return 'null'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if type(value) is int:
        require(abs(value) <= 9007199254740991, 'Unsupported unsafe integer')
        return str(value)
    if type(value) is float:
        require(math.isfinite(value), 'Nonfinite number')
        if value == 0:
            return '0'
        text = repr(value).lower()
        if 1e-6 <= abs(value) < 1e21:
            return format(Decimal(text), 'f').rstrip('0').rstrip('.') if '.' in format(Decimal(text), 'f') else format(Decimal(text), 'f')
        if 'e' not in text:
            text = format(value, '.16e')
        mantissa, exponent = text.split('e')
        mantissa = mantissa.rstrip('0').rstrip('.') if '.' in mantissa else mantissa
        number = int(exponent)
        return mantissa + 'e' + ('+' if number >= 0 else '') + str(number)
    if isinstance(value, str):
        value.encode('utf-8', errors='strict')
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return '[' + ','.join(stable(item) for item in value) + ']'
    require(isinstance(value, dict), 'JSON data required')
    return '{' + ','.join(stable(key) + ':' + stable(value[key])
                          for key in sorted(value, key=lambda key: key.encode('utf-16-be'))) + '}'


def digest(value):
    return hashlib.sha256(stable(value).encode('utf-8')).hexdigest()


def bounded(value, depth=0, budget=None):
    budget = budget if budget is not None else [0]
    budget[0] += 1
    require(depth <= 24 and budget[0] <= 500000, 'Snapshot structure exceeds bounds')
    if isinstance(value, dict):
        require(all(isinstance(k, str) and k not in ('__proto__', 'constructor', 'prototype') for k in value), 'Unsafe JSON key')
        for child in value.values():
            bounded(child, depth + 1, budget)
    elif isinstance(value, list):
        for child in value:
            bounded(child, depth + 1, budget)
    else:
        require(value is None or type(value) in (str, int, float, bool), 'JSON scalar required')
    return value


def field(value):
    require(isinstance(value, dict) and value.get('status') in ('specified', 'unspecified', 'not_applicable', 'unrestricted'), 'Invalid card field')
    fields(value, ('status', 'value') if value['status'] == 'specified' else ('status',), 'Card field')
    return value


def literal(name, value):
    if name in ('a', 'b'):
        require(integer(value, 0, 28), 'Invalid affine alternative')
    elif name in ('reset', 'unit'):
        require(value in ('page', 'line', 'word'), 'Invalid boundary alternative')
    elif name == 'direction':
        require(value in ('add', 'subtract'), 'Invalid arithmetic alternative')
    elif name in ('key', 'interrupts'):
        require(isinstance(value, list) and 1 <= len(value) <= (20000 if name == 'key' else 29)
                and all(integer(v, 0, 28) for v in value), 'Invalid GP index alternative')
        if name == 'interrupts':
            require(value == sorted(set(value)), 'Interrupters must be sorted and unique')
    else:
        raise ValueError('Unsupported declared parameter')


def declaration(card, *, max_cases=4096, check_expanded_budget=True):
    """Shared declaration grammar; historical v1 budgets remain the defaults."""
    require(type(max_cases) is int and 1 <= max_cases <= 76800 and type(check_expanded_budget) is bool, 'Invalid audit budgets')
    fields(card, ('version', 'outcome', 'method', 'scope', 'rules', 'unresolved'), 'Original card')
    require(type(card['version']) is int and card['version'] == 1 and len(stable(card).encode('utf-8')) <= 12000, 'Invalid original card version/size')
    for key in ('outcome', 'method', 'scope'):
        field(card[key])
    if card['outcome']['status'] == 'specified':
        fields(card['outcome']['value'], ('outcomeId', 'detail'), 'Outcome')
        require(card['outcome']['value']['outcomeId'] in ('decipher', 'measure', 'reproduce', 'explain', 'verify_source', 'unclassified')
                and isinstance(card['outcome']['value']['detail'], str), 'Unsupported outcome')
        if card['outcome']['value']['outcomeId'] == 'unclassified':
            alias = re.sub(r'[.!?]$', '', card['outcome']['value']['detail'].strip().lower()).strip()
            require(alias not in CLASSIFIED_ALIASES, 'Noncanonical outcome alias')
    fields(card['rules'], RULES, 'Rules')
    for value in card['rules'].values():
        field(value)
        require(value['status'] != 'unrestricted', 'Unrestricted conditions are unsupported')
    require(card['unresolved'] == [], 'Unresolved conditions cannot be ignored')
    require(card['method']['status'] == 'specified' and card['scope']['status'] == 'specified', 'Exact method/scope required')
    fields(card['method']['value'], ('operations',), 'Method')
    operations = card['method']['value']['operations']
    require(isinstance(operations, list) and 1 <= len(operations) <= 8, 'Invalid operation count')
    fields(card['scope']['value'], ('pages',), 'Scope')
    pages = card['scope']['value']['pages']
    require(isinstance(pages, list) and 1 <= len(pages) <= 75 and len(set(pages)) == len(pages)
            and all(isinstance(p, str) and re.fullmatch(r'lp[12]-\d{2}', p) and int(p[4:]) <= (16 if p[2] == '1' else 57) for p in pages), 'Invalid complete page scope')
    require(pages == sorted(pages), 'Original page scope is not canonical')
    bound = card['rules']['searchBounds']
    require(bound['status'] == 'specified', 'A literal finite declaration is required')
    fields(bound['value'], ('kind', 'version', 'parameters'), 'Finite bounds')
    require(bound['value']['kind'] == 'finite-settings' and type(bound['value']['version']) is int and bound['value']['version'] == 1, 'Unsupported finite declaration')
    axes = bound['value']['parameters']
    require(isinstance(axes, list) and 1 <= len(axes) <= 56, 'Invalid finite axes')
    seen, normalized, count = set(), [], 1
    for axis in axes:
        fields(axis, ('operation', 'name', 'values'), 'Finite axis')
        op, name, values = axis['operation'], axis['name'], axis['values']
        require(integer(op, 0, len(operations) - 1) and isinstance(name, str) and isinstance(values, list)
                and 1 <= len(values) <= 1024 and (op, name) not in seen, 'Invalid/repeated finite axis')
        require(name not in operations[op], 'A finite axis cannot replace a fixed parameter')
        seen.add((op, name))
        for value in values:
            literal(name, value)
        require(len({stable(v) for v in values}) == len(values), 'Duplicate finite values')
        count *= len(values)
        require(count <= 1024, 'Too many finite programs')
        normalized.append({'operation': op, 'name': name, 'values': sorted(values, key=lambda v: tuple(v) if isinstance(v, list) else v)})
    require(count * len(pages) <= max_cases, 'Too many page/program cases')
    normalized.sort(key=lambda a: (a['operation'], a['name']))
    declared = {'kind': 'finite-settings', 'version': 1, 'parameters': normalized, 'programCount': count, 'caseCount': count * len(pages)}
    largest = [{'operation': a['operation'], 'name': a['name'], 'value': max(a['values'], key=lambda v: len(stable(v).encode('utf-8')))} for a in normalized]
    member = copy.deepcopy(card)
    member['rules']['searchBounds'] = {'status': 'not_applicable'}
    for setting in largest:
        member['method']['value']['operations'][setting['operation']][setting['name']] = setting['value']
    if check_expanded_budget:
        require(len(stable({'declaration': declared, 'variants': []}).encode('utf-8')) + count * (len(stable({'settings': largest, 'card': member}).encode('utf-8')) + 1) <= MAX_BYTES, 'Detached member budget exceeded')
    return operations, normalized, count


LABELS = {'affine': ('Affine', 'Affine substitution'), 'reverse_runes': ('Reverse rune order within each page', 'Reverse rune order within each word', 'Reverse rune order within each line'),
          'reverse_row_runes': ('Reverse rune order within rows', 'Reverse rune order within each row'), 'cumulative_difference': ('Cumulative difference',),
          'vigenere': ('Vigenere', 'Vigenère'), 'repeating_key': ('Repeating key', 'Repeating-key', 'Vigenere', 'Vigenère'),
          'plaintext_autokey': ('Plaintext autokey', 'Plaintext-autokey'), 'ciphertext_autokey': ('Ciphertext autokey', 'Ciphertext-autokey'),
          'finite_key': ('Finite key stream',), 'interrupted_repeating_key': ('Interrupted repeating key',)}


def compile_steps(operations, rules):
    """Explicit typed fixed-plan subset; opaque adapters are rejected, not guessed."""
    specified = lambda k: rules[k]['status'] == 'specified'
    for key, expected in (('representation', 'GP29'), ('unmapped', 'preserve'), ('wordBoundaries', 'preserve')):
        require(not specified(key) or rules[key]['value'] == expected, 'Unsupported ' + key)
    require(not any(specified(k) for k in ('searchProtocol', 'exceptionalCases')), 'Unsupported extra search condition')
    steps, reverse, cumulative, keyed = [], False, False, False
    modes = {'vigenere': 'repeat', 'repeating_key': 'repeat', 'plaintext_autokey': 'plaintext-autokey', 'ciphertext_autokey': 'ciphertext-autokey'}
    for original in operations:
        op = dict(original)
        if 'declaredFamilyId' in op:
            require(op.pop('declaredFamilyId') in ('fixed-substitution', 'polyalphabetic', 'feedback', 'transposition', 'prime-indices', 'number-streams', 'book-codes', 'repetition'), 'Unknown filing category')
        kind = op.get('id')
        require(kind in LABELS and set(op) <= {'id', 'label', 'a', 'b', 'reset', 'unit', 'key', 'direction', 'interrupts'}, 'Unsupported operation/metadata contract')
        require('label' not in op or op['label'] in LABELS[kind], 'Unsupported operation wording')
        if kind == 'affine':
            require(set(op) <= {'id', 'label', 'a', 'b'} and integer(op.get('a'), 0, 28) and integer(op.get('b'), 0, 28), 'Incomplete affine operation')
            steps.append({'op': 'affine', 'a': op['a'], 'b': op['b']})
        elif kind in ('reverse_runes', 'reverse_row_runes'):
            require(set(op) <= {'id', 'label', 'unit'} and (kind != 'reverse_row_runes' or 'unit' not in op), 'Unsupported reversal parameters')
            unit = op.get('unit') if kind == 'reverse_runes' else ('word' if specified('boundaryMode') and rules['boundaryMode']['value'] == 'within_words' else 'line')
            require(unit in ('line', 'word', 'page'), 'Missing reversal unit')
            if kind == 'reverse_runes' and 'label' in op:
                require(op['label'] == 'Reverse rune order within each ' + unit, 'Conflicting reversal wording')
            if kind == 'reverse_row_runes' and specified('wordBoundaries'):
                require(specified('boundaryMode'), 'Ambiguous row boundary convention')
            if specified('boundaryMode'):
                require(unit != 'page' and rules['boundaryMode']['value'] == ('within_words' if unit == 'word' else 'fixed_spaces'), 'Conflicting reversal boundary')
            reverse = True
            steps.append({'op': 'reverse', 'unit': unit})
        else:
            allowed = {'id', 'label', 'reset'} if kind == 'cumulative_difference' else {'id', 'label', 'key', 'direction', 'reset', *(['interrupts'] if kind == 'interrupted_repeating_key' else [])}
            require(set(op) <= allowed and op.get('reset') in ('page', 'line', 'word'), 'Unsupported stateful parameters')
            require(rules['reset']['status'] != 'not_applicable', 'Reset marked inapplicable')
            if specified('reset'):
                reset = rules['reset']['value']
                if isinstance(reset, str):
                    match = re.fullmatch(r'reset at each (page|line|word)', reset, re.I)
                    reset = match[1].lower() if match else reset
                require(reset == op['reset'], 'Conflicting global reset')
            if kind == 'cumulative_difference':
                require(rules['initialState']['status'] != 'not_applicable' and (not specified('initialState') or type(rules['initialState']['value']) is int and rules['initialState']['value'] == 0), 'Unsupported cumulative initial state')
                cumulative = True
                steps.append({'op': 'cumulative-difference', 'reset': op['reset']})
            else:
                literal('key', op.get('key'))
                require(len(op['key']) <= (20000 if kind == 'finite_key' else 256) and op.get('direction') in ('add', 'subtract'), 'Invalid literal key/direction')
                step = {'op': 'finite-shift' if kind == 'finite_key' else 'interrupted-keyed-shift' if kind == 'interrupted_repeating_key' else 'keyed-shift', 'key': op['key'], 'direction': op['direction'], 'reset': op['reset']}
                if kind in modes:
                    step['mode'] = modes[kind]
                if kind == 'interrupted_repeating_key':
                    require(op.get('label') == 'Interrupted repeating key', 'Missing interrupted-key label')
                    literal('interrupts', op.get('interrupts'))
                    step['interrupts'] = op['interrupts']
                keyed = True
                steps.append(step)
    require(not specified('boundaryMode') or reverse, 'Unconsumed boundary condition')
    require(not specified('initialState') or cumulative, 'Unconsumed initial-state condition')
    require(not specified('reset') or cumulative or keyed, 'Unconsumed reset condition')
    return steps


def protocol(question, steps):
    return digest({'schema': 'liberpedia-computation-protocol-v1', 'engine': question['engine'],
                   'inputVersion': question['inputVersion'], 'alphabet': question['alphabet'],
                   'steps': steps, 'criterion': question['criterion']})


def task_check(task):
    runner.validate(task)
    require(task['taskId'] == digest({k: v for k, v in task.items() if k != 'taskId'}), 'Source task identity mismatch')


def verify(snapshot):
    bounded(snapshot)
    require(len(stable(snapshot).encode('utf-8')) <= MAX_BYTES, 'Snapshot exceeds 8 MiB')
    fields(snapshot, ('schema', 'original', 'question', 'evidence', 'finding', 'snapshotId'), 'Snapshot')
    require(snapshot['schema'] == 'liberpedia-finite-search-snapshot-v1', 'Unsupported snapshot schema')
    require(snapshot['snapshotId'] == digest({k: v for k, v in snapshot.items() if k != 'snapshotId'}), 'Snapshot digest mismatch')
    original, q, e = snapshot['original'], snapshot['question'], snapshot['evidence']
    fields(original, ('proposalId', 'card'), 'Original')
    card = original['card']
    require(original['proposalId'] == 'p_' + digest(card), 'Original proposal identity mismatch')
    operations, axes, count = declaration(card)
    fields(q, ('domainId', 'engine', 'inputVersion', 'alphabet', 'pages', 'criterion', 'programs', 'cases', 'totalCases'), 'Question')
    require(q['engine'] == runner.ENGINE and q['inputVersion'] in ('raw', 'reviewed'), 'Unsupported engine/edition')
    require(card['rules']['inputVersion'] == {'status': 'specified', 'value': q['inputVersion']} and card['rules']['evaluation'] == {'status': 'specified', 'value': q['criterion']}, 'Original edition/criterion changed')
    require(q['criterion'].get('kind') == 'exact-prefix', 'Only exact-prefix finite snapshots are supported')
    require([p['id'] for p in q['pages']] == sorted(card['scope']['value']['pages']), 'Question scope differs from original')
    probe = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE, 'title': 'Offline validation only', 'alphabet': q['alphabet'], 'pages': q['pages'], 'steps': [], 'criterion': q['criterion']}
    task_check({**probe, 'taskId': digest(probe)})
    rune_set = {v['rune'] for v in q['alphabet']}
    require(sum(sum(ch in rune_set for ch in p['text']) for p in q['pages']) * count <= 2000000, 'Rune work exceeds bound')
    require(len(stable({'pages': q['pages'], 'alphabet': q['alphabet']}).encode('utf-8')) * count <= MAX_BYTES, 'Expanded source budget exceeded')
    programs, expanded_bytes = {}, 0
    for values in itertools.product(*(axis['values'] for axis in axes)):
        member = copy.deepcopy(operations)
        for axis, value in zip(axes, values):
            member[axis['operation']][axis['name']] = value
        steps = compile_steps(member, card['rules'])
        # Structural validation includes finite-key segment coverage, but never
        # computes output for any unrepresented case.
        candidate = {**probe, 'steps': steps}
        runner.validate({**candidate, 'taskId': digest(candidate)})
        expanded_bytes += len(stable({'title': 'Declared finite search member', 'alphabet': q['alphabet'], 'pages': q['pages'], 'steps': steps, 'criterion': q['criterion']}).encode('utf-8'))
        require(expanded_bytes <= MAX_BYTES, 'Complete compiled programs exceed budget')
        identifier = protocol(q, steps)
        require(identifier not in programs, 'Declared settings compile to duplicate programs')
        programs[identifier] = steps
    expected_programs = [{'id': identifier, 'steps': programs[identifier]} for identifier in sorted(programs)]
    require(q['programs'] == expected_programs, 'Listed programs do not exhaust the original declared settings')
    cases = sorted(({'id': digest({'protocolId': p, 'page': page}), 'programId': p, 'pageId': page['id']}
                    for p in programs for page in q['pages']), key=lambda c: c['id'])
    require(q['cases'] == cases and integer(q['totalCases'], 1, 4096) and q['totalCases'] == len(cases), 'Finite case domain changed')
    require(q['domainId'] == digest({'schema': 'liberpedia-finite-program-question-v1', 'inputVersion': q['inputVersion'], 'programIds': sorted(programs), 'caseIds': [c['id'] for c in cases]}), 'Finite domain identity mismatch')
    fields(e, ('provenanceMeaning', 'tasks', 'results', 'sources', 'caseSources', 'sourceLocations', 'coveredCaseIds', 'matchingCaseIds', 'missingCaseIds', 'lookup'), 'Evidence')
    require(e['provenanceMeaning'] == PROVENANCE, 'Provenance meaning changed')
    fields(e['lookup'], ('recordedComplete', 'meaning'), 'Lookup')
    require(type(e['lookup']['recordedComplete']) is bool and e['lookup']['meaning'] == LOOKUP, 'Lookup snapshot is not an absence proof')
    require(all(isinstance(e[k], list) and len(e[k]) <= 4096 for k in ('tasks', 'results', 'sources', 'caseSources', 'sourceLocations')), 'Evidence collection exceeds bound')
    tasks, results = {}, {}
    for item in e['tasks']:
        fields(item, ('id', 'task'), 'Source task entry')
        task_check(item['task'])
        require(item['id'] == item['task']['taskId'] and item['id'] not in tasks, 'Duplicate/incorrect source task')
        tasks[item['id']] = item['task']
    for item in e['results']:
        fields(item, ('id', 'result'), 'Source result entry')
        require(item['id'] == digest(item['result']) and item['id'] not in results, 'Duplicate/incorrect source result')
        results[item['id']] = item['result']
    require([i['id'] for i in e['tasks']] == sorted(tasks) and [i['id'] for i in e['results']] == sorted(results), 'Noncanonical evidence order')
    claims, source_keys, replayed, used_tasks, used_results = {}, set(), {}, set(), set()
    case_index = {(c['programId'], c['pageId']): c for c in cases}
    exact_pages = {p['id']: p['text'] for p in q['pages']}
    for source in e['sources']:
        fields(source, ('taskId', 'resultId', 'inputVersion', 'createdAt'), 'Source receipt')
        require(source['inputVersion'] == q['inputVersion'] and source['taskId'] in tasks and source['resultId'] in results, 'Unbound source receipt')
        date = source['createdAt']
        require(isinstance(date, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', date), 'Invalid original source date')
        datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        key = stable([source['taskId'], source['resultId'], date])
        require(key not in source_keys, 'Duplicate source receipt')
        source_keys.add(key)
        task, result = tasks[source['taskId']], results[source['resultId']]
        require(task['engine'] == q['engine'] and task['alphabet'] == q['alphabet'] and task['criterion'] == q['criterion'], 'Source changed the exact protocol')
        p = protocol(q, task['steps'])
        require(p in programs, 'Source is outside the declared alternatives')
        replay_key = (source['taskId'], source['resultId'])
        if replay_key not in replayed:
            replay = runner.run(task)
            require(stable(replay) == stable(result), 'Source result failed independent replay')
            replayed[replay_key] = replay
        used_tasks.add(source['taskId'])
        used_results.add(source['resultId'])
        relevant = False
        for page in task['pages']:
            if exact_pages.get(page['id']) != page['text']:
                continue
            relevant = True
            entry = case_index[p, page['id']]
            matched = next(v['matched'] for v in result['matches'] if v['page'] == page['id'])
            text = next(v['text'] for v in result['transformed'] if v['page'] == page['id'])
            ref = {'caseId': entry['id'], 'taskId': source['taskId'], 'resultId': source['resultId'], 'createdAt': date, 'pageId': page['id']}
            previous = claims.get(entry['id'])
            require(not previous or previous[1:3] == (matched, text), 'Conflicting exact source evidence')
            if not previous or key < previous[0]:
                claims[entry['id']] = (key, matched, text, ref)
        require(relevant, 'Source has no exact page intersection')
    require(used_tasks == set(tasks) and used_results == set(results), 'Unreferenced evidence bodies')
    covered = [c['id'] for c in cases if c['id'] in claims]
    missing = [c['id'] for c in cases if c['id'] not in claims]
    matching = [c for c in covered if claims[c][1]]
    require(e['coveredCaseIds'] == covered and e['missingCaseIds'] == missing and e['matchingCaseIds'] == matching
            and e['caseSources'] == [claims[c][3] for c in covered], 'Claimed coverage or matching output changed')
    seen_links = set()
    for link in e['sourceLocations']:
        fields(link, ('taskId', 'href', 'label'), 'Source location')
        require(link['taskId'] in tasks and link['href'] == 'run.html#task=' + link['taskId'] and isinstance(link['label'], str)
                and 0 < len(link['label'].strip()) <= 300 and stable(link) not in seen_links, 'Unsupported/duplicate source location')
        seen_links.add(stable(link))
    fields(snapshot['finding'], ('kind', 'limit'), 'Finding')
    answer = 'prefix-found' if matching else 'prefix-not-found' if not missing else 'incomplete'
    require(snapshot['finding'] == {'kind': answer, 'limit': LIMIT}, 'Snapshot answer or scientific limit changed')
    return {'snapshotId': snapshot['snapshotId'], 'domainId': q['domainId'], 'finding': answer,
            'coveredCases': len(covered), 'missingCases': len(missing), 'matchingCases': len(matching),
            'replayedSources': len(replayed), 'recordedLookupComplete': e['lookup']['recordedComplete'],
            'limit': LIMIT, 'lookupMeaning': LOOKUP}


def load(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'Snapshot file exceeds 8 MiB')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=runner.unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid number')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(load(args.snapshot)), ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, UnicodeError, OSError) as error:
        parser.exit(1, 'Snapshot verification failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
