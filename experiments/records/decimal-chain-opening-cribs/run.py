"""Exhaustive five-decimal-primer chain stream against fixed LP2 openings."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX = {rune: i for i, rune in enumerate(ALPHABET)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chain(primer):
    digits = [int(c) for c in primer]
    for i in range(5, 12):
        digits.append((digits[i-5] + digits[i-4]) % 10)
    return tuple(digits)


def inventory():
    all_streams = {}
    inventory_hash = hashlib.sha256()
    for value in range(100000):
        primer = f'{value:05d}'
        stream = chain(primer)
        assert stream[:5] == tuple(int(c) for c in primer)
        all_streams[stream[:5]] = stream
        inventory_hash.update(f'{primer}\t{"".join(map(str,stream))}\n'.encode())
    assert len(all_streams) == 100000
    return all_streams, inventory_hash.hexdigest()


def run():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    opening_path = ROOT / plan['inputs'][0]['path']
    assert sha(opening_path) == plan['inputs'][0]['sha256']
    openings = [(x['id'], tuple(x['indices']))
                for x in json.loads(opening_path.read_text(encoding='utf-8'))['openings']]
    assert len(openings) == 9 and all(len(x) == 12 for _, x in openings)
    streams, inventory_digest = inventory()
    pages, inputs = [], []
    for number in range(56):
        path = ROOT / f'text/lp2-{number:02d}.txt'
        symbols = tuple(INDEX[c] for c in path.read_text(encoding='utf-8') if c in INDEX)
        inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                       'runes': len(symbols)})
        if symbols:
            pages.append((path.stem, symbols[:12]))
    assert len(pages) == 55
    results = {}
    best = 0
    best_examples = []
    for sign in (-1, 1):
        histogram = [0] * 13
        for page, ciphertext in pages:
            for opening_id, target in openings:
                required = tuple((sign * (target[i] - ciphertext[i])) % 29 for i in range(12))
                # The first five key digits uniquely identify a primer when valid.
                first_five_valid = all(d <= 9 for d in required[:5])
                stream = streams.get(required[:5]) if first_five_valid else None
                ge = [100000]
                for length in range(1, 6):
                    ge.append(10 ** (5-length) if all(d <= 9 for d in required[:length]) else 0)
                for length in range(6, 13):
                    ge.append(int(stream is not None and stream[:length] == required[:length]))
                assert all(ge[j] >= ge[j+1] for j in range(12))
                for length in range(12):
                    histogram[length] += ge[length] - ge[length+1]
                histogram[12] += ge[12]
                local_best = max(j for j in range(13) if ge[j])
                if local_best > best:
                    best = local_best
                    best_examples = []
                if local_best == best and len(best_examples) < 5:
                    primer = ''.join(map(str, required[:5])) if first_five_valid else None
                    best_examples.append({'sign': sign, 'page': page, 'opening': opening_id,
                                          'primer': primer, 'prefix': local_best})
        assert sum(histogram) == 100000 * len(pages) * len(openings)
        results[str(sign)] = {'prefix_histogram': histogram,
                              'exact_matches': histogram[12],
                              'comparison_count': sum(histogram)}
    # The planted page opening has a unique first-five-digit inverse.
    planted = {}
    opening_id, plaintext = openings[0]
    primer = '31415'
    key = chain(primer)
    for sign in (-1, 1):
        synthetic = tuple((p - sign*k) % 29 for p, k in zip(plaintext, key))
        inferred = tuple((sign*(p-c)) % 29 for p, c in zip(plaintext, synthetic))
        assert streams.get(inferred[:5]) == inferred
        planted[str(sign)] = {'opening': opening_id, 'primer': primer,
                              'cipher_indices': synthetic, 'recovered': True}
    assert sum(r['comparison_count'] for r in results.values()) == 99000000
    return {'schema': 'liberpedia-decimal-chain-opening-results-v1',
            'plan_sha256': sha(plan_path), 'opening_plan_sha256': sha(opening_path),
            'inputs': inputs, 'primer_count': len(streams), 'signs': [-1, 1],
            'page_count': len(pages), 'opening_count': len(openings),
            'total_comparisons': 99000000,
            'total_exact_matches': sum(r['exact_matches'] for r in results.values()),
            'max_prefix': best, 'max_prefix_examples': best_examples,
            'by_sign': results, 'planted_controls': planted,
            'primer_inventory_sha256': inventory_digest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = run()
    target = HERE / 'results.json'
    if args.check:
        assert report == json.loads(target.read_text(encoding='utf-8'))
    else:
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')
    print(report['primer_count'], report['total_comparisons'], report['total_exact_matches'],
          report['max_prefix'])
