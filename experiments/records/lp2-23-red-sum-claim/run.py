"""Audit a named red-heading/phrase sum under explicit GP conventions."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def calculate():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
    alphabet = json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']
    by_rune = {x['rune']: x for x in alphabet}
    by_label = {x['latin']: x for x in alphabet}
    raw = (ROOT / 'text/lp2-23.txt').read_text(encoding='utf-8')
    prefix = raw.split('.', 1)[0]
    header = [by_rune[c] for c in prefix if c in by_rune]
    words = [[by_rune[c] for c in word if c in by_rune] for word in prefix.split('-')]
    compact = [[by_label[c] for c in word] for word in plan['phrase_tokens']]
    split = [compact[0], [by_label[c] for c in ['T', 'H', 'E']], compact[2]]
    def describe(words):
        flat = [x for word in words for x in word]
        return {'runes': ''.join(x['rune'] for x in flat), 'labels': [x['latin'] for x in flat],
                'values': [x['prime'] for x in flat], 'word_lengths': [len(w) for w in words],
                'word_sums': [sum(x['prime'] for x in w) for w in words],
                'rune_count': len(flat), 'sum': sum(x['prime'] for x in flat)}
    observed, phrase, phrase_split = describe(words), describe(compact), describe(split)
    assert header[1]['latin'] == 'A'
    substituted = observed['sum'] - header[1]['prime'] + by_label['F']['prime']
    return {'schema': 'liberpedia-red-sum-claim-v1', 'plan_sha256': hashlib.sha256(plan_bytes).hexdigest(),
            'header': observed, 'phrase_th_rune': phrase, 'phrase_split_th': phrase_split,
            'same_sum': observed['sum'] == phrase['sum'], 'difference': observed['sum'] - phrase['sum'],
            'a_to_f_sensitivity': {'rune_ordinal_zero_based': 1, 'before': header[1]['prime'],
                                   'after': by_label['F']['prime'], 'sum': substituted,
                                   'is_transcription_correction': False}}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    path = HERE / 'results.json'
    if args.check:
        assert json.loads(path.read_bytes()) == result
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: result[key]['sum'] for key in ('header','phrase_th_rune','phrase_split_th')}))


if __name__ == '__main__':
    main()
