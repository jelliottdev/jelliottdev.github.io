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
    for name in ('searchBounds', 'searchProtocol', 'exceptionalCases'):
        require(card['rules'][name]['status'] != 'specified', 'unhandled rule ' + name)
    operations = method['operations']
    require(isinstance(operations, list) and 1 <= len(operations) <= 8, 'need 1..8 ordered operations')
    if any(isinstance(op, dict) and op.get('id') == 'word_affine_count' for op in operations):
        require(len(operations) == 1, 'word-pair measurement cannot include transforms')
        op = operations[0]
        fields(op, ('id', 'label', 'lag', 'a', 'b', 'boundaries'), 'word-pair operation')
        require(op['label'] == 'Within-word affine pair count', 'word-pair operation wording')
        require(type(op['lag']) is int and 1 <= op['lag'] <= 12
                and all(type(op[name]) is int and 0 <= op[name] <= 28 for name in ('a', 'b'))
                and op['boundaries'] in ('non-rune', 'hyphen-period'), 'word-pair parameters')
        expected = {'kind': 'word-affine-count', **{name: op[name] for name in ('lag', 'a', 'b', 'boundaries')}}
        fields(criterion, expected, 'word-pair evaluation')
        require(criterion == expected, 'word-pair evaluation conflicts with method')
        for name in ('boundaryMode', 'reset', 'initialState'):
            require(values[name] is None, 'irrelevant word-pair rule ' + name)
        return {'pages': scope['pages'], 'steps': [], 'criterion': criterion, 'inputVersion': values['inputVersion']}
    if criterion == 'measurement':
        criterion = {'kind': 'measurement'}
    else:
        fields(criterion, ('kind', 'values'), 'evaluation')
        require(criterion['kind'] == 'exact-prefix', 'explicit evaluation required')
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
        require(isinstance(identifier, str), 'operation needs a known string id')
        if identifier in modes:
            require(set(op) in ({'id', 'key', 'direction', 'reset'}, {'id', 'label', 'key', 'direction', 'reset'}), 'keyed operation fields')
            require('label' not in op or op['label'] in labels[identifier], 'unsupported operation wording')
            steps.append({'op': 'keyed-shift', 'key': op['key'], 'mode': modes[identifier],
                          'direction': op['direction'], 'reset': op['reset']})
        elif identifier == 'finite_key':
            require(set(op) in ({'id', 'key', 'direction', 'reset'}, {'id', 'label', 'key', 'direction', 'reset'})
                    and ('label' not in op or op['label'] == 'Finite key stream'), 'finite operation fields/wording')
            require(isinstance(op['key'], list) and 1 <= len(op['key']) <= 20000
                    and all(type(n) is int and 0 <= n <= 28 for n in op['key']), 'finite key needs 1..20000 GP29 indices')
            require(op['direction'] in ('add', 'subtract') and op['reset'] in ('page', 'line', 'word'),
                    'finite key needs explicit direction and reset')
            steps.append({'op': 'finite-shift', 'key': op['key'], 'direction': op['direction'], 'reset': op['reset']})
        elif identifier == 'interrupted_repeating_key':
            fields(op, ('id', 'label', 'key', 'direction', 'reset', 'interrupts'), 'interrupted repeating key')
            require(op['label'] == 'Interrupted repeating key', 'interrupted operation wording')
            require(isinstance(op['key'], list) and 1 <= len(op['key']) <= 256
                    and all(type(n) is int and 0 <= n <= 28 for n in op['key']), 'interrupted key needs 1..256 GP29 indices')
            require(op['direction'] in ('add', 'subtract') and op['reset'] in ('page', 'line', 'word'),
                    'interrupted key needs explicit direction and reset')
            interrupts = op['interrupts']
            require(isinstance(interrupts, list) and 1 <= len(interrupts) <= 29
                    and all(type(n) is int and 0 <= n <= 28 for n in interrupts)
                    and interrupts == sorted(set(interrupts)), 'interrupts must be explicit sorted unique GP29 indices')
            steps.append({'op': 'interrupted-keyed-shift', 'key': op['key'], 'direction': op['direction'],
                          'reset': op['reset'], 'interrupts': interrupts})
        elif identifier == 'reverse_runes':
            fields(op, ('id', 'label', 'unit'), 'reverse operation')
            require(op['unit'] in ('line', 'word', 'page')
                    and op['label'] == 'Reverse rune order within each ' + op['unit'], 'reverse wording')
            steps.append({'op': 'reverse', 'unit': op['unit']})
        elif identifier == 'affine':
            require(set(op) in ({'id', 'a', 'b'}, {'id', 'label', 'a', 'b'})
                    and ('label' not in op or op['label'] in ('Affine', 'Affine substitution')), 'affine operation fields/wording')
            steps.append({'op': 'affine', 'a': op['a'], 'b': op['b']})
        elif identifier == 'cumulative_difference':
            require(set(op) in ({'id', 'reset'}, {'id', 'label', 'reset'})
                    and ('label' not in op or op['label'] == 'Cumulative difference'), 'cumulative operation fields/wording')
            steps.append({'op': 'cumulative-difference', 'reset': op['reset']})
        elif identifier == 'reverse_row_runes':
            require(set(op) in ({'id'}, {'id', 'label'}) and ('label' not in op or op['label'] in
                    ('Reverse rune order within rows', 'Reverse rune order within each row')), 'row reversal fields/wording')
            steps.append({'op': 'reverse', 'unit': 'word' if values['boundaryMode'] == 'within_words' else 'line'})
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
            prose(recipe[name], name, 300 if name == 'title' else 1200)
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
        prose(control['label'], 'control label', 300)
        require('synthetic' in control['label'].lower() and 'synthetic' in control['task'].get('title', '').lower(), 'control must be labeled synthetic')
        task = control['task']
        runner.validate(task)
        require(task['alphabet'] == ordered_alphabet and task['steps'] == plan['steps'],
                'control differs from proposed target program')
        if plan['criterion']['kind'] == 'measurement':
            require(task['criterion']['kind'] == 'exact-prefix', 'measurement target requires an exact synthetic control')
            control_runes = {entry['rune'] for entry in ordered_alphabet}
            require(all(sum(ch in control_runes for ch in page['text']) == len(task['criterion']['values'])
                        for page in task['pages']), 'measurement control must check every synthetic output rune')
        else:
            require(task['criterion'] == plan['criterion'], 'control differs from proposed target criterion')
        result = runner.run(task)
        if plan['criterion']['kind'] == 'word-affine-count':
            measured = result['wordPairs']
            expected = measured['expected']
            require(measured['matches'] == measured['opportunities'] > 0
                    and int(expected['numerator']) < measured['opportunities'] * int(expected['denominator']),
                    'synthetic word-pair control lacks a detectable complete planted relation')
        else:
            require(result['matches'] and all(m['matched'] for m in result['matches']), 'synthetic control failed exact-prefix criterion')
        require(control['expected_result_sha256'] == digest(result), 'complete control result digest mismatch')
    return value


def warning_plaintext(root, ordered_alphabet):
    """Independently join the full documented Warning with its exact separators."""
    root = Path(root)
    runes = [row['rune'] for row in ordered_alphabet]
    indices = {r: i for i, r in enumerate(runes)}
    # Warning's complete known plaintext, with original separators unchanged.
    raw = json.loads((root / 'data/pages/lp1-01.json').read_text(encoding='utf-8'))['raw']
    plaintext = ''.join(runes[28 - indices[ch]] if ch in indices else ch for ch in raw)
    trace = list(csv.DictReader(io.StringIO((root / 'exports/readings/warning.csv').read_text(encoding='utf-8'))))
    expected = [int(row['output_index']) for row in trace]
    require(all(row['page'] == 'lp1-01' and int(row['page_rune_ordinal']) == n for n, row in enumerate(trace)), 'Warning trace ordinal mismatch')
    require([indices[ch] for ch in plaintext if ch in indices] == expected and expected[:12] == WARNING12, 'Warning plaintext/trace mismatch')
    return plaintext, expected


def inverse_step(plaintext, step, ordered_alphabet):
    """Construct a synthetic step input from its desired complete output.

    This is an independent encoder, not a decoder-direction toggle: ciphertext
    autokey depends on newly constructed ciphertext, plaintext autokey on the
    supplied step output. Histories reset only at the declared boundary.
    """
    runes = [entry['rune'] for entry in ordered_alphabet]
    indices = {ch: i for i, ch in enumerate(runes)}
    output = list(plaintext)
    if step['op'] == 'reverse':
        positions = []
        def flush():
            values = [plaintext[i] for i in positions][::-1]
            for position, value in zip(positions, values):
                output[position] = value
            positions.clear()
        for i, ch in enumerate(plaintext):
            if ch in indices:
                positions.append(i)
            elif step['unit'] == 'word' or step['unit'] == 'line' and ch in '\r\n':
                flush()
        flush()
    elif step['op'] == 'affine':
        require(step['a'] != 0, 'noninvertible affine coefficient a=0 cannot encode a full control')
        inverse = pow(step['a'], -1, 29)
        output = [runes[((indices[ch] - step['b']) * inverse) % 29] if ch in indices else ch for ch in plaintext]
    else:
        ciphertext, known_plaintext = [], []
        cumulative = 0
        for i, ch in enumerate(plaintext):
            if ch not in indices:
                if step['reset'] == 'word' or step['reset'] == 'line' and ch in '\r\n':
                    ciphertext.clear()
                    known_plaintext.clear()
                    cumulative = 0
                continue
            value = indices[ch]
            if step['op'] == 'cumulative-difference':
                cumulative = (cumulative + value) % 29
                encoded = cumulative
            elif step['op'] == 'finite-shift':
                position = len(ciphertext)
                require(position < len(step['key']), 'finite key exhausted while encoding the complete synthetic control')
                amount = step['key'][position]
                encoded = (value + (amount if step['direction'] == 'subtract' else -amount)) % 29
            elif step['op'] == 'interrupted-keyed-shift':
                if value in step['interrupts']:
                    # Deliberately choose literal passthrough where both
                    # passthrough and ordinary decoding could yield this value.
                    # This is one partial encoder, not a bijective inverse.
                    output[i] = ch
                    continue
                amount = step['key'][len(ciphertext) % len(step['key'])]
                encoded = (value + (amount if step['direction'] == 'subtract' else -amount)) % 29
                require(encoded not in step['interrupts'],
                        'desired synthetic plaintext cannot be encoded at this interrupted key position')
            else:
                key, mode, position = step['key'], step['mode'], len(ciphertext)
                if mode == 'repeat':
                    amount = key[position % len(key)]
                elif position < len(key):
                    amount = key[position]
                else:
                    history = known_plaintext if mode == 'plaintext-autokey' else ciphertext
                    amount = history[position - len(key)]
                encoded = (value + (amount if step['direction'] == 'subtract' else -amount)) % 29
            output[i] = runes[encoded]
            ciphertext.append(encoded)
            known_plaintext.append(value)
    return ''.join(output)


def _construct_followup(root, *, identifier, title, question, scope_change, limitation,
                        operations, pages, input_version='raw', prefix=WARNING12,
                        control_title=None, outcome_detail=None):
    root = Path(root)
    a = alphabet(root)
    plaintext, expected = warning_plaintext(root, a)
    require(isinstance(prefix, list) and 1 <= len(prefix) <= len(expected)
            and all(type(n) is int and 0 <= n <= 28 for n in prefix)
            and prefix == expected[:len(prefix)], 'prefix must be an exact initial slice of the documented Warning reading')
    require(isinstance(pages, (list, tuple)) and all(isinstance(p, str) for p in pages)
            and len(set(pages)) == len(pages), 'pages must be an explicit unique list')
    pages = sorted(pages)
    operations = copy.deepcopy(operations)
    criterion = {'kind': 'exact-prefix', 'values': prefix[:]}
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in RULES}
    rules.update({name: specified(value) for name, value in {
        'inputVersion': input_version, 'representation': 'GP29', 'unmapped': 'preserve',
        'wordBoundaries': 'preserve', 'evaluation': criterion}.items()})
    require(isinstance(operations, list) and all(isinstance(op, dict) for op in operations), 'operations must be an explicit list')
    resets = [op.get('reset') for op in operations if op.get('id') in
              ('repeating_key', 'vigenere', 'plaintext_autokey', 'ciphertext_autokey', 'cumulative_difference', 'finite_key', 'interrupted_repeating_key')]
    if resets and all(reset == resets[0] for reset in resets):
        rules['reset'] = specified(resets[0])
    if any(op.get('id') == 'cumulative_difference' for op in operations):
        rules['initialState'] = specified(0)
    if any(op.get('id') == 'reverse_row_runes' for op in operations):
        require(not any(op.get('id') == 'reverse_runes' and op.get('unit') != 'line' for op in operations),
                'use explicit reverse_runes units for mixed row/word/page reversal steps')
        rules['boundaryMode'] = specified('fixed_spaces')
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': outcome_detail or
            'Test only the fixed ' + str(len(prefix)) + '-rune Warning opening under the declared hypothesis; a match is not a complete decipherment.'}),
            'method': specified({'operations': operations}), 'scope': specified({'pages': pages}),
            'rules': rules, 'unresolved': []}
    plan = compile_card(card)
    task = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
            'title': control_title or 'Synthetic Warning control: ' + identifier,
            'pages': [{'id': 'lp1-01', 'text': plaintext}], 'alphabet': a,
            'steps': plan['steps'], 'criterion': criterion}
    task['taskId'] = runner.task_identity(task)
    runner.validate(task)  # Reject incomplete/boolean/out-of-range parameters before encoding.
    encoded = plaintext
    for step in reversed(plan['steps']):
        encoded = inverse_step(encoded, step, a)
    task['pages'][0]['text'] = encoded
    task['taskId'] = runner.task_identity(task)
    result = runner.run(task)
    require(result['transformed'][0]['text'] == plaintext, 'complete Warning control recovery failed')
    pins, target_pages = [], []
    for page_id in pages:
        source = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
        text = source.get('raw' if input_version == 'raw' else 'reviewed_text')
        require(isinstance(text, str), 'requested exact source text unavailable: ' + page_id)
        pins.append({'id': page_id, 'text_sha256': text_hash(text)})
        target_pages.append({'id': page_id, 'text': text})
    if any(step['op'] == 'finite-shift' for step in plan['steps']):
        # Length validation is structural only: finite keys must cover every
        # declared segment, not merely the acceptance prefix or the control.
        target_shape = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
                        'title': title, 'pages': target_pages, 'alphabet': a,
                        'steps': plan['steps'], 'criterion': criterion}
        target_shape['taskId'] = runner.task_identity(target_shape)
        runner.validate(target_shape)
    recipe = {
        'id': identifier, 'title': title, 'question': question, 'scope_change': scope_change,
        'limitation': limitation, 'card': card,
        'inputs': {'version': input_version, 'alphabet_sha256': digest(a), 'pages': pins},
        'control': {'label': 'Recover the known Warning text from synthetic ciphertext',
                    'task': task, 'expected_result_sha256': digest(result)}}
    validate_followups([recipe], root)
    return recipe


def construct_followup(root, *, identifier, title, question, scope_change, limitation,
                       operations, pages, input_version='raw', prefix=WARNING12):
    """Return one authored declaration without writing files or decoding targets.

    operations are explicit canonical planCard operations, not runner IR or prose.
    pages become canonical sorted exact IDs. prefix must be a known Warning
    initial slice (default 12; up to its complete 184 runes). Mixed step resets
    remain per-step; no conflicting global reset is invented. Controls are
    synthetic inverse encodings, never claimed historical manuscript inputs.
    """
    return _construct_followup(root, identifier=identifier, title=title, question=question,
                               scope_change=scope_change, limitation=limitation,
                               operations=operations, pages=pages,
                               input_version=input_version, prefix=prefix)


def construct_word_pair_followup(root, *, identifier, title, question, scope_change,
                                 limitation, pages, lag, a, b, boundaries,
                                 input_version='raw'):
    """Author one fixed count and a planted synthetic control; never count targets.

    This is deliberately separate from transform construction. No reset, cipher,
    significance threshold, lag search or shuffled-trial protocol is inferred.
    """
    root = Path(root)
    ordered_alphabet = alphabet(root)
    require(isinstance(pages, (list, tuple)) and all(isinstance(p, str) for p in pages)
            and len(set(pages)) == len(pages), 'pages must be an explicit unique list')
    pages = sorted(pages)
    operation = {'id': 'word_affine_count', 'label': 'Within-word affine pair count',
                 'lag': lag, 'a': a, 'b': b, 'boundaries': boundaries}
    criterion = {'kind': 'word-affine-count', 'lag': lag, 'a': a, 'b': b, 'boundaries': boundaries}
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'not_applicable'} for name in RULES}
    rules.update({name: specified(value) for name, value in {
        'inputVersion': input_version, 'representation': 'GP29', 'unmapped': 'preserve',
        'wordBoundaries': 'preserve', 'evaluation': criterion}.items()})
    card = {'version': 1, 'outcome': specified({'outcomeId': 'measure',
            'detail': 'Count one fixed affine relation at one fixed lag under the declared word boundaries; this does not identify a cipher.'}),
            'method': specified({'operations': [operation]}), 'scope': specified({'pages': pages}),
            'rules': rules, 'unresolved': []}
    compile_card(card)  # Validate parameters before building synthetic input.
    runes = [entry['rune'] for entry in ordered_alphabet]
    task = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
            'title': 'Synthetic planted word-pair control: ' + identifier,
            'pages': [], 'alphabet': ordered_alphabet, 'steps': [], 'criterion': criterion}
    result = None
    # 29 explicitly bounded seed rotations. Every lag-separated successor is
    # planted by the declared equation, without inspecting manuscript values.
    # Two copies exercise the exact layout-boundary policy as well.
    for seed in range(29):
        values = [(seed + n) % 29 for n in range(lag)]
        for position in range(10):
            values.append((a * values[position] + b) % 29)
        word = ''.join(runes[n] for n in values)
        # Exercise layout continuation as well as the planted equation. The
        # two supported segmentation rules must not accept an indistinguishable
        # fixture merely because it contains only uninterrupted rune text.
        if boundaries == 'non-rune':
            control_text = word + ' /\r\n' + word
        else:
            split = len(word) // 2
            control_text = word[:split] + ' /\r\n' + word[split:] + '. ' + word
        task['pages'] = [{'id': 'lp1-01', 'text': control_text}]
        task['taskId'] = runner.task_identity(task)
        candidate = runner.run(task)
        measured = candidate['wordPairs']
        expected = measured['expected']
        if measured['matches'] == measured['opportunities'] > 0 and int(expected['numerator']) < measured['opportunities'] * int(expected['denominator']):
            alternate = copy.deepcopy(task)
            alternate['criterion']['boundaries'] = 'hyphen-period' if boundaries == 'non-rune' else 'non-rune'
            alternate['taskId'] = runner.task_identity(alternate)
            alternate_result = runner.run(alternate)
            if alternate_result['wordPairs'] != measured:
                result = candidate
                break
    require(result is not None, 'no detectable planted word-pair control among the 29 declared seeds')
    pins = []
    for page_id in pages:
        source = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
        text = source.get('raw' if input_version == 'raw' else 'reviewed_text')
        require(isinstance(text, str), 'requested exact source text unavailable: ' + page_id)
        pins.append({'id': page_id, 'text_sha256': text_hash(text)})
    recipe = {'id': identifier, 'title': title, 'question': question,
              'scope_change': scope_change, 'limitation': limitation, 'card': card,
              'inputs': {'version': input_version, 'alphabet_sha256': digest(ordered_alphabet), 'pages': pins},
              'control': {'label': 'Count every planted synthetic pair using the declared word boundaries and distinguish its shuffled-order mean',
                          'task': task, 'expected_result_sha256': digest(result)}}
    validate_followups([recipe], root)
    return recipe


def construct_measurement_followup(root, *, identifier, title, question, scope_change,
                                   limitation, operations, pages, control_cipher,
                                   control_plain, input_version='raw'):
    """Pin a descriptive transform and an explicit complete synthetic witness.

    The caller must independently derive control_plain. The target has no
    plaintext acceptance criterion; the control checks every supplied rune.
    No manuscript target is transformed here.
    """
    root = Path(root)
    ordered_alphabet = alphabet(root)
    runes = {row['rune']: n for n, row in enumerate(ordered_alphabet)}
    require(isinstance(control_cipher, str) and isinstance(control_plain, str)
            and len(control_cipher) == len(control_plain), 'control texts need equal exact lengths')
    require(all((left in runes) == (right in runes) and (left in runes or left == right)
                for left, right in zip(control_cipher, control_plain)), 'control separators must be identical')
    expected = [runes[ch] for ch in control_plain if ch in runes]
    require(1 <= len(expected) <= 256, 'control must contain 1..256 explicitly expected runes')
    require(isinstance(pages, (list, tuple)) and all(isinstance(p, str) for p in pages)
            and len(set(pages)) == len(pages), 'pages must be an explicit unique list')
    pages = sorted(pages)
    operations = copy.deepcopy(operations)
    specified = lambda value: {'status': 'specified', 'value': value}
    require(isinstance(operations, list) and all(isinstance(op, dict) for op in operations),
            'operations must be an explicit list')
    rules = {name: {'status': 'unspecified'} for name in RULES}
    rules.update({name: specified(value) for name, value in {
        'inputVersion': input_version, 'representation': 'GP29', 'unmapped': 'preserve',
        'wordBoundaries': 'preserve', 'evaluation': 'measurement'}.items()})
    resets = [op.get('reset') for op in operations if isinstance(op, dict) and op.get('id') in
              ('repeating_key', 'vigenere', 'plaintext_autokey', 'ciphertext_autokey',
               'cumulative_difference', 'finite_key', 'interrupted_repeating_key')]
    if resets and all(reset == resets[0] for reset in resets):
        rules['reset'] = specified(resets[0])
    if any(isinstance(op, dict) and op.get('id') == 'cumulative_difference' for op in operations):
        rules['initialState'] = specified(0)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'measure',
            'detail': 'Report the declared transform and descriptive rune metrics; no plaintext or significance threshold is inferred.'}),
            'method': specified({'operations': operations}), 'scope': specified({'pages': pages}),
            'rules': rules, 'unresolved': []}
    plan = compile_card(card)
    task = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
            'title': 'Synthetic complete-output control: ' + identifier,
            'pages': [{'id': 'lp1-01', 'text': control_cipher}], 'alphabet': ordered_alphabet,
            'steps': plan['steps'], 'criterion': {'kind': 'exact-prefix', 'values': expected}}
    task['taskId'] = runner.task_identity(task)
    result = runner.run(task)
    require(result['transformed'][0]['text'] == control_plain, 'independent complete synthetic output differs')
    pins = []
    for page_id in pages:
        source = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
        text = source.get('raw' if input_version == 'raw' else 'reviewed_text')
        require(isinstance(text, str), 'requested exact source text unavailable: ' + page_id)
        pins.append({'id': page_id, 'text_sha256': text_hash(text)})
    recipe = {'id': identifier, 'title': title, 'question': question, 'scope_change': scope_change,
              'limitation': limitation, 'card': card,
              'inputs': {'version': input_version, 'alphabet_sha256': digest(ordered_alphabet), 'pages': pins},
              'control': {'label': 'Recover every independently specified output rune in a synthetic control',
                          'task': task, 'expected_result_sha256': digest(result)}}
    validate_followups([recipe], root)
    return recipe


def construct_second_koan_word_reset(root):
    """Preserve the original authored declaration exactly through the shared constructor."""
    return _construct_followup(
        root, identifier='second-koan-word-reset-warning',
        title='Restart the second-koan key at each word',
        question='Does repeating the second-koan key from its first rune at every transcription word recover the fixed 12-rune Warning opening at a page start?',
        scope_change='Only LP2-54 remains eligible: on the other 54 rune pages, the saved page-reset output already disagrees with the Warning opening before a word reset could change anything. This checks the remaining page with one key, subtraction and phase zero.',
        limitation='A match establishes only compatibility with this 12-rune beginning, not a complete reading. Every non-rune ends a transcription word; headings remain included. No skips, later offsets, alternative phases or other openings are tested. Surviving the prefix check does not mean LP2-54 is a match.',
        operations=[{'id': 'repeating_key', 'label': 'Repeating key', 'key': KEY[:], 'direction': 'subtract', 'reset': 'word'}],
        pages=['lp2-54'],
        control_title='Synthetic Warning control: second-koan key with word resets',
        outcome_detail='Test only the fixed 12-rune Warning opening under the declared second-koan word-reset hypothesis; a match is not a complete decipherment.')
