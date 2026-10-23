"""Compare four printed LP2-56 16-byte blocks with MD5 of frozen artifact bytes."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(entry):
    data = (ROOT / entry['path']).read_bytes()
    assert len(data) == entry['size'] and sha(data) == entry['sha256'], entry['path']
    return data


def text_bytes(value, variant):
    if variant == 'crlf':
        value = value.replace('\n', '\r\n')
    elif variant == 'drop-final-lf':
        value = value[:-1] if value.endswith('\n') else value
    elif variant == 'one-final-lf':
        value = value.rstrip('\r\n') + '\n'
    else:
        assert variant == 'exact'
    return value.encode('utf-8')


def inputs_and_target():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    assert plan['schema'] == 'liberpedia-lp2-56-four-md5-target-blocks-plan-v1'
    source_bytes = (ROOT / plan['candidate_plan']['path']).read_bytes()
    assert sha(source_bytes) == plan['candidate_plan']['sha256']
    source = json.loads(source_bytes)
    assert source['schema'] == 'liberpedia-lp2-56-artifact-hash-plan-v1'
    assert source['target']['hex'] == plan['printed_target']['hex']
    target_page = json.loads((ROOT / plan['printed_target']['path']).read_text(encoding='utf-8'))
    literal_chunks = target_page['reading']['literal'].split('\n&\n')
    print_lines = literal_chunks[1].splitlines()
    assert len(print_lines) == 5 and all(line.endswith('/') for line in print_lines)
    hex_lines = [line[:-1] for line in print_lines]
    assert all(line and all(c in '0123456789abcdef' for c in line) for line in hex_lines)
    assert ''.join(hex_lines) == plan['printed_target']['hex']
    target = bytes.fromhex(''.join(hex_lines))
    assert len(target) == plan['printed_target']['bytes'] == 64

    page_data = {}
    image_data = {}
    for page in source['pages']:
        page_data[page['id']] = json.loads(checked(page['page']))
        image_data[page['id']] = checked(page['image'])
    variants = [v['id'] for v in source['text_variants']]
    assert variants == ['exact', 'crlf', 'drop-final-lf', 'one-final-lf']
    inputs = []
    for page in source['pages']:
        inputs.append(('image-original', page['id'], 'exact', image_data[page['id']]))
    for page in source['pages']:
        for variant in variants:
            inputs.append(('page-raw', page['id'], variant,
                           text_bytes(page_data[page['id']]['raw'], variant)))
    for section in source['sections']:
        literal = ''.join(page_data[pid]['reading']['literal'] for pid in section['pages'])
        for variant in variants:
            inputs.append(('section-literal', section['id'], variant, text_bytes(literal, variant)))
    inputs.append(('grid-payload', 'resolved-256', 'exact', checked(source['payload'])))
    assert len(inputs) == plan['candidate_plan']['variants'] == 412
    return plan_bytes, target, inputs


def positions(container, digest):
    assert len(container) == 64 and len(digest) == 16
    return [i for i in range(4) if container[16*i:16*(i+1)] == digest]


def build():
    plan_bytes, target, inputs = inputs_and_target()
    assert hashlib.md5(b'abc').hexdigest() == '900150983cd24fb0d6963f7d28e17f72'
    unique = {}
    for family, candidate, variant, raw in inputs:
        key = sha(raw)
        if key in unique:
            assert unique[key][0] == raw
            unique[key][1].append(f'{family}/{candidate}/{variant}')
        else:
            unique[key] = (raw, [f'{family}/{candidate}/{variant}'])
    assert len(unique) == 324
    blocks = [target[16*i:16*(i+1)] for i in range(4)]
    matches = [[] for _ in range(4)]
    for key, (raw, aliases) in unique.items():
        value = hashlib.md5(raw).digest()  # one digest per distinct candidate byte string
        for i, block in enumerate(blocks):
            if value == block:
                matches[i].append({'input_sha256': key, 'aliases': aliases, 'md5': value.hex()})

    first_raw = next(iter(unique.values()))[0]
    last_raw = next(reversed(unique.values()))[0]
    first = hashlib.md5(first_raw).digest()
    last = hashlib.md5(last_raw).digest()
    synthetic = first + b'\xa7' * 32 + last
    assert positions(synthetic, first) == [0]
    assert positions(synthetic, last) == [3]
    assert not positions(synthetic, first[::-1]) and not positions(synthetic, last[::-1])
    return {
        'schema': 'liberpedia-lp2-56-four-md5-target-blocks-results-v1',
        'plan_sha256': sha(plan_bytes),
        'candidate_plan_sha256': sha((ROOT / json.loads(plan_bytes)['candidate_plan']['path']).read_bytes()),
        'target_hex': target.hex(), 'target_bytes': len(target),
        'blocks': [{'index': i, 'start_byte': 16*i, 'end_byte_exclusive': 16*(i+1),
                    'hex': block.hex(), 'matches': matches[i]} for i, block in enumerate(blocks)],
        'candidate_variants': len(inputs), 'unique_candidate_bytes': len(unique),
        'md5_computations': len(unique), 'block_comparisons': len(unique)*4,
        'matching_blocks': sum(bool(m) for m in matches),
        'synthetic_controls': {'first_block': positions(synthetic, first),
                               'last_block': positions(synthetic, last),
                               'reversed_first_block': positions(synthetic, first[::-1]),
                               'reversed_last_block': positions(synthetic, last[::-1])},
    }


if __name__ == '__main__':
    result = build()
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    path = HERE / 'results.json'
    if sys.argv[1:] == ['--write']:
        path.write_bytes(encoded)
    elif not sys.argv[1:] or sys.argv[1:] == ['--check']:
        assert path.read_bytes() == encoded
    else:
        raise SystemExit('usage: run.py [--check|--write]')
    print(f"{result['candidate_variants']} variants, {result['unique_candidate_bytes']} distinct byte strings, "
          f"{result['block_comparisons']} comparisons, {result['matching_blocks']} matching blocks")
