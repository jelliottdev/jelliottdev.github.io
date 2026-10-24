"""Validate authored browser recipes and synthetic controls, never target decodes.

The independent standard-library runner checks the complete synthetic result.
Only input text hashes are read for target pages. This module does not publish
files, call services, or execute a record's reproduction scripts.
"""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import research_runner as runner

RULES = ('representation', 'wordBoundaries', 'boundaryMode', 'unmapped', 'inputVersion',
         'evaluation', 'reset', 'initialState', 'searchBounds', 'searchProtocol', 'exceptionalCases')
STATES = ('specified', 'unspecified', 'not_applicable', 'unrestricted')
OUTCOMES = ('decipher', 'measure', 'reproduce', 'explain', 'verify_source', 'unclassified')
RECIPE_FIELDS = {'id', 'title', 'question', 'scope_change', 'limitation', 'card', 'inputs', 'control'}
KEY = [0, 10, 4, 0, 1, 19, 0, 18, 4, 18, 9, 0, 18]
WARNING12 = [24, 7, 24, 4, 9, 21, 17, 18, 20, 10, 18, 1]


def require(condition, message):
    if not condition:
        raise ValueError('browser_followups: ' + message)


def stable(value):
    # JS stable() writes integral numbers without a decimal suffix.
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, list):
        return '[' + ','.join(stable(v) for v in value) + ']'
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + stable(value[k])
                              for k in sorted(value)) + '}'
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(stable(value).encode('utf-8')).hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def fields(value, expected, label):
    require(isinstance(value, dict) and set(value) == set(expected), label + ': invalid fields')


def prose(value, label, maximum=1200):
    require(isinstance(value, str) and value.strip() and len(value) <= maximum
            and not re.search(r'[<>\x00-\x08\x0b\x0c\x0e-\x1f]', value), label + ': invalid plain text')


def field(value, label):
    require(isinstance(value, dict) and value.get('status') in STATES, label + ': invalid state')
    fields(value, ('status', 'value') if value['status'] == 'specified' else ('status',), label)
    return value.get('value')


def compile_card(card):
    """Conservative independent compiler for the reviewed primitive subset.

    No wording inference, measurement defaults or unknown rule wildcards.
    Production planCard parity is separately tested with the authored recipe.
    """
    fields(card, ('version', 'outcome', 'method', 'scope', 'rules', 'unresolved'), 'card')
    require(type(card['version']) is int and card['version'] == 1, 'card version')
    require(len(stable(card).encode('utf-8')) <= 12000, 'card exceeds 12,000 bytes')
    outcome = field(card['outcome'], 'outcome')
    if outcome is not None:
        fields(outcome, ('outcomeId', 'detail'), 'outcome value')
        require(outcome['outcomeId'] in OUTCOMES and isinstance(outcome['detail'], str), 'outcome value')
    method = field(card['method'], 'method')
    scope = field(card['scope'], 'scope')
    fields(method, ('operations',), 'method value')
    fields(scope, ('pages',), 'scope value')
    require(isinstance(scope['pages'], list) and 1 <= len(scope['pages']) <= 75
            and all(isinstance(p, str) and re.fullmatch(r'lp[12]-[0-9]{2}', p)
                    and int(p[4:]) <= (16 if p.startswith('lp1') else 57) for p in scope['pages'])
            and scope['pages'] == sorted(set(scope['pages'])), 'scope needs canonical unique exact complete pages')
    fields(card['rules'], RULES, 'rules')
    values = {name: field(card['rules'][name], 'rule ' + name) for name in RULES}
    require(card['unresolved'] == [], 'unresolved constraints')
    require(not any(f['status'] == 'unrestricted' for f in card['rules'].values()), 'unrestricted rule')
    for name, expected in [('representation', 'GP29'), ('unmapped', 'preserve'), ('wordBoundaries', 'preserve')]:
        require(values[name] == expected, 'explicit ' + name + ' required')
    require(values['inputVersion'] in ('raw', 'reviewed'), 'explicit inputVersion required')
    criterion = values['evaluation']
    fields(criterion, ('kind', 'values'), 'evaluation')
    require(criterion['kind'] == 'exact-prefix', 'exact-prefix evaluation required')
    for name in ('searchBounds', 'searchProtocol', 'exceptionalCases'):
        require(card['rules'][name]['status'] != 'specified', 'unhandled rule ' + name)
    operations = method['operations']
    require(isinstance(operations, list) and 1 <= len(operations) <= 8, 'need 1..8 ordered operations')
    steps = []
    labels = {'repeating_key': ('Repeating key', 'Repeating-key', 'Vigenere', 'Vigenère'),
              'vigenere': ('Vigenere', 'Vigenère'),
              'plaintext_autokey': ('Plaintext autokey', 'Plaintext-autokey'),
              'ciphertext_autokey': ('Ciphertext autokey', 'Ciphertext-autokey')}
    modes = {'repeating_key': 'repeat', 'vigenere': 'repeat',
             'plaintext_autokey': 'plaintext-autokey', 'ciphertext_autokey': 'ciphertext-autokey'}
    for op in operations:
        require(isinstance(op, dict), 'operation must be object')
        identifier = op.get('id')
        if identifier in modes:
            require(set(op) in ({'id', 'key', 'direction', 'reset'}, {'id', 'label', 'key', 'direction', 'reset'}), 'keyed operation fields')
            require('label' not in op or op['label'] in labels[identifier], 'unsupported operation wording')
            steps.append({'op': 'keyed-shift', 'key': op['key'], 'mode': modes[identifier],
                          'direction': op['direction'], 'reset': op['reset']})
        elif identifier == 'reverse_runes':
            fields(op, ('id', 'label', 'unit'), 'reverse operation')
            require(op['unit'] in ('line', 'word', 'page')
                    and op['label'] == 'Reverse rune order within each ' + op['unit'], 'reverse wording')
            steps.append({'op': 'reverse', 'unit': op['unit']})
        elif identifier == 'affine':
            fields(op, ('id', 'a', 'b'), 'affine operation')
            steps.append({'op': 'affine', 'a': op['a'], 'b': op['b']})
        elif identifier == 'cumulative_difference':
            fields(op, ('id', 'reset'), 'cumulative operation')
            steps.append({'op': 'cumulative-difference', 'reset': op['reset']})
        else:
            raise ValueError('browser_followups: unsupported operation')
    for step in steps:
        if 'reset' in step:
            require(card['rules']['reset']['status'] != 'not_applicable', 'reset marked inapplicable')
            require(values['reset'] is None or values['reset'] == step['reset'], 'conflicting reset')
        if step['op'] == 'reverse' and values['boundaryMode'] is not None:
            require(step['unit'] != 'page' and values['boundaryMode'] ==
                    ('within_words' if step['unit'] == 'word' else 'fixed_spaces'), 'conflicting boundary')
        if step['op'] == 'cumulative-difference':
            require(card['rules']['initialState']['status'] != 'not_applicable'
                    and (values['initialState'] is None or type(values['initialState']) is int and values['initialState'] == 0), 'initial state')
    require(values['boundaryMode'] is None or any(s['op'] == 'reverse' for s in steps), 'unused boundaryMode')
    require(values['reset'] is None or any('reset' in s for s in steps), 'unused reset')
    require(values['initialState'] is None or any(s['op'] == 'cumulative-difference' for s in steps), 'unused initialState')
    return {'pages': scope['pages'], 'steps': steps, 'criterion': criterion, 'inputVersion': values['inputVersion']}


def alphabet(root):
    return [{key: row[key] for key in ('rune', 'latin', 'prime')}
            for row in json.loads((Path(root) / 'data/index.json').read_text(encoding='utf-8'))['alphabet']]


def validate_followups(value, root, known_pages=None):
    require(isinstance(value, list) and 1 <= len(value) <= 8, 'need 1..8 recipes')
    root = Path(root)
    ordered_alphabet = alphabet(root)
    seen = set()
    for recipe in value:
        fields(recipe, RECIPE_FIELDS, 'recipe')
        identifier = recipe['id']
        require(isinstance(identifier, str) and re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier)
                and len(identifier) <= 100 and identifier not in seen, 'invalid or duplicate id')
        seen.add(identifier)
        for name in ('title', 'question', 'scope_change', 'limitation'):
            prose(recipe[name], name)
        plan = compile_card(recipe['card'])
        pins = recipe['inputs']
        fields(pins, ('version', 'alphabet_sha256', 'pages'), 'inputs')
        require(pins['version'] == plan['inputVersion'], 'input version mismatch')
        require(pins['alphabet_sha256'] == digest(ordered_alphabet), 'alphabet pin mismatch')
        require(isinstance(pins['pages'], list) and len(pins['pages']) == len(plan['pages']), 'page pin count')
        for pin, page_id in zip(pins['pages'], plan['pages']):
            fields(pin, ('id', 'text_sha256'), 'page pin')
            require(pin['id'] == page_id and (known_pages is None or page_id in known_pages), 'page order/id mismatch')
            page = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
            text = page.get('raw' if plan['inputVersion'] == 'raw' else 'reviewed_text')
            require(page.get('id') == page_id and isinstance(text, str) and text_hash(text) == pin['text_sha256'], 'page text pin mismatch: ' + page_id)
        control = recipe['control']
        fields(control, ('label', 'task', 'expected_result_sha256'), 'control')
        prose(control['label'], 'control label')
        require('synthetic' in control['label'].lower() and 'synthetic' in control['task'].get('title', '').lower(), 'control must be labeled synthetic')
        task = control['task']
        runner.validate(task)
        require(task['alphabet'] == ordered_alphabet and task['steps'] == plan['steps']
                and task['criterion'] == plan['criterion'], 'control differs from proposed target protocol')
        result = runner.run(task)
        require(result['matches'] and all(m['matched'] for m in result['matches']), 'synthetic control failed exact-prefix criterion')
        require(control['expected_result_sha256'] == digest(result), 'complete control result digest mismatch')
    return value


def construct_second_koan_word_reset(root):
    """Author the fixed recipe; called explicitly, never by the export builder."""
    root = Path(root)
    a = alphabet(root)
    runes = [row['rune'] for row in a]
    indices = {r: i for i, r in enumerate(runes)}
    # Warning's complete known plaintext, with original separators unchanged.
    raw = json.loads((root / 'data/pages/lp1-01.json').read_text(encoding='utf-8'))['raw']
    plaintext = ''.join(runes[28 - indices[ch]] if ch in indices else ch for ch in raw)
    trace = list(csv.DictReader(io.StringIO((root / 'exports/readings/warning.csv').read_text(encoding='utf-8'))))
    expected = [int(row['output_index']) for row in trace]
    require(all(row['page'] == 'lp1-01' and int(row['page_rune_ordinal']) == n for n, row in enumerate(trace)), 'Warning trace ordinal mismatch')
    require([indices[ch] for ch in plaintext if ch in indices] == expected and expected[:12] == WARNING12, 'Warning plaintext/trace mismatch')
    encoded, position = [], 0
    for ch in plaintext:
        if ch in indices:
            encoded.append(runes[(indices[ch] + KEY[position % len(KEY)]) % 29])
            position += 1
        else:
            encoded.append(ch)
            position = 0
    steps = [{'op': 'keyed-shift', 'key': KEY[:], 'mode': 'repeat', 'direction': 'subtract', 'reset': 'word'}]
    criterion = {'kind': 'exact-prefix', 'values': WARNING12[:]}
    task = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
            'title': 'Synthetic Warning control: second-koan key with word resets',
            'pages': [{'id': 'lp1-01', 'text': ''.join(encoded)}], 'alphabet': a,
            'steps': steps, 'criterion': criterion}
    task['taskId'] = runner.task_identity(task)
    result = runner.run(task)
    require(result['transformed'][0]['text'] == plaintext, 'complete Warning control recovery failed')
    pages = ['lp2-' + str(n).zfill(2) for n in range(56) if n != 50]
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in RULES}
    rules.update({name: specified(value) for name, value in {
        'inputVersion': 'raw', 'representation': 'GP29', 'unmapped': 'preserve',
        'wordBoundaries': 'preserve', 'reset': 'word', 'evaluation': criterion}.items()})
    return {
        'id': 'second-koan-word-reset-warning',
        'title': 'Restart the second-koan key at each word',
        'question': 'Does repeating the second-koan key from its first rune at every transcription word recover the fixed 12-rune Warning opening at a page start?',
        'scope_change': 'A newly specified word-reset variant of the known-key test: one key, subtraction, phase zero, and one fixed opening on 55 rune-bearing LP2-00–55 pages. This is not the original nine-opening, all-phase search.',
        'limitation': 'A match establishes only compatibility with this 12-rune beginning, not a complete reading. Every non-rune ends a transcription word; headings remain included. No skips, later offsets, alternative phases or other openings are tested. LP2-50 contributes no runes and is omitted.',
        'card': {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Test only the fixed 12-rune Warning opening under the declared second-koan word-reset hypothesis; a match is not a complete decipherment.'}),
                 'method': specified({'operations': [{'id': 'repeating_key', 'label': 'Repeating key', 'key': KEY[:], 'direction': 'subtract', 'reset': 'word'}]}),
                 'scope': specified({'pages': pages}), 'rules': rules, 'unresolved': []},
        'inputs': {'version': 'raw', 'alphabet_sha256': digest(a), 'pages': [
            {'id': p, 'text_sha256': text_hash(json.loads((root / 'data/pages' / (p + '.json')).read_text(encoding='utf-8'))['raw'])} for p in pages]},
        'control': {'label': 'Recover the known Warning text from synthetic ciphertext',
                    'task': task, 'expected_result_sha256': digest(result)}}
