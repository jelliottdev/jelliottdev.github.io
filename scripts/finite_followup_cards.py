"""Independent finite-settings expansion for authored followups, never execution.

The declaration and detached cards mirror finite-settings.js factored.expand.
Every member must also pass the maintained browser_followups fixed compiler;
this is intentionally its conservative primitive subset, not a new compiler.
"""
import copy
import itertools
import math
import re

import browser_followups as fixed

LIMITS = {'programs': 1024, 'cases': 76800, 'pages': 75, 'operations': 8,
          'parameters': 56, 'expandedBytes': 8 * 1024 * 1024}
NAMES = {'a', 'b', 'reset', 'unit', 'key', 'direction', 'interrupts', 'offset'}
UNSAFE = {'__proto__', 'prototype', 'constructor'}
# These exact aliases are canonicalized by ClaimSpecification.normalizeOutcome.
ALIASES = {
    'decipher': ['decipher', 'decipher the text', 'decipher lp2', 'decrypt', 'decrypt the text', 'decrypt lp2', 'solve lp2', 'solving lp2', 'solving', 'solve liber primus', 'find readable text', 'find plaintext', 'recover plaintext', 'produce readable text', 'find readable plaintext'],
    'measure': ['measure', 'test a pattern', 'test a statistical effect', 'test statistical effect', 'measure a pattern', 'test a statistical pattern'],
    'reproduce': ['reproduce', 'reproduce a result', 'reproduce an existing result', 'replicate a result', 'rerun a result'],
    'explain': ['explain', 'explain a feature', 'explain a manuscript feature'],
    'verify_source': ['verify source material', 'verify the source', 'check source material', 'verify a transcription', 'check a transcription'],
}


def require(condition, message):
    if not condition:
        raise ValueError('finite_followup_cards: ' + message)


def exact(value, keys):
    return type(value) is dict and set(value) == set(keys)


def capture(value, depth=0, budget=None):
    """Bound and detach JSON before inspecting nested fields."""
    if budget is None:
        budget = [0]
    budget[0] += 1
    require(depth <= 16 and budget[0] <= 6000, 'card structure bounds exceeded')
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            require(not any(0xD800 <= ord(c) <= 0xDFFF for c in value), 'invalid Unicode string')
        return value
    if type(value) in (int, float):
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        require(finite, 'finite JSON numbers required')
        return int(value) if value == int(value) else value
    if type(value) is list:
        return [capture(v, depth + 1, budget) for v in value]
    require(type(value) is dict and all(type(k) is str and k not in UNSAFE for k in value), 'unsafe or non-JSON object')
    return {k: capture(v, depth + 1, budget) for k, v in value.items()}


def size(value):
    return len(fixed.stable(value).encode('utf-8'))


def canonical(card):
    card = capture(card)
    require(size(card) <= 12000, 'canonical card exceeds 12000 bytes')
    require(exact(card, ('version', 'outcome', 'method', 'scope', 'rules', 'unresolved'))
            and type(card['version']) is int and card['version'] == 1, 'canonical card fields/version')
    for name in ('outcome', 'method', 'scope'):
        fixed.field(card[name], name)
    if card['outcome']['status'] == 'specified':
        value = card['outcome']['value']
        require(exact(value, ('outcomeId', 'detail')) and value['outcomeId'] in fixed.OUTCOMES
                and type(value['detail']) is str, 'canonical outcome')
        if value['outcomeId'] == 'unclassified':
            alias = value['detail'].strip().lower()
            if alias[-1:] in ('.', '!', '?'):
                alias = alias[:-1].strip()
            require(not any(alias in values for values in ALIASES.values()), 'outcome alias is not canonical')
    require(exact(card['rules'], fixed.RULES), 'complete canonical rule fields required')
    for name, value in card['rules'].items():
        fixed.field(value, name)
    require(type(card['unresolved']) is list and len(card['unresolved']) <= 64, 'canonical unresolved constraints')
    require(card['method']['status'] == 'specified' and exact(card['method']['value'], ('operations',)), 'specified ordered operations required')
    operations = card['method']['value']['operations']
    require(type(operations) is list and 1 <= len(operations) <= LIMITS['operations'], 'need one to eight operations')
    for op in operations:
        require(type(op) is dict and type(op.get('id')) is str and op['id'].strip()
                and not {'sourceText', 'provenance', 'editHistory'}.intersection(op), 'canonical operation')
    require(card['scope']['status'] == 'specified' and exact(card['scope']['value'], ('pages',)), 'exact page scope required')
    pages = card['scope']['value']['pages']
    require(type(pages) is list and 1 <= len(pages) <= LIMITS['pages']
            and all(type(p) is str and re.fullmatch(r'lp[12]-[0-9]{2}', p)
                    and int(p[4:]) <= (16 if p.startswith('lp1') else 57) for p in pages)
            and pages == sorted(set(pages)), 'canonical unique ordered pages required')
    return card


def literal(name, value):
    if name in ('a', 'b'):
        require(type(value) is int and 0 <= value <= 28, 'affine index must be 0..28')
    elif name == 'offset':
        require(type(value) is int and 0 <= value <= 28, 'sequence offset must be 0..28')
    elif name in ('reset', 'unit'):
        require(value in ('page', 'line', 'word'), 'boundary must be page, line or word')
    elif name == 'direction':
        require(value in ('subtract', 'add'), 'direction must be add or subtract')
    elif name in ('key', 'interrupts'):
        require(type(value) is list and 1 <= len(value) <= (20000 if name == 'key' else 29)
                and all(type(n) is int and 0 <= n <= 28 for n in value), 'explicit GP index array required')
        if name == 'interrupts':
            require(value == sorted(set(value)), 'interrupts must be sorted distinct indices')
    else:
        raise ValueError('finite_followup_cards: unsupported axis')
    return copy.deepcopy(value)


def member_card(card, settings):
    member = copy.deepcopy(card)
    member['rules']['searchBounds'] = {'status': 'not_applicable'}
    for setting in settings:
        member['method']['value']['operations'][setting['operation']][setting['name']] = copy.deepcopy(setting['value'])
    return canonical(member)


def _expand(input_card, include_compiled):
    card = canonical(input_card)
    bound = card['rules']['searchBounds']
    require(bound['status'] == 'specified' and exact(bound['value'], ('kind', 'version', 'parameters'))
            and bound['value']['kind'] == 'finite-settings' and type(bound['value']['version']) is int
            and bound['value']['version'] == 1, 'declare version 1 finite-settings')
    axes = bound['value']['parameters']
    require(type(axes) is list and 1 <= len(axes) <= LIMITS['parameters'], 'bounded nonempty axes required')
    operations = card['method']['value']['operations']
    parameters, seen, count = [], set(), 1
    for axis in axes:
        require(exact(axis, ('operation', 'name', 'values')) and type(axis['operation']) is int
                and 0 <= axis['operation'] < len(operations) and type(axis['name']) is str
                and axis['name'] in NAMES and type(axis['values']) is list
                and 1 <= len(axis['values']) <= LIMITS['programs'], 'axis needs an existing operation and supported explicit values')
        identity = (axis['operation'], axis['name'])
        require(identity not in seen, 'repeated parameter')
        seen.add(identity)
        require(axis['name'] not in operations[axis['operation']], 'cannot replace supplied fixed parameter')
        values = [literal(axis['name'], v) for v in axis['values']]
        require(len({fixed.stable(v) for v in values}) == len(values), 'repeated alternative')
        # Each axis has one literal type; lists use numeric lexicographic order.
        values.sort()
        count *= len(values)
        require(count <= LIMITS['programs'], 'exceeds 1024 programs; nothing truncated')
        parameters.append({'operation': axis['operation'], 'name': axis['name'], 'values': values})
    parameters.sort(key=lambda a: (a['operation'], a['name']))
    cases = count * len(card['scope']['value']['pages'])
    require(cases <= LIMITS['cases'], 'exceeds 76800 program-page cases; nothing truncated')
    declaration = {'kind': 'finite-settings', 'version': 1, 'parameters': parameters,
                   'programCount': count, 'caseCount': cases}
    largest = [{'operation': a['operation'], 'name': a['name'], 'value': max(a['values'], key=size)} for a in parameters]
    maximum = {'settings': largest, 'card': member_card(card, largest)}
    require(size({'declaration': declaration, 'variants': []}) + count * (size(maximum) + 1)
            <= LIMITS['expandedBytes'], 'exceeds 8 MiB detached budget; nothing truncated')
    variants = []
    for values in itertools.product(*(a['values'] for a in parameters)):
        settings = [{'operation': a['operation'], 'name': a['name'], 'value': copy.deepcopy(v)} for a, v in zip(parameters, values)]
        member = member_card(card, settings)
        compiled = fixed.compile_card(member)
        variant = {'settings': settings, 'card': member}
        if include_compiled:
            variant['compiled'] = compiled
        variants.append(variant)
    return {'declaration': declaration, 'variants': variants}


def expand(card):
    """Return JS-parity detached cards, validating every fixed program."""
    return _expand(card, False)


def compile_card(card):
    """Also return the existing fixed compiler's plan for every member."""
    return _expand(card, True)
