"""Independent map check and optional comparison to both archived outputs."""
import argparse
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)
LABELS = ('F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO',
          'P', 'X', 'S', 'T', 'B', 'E', 'M', 'L', 'NG', 'OE', 'D', 'A', 'AE', 'Y', 'IA', 'EA')


def heading_chunks(path):
    text = path.read_text(encoding='utf-8')
    chunks = re.split(r'-{6,} ↓  Page \d+  ↓ -{6,}', text)
    assert len(chunks) == 58, len(chunks)  # Source also has page 56.
    for chunk in chunks[1:57]:
        lines = [re.sub(r'^\s*\d+\s+', '', line.strip()) for line in chunk.splitlines()]
        first = next((line for line in lines if line and not re.search(r'\d', line)
                      and re.search('[A-Z]', line)), '')
        yield re.sub('[^A-Z]', '', first.upper())


def match_latin(measured, archived):
    variants = [('IA', 'IO') if rune == 'ᛡ' else (LABELS[RUNES.index(rune)],)
                for rune in measured]
    return any(archived.startswith(''.join(parts)) or ''.join(parts).startswith(archived)
               for parts in itertools.product(*variants))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path)
    args = parser.parse_args()
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    assert len(result['pages']) == 56
    for radius, radii in (('index', range(29)), ('prime', PRIMES)):
        for rounding in ('nearest', 'truncate'):
            name = f'{radius}-{rounding}'
            # None of these products falls exactly halfway between integers.
            operation = (lambda x: math.floor(x + 0.5)) if rounding == 'nearest' else math.floor
            table = [operation(2 * math.pi * r) % 29 for r in radii]
            assert table == result['maps'][name]['output_indices']
            assert len(set(table)) == result['maps'][name]['distinct_outputs']
            for entry in result['pages']:
                source = ROOT / 'text' / (entry['page'] + '.txt')
                raw = source.read_text(encoding='utf-8')
                assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['input_sha256']
                transformed = ''.join(RUNES[table[RUNES.index(c)]] if c in RUNES else c
                                      for c in raw)
                assert hashlib.sha256(transformed.encode()).hexdigest() == entry['outputs'][name]['output_sha256']
    print('PASS: four maps, all 56 page hashes, and per-page output digests reproduce')
    if args.source_directory:
        for radius, source in zip(('index', 'prime'), plan['source_outputs']):
            path = args.source_directory / Path(source['path']).name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
            pairs = [(entry['outputs'][f'{radius}-truncate']['first_nine_runes'], heading)
                     for entry, heading in zip(result['pages'], heading_chunks(path))]
            tested = [(runes, heading) for runes, heading in pairs if runes and heading]
            matching = sum(match_latin(runes, heading) for runes, heading in tested)
            print(json.dumps({'radius': radius, 'archive_pages_compared': len(tested),
                              'matching_first_lines': matching}))
            assert matching == len(tested), 'Public archive output diverges'


if __name__ == '__main__':
    main()
