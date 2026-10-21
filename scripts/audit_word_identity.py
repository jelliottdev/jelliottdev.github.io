"""Check word-lookup ambiguity in the fixed four-section, 464-word object.

Word boundaries and apostrophes are retained from the archived word inventory.
Decoded forms use output rune indices, not contextual English spellings.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

from audit_reading_fixed_points import audit

ROOT = Path(__file__).resolve().parents[1]


def calculate():
    baseline = audit()
    assert baseline == json.loads((ROOT / 'exports/reading-fixed-points.json').read_bytes())
    spec = importlib.util.spec_from_file_location('word_baseline', ROOT / 'experiments/records/lp1-word-length-balance/run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan = json.loads((ROOT / 'experiments/records/lp1-word-length-balance/plan.json').read_bytes())
    words, _ = module.reconstruct(plan)
    assert words == json.loads((ROOT / 'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    alphabet = [a['rune'] for a in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']]
    traces = {}
    counters = {}
    for section in plan['sections']:
        name = section['id']
        with (ROOT / f'exports/readings/{name}.csv').open(encoding='utf-8', newline='') as stream:
            traces[name] = list(csv.DictReader(stream))
        counters[name] = 0
    records = []
    for word in words:
        name = word['section']
        output = []
        for char in word['ciphertext']:
            if char == "'":
                output.append(char)
                continue
            row = traces[name][counters[name]]
            assert row['input_rune'] == char
            output.append(alphabet[int(row['output_index'])])
            counters[name] += 1
        records.append({**word, 'decoded_runes': ''.join(output)})
    assert all(counters[name] == len(rows) for name, rows in traces.items())
    assert len(records) == 464
    summaries = {}
    inventories = {}
    for representation in ['ciphertext', 'decoded_runes']:
        by_form = defaultdict(list)
        for word in records:
            by_form[word[representation]].append(word['word'])
        inventories[representation] = [{'form': form, 'count': len(positions), 'positions': positions}
                                      for form, positions in sorted(by_form.items(), key=lambda item: (-len(item[1]), item[0]))]
        singleton = sum(len(positions) == 1 for positions in by_form.values())
        summaries[representation] = {'positions': len(records), 'distinct_forms': len(by_form),
                                     'singleton_forms_and_positions': singleton,
                                     'repeated_forms': len(by_form) - singleton,
                                     'positions_with_nonunique_form': len(records) - singleton,
                                     'extra_occurrences_beyond_first': len(records) - len(by_form),
                                     'matching_position_pairs': sum(len(p)*(len(p)-1)//2 for p in by_form.values())}
        # Independent direct pair comparison checks the grouped formula.
        direct_pairs = sum(records[i][representation] == records[j][representation]
                           for i in range(len(records)) for j in range(i))
        assert direct_pairs == summaries[representation]['matching_position_pairs']
    paths = ['scripts/audit_reading_fixed_points.py', 'exports/reading-fixed-points.json',
             'experiments/records/lp1-word-length-balance/run.py',
             'experiments/records/lp1-word-length-balance/words.json']
    return {'scope': __doc__, 'summaries': summaries, 'forms': inventories, 'words': records,
            'source_sha256': {**baseline['source_sha256'], **{p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}},
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limits': 'Exact rune-word equality only. Repeated positions are not necessarily adjacent. No carrier matching, grille extraction, chance model or inferred intent.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = calculate()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(report['summaries'], indent=2))
