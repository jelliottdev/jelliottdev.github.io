"""Source-authored finite transform recipes and complete synthetic witnesses.

Only synthetic controls execute. Target pages are read solely to verify pins;
fixed browser recipes retain their existing validator without schema changes.
"""
import copy
import json
from pathlib import Path
import re

import browser_followups as fixed
import finite_followup_cards as finite
import finite_control_storage as storage

FIELDS = fixed.RECIPE_FIELDS | {'kind'}


def require(condition, message):
    if not condition:
        raise ValueError('authored_finite_followups: ' + message)


def _metadata(recipe):
    fixed.fields(recipe, FIELDS | ({'motivation'} if 'motivation' in recipe else set()), 'finite recipe')
    require(recipe['kind'] == 'finite-settings', 'unknown recipe kind')
    identifier = recipe['id']
    require(type(identifier) is str and len(identifier) <= 100
            and re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier), 'invalid recipe id')
    for name in ('title', 'question', 'scope_change', 'limitation'):
        fixed.prose(recipe[name], name, 300 if name == 'title' else 1200)
    if 'motivation' in recipe:
        value = recipe['motivation']
        require(type(value) is str and value == value.strip() and 1 <= len(value) <= 500
                and not re.search(r'[<>\[\]`*\\\x00-\x1f\x7f-\x9f\u2028\u2029\ud800-\udfff]', value), 'invalid motivation')


def _inputs(pins, plan, root, ordered_alphabet, known_pages):
    fixed.fields(pins, ('version', 'alphabet_sha256', 'pages'), 'finite inputs')
    require(pins['version'] == plan['inputVersion'], 'input version mismatch')
    require(pins['alphabet_sha256'] == fixed.digest(ordered_alphabet), 'alphabet pin mismatch')
    require(type(pins['pages']) is list and len(pins['pages']) == len(plan['pages']), 'page pin count')
    for pin, page_id in zip(pins['pages'], plan['pages']):
        fixed.fields(pin, ('id', 'text_sha256'), 'finite page pin')
        require(pin['id'] == page_id and (known_pages is None or page_id in known_pages), 'page order/id mismatch')
        source = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
        text = source.get('raw' if plan['inputVersion'] == 'raw' else 'reviewed_text')
        require(source.get('id') == page_id and type(text) is str
                and fixed.text_hash(text) == pin['text_sha256'], 'page text pin mismatch: ' + page_id)


def _control(control, plan, ordered_alphabet):
    fixed.fields(control, ('label', 'task', 'expected_result_sha256'), 'finite control')
    fixed.prose(control['label'], 'control label', 300)
    task = control['task']
    require(type(task) is dict and 'synthetic' in control['label'].lower()
            and type(task.get('title')) is str and 'synthetic' in task['title'].lower(), 'control must be labeled synthetic')
    fixed.runner.validate(task)
    require(task['alphabet'] == ordered_alphabet and task['steps'] == plan['steps'], 'control differs from declared member program')
    require(plan['criterion']['kind'] in ('measurement', 'language-score', 'exact-prefix'), 'finite controls support transform evaluations only')
    require(task['criterion']['kind'] == 'exact-prefix', 'finite control needs exact complete known output')
    runes = {entry['rune'] for entry in ordered_alphabet}
    require(len(task['pages']) == 1, 'finite control needs exactly one synthetic page')
    count = sum(ch in runes for ch in task['pages'][0]['text'])
    require(1 <= count <= 256 and count == len(task['criterion']['values']),
            'finite control must check every synthetic output rune (1..256)')
    result = fixed.runner.run(task)
    require(result['matches'] and all(item['matched'] for item in result['matches']), 'complete synthetic control failed')
    require(control['expected_result_sha256'] == fixed.digest(result), 'complete control result digest mismatch')


def validate_recipe(recipe, root, known_pages=None):
    """Validate exact expansion, shared source pins and every synthetic member."""
    require(type(recipe) is dict, 'finite recipe must be object')
    _metadata(recipe)
    expanded = finite.compile_card(recipe['card'])
    variants = expanded['variants']
    root = Path(root)
    ordered_alphabet = fixed.alphabet(root)
    # Expansion preserves exact scope/version; validate shared pins once.
    _inputs(recipe['inputs'], variants[0]['compiled'], root, ordered_alphabet, known_pages)
    controls = storage.expand(recipe['control'])
    fixed.fields(controls, ('kind', 'members'), 'finite program controls')
    require(controls['kind'] == 'finite-program-controls' and type(controls['members']) is list
            and len(controls['members']) == len(variants), 'one complete control per declared member required')
    for member, variant in zip(controls['members'], variants):
        fixed.fields(member, ('settings', 'control'), 'finite control member')
        require(fixed.stable(member['settings']) == fixed.stable(variant['settings']),
                'control settings must match each unique member in canonical expansion order')
        _control(member['control'], variant['compiled'], ordered_alphabet)
    return recipe


def validate_followups(value, root, known_pages=None):
    """Dispatch by explicit kind; preserve the existing fixed recipe branch."""
    require(type(value) is list and 1 <= len(value) <= 8, 'need 1..8 recipes')
    seen = set()
    for recipe in value:
        require(type(recipe) is dict and type(recipe.get('id')) is str
                and recipe['id'] not in seen, 'invalid or duplicate recipe id')
        seen.add(recipe['id'])
        if 'kind' in recipe:
            validate_recipe(recipe, root, known_pages)
        else:
            fixed.validate_followups([recipe], root, known_pages)
    return value


def construct_followup(root, *, card, identifier, title, question, scope_change,
                       limitation, motivation=None):
    """Construct one generic finite source recipe; no files or targets execute.

    Each explicit member inverse-encodes the same independently documented full
    Warning. Noninvertible or unencodable members fail instead of substituting
    another witness, changing the declared settings or discarding alternatives.
    """
    root = Path(root)
    expanded = finite.compile_card(card)
    ordered_alphabet = fixed.alphabet(root)
    plaintext, expected = fixed.warning_plaintext(root, ordered_alphabet)
    members = []
    for n, variant in enumerate(expanded['variants']):
        plan = variant['compiled']
        require(plan['criterion']['kind'] in ('measurement', 'language-score', 'exact-prefix'), 'finite controls support transform evaluations only')
        encoded = plaintext
        for step in reversed(plan['steps']):
            encoded = fixed.inverse_step(encoded, step, ordered_alphabet)
        task = {'schema': fixed.runner.TASK_SCHEMA, 'engine': fixed.runner.ENGINE,
                'title': 'Synthetic complete-output finite control: ' + identifier + ' member ' + str(n + 1),
                'pages': [{'id': 'lp1-01', 'text': encoded}], 'alphabet': copy.deepcopy(ordered_alphabet),
                'steps': copy.deepcopy(plan['steps']), 'criterion': {'kind': 'exact-prefix', 'values': expected[:]}}
        task['taskId'] = fixed.runner.task_identity(task)
        result = fixed.runner.run(task)
        require(result['transformed'][0]['text'] == plaintext, 'independent complete Warning recovery failed')
        members.append({'settings': copy.deepcopy(variant['settings']), 'control': {
            'label': 'Recover every known Warning rune from synthetic ciphertext',
            'task': task, 'expected_result_sha256': fixed.digest(result)}})
    plan = expanded['variants'][0]['compiled']
    pins = []
    for page_id in plan['pages']:
        source = json.loads((root / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
        text = source.get('raw' if plan['inputVersion'] == 'raw' else 'reviewed_text')
        require(type(text) is str, 'requested source text unavailable: ' + page_id)
        pins.append({'id': page_id, 'text_sha256': fixed.text_hash(text)})
    recipe = {'kind': 'finite-settings', 'id': identifier, 'title': title, 'question': question,
              'scope_change': scope_change, 'limitation': limitation, 'card': copy.deepcopy(card),
              'inputs': {'version': plan['inputVersion'], 'alphabet_sha256': fixed.digest(ordered_alphabet), 'pages': pins},
              'control': storage.compact({'kind': 'finite-program-controls', 'members': members})}
    if motivation is not None:
        recipe['motivation'] = motivation
    validate_recipe(recipe, root)
    return recipe
