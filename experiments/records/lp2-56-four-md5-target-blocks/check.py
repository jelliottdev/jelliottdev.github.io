"""Independent MD5 target-block check from source-plan files and page-56 literal."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def verified(entry):
    raw = (ROOT / entry['path']).read_bytes()
    if len(raw) != entry['size'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise AssertionError(entry['path'])
    return raw


def variants(text):
    return {
        'exact': text.encode('utf-8'),
        'crlf': text.replace('\n', '\r\n').encode('utf-8'),
        'drop-final-lf': (text[:-1] if text.endswith('\n') else text).encode('utf-8'),
        'one-final-lf': (text.rstrip('\r\n') + '\n').encode('utf-8'),
    }


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    plan_raw = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_raw)
    assert hashlib.sha256(plan_raw).hexdigest() == result['plan_sha256']
    source_raw = (ROOT / plan['candidate_plan']['path']).read_bytes()
    assert hashlib.sha256(source_raw).hexdigest() == plan['candidate_plan']['sha256'] == result['candidate_plan_sha256']
    source = json.loads(source_raw)
    page = json.loads((ROOT / plan['printed_target']['path']).read_text(encoding='utf-8'))
    literal = page['reading']['literal']
    chunks = literal.split('\n&\n')
    assert len(chunks) >= 3
    lines = chunks[1].splitlines()
    assert len(lines) == 5 and all(line.endswith('/') for line in lines)
    hex_text = ''.join(line[:-1] for line in lines)
    assert all(c in '0123456789abcdef' for c in hex_text)
    assert hex_text == source['target']['hex'] == plan['printed_target']['hex'] == result['target_hex']
    target = bytes.fromhex(hex_text)
    assert len(target) == result['target_bytes'] == 64

    page_objects = {entry['id']: json.loads(verified(entry['page'])) for entry in source['pages']}
    names = [entry['id'] for entry in source['text_variants']]
    assert names == ['exact', 'crlf', 'drop-final-lf', 'one-final-lf']
    candidates = []
    for entry in source['pages']:
        candidates.append(verified(entry['image']))
    for entry in source['pages']:
        candidates.extend(variants(page_objects[entry['id']]['raw'])[name] for name in names)
    for section in source['sections']:
        joined = ''.join(page_objects[pid]['reading']['literal'] for pid in section['pages'])
        candidates.extend(variants(joined)[name] for name in names)
    candidates.append(verified(source['payload']))
    assert len(candidates) == result['candidate_variants'] == 412
    by_hash = {hashlib.sha256(data).hexdigest(): data for data in candidates}
    assert len(by_hash) == result['unique_candidate_bytes'] == result['md5_computations'] == 324
    md5_values = {key: hashlib.md5(raw).digest() for key, raw in by_hash.items()}
    for index, block_record in enumerate(result['blocks']):
        block = target[index*16:(index+1)*16]
        assert block_record['index'] == index
        assert block_record['start_byte'] == index*16 and block_record['end_byte_exclusive'] == (index+1)*16
        assert block_record['hex'] == block.hex()
        expected = {key for key, value in md5_values.items() if value == block}
        observed = {match['input_sha256'] for match in block_record['matches']}
        assert observed == expected and len(block_record['matches']) == len(expected)
        assert all(bytes.fromhex(row['md5']) == block for row in block_record['matches'])
    assert result['block_comparisons'] == 4 * len(by_hash) == 1296
    assert result['matching_blocks'] == sum(bool(record['matches']) for record in result['blocks'])

    first = hashlib.md5(candidates[0]).digest()
    last = hashlib.md5(candidates[-1]).digest()
    # Controls test exact aligned offsets rather than searching anywhere in a stream.
    container = first + bytes([167]) * 32 + last
    offsets = lambda value: [i for i in range(4) if container[i*16:(i+1)*16] == value]
    assert offsets(first) == [0] and offsets(last) == [3]
    assert not offsets(first[::-1]) and not offsets(last[::-1])
    assert result['synthetic_controls'] == {
        'first_block': [0], 'last_block': [3],
        'reversed_first_block': [], 'reversed_last_block': []}
    print('PASS: 64 printed bytes, 324 unique candidate bytes, four exact MD5 block comparisons and planted controls')


if __name__ == '__main__':
    main()
