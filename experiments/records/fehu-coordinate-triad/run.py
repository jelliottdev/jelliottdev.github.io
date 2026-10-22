"""Replay the reported LP2 Fehu-coordinate triad under one fixed rule."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAGE_PATHS = [ROOT / 'data/pages' / f'lp2-{i:02d}.json' for i in range(58)]
ALPHABET_PATH = ROOT / 'data/index.json'
PLAN_PATH = HERE / 'plan.json'
OUTPUT_PATH = HERE / 'results.json'
RUNE = '\u16a0'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate():
    plan = json.loads(PLAN_PATH.read_text(encoding='utf-8'))
    alphabet = json.loads(ALPHABET_PATH.read_text(encoding='utf-8'))['alphabet']
    prime = [entry['prime'] for entry in alphabet]
    rune_set = {entry['rune'] for entry in alphabet}
    stream = ''.join(ch for path in PAGE_PATHS
                     for ch in json.loads(path.read_text(encoding='utf-8'))['raw']
                     if ch in rune_set)
    positions = [i for i, ch in enumerate(stream) if ch == RUNE]
    width = len(alphabet)
    window = plan['window']
    step = plan['start_step']
    targets = plan['targets']
    axes = plan['axis_order']
    origins = plan['origins']

    def score(first, include_streams=False):
        sums = []
        streams = []
        for segment, axis in enumerate(axes):
            begin = first + segment * step
            origin = positions[first + origins[segment] * step]
            values = []
            for pos in positions[begin:begin + window]:
                offset = pos - origin
                coordinate = offset % width if axis == 'X' else (offset // width) % width
                values.append(coordinate)
            sums.append(sum(prime[value] for value in values))
            streams.append(values)
        return (sums, streams) if include_streams else sums

    starts = len(positions) - ((len(axes) - 1) * step + window) + 1
    assert starts > 0
    rows = [{'start_fehu': i + 1, 'sums': score(i)} for i in range(starts)]
    matches = [row for row in rows if row['sums'] == targets]
    reported = rows[plan['reported_start'] - 1]
    _, reported_streams = score(plan['reported_start'] - 1, include_streams=True)
    labels = {entry['latin']: entry['index'] for entry in alphabet}
    labels['V'] = labels['U']
    source_streams = [[labels[token] for token in line.split()] for line in plan['reported_streams']]
    assert reported_streams == source_streams, 'Coordinate streams differ from the supplied three-line trace'
    return {
        'plan_sha256': digest(PLAN_PATH),
        'alphabet_sha256': digest(ALPHABET_PATH),
        'page_sha256': {path.name: digest(path) for path in PAGE_PATHS},
        'runes': len(stream),
        'fehu_count': len(positions),
        'reported_start_fehu': plan['reported_start'],
        'reported_start_rune_index': positions[plan['reported_start'] - 1],
        'reported_sums': reported['sums'],
        'reported_coordinate_indices': reported_streams,
        'reported_streams_match_supplied_trace': True,
        'fixed_rule_start_count': starts,
        'exact_matches': matches,
        'rows': rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='compare with saved report')
    args = parser.parse_args()
    result = calculate()
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert OUTPUT_PATH.read_text(encoding='utf-8') == output, 'Saved result differs from replay'
        print('PASS: reported sums and complete fixed-rule start scan reproduce saved result')
    else:
        OUTPUT_PATH.write_text(output, encoding='utf-8', newline='\n')
        print(f"{len(result['exact_matches'])} exact triad(s) in {result['fixed_rule_start_count']} fixed-rule starts")


if __name__ == '__main__':
    main()
