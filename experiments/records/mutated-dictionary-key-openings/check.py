"""Independent enumeration and clock comparison; no import from run.py."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
N = {c: i for i, c in enumerate(A)}


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
    key_rows = json.loads((ROOT / 'experiments/records/public-wordlist-vigenere/plan.json').read_text(encoding='utf-8'))['keys']
    crib_rows = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))['openings']
    named = Counter()
    altered = defaultdict(set)
    for row in key_rows:
        original = row['runes']
        for i, rune in enumerate(original):
            for replacement in A:
                if replacement != rune:
                    altered[original[:i] + replacement + original[i + 1:]].add('position')
                    named['position'] += 1
        for rune in set(original):
            for replacement in A:
                if replacement != rune:
                    altered[''.join(replacement if x == rune else x for x in original)].add('rune-type')
                    named['rune-type'] += 1
    needed = set()
    page_count = 0
    for number in range(56):
        text = (ROOT / f'text/lp2-{number:02d}.txt').read_text(encoding='utf-8')
        cipher = [N[c] for c in text if c in N][:12]
        if not cipher:
            assert number == 50
            continue
        assert len(cipher) == 12
        page_count += 1
        for row in crib_rows:
            plain = row['indices']
            needed.add(bytes((c - p) % 29 for c, p in zip(cipher, plain)))
            needed.add(bytes((p - c) % 29 for c, p in zip(cipher, plain)))
    digest = hashlib.sha256()
    phase_count = 0
    collisions = 0
    clocks = set()
    mode_phases = Counter()
    for changed in sorted(altered):
        values = bytes(N[r] for r in changed)
        for phase in range(len(values)):
            candidate = (values * ((phase + 12) // len(values) + 2))[phase:phase + 12]
            assert len(candidate) == 12
            digest.update(candidate)
            clocks.add(candidate)
            phase_count += 1
            for mode in altered[changed]:
                mode_phases[mode] += 1
            collisions += candidate in needed
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert len(key_rows) == result['source_key_count'] == 43
    assert len(crib_rows) == result['opening_count'] == 9
    assert page_count == result['page_count'] == 55
    assert dict(sorted(named.items())) == result['named_mutations']
    assert len(altered) == result['unique_mutated_keys'] == 9856
    assert phase_count == result['phase_settings'] == 83328
    assert len(clocks) == result['unique_12_rune_clocks'] == 77048
    assert dict(sorted(mode_phases.items())) == result['mode_phase_settings']
    assert len(needed) == result['distinct_required_clocks']
    assert digest.hexdigest() == result['clock_stream_sha256']
    assert collisions == result['match_count'] == 0
    assert result['exact_matches'] == []
    assert result['nominal_comparisons'] == phase_count * page_count * len(crib_rows) * 2
    assert result['plan_sha256'] == hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest()
    print(f'Independent check: {phase_count:,} settings, {result["nominal_comparisons"]:,} named comparisons, zero exact matches')


if __name__ == '__main__':
    main()
