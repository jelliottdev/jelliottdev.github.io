"""Detached count-bounded planning; no target execution or admission authority.

registry is a trusted internal audit/test seam, not caller-supplied wire data.
Default bank references must match the maintained pinned registry completely.
"""
import copy
import hashlib
import json
import math
import re
import unicodedata
import build_repeating_key_banks as banks

SCHEMA = 'liberpedia-pinned-program-domain-v1'
PLAN = 'liberpedia-pinned-domain-partitions-v1'
MAX = 8 * 1024 * 1024
SAFE = 2 ** 53 - 1
ALPHABET = '06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f'
HEX = re.compile(r'[a-f0-9]{64}')
PAGE = re.compile(r'lp(?:1-(?:0[0-9]|1[0-6])|2-(?:[0-4][0-9]|5[0-7]))')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def stable(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def capture(value, max_bytes=2 * 1024 * 1024):
    seen, nodes = set(), 0
    def visit(v, depth):
        nonlocal nodes
        nodes += 1
        need(nodes <= 500000 and depth <= 24, 'Pinned domain exceeds its node or depth bound')
        if v is None or type(v) is bool:
            return v
        if type(v) in (int, float):
            need(math.isfinite(v), 'Invalid JSON number')
            return int(v) if type(v) is float and v.is_integer() else v
        if type(v) is str:
            need(not any(0xD800 <= ord(ch) <= 0xDFFF for ch in v), 'Invalid Unicode in pinned domain')
            return v
        need(type(v) in (dict, list) and id(v) not in seen, 'Use plain acyclic pinned domain JSON')
        seen.add(id(v))
        if type(v) is list:
            out = [visit(x, depth + 1) for x in v]
        else:
            need(all(type(k) is str and k not in ('__proto__', 'constructor', 'prototype') for k in v), 'Invalid JSON object key')
            out = {}
            for k, x in v.items():
                need(not any(0xD800 <= ord(ch) <= 0xDFFF for ch in k), 'Invalid Unicode in pinned domain')
                out[k] = visit(x, depth + 1)
        seen.remove(id(v))
        return out
    result = visit(value, 0)
    need(len(stable(result).encode()) <= max_bytes, 'Pinned domain exceeds its byte bound')
    return result


def exact(v, keys):
    return type(v) is dict and set(v) == set(keys)


def integer(v, minimum, maximum):
    return type(v) is int and minimum <= v <= maximum


def vector(v, maximum):
    return type(v) is list and 1 <= len(v) <= maximum and all(integer(n, 0, 28) for n in v)


def pins(values):
    need(type(values) is list and 1 <= len(values) <= 1024, 'Declare bounded source pins')
    seen = set()
    for p in values:
        need(exact(p, ('path', 'sha256')) and type(p['path']) is str and len(p['path']) <= 350
             and re.fullmatch(r'[a-zA-Z0-9_./-]+', p['path']) and all(s and s not in ('.', '..') for s in p['path'].split('/'))
             and type(p['sha256']) is str and HEX.fullmatch(p['sha256']) and p['path'] not in seen, 'Invalid or conflicting source pin')
        seen.add(p['path'])


def openings(c):
    if exact(c, ('kind',)) and c['kind'] == 'measurement':
        return None
    if exact(c, ('kind', 'values')) and c['kind'] == 'exact-prefix' and vector(c['values'], 256):
        return 1
    if c == dict(kind='language-score', modelId='gp29-flores-trigram-v1', modelSha256='8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'):
        return None
    need(exact(c, ('kind', 'openings')) and c['kind'] == 'exact-prefix-set' and type(c['openings']) is list and 1 <= len(c['openings']) <= 32, 'Unsupported declared evaluation')
    ids, vectors = set(), set()
    for o in c['openings']:
        need(exact(o, ('id', 'values')) and type(o['id']) is str and re.fullmatch(r'[a-z][a-z0-9-]{0,63}', o['id']) and vector(o['values'], 256)
             and o['id'] not in ids and stable(o['values']) not in vectors, 'Invalid exact opening set')
        ids.add(o['id'])
        vectors.add(stable(o['values']))
    return len(ids)


def step(s, keyless):
    op = s.get('op') if type(s) is dict else None
    fields = {'reverse': ['op', 'unit'], 'affine': ['op', 'a', 'b'], 'cumulative-difference': ['op', 'reset'],
              'keyed-shift': ['op', 'mode', 'direction', 'reset'] + ([] if keyless else ['key']),
              'finite-shift': ['op', 'direction', 'reset'] + ([] if keyless else ['key']),
              'interrupted-keyed-shift': ['op', 'direction', 'reset', 'interrupts', 'key']}.get(op)
    need(fields is not None and exact(s, fields), 'Unsupported or ambiguous ordered operation')
    if op == 'reverse':
        need(s['unit'] in ('page', 'line', 'word'), 'Invalid reversal boundary')
    elif op == 'affine':
        need(integer(s['a'], 0, 28) and integer(s['b'], 0, 28), 'Invalid affine numbers')
    else:
        need(s['reset'] in ('page', 'line', 'word'), 'Invalid reset')
        if op != 'cumulative-difference':
            need(s['direction'] in ('add', 'subtract'), 'Invalid arithmetic direction')
            if op == 'keyed-shift':
                need(s['mode'] in ('repeat', 'plaintext-autokey', 'ciphertext-autokey'), 'Invalid key mode')
            if not keyless:
                need(vector(s['key'], 20000 if op == 'finite-shift' else 256), 'Invalid fixed literal key')
            if op == 'interrupted-keyed-shift':
                need(vector(s['interrupts'], 29) and all(a < b for a, b in zip(s['interrupts'], s['interrupts'][1:])), 'Invalid interruptions')


def digest(value):
    return hashlib.sha256(stable(value).encode()).hexdigest()


class MaintainedRegistry:
    """One source authentication per planning session; detached bounded replies."""
    def __init__(self):
        data = banks.prepare()
        need(json.loads((banks.ROOT / 'data/repeating-key-banks.json').read_bytes()) == data,
             'The maintained repeating key banks changed')
        self._banks = {b['id']: copy.deepcopy(b) for b in data['banks']}
        self._vectors = {}

    def list(self):
        return [{k: copy.deepcopy(v) for k, v in b.items() if k != 'seeds'} for b in self._banks.values()]

    def resolve(self, ref):
        need(exact(ref, ('bankId', 'bankSha256', 'start', 'count')), 'Use an exact repeating key bank slice')
        bank = self._banks.get(ref['bankId']) if type(ref['bankId']) is str else None
        need(bank is not None and bank['sha256'] == ref['bankSha256']
             and integer(ref['start'], 0, SAFE) and integer(ref['count'], 1, 1024)
             and ref['start'] + ref['count'] <= bank['total'], 'Repeating key bank slice is outside its exact bounds')
        if bank['id'] not in self._vectors:
            values = banks.vectors(bank)
            need(len(values) == bank['total'] and all(vector(k, 324) for k in values), 'The maintained complete vectors changed')
            self._vectors[bank['id']] = tuple(tuple(key) for key in values)
        return [list(key) for key in self._vectors[bank['id']][ref['start']:ref['start'] + ref['count']]]


def prepare(value, registry=None):
    domain = capture(value)
    def unchanged():
        need(stable(capture(value)) == stable(domain), 'The declared domain changed during planning')
    registry = MaintainedRegistry() if registry is None else registry
    need(exact(domain, ('schema', 'aim', 'bank', 'keyOperation', 'steps', 'inputVersion', 'pages', 'alphabetSha256', 'criterion', 'sourcePins')) and domain['schema'] == SCHEMA, 'Use an exact pinned program domain')
    aim = domain['aim']
    need(exact(aim, ('outcomeId', 'detail')) and aim['outcomeId'] in ('decipher', 'measure', 'reproduce', 'explain', 'verify_source')
         and type(aim['detail']) is str and aim['detail'].strip() == aim['detail'] and 1 <= len(aim['detail']) <= 1000
         and not any(unicodedata.category(ch) in ('Cc', 'Cf') for ch in aim['detail']), 'Declare an explicit essential aim and bounded plain detail')
    ref = domain['bank']
    need(exact(ref, ('bankId', 'bankSha256', 'start', 'count')) and type(ref['bankId']) is str and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', ref['bankId']) and type(ref['bankSha256']) is str and HEX.fullmatch(ref['bankSha256']) and ref['start'] == 0 and type(ref['start']) is int and integer(ref['count'], 1, SAFE), 'Declare the complete pinned bank, starting at zero')
    need(domain['inputVersion'] in ('raw', 'reviewed') and domain['alphabetSha256'] == ALPHABET, 'Declare the canonical alphabet and exact input edition')
    pins(domain['sourcePins'])
    need(type(domain['pages']) is list and 1 <= len(domain['pages']) <= 75, 'Declare one to75 complete ordered pages')
    seen_pages = set()
    for p in domain['pages']:
        need(exact(p, ('id', 'textSha256')) and type(p['id']) is str and len(p['id']) == 6 and PAGE.fullmatch(p['id']) and type(p['textSha256']) is str and HEX.fullmatch(p['textSha256']) and p['id'] not in seen_pages, 'Invalid or repeated page source pin')
        seen_pages.add(p['id'])
    need(type(domain['steps']) is list and 1 <= len(domain['steps']) <= 8 and integer(domain['keyOperation'], 0, len(domain['steps']) - 1) and type(domain['steps'][domain['keyOperation']]) is dict and domain['steps'][domain['keyOperation']].get('op') in ('keyed-shift', 'finite-shift'), 'Choose one ordered key-bank operation')
    for i, s in enumerate(domain['steps']):
        step(s, i == domain['keyOperation'])
    opening_count = openings(domain['criterion'])
    metadata = capture(registry.list())
    unchanged()
    need(type(metadata) is list, 'Invalid maintained bank metadata')
    need(all(type(b) is dict for b in metadata), 'Invalid maintained bank metadata')
    matches = [b for b in metadata if b.get('id') == ref['bankId'] and b.get('sha256') == ref['bankSha256']]
    need(len(matches) == 1 and type(matches[0]['total']) is int and matches[0]['total'] == ref['count'], 'The declared bank is not the complete maintained pinned domain')
    bank = matches[0]
    pins(bank['sourcePins'])
    need(all(p in domain['sourcePins'] for p in bank['sourcePins']), 'The domain omitted a maintained bank source pin')
    seen, retained, maximum, over = set(), 0, 0, 0
    # Maintained vectors are independently checked at <=324; unknown internal
    # registries retain the smaller reply bound for vectors up to20,000 values.
    scan = 128 if type(registry) is MaintainedRegistry else 16
    for start in range(0, ref['count'], scan):
        count = min(scan, ref['count'] - start)
        keys = capture(registry.resolve({**ref, 'start': start, 'count': count}), MAX)
        unchanged()
        need(type(keys) is list and len(keys) == count, 'The maintained bank silently truncated a planning scan')
        for key in keys:
            need(vector(key, 20000), 'The maintained bank returned an invalid complete vector')
            signature = stable(key)
            need(signature not in seen, 'The maintained bank repeated a vector')
            seen.add(signature)
            retained += len(signature.encode())
            need(retained <= MAX, 'The complete bank exceeds the bounded planning scan budget')
            maximum = max(maximum, len(key))
            over += len(key) > 256
    domain_id = 'd_' + digest(domain)
    per_slice = min(1024, 76800 // len(domain['pages']))
    jobs, planned = [], len(stable(domain).encode()) + 1024
    for start in range(0, ref['count'], per_slice):
        count = min(per_slice, ref['count'] - start)
        key_range = dict(start=start, count=count)
        job = dict(id='j_' + digest(dict(schema='liberpedia-pinned-domain-slice-id-v1', domainId=domain_id, range=key_range)), domainId=domain_id,
                   bank={**ref, **key_range}, programs=count, pageCases=count * len(domain['pages']), openingComparisons=None if opening_count is None else count * len(domain['pages']) * opening_count)
        planned += len(stable(job).encode()) + 1
        need(planned <= MAX, 'The complete partition plan exceeds its byte bound')
        jobs.append(job)
    counters = dict(programs=ref['count'], pages=len(domain['pages']), pageCases=ref['count'] * len(domain['pages']), openingComparisons=None if opening_count is None else ref['count'] * len(domain['pages']) * opening_count)
    need(all(integer(v, 0, SAFE) for v in counters.values() if v is not None), 'Domain counters exceed exact integer arithmetic')
    unchanged()
    return capture(dict(schema=PLAN, status='planning-only', domainId=domain_id, domain=domain, jobs=jobs, counters=counters,
                        telemetry=dict(maxKeyLength=maximum, overRepeatingKeyLimit=over), checks=dict(admission=False, execution=False, controlBudget=False), limits=dict(programsPerSlice=1024, pageCasesPerSlice=76800)), MAX)


def validate(domain, plan, registry=None):
    snapshot, expected = capture(plan, MAX), prepare(domain, registry)
    need(stable(capture(plan, MAX)) == stable(snapshot) and stable(snapshot) == stable(expected), 'The detached partition plan changed')
    return expected
