"""Author-declared restart variations; source cards only, never execution.

``variants(card, operation_index=0, allowed_resets=['word', 'line'])``
returns independent replacement cards. ``family`` represents exactly those
choices as one finite reset axis. Existing other axes, inputs, scope and the
evaluation are unchanged. Allowed choices may deliberately omit the current
restart; these functions do not claim to exhaust a cipher family.

Compilation checks card grammar and finite expansion bounds. In particular,
finite-key text/segment coverage still requires the ordinary input-aware plan
admission; producing a source card does not grant execution authority.
"""
import copy

import browser_followups as fixed
import finite_followup_cards as finite

OPERATIONS = frozenset(('repeating_key', 'vigenere', 'plaintext_autokey',
                        'ciphertext_autokey', 'interrupted_repeating_key', 'finite_key'))
RESETS = frozenset(('page', 'line', 'word'))


def require(condition, message):
    if not condition:
        raise ValueError('browser_boundary_variations: ' + message)


def _compile(card):
    if card['rules']['searchBounds']['status'] == 'specified':
        return finite.compile_card(card)
    return fixed.compile_card(card)


def _prepare(card, operation_index, allowed_resets):
    # canonical captures bounded plain JSON and detaches it before inspection.
    result = finite.canonical(card)
    require(type(operation_index) is int and 0 <= operation_index < len(result['method']['value']['operations']),
            'author must select one existing operation index')
    require(type(allowed_resets) in (list, tuple) and 1 <= len(allowed_resets) <= 3
            and all(type(value) is str and value in RESETS for value in allowed_resets)
            and len(set(allowed_resets)) == len(allowed_resets),
            'author must supply unique explicit page, line or word choices')
    choices = sorted(allowed_resets)
    selected = result['method']['value']['operations'][operation_index]
    require(selected['id'] in OPERATIONS, 'selected operation has no supported keyed restart variation')
    for name in ('reset', 'boundaryMode'):
        require(result['rules'][name]['status'] not in ('specified', 'unrestricted'),
                'explicit global ' + name + ' must not be silently replaced')
    _compile(result)  # Reject invalid source declarations before any replacement.
    bound = result['rules']['searchBounds']
    axes = bound['value']['parameters'] if bound['status'] == 'specified' else []
    matching = [axis for axis in axes if axis['operation'] == operation_index and axis['name'] == 'reset']
    require(len(matching) <= 1, 'ambiguous existing restart axis')
    if matching:
        require(sorted(matching[0]['values']) == choices,
                'existing restart axis must exactly match explicit allowed choices')
    else:
        require(selected.get('reset') in RESETS, 'source operation needs an explicit fixed restart or matching axis')
    return result, choices, bool(matching)


def variants(card, *, operation_index, allowed_resets):
    """Replace only the author's selected restart, retaining other finite axes.

    An existing selected reset axis must describe exactly the supplied choices.
    It is removed in each replacement, leaving any other axes intact; if it was
    the sole axis, searchBounds becomes not_applicable. Input is never mutated.
    ``compiled`` is the existing fixed or finite compiler result, not a task.
    """
    source, choices, has_axis = _prepare(card, operation_index, allowed_resets)
    rows = []
    for reset in choices:
        value = copy.deepcopy(source)
        value['method']['value']['operations'][operation_index]['reset'] = reset
        if has_axis:
            remaining = [axis for axis in value['rules']['searchBounds']['value']['parameters']
                         if not (axis['operation'] == operation_index and axis['name'] == 'reset')]
            if remaining:
                value['rules']['searchBounds']['value']['parameters'] = remaining
            else:
                value['rules']['searchBounds'] = {'status': 'not_applicable'}
        rows.append({'reset': reset, 'card': value, 'compiled': _compile(value)})
    return rows


def family(card, *, operation_index, allowed_resets):
    """Declare exactly the allowed restarts as one bounded finite source card."""
    value, choices, has_axis = _prepare(card, operation_index, allowed_resets)
    if not has_axis:
        del value['method']['value']['operations'][operation_index]['reset']
        axis = {'operation': operation_index, 'name': 'reset', 'values': choices}
        if value['rules']['searchBounds']['status'] == 'specified':
            value['rules']['searchBounds']['value']['parameters'].append(axis)
        else:
            value['rules']['searchBounds'] = {'status': 'specified', 'value': {
                'kind': 'finite-settings', 'version': 1, 'parameters': [axis]}}
    return {'card': value, 'compiled': finite.compile_card(value)}
