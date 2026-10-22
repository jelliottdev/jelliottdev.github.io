"""Independent census of the preserved candidate corpus and saved results."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan_bytes = (HERE / 'plan.json').read_bytes()
plan = json.loads(plan_bytes)
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
manifest = json.loads((HERE / 'source/SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
assert result['plan_sha256'] == hashlib.sha256(plan_bytes).hexdigest()
assert manifest['revision'] == result['source_revision'] == plan['corpus_revision']
assert len(manifest['files']) == result['source_files']

values = {entry['rune']: entry['prime'] for entry in
          json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']}
assert values['ᛄ'] == 37
assert 'ᛂ' not in values
values['ᛂ'] = 37
hist = defaultdict(Counter)
matches = defaultdict(list)
words = set()
alias_rows = 0
flags = Counter()
for item in manifest['files']:
    source = HERE / 'source' / item['path']
    data = source.read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    with source.open(encoding='utf-8', newline='') as stream:
        for row in csv.reader(stream):
            assert len(row) == 5, (source, row)
            word, frequency, flag, runes, printed_gp = row
            assert word not in words
            words.add(word)
            assert frequency.isdecimal() and flag in {'0', '1'}
            assert int(printed_gp) == sum(values[char] for char in runes)
            hist[len(runes)][int(printed_gp)] += 1
            flags[flag] += 1
            alias_rows += 'ᛂ' in runes
            if int(printed_gp) in plan['target_sums']:
                matches[int(printed_gp)].append((word, len(runes), int(frequency), item['path']))

assert len(words) == result['source_rows'] == result['unique_words']
assert alias_rows == result['source_j_alias_rows']
assert dict(flags) == result['source_flag_counts']
for length, sums in hist.items():
    assert {str(total): count for total, count in sorted(sums.items())} == result['count_by_rune_length_and_gp_sum'][str(length)]
for total in plan['target_sums']:
    saved = {(row['word'], row['rune_length'], row['source_count'], row['file'])
             for row in result['target_matches'][str(total)]}
    assert saved == set(matches[total])
slot_counts = []
for slot, saved in zip(plan['phrase_slots'], result['slots']):
    count = sum(length == slot['rune_length'] for _, length, _, _ in matches[slot['gp_sum']])
    assert count == saved['candidate_count']
    assert all(saved[key] == slot[key] for key in slot)
    slot_counts.append(count)
product = 1
for count in slot_counts:
    product *= count
assert product == result['ordered_slot_combinations']
assert slot_counts[0] == slot_counts[3]
assert slot_counts[0] * slot_counts[1] * slot_counts[2] * (slot_counts[3] - 1) == result['ordered_combinations_with_distinct_131_words']
print(f'PASS: {len(words)} distinct corpus words, all printed GP values, three target lists and both Cartesian-product counts')
