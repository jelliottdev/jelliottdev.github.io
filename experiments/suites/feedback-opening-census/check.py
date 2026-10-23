"""Independent full-census verifier for the bounded LP2 feedback family.

This checker reads page JSON and known-reading CSVs directly. It does not import
the suite engine, runner, or their text parser.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'experiments/records/lp2-54-header-feedback/results.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pages(alphabet: str):
    lookup = {rune: index for index, rune in enumerate(alphabet)}
    pages = []
    for page_number in range(56):
        name = f'lp2-{page_number:02}'
        page = json.loads((ROOT/f'data/pages/{name}.json').read_text(encoding='utf-8'))
        assert page['id'] == name
        # Use the individual rows, not text/*.txt or the page's aggregate raw.
        raw = ''.join(row['raw'] for row in page['lines'])
        indexed = []
        segment = 0
        for char in raw:
            if char in lookup:
                indexed.append((lookup[char], segment))
            elif char in '-.':
                segment += 1
        assert len(indexed) == page['rune_count']
        if indexed:
            pages.append((name, indexed))
    assert len(pages) == 55
    assert sum(len(x) for _, x in pages) == 12956
    return pages


def decipher(indexed, mode: str, lag: int, primer: int, boundary: str):
    out = []
    first_by_segment = {}
    for i, (symbol, segment) in enumerate(indexed):
        start = 0 if boundary == 'continuous' else first_by_segment.setdefault(segment, i)
        back = i - lag
        if back < start:
            key = primer
        elif mode == 'ciphertext':
            key = indexed[back][0]
        else:
            assert mode == 'plaintext'
            key = out[back]
        out.append((symbol - key) % 29)
    return out


def encrypt(plain, mode: str, lag: int, primer: int, boundary: str):
    cipher = []
    for i, (value, segment) in enumerate(plain):
        first = next((j for j in range(i, -1, -1) if plain[j][1] != segment), -1) + 1 if boundary != 'continuous' else 0
        back = i - lag
        if back < first:
            key = primer
        elif mode == 'ciphertext':
            key = cipher[back]
        else:
            key = plain[back][0]
        cipher.append((value + key) % 29)
    return [(value, seg) for value, (_, seg) in zip(cipher, plain)]


def load_cribs(manifest):
    source = json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))['openings']
    assert len(source) == 9
    declared = manifest['cribs']
    assert [(row['id'], row['indices']) for row in declared] == [(row['id'], row['indices']) for row in source]
    for row in declared:
        assert row['source'] in {item['source'] for item in source}
        assert sha((ROOT/row['source']).read_bytes()) == row['sha256']
        with (ROOT/row['source']).open(encoding='utf-8', newline='') as handle:
            table = list(csv.DictReader(handle))
        # The archived control openings are the first twelve output rune indices.
        assert [int(x['output_index']) for x in table[:12]] == row['indices']
    return declared


def evaluate(mode, lag, primer, boundary, pages, cribs):
    digest = hashlib.sha256()
    hits = []
    best = -1
    ties = []
    page54 = None
    for name, indexed in pages:
        decoded = decipher(indexed, mode, lag, primer, boundary)
        digest.update((name+'\t'+','.join(map(str, decoded))+'\n').encode('utf-8'))
        if name == 'lp2-54':
            page54 = decoded
        for crib in cribs:
            target = crib['indices']
            length = 0
            while length < 12 and decoded[length] == target[length]:
                length += 1
            row = {'page': name, 'opening': crib['id']}
            if length == 12:
                hits.append(row)
            if length > best:
                best = length
                ties = [row]
            elif length == best:
                ties.append(row)
    assert len(pages)*len(cribs) == 495
    return {'decode_sha256': digest.hexdigest(), 'comparison_count': 495,
            'opening_matches': hits, 'max_prefix_length': best,
            'max_prefix_ties': ties}, page54


def main():
    manifest = json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    results = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    case_data = json.loads((HERE/'cases.json').read_text(encoding='utf-8'))
    assert case_data['schema'] == 'liberpedia-feedback-opening-cases-v1'
    assert sha((HERE/'cases.json').read_bytes()) == results['cases_sha256']
    alphabet = ''.join(row['rune'] for row in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet'])
    assert len(alphabet) == 29 and len(set(alphabet)) == 29
    pages = read_pages(alphabet)
    cribs = load_cribs(manifest)
    old = json.loads(OLD.read_text(encoding='utf-8'))
    old_by_case = {(row['mode'], row['primer']): row for row in old['cases']}
    expected_order = [(mode, lag, primer, boundary)
                      for mode in ('ciphertext', 'plaintext')
                      for lag in range(1, 17)
                      for primer in range(29)
                      for boundary in ('continuous', 'word-reset')]
    cases = case_data['cases']
    assert len(cases) == len(expected_order) == results['case_count'] == 1856
    total_matches = 0
    distribution = {}
    for case, (mode, lag, primer, boundary) in zip(cases, expected_order):
        assert (case['mode'], case['lag'], case['primer'], case['boundary']) == (mode, lag, primer, boundary)
        assert case['id'] == f'{mode}-lag{lag:02}-primer{primer:02}-{boundary}'
        independent, page54 = evaluate(mode, lag, primer, boundary, pages, cribs)
        for field, value in independent.items():
            assert case[field] == value, (case['id'], field)
        total_matches += len(case['opening_matches'])
        length = case['max_prefix_length']
        distribution[str(length)] = distribution.get(str(length), 0) + 1
        if lag == 1 and boundary == 'continuous':
            former_mode = mode+'_feedback'
            assert page54[:9] == old_by_case[(former_mode, primer)]['header_indices']
        # Positive control for the exact config, with two nonempty segments.
        known = [(v, 0 if i < 6 else 1) for i, v in enumerate(cribs[0]['indices'])]
        encoded = encrypt(known, mode, lag, primer, boundary)
        assert decipher(encoded, mode, lag, primer, boundary) == [v for v, _ in known]
    assert total_matches == results['full_match_count']
    assert distribution == results['max_prefix_distribution']
    print('feedback-opening-census: all 1,856 cases, 918,720 comparisons, digests, positives, and LP2-54 cross-check verified')


if __name__ == '__main__':
    main()
