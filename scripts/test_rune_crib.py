"""Check pattern search against explicit permutations and archived source spans."""
from itertools import permutations, product
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from rune_crib import ROOT, matching_starts, report


def main():
    sequences = list(product(range(3), repeat=4))
    for cipher in sequences:
        possible = {tuple(mapping[x] for x in cipher) for mapping in permutations(range(3))}
        for plain in sequences:
            assert bool(matching_starts(cipher, plain)) == (plain in possible)
    assert matching_starts([0, 0, 0], [1, 1]) == [0, 1]
    assert matching_starts([0], [1, 2]) == []
    result = report('lp2-42', 'F U F U TH')
    text = (ROOT / 'text/lp2-42.txt').read_bytes().decode('utf-8')
    alphabet = json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']
    indices = {entry['rune']: entry['index'] for entry in alphabet}
    assert any(m['source_start'] == 229 and m['source_end'] == 234 for m in result['matches'])
    for m in result['matches']:
        assert text[m['source_start']:m['source_end']] == m['source_text']
        cipher = [indices[c] for c in m['source_text'] if c in indices]
        assert cipher == m['cipher_indices']
        mapping = {p['cipher_index']: p['plain_index'] for p in m['mapping']}
        assert len(set(mapping.values())) == len(mapping)
        assert [mapping[c] for c in cipher] == result['crib_indices']
    assert report('lp2-42', 'IA IO')['pattern'] == [0, 0]
    for crib in ('', 'THE', 'F '*65):
        try:
            report('lp2-42', crib)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid crib accepted')
    with tempfile.TemporaryDirectory(prefix='crib-output-') as folder:
        output = Path(folder) / 'result.json'
        command = [sys.executable, str(ROOT/'scripts/rune_crib.py'), 'lp2-42',
                   '--crib', 'F U F U TH', '--output', str(output)]
        first = subprocess.run(command, capture_output=True)
        assert first.returncode == 0, first.stderr
        saved = output.read_bytes()
        assert json.loads(saved) == result
        assert subprocess.run(command, capture_output=True).returncode != 0
        assert output.read_bytes() == saved
    print('PASS: 6561 permutation comparisons, overlapping windows, source spans, aliases and no-overwrite export')


if __name__ == '__main__':
    main()
