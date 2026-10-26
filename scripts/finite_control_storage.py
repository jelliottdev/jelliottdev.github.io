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
POOLED = 'finite-program-controls-pooled-v1'
ASCII64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
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
    if type(value.get('kind')) is str and value['kind'].startswith('finite-program-controls-pooled'):
        require(value['kind'] == POOLED, 'unsupported pooled control version')
        _expand_pooled(value)
        return value
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
    if type(value) is dict and type(value.get('kind')) is str and value['kind'].startswith('finite-program-controls-pooled'):
        require(value['kind'] == POOLED, 'unsupported pooled control version')
        return _expand_pooled(value)
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


class _PackedText:
    def __init__(self, entry, symbols):
        self.entry, self.symbols = entry, symbols
        if entry[0] == 0:
            self.bytes = len(stable(entry[1]).encode('utf8'))
        else:
            costs = [len(stable(symbol).encode('utf8')) - 2 for symbol in symbols]
            self.bytes = 2 + sum(costs[ASCII64.index(ch)] for ch in entry[1])
        require(self.bytes <= LIMITS['bytes'], 'expanded text exceeds JSON byte bound')

    def decode(self):
        return self.entry[1] if self.entry[0] == 0 else ''.join(self.symbols[ASCII64.index(ch)] for ch in self.entry[1])


def _pool_ref(pool, ref):
    require(type(ref) is int and 0 <= ref < len(pool), 'invalid pooled reference')
    return pool[ref]


def _key(value):
    return type(value) is list and 1 <= len(value) <= 20000 and all(type(n) is int and 0 <= n <= 28 for n in value)


def _preflight(value):
    """Measure virtual expanded JSON before decoding text or copying pooled keys."""
    nodes = [0]
    def visit(item, depth=0):
        nodes[0] += 1
        require(depth <= LIMITS['depth'] and nodes[0] <= LIMITS['nodes'], 'expanded JSON structure bounds exceeded')
        if isinstance(item, _PackedText):
            return item.bytes
        if type(item) is dict:
            total = 2 + max(0, len(item) - 1)
            for k, v in item.items():
                total += visit(k, depth + 1) + 1 + visit(v, depth + 1)
                require(total <= LIMITS['bytes'], 'expanded JSON byte bound exceeded')
            return total
        if type(item) is list:
            total = 2 + max(0, len(item) - 1)
            for v in item:
                total += visit(v, depth + 1)
                require(total <= LIMITS['bytes'], 'expanded JSON byte bound exceeded')
            return total
        return len(stable(item).encode('utf8'))
    require(visit(value) <= LIMITS['bytes'], 'expanded JSON byte bound exceeded')


def _expand_pooled(value):
    _exact(value, ('kind', 'alphabet', 'criterion', 'textSymbols', 'pools', 'rows'), 'pooled envelope')
    require(value['kind'] == POOLED, 'unknown pooled kind')
    symbols, pools, rows = value['textSymbols'], value['pools'], value['rows']
    require(type(symbols) is list and len(symbols) <= 64 and all(type(ch) is str and len(ch) == 1 for ch in symbols)
            and len(set(symbols)) == len(symbols), 'invalid pooled text symbols')
    _exact(pools, ('strings', 'keys', 'texts', 'steps'), 'pools')
    require(all(type(pool) is list for pool in pools.values()), 'pooled arrays required')
    require(all(type(v) is str for v in pools['strings']) and all(_key(k) for k in pools['keys']), 'invalid pooled strings or keys')
    used = {name: set() for name in pools}
    def ref(name, index):
        result = _pool_ref(pools[name], index)
        used[name].add(index)
        return result
    texts = []
    for entry in pools['texts']:
        require(type(entry) is list and len(entry) == 2 and type(entry[0]) is int and entry[0] in (0, 1)
                and type(entry[1]) is str, 'invalid pooled text entry')
        if entry[0] == 1:
            require(all(ch in ASCII64 and ASCII64.index(ch) < len(symbols) for ch in entry[1]), 'invalid encoded text symbol')
        texts.append(_PackedText(entry, symbols))
    steps = []
    for entry in pools['steps']:
        require(type(entry) is list and len(entry) == 2 and type(entry[0]) is dict, 'invalid pooled step')
        step = dict(entry[0])
        if entry[1] is not None:
            require('key' not in step, 'ambiguous pooled step key')
            step['key'] = _pool_ref(pools['keys'], entry[1])
        steps.append(step)
    require(type(rows) is list and 1 <= len(rows) <= LIMITS['members'], 'need1..1024 pooled rows')
    members = []
    for row in rows:
        require(type(row) is list and len(row) == 9 and type(row[0]) is list and len(row[0]) <= 56
                and type(row[5]) is list and 1 <= len(row[5]) <= 75 and type(row[6]) is list and len(row[6]) <= 8,
                'invalid pooled row')
        settings = []
        for setting in row[0]:
            require(type(setting) is list and len(setting) == 3 and type(setting[2]) is list
                    and len(setting[2]) == 2 and type(setting[2][0]) is int and setting[2][0] in (0, 1), 'invalid pooled setting')
            tag, literal = setting[2]
            settings.append({'operation': setting[0], 'name': ref('strings', setting[1]),
                             'value': ref('keys', literal) if tag == 1 else literal})
        pages = []
        for page in row[5]:
            require(type(page) is list and len(page) == 2, 'invalid pooled page')
            ref('texts', page[1])
            pages.append({'id': ref('strings', page[0]), 'text': _pool_ref(texts, page[1])})
        task = {'schema': ref('strings', row[1]), 'engine': ref('strings', row[2]),
                'title': ref('strings', row[3]), 'pages': pages,
                'steps': [], 'taskId': row[7]}
        for index in row[6]:
            entry = ref('steps', index)
            if entry[1] is not None:
                ref('keys', entry[1])
            task['steps'].append(_pool_ref(steps, index))
        member = {'settings': settings, 'control': {'label': ref('strings', row[4]), 'task': task, 'expected_result_sha256': row[8]}}
        # Validate all ordinary shared fields with empty text placeholders;
        # actual virtual text JSON costs are checked before decoding below.
        placeholder = {'settings': settings, 'control': {**member['control'], 'task': {**task, 'pages': [{'id': p['id'], 'text': ''} for p in pages]}}}
        _validate({'kind': COMPACT, 'alphabet': value['alphabet'], 'criterion': value['criterion'], 'members': [placeholder]})
        members.append(member)
    require(all(len(used[name]) == len(pools[name]) for name in pools), 'unused pooled control values')
    virtual = {'kind': LEGACY, 'members': [{**m, 'control': {**m['control'], 'task': {**m['control']['task'], 'alphabet': value['alphabet'], 'criterion': value['criterion']}}} for m in members]}
    _preflight(virtual)
    def restore(item):
        if isinstance(item, _PackedText):
            return item.decode()
        if type(item) is list:
            return [restore(v) for v in item]
        if type(item) is dict:
            return {k: restore(v) for k, v in item.items()}
        return item
    return _capture(restore(virtual))


def compact_pooled(control):
    """Explicit lossless opt-in; compact() keeps its shared-v1 default output."""
    value = _capture(control)
    if type(value) is dict and value.get('kind') == POOLED:
        _expand_pooled(value)
        return value
    shared = compact(value)
    if type(shared) is not dict or shared.get('kind') != COMPACT:
        return shared
    members = shared['members']
    symbols = sorted({ch for m in members for p in m['control']['task']['pages'] for ch in p['text']}, key=ord)
    if len(symbols) > 64:
        symbols = []
    symbol_index = {ch: n for n, ch in enumerate(symbols)}
    pools = {'strings': [], 'keys': [], 'texts': [], 'steps': []}
    indexes = {name: {} for name in pools}
    def intern(name, item):
        identity = stable(item)
        if identity not in indexes[name]:
            indexes[name][identity] = len(pools[name])
            pools[name].append(item)
        return indexes[name][identity]
    rows = []
    for member in members:
        task, ctrl = member['control']['task'], member['control']
        settings = []
        for setting in member['settings']:
            settings.append([setting['operation'], intern('strings', setting['name']),
                             [1, intern('keys', setting['value'])] if _key(setting['value']) else [0, setting['value']]])
        metadata = [intern('strings', task[k]) for k in ('schema', 'engine', 'title')]
        metadata.append(intern('strings', ctrl['label']))
        pages = []
        for page in task['pages']:
            packed = [1, ''.join(ASCII64[symbol_index[ch]] for ch in page['text'])] if symbols else [0, page['text']]
            pages.append([intern('strings', page['id']), intern('texts', packed)])
        step_refs = []
        for step in task['steps']:
            if _key(step.get('key')):
                rest = {k: v for k, v in step.items() if k != 'key'}
                packed = [rest, intern('keys', step['key'])]
            else:
                packed = [step, None]
            step_refs.append(intern('steps', packed))
        rows.append([settings, *metadata, pages, step_refs, task['taskId'], ctrl['expected_result_sha256']])
    result = _capture({'kind': POOLED, 'alphabet': shared['alphabet'], 'criterion': shared['criterion'], 'textSymbols': symbols, 'pools': pools, 'rows': rows})
    _expand_pooled(result)
    return result
