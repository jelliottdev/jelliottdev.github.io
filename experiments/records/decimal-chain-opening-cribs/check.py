"""Independent exhaustive prefix census from page JSON and all decimal primers."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ABC = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
TABLE = {c: i for i, c in enumerate(ABC)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independently_extend(value):
    out = tuple(map(int, f'{value:05d}'))
    while len(out) < 12:
        out += ((out[-5] + out[-4]) % 10,)
    return out


def check():
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    opening_path = ROOT / plan['inputs'][0]['path']
    assert saved['plan_sha256'] == digest(HERE / 'plan.json')
    assert saved['opening_plan_sha256'] == digest(opening_path)
    openings = [(x['id'], tuple(x['indices']))
                for x in json.loads(opening_path.read_text(encoding='utf-8'))['openings']]
    pages = []
    for source in saved['inputs']:
        path = ROOT / source['path']
        assert digest(path) == source['sha256']
        obj = json.loads((ROOT / 'data/pages' / (path.stem + '.json')).read_text(encoding='utf-8'))
        runes = tuple(TABLE[c] for line in obj['lines'] for c in line['raw'] if c in TABLE)
        assert len(runes) == source['runes']
        if runes:
            pages.append((path.stem, runes[:12]))
    assert len(pages) == 55 and len(openings) == 9
    contexts = []
    wanted = [set() for _ in range(13)]
    for sign in (-1, 1):
        for page, ciphertext in pages:
            for opening_id, plain in openings:
                target_key = tuple((sign * (plain[j]-ciphertext[j])) % 29 for j in range(12))
                contexts.append((sign, page, opening_id, target_key))
                for length in range(1, 13):
                    wanted[length].add(target_key[:length])
    counts = [collections.Counter() for _ in range(13)]
    inventory_hash = hashlib.sha256()
    # Every one of the 100,000 primers is generated. Count only prefixes that
    # one of the declared target contexts requests; this is an exact index.
    for number in range(100000):
        seq = independently_extend(number)
        inventory_hash.update(f'{number:05d}\t{"".join(str(x) for x in seq)}\n'.encode())
        for length in range(1, 13):
            prefix = seq[:length]
            if prefix in wanted[length]:
                counts[length][prefix] += 1
    assert inventory_hash.hexdigest() == saved['primer_inventory_sha256']
    hist = {-1: [0]*13, 1: [0]*13}
    best = 0
    examples = []
    for sign, page, opening_id, target in contexts:
        ge = [100000] + [counts[length][target[:length]] for length in range(1, 13)]
        assert all(ge[length] >= ge[length+1] for length in range(12))
        for length in range(12):
            hist[sign][length] += ge[length] - ge[length+1]
        hist[sign][12] += ge[12]
        local_best = max(length for length, count in enumerate(ge) if count)
        if local_best > best:
            best = local_best
            examples = []
        if local_best == best and len(examples) < 5:
            primer = ''.join(map(str, target[:5])) if all(d <= 9 for d in target[:5]) else None
            examples.append({'sign': sign, 'page': page, 'opening': opening_id,
                             'primer': primer, 'prefix': local_best})
    assert saved['primer_count'] == 100000
    assert saved['total_comparisons'] == 99000000
    assert saved['max_prefix'] == best
    assert saved['max_prefix_examples'] == examples
    for sign in (-1, 1):
        assert saved['by_sign'][str(sign)]['prefix_histogram'] == hist[sign]
        assert saved['by_sign'][str(sign)]['exact_matches'] == hist[sign][12]
        assert sum(hist[sign]) == 49500000
    assert saved['total_exact_matches'] == hist[-1][12] + hist[1][12]
    plain = openings[0][1]
    for sign in (-1, 1):
        control = saved['planted_controls'][str(sign)]
        assert control['primer'] == '31415'
        assert tuple((c+sign*k)%29 for c,k in zip(control['cipher_indices'],independently_extend(31415))) == plain
        required = tuple((sign*(p-c))%29 for p,c in zip(plain,control['cipher_indices']))
        assert required == independently_extend(31415)
    print('PASS 100000 primers, 99000000 comparisons,', best, 'longest prefix,',
          saved['total_exact_matches'], 'full matches')


if __name__ == '__main__':
    check()
