"""Lossless finite synthetic-control storage codec, without execution authority.

compact(control) shares identical alphabets and complete-prefix criteria when
the legacy structure permits it. Unsupported/nonshared legacy JSON is copied
unchanged. expand(control) restores the legacy envelope. Recognized compact
envelopes are strictly structural; task identities, pins and scientific control
validity remain the responsibility of the existing caller after expansion.
"""
import json
import math
import re

LEGACY = 'finite-program-controls'
COMPACT = 'finite-program-controls-shared-v1'
LIMITS = {'bytes': 2 * 1024 * 1024, 'depth': 24, 'nodes': 300_000, 'members': 1024}
TASK_FIELDS = {'schema', 'engine', 'title', 'pages', 'steps', 'taskId'}
HEX = re.compile(r'[a-f0-9]{64}')


def require(condition, message):
    if not condition:
        raise ValueError('finite_control_storage: ' + message)


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _capture(value):
    """Reject Python objects/subclasses before accessing user-defined methods."""
    budget = [0, 0]
    def visit(item, depth=0):
        budget[0] += 1
        require(depth <= LIMITS['depth'] and budget[0] <= LIMITS['nodes'], 'JSON structure bounds exceeded')
        if item is None or type(item) is bool:
            return item
        if type(item) in (int, float):
            try:
                valid = math.isfinite(item)
            except OverflowError:
                valid = False
            require(valid, 'finite JSON numbers required')
            return item
        if type(item) is str:
            require(not any(0xD800 <= ord(char) <= 0xDFFF for char in item), 'invalid Unicode')
            budget[1] += len(item.encode('utf-8'))
            require(budget[1] <= LIMITS['bytes'], 'JSON byte bound exceeded')
            return item
        if type(item) is list:
            return [visit(child, depth + 1) for child in item]
        require(type(item) is dict, 'plain JSON objects required')
        result = {}
        for key, child in item.items():
            require(type(key) is str and key not in ('__proto__', 'constructor', 'prototype'), 'unsafe JSON key')
            visit(key, depth + 1)
            result[key] = visit(child, depth + 1)
        return result
    result = visit(value)
    require(len(stable(result).encode('utf-8')) <= LIMITS['bytes'], 'JSON byte bound exceeded')
    return result


def _exact(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), 'exact ' + label + ' fields required')


def _validate(value):
    _exact(value, ('kind', 'alphabet', 'criterion', 'members'), 'compact envelope')
    require(value['kind'] == COMPACT, 'unknown compact kind')
    alphabet, criterion = value['alphabet'], value['criterion']
    require(type(alphabet) is list and len(alphabet) == 29, 'shared alphabet needs 29 entries')
    for row in alphabet:
        _exact(row, ('rune', 'latin', 'prime'), 'alphabet row')
        require(type(row['rune']) is str and len(row['rune']) == 1
                and type(row['latin']) is str and 1 <= len(row['latin']) <= 16
                and type(row['prime']) is int and 0 < row['prime'] <= 1_000_000,
                'invalid alphabet field types')
    _exact(criterion, ('kind', 'values'), 'shared criterion')
    require(criterion['kind'] == 'exact-prefix' and type(criterion['values']) is list
            and 1 <= len(criterion['values']) <= 256
            and all(type(n) is int and 0 <= n <= 28 for n in criterion['values']),
            'shared criterion must be a bounded exact prefix')
    require(type(value['members']) is list and 1 <= len(value['members']) <= LIMITS['members'], 'need 1..1024 members')
    for member in value['members']:
        _exact(member, ('settings', 'control'), 'member')
        require(type(member['settings']) is list and len(member['settings']) <= 56, 'bounded settings array required')
        for setting in member['settings']:
            _exact(setting, ('operation', 'name', 'value'), 'setting')
            require(type(setting['operation']) is int and 0 <= setting['operation'] < 8
                    and type(setting['name']) is str and 1 <= len(setting['name']) <= 32,
                    'invalid setting fields')
        control = member['control']
        _exact(control, ('label', 'task', 'expected_result_sha256'), 'control')
        require(type(control['label']) is str and 1 <= len(control['label']) <= 1200
                and type(control['expected_result_sha256']) is str
                and HEX.fullmatch(control['expected_result_sha256']), 'invalid control label or digest')
        task = control['task']
        _exact(task, TASK_FIELDS, 'compact task')
        require(all(type(task[key]) is str and 1 <= len(task[key]) <= limit
                    for key, limit in [('schema', 100), ('engine', 100), ('title', 300)])
                and type(task['taskId']) is str and HEX.fullmatch(task['taskId']), 'invalid task metadata')
        require(type(task['pages']) is list and 1 <= len(task['pages']) <= 75, 'bounded task pages required')
        for page in task['pages']:
            _exact(page, ('id', 'text'), 'task page')
            require(type(page['id']) is str and 1 <= len(page['id']) <= 100 and type(page['text']) is str,
                    'invalid task page fields')
        require(type(task['steps']) is list and len(task['steps']) <= 8
                and all(type(step) is dict for step in task['steps']), 'bounded task steps required')
    return value


def compact(control):
    """Detach JSON; share exact common fields, otherwise preserve legacy JSON."""
    value = _capture(control)
    if type(value) is not dict:
        return value
    require(not (type(value.get('kind')) is str and value['kind'].startswith('finite-program-controls-shared')
                 and value['kind'] != COMPACT), 'unsupported shared control version')
    if value.get('kind') == COMPACT:
        return _validate(value)
    if set(value) != {'kind', 'members'} or value.get('kind') != LEGACY:
        return value
    members = value.get('members')
    if type(members) is not list or not members:
        return value
    try:
        first = members[0]['control']['task']
        alphabet, criterion = first['alphabet'], first['criterion']
        common = (stable(alphabet), stable(criterion))
        detached = _capture(value)
        for member in detached['members']:
            task = member['control']['task']
            if (stable(task['alphabet']), stable(task['criterion'])) != common:
                return value
            del task['alphabet']
            del task['criterion']
        result = {'kind': COMPACT, 'alphabet': alphabet, 'criterion': criterion, 'members': detached['members']}
        return _validate(result)
    except (KeyError, TypeError, ValueError):
        # Unsupported legacy formats still receive their ordinary full caller
        # validation. The codec must not silently remove any unknown field.
        return value


def expand(control):
    """Restore exact legacy stable JSON; malformed known compact forms fail."""
    value = _capture(control)
    if type(value) is dict:
        require(not (type(value.get('kind')) is str and value['kind'].startswith('finite-program-controls-shared')
                     and value['kind'] != COMPACT), 'unsupported shared control version')
    if type(value) is not dict or value.get('kind') != COMPACT:
        return value
    _validate(value)
    members = []
    for member in value['members']:
        # Detach shared values per task as well; callers may edit one returned
        # member without changing a sibling's alphabet or expected output.
        restored = _capture(member)
        restored['control']['task']['alphabet'] = _capture(value['alphabet'])
        restored['control']['task']['criterion'] = _capture(value['criterion'])
        members.append(restored)
    result = {'kind': LEGACY, 'members': members}
    return _capture(result)
