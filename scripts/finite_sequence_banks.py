"""Four audited finite streams. A bank pin authorizes only its stored 305 terms.

get(id, sha256) returns a detached descriptor. resolve(id, sha256, offset)
returns the entire stored tail, without repetition, truncation or extension.
Offsets 0..28 preserve the source's named settings, including Fibonacci aliases.
Neither API executes a manuscript transform or evaluates a proposed plaintext.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'prime-minus-one-v1': '61add0f42e87c8d2b71a32e54d1b005ac4ca77c5b818bf52d97600da248988dc',
    'prime-v1': '3e0668ec3551b8dce1245a918c614b6861b80d210fe492d29c9b261439b21bcc',
    'fibonacci-v1': '6e3475d825d2da7975e139407b1af1c7f2d908deb0c5ab0c91db39ac2b4c31b8',
    'totient-v1': '822e947c36fd3ebf492ab5e8e2d86f287e2348968b99ccccb1aa4b4edf9dc75d'}


def require(condition, message):
    if not condition:
        raise ValueError('finite_sequence_banks: ' + message)


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def bank_hash(identifier, values):
    return hashlib.sha256(stable({'schema': 'liberpedia-finite-sequence-bank-v1',
                                 'id': identifier, 'values': values}).encode()).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field')
        result[key] = value
    return result


def get(identifier, sha256):
    require(type(identifier) is str and identifier in PINS and type(sha256) is str
            and sha256 == PINS[identifier], 'unknown bank or unsupported hash')
    raw = (ROOT / 'data/finite-sequence-banks.json').read_bytes()
    require(len(raw) <= 256 * 1024, 'bank manifest exceeds bound')
    value = json.loads(raw, object_pairs_hook=_object,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite bank JSON')))
    require(type(value) is dict and set(value) == {'schema', 'banks', 'sourceAudit'}
            and value['schema'] == 'finite-sequence-banks-v1' and type(value['banks']) is list
            and len(value['banks']) == 4, 'invalid bank manifest')
    seen = set()
    for bank in value['banks']:
        require(type(bank) is dict and set(bank) == {'id', 'sha256', 'values'}
                and type(bank['id']) is str and bank['id'] in PINS and bank['id'] not in seen,
                'invalid bank descriptor')
        seen.add(bank['id'])
        require(type(bank['values']) is list and len(bank['values']) == 305
                and all(type(n) is int and 0 <= n <= 28 for n in bank['values'])
                and bank['sha256'] == PINS[bank['id']] == bank_hash(bank['id'], bank['values']),
                'bank data or hash changed')
    require(seen == set(PINS), 'incomplete bank manifest')
    return next(bank for bank in value['banks'] if bank['id'] == identifier)


def resolve(identifier, sha256, offset):
    require(type(offset) is int and 0 <= offset <= 28, 'audited offset must be an integer 0..28')
    return get(identifier, sha256)['values'][offset:]
