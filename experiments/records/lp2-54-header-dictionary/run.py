"""Fixed A/I/O autokey header cribs against a preserved rune-word corpus."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
RX = re.compile('[' + ALPHABET + ']+')
FIRST = {'A': 24, 'I': 10, 'O': 3}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def words():
    source = ROOT / 'experiments/records/word-sum-corpus-control/source'
    manifest = json.loads((source / 'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
    selected = {}
    rows = 0
    for item in manifest['files']:
        path = source / item['path']
        if sha(path) != item['sha256']:
            raise ValueError('Corpus checksum changed: ' + str(path))
        for word, _count, _flag, runes, _sum in csv.reader(path.read_text(encoding='utf-8').splitlines()):
            rows += 1
            # Preserved corpus uses a shape variant for J; both have GP index 11.
            runes = runes.replace('ᛂ', 'ᛄ')
            if len(runes) == 8 and all(r in ALPHABET for r in runes):
                selected.setdefault(runes, []).append(word)
    return selected, rows


def outputs(cipher, first):
    c = [ALPHABET.index(r) for r in cipher]
    primer = (c[0] - first) % 29
    out = {}
    for mode in ('ciphertext', 'plaintext'):
        plain = [first]
        for i in range(1, 9):
            predecessor = c[i - 1] if mode == 'ciphertext' else plain[-1]
            plain.append((c[i] - predecessor) % 29)
        out[mode] = {'primer': primer, 'runes': ''.join(ALPHABET[x] for x in plain),
                     'second_word': ''.join(ALPHABET[x] for x in plain[1:])}
    return out


def collect():
    dictionary, source_rows = words()
    planted_word = 'ᛗᚩᚢᚾᛏᚪᛁᚾ'  # MOUNTAIN in the pinned dictionary: eight runes.
    if 'mountain' not in dictionary.get(planted_word, []):
        raise ValueError('Positive-control word missing from pinned corpus')
    positive = []
    for mode in ('ciphertext', 'plaintext'):
        plain = [FIRST['A']] + [ALPHABET.index(r) for r in planted_word]
        cipher = [(plain[0] + 7) % 29]
        for i in range(1, 9):
            prior = cipher[-1] if mode == 'ciphertext' else plain[i - 1]
            cipher.append((plain[i] + prior) % 29)
        encoded = ''.join(ALPHABET[x] for x in cipher)
        decoded = outputs(encoded, FIRST['A'])[mode]
        if decoded['second_word'] != planted_word or decoded['primer'] != 7:
            raise ValueError('Planted header did not decode')
        positive.append({'mode': mode, 'cipher': encoded, 'decoded_word': 'mountain', 'primer': 7})
    cases = []
    for number in range(56):
        page = f'lp2-{number:02d}'
        raw = (ROOT / 'text' / f'{page}.txt').read_text(encoding='utf-8')
        runs = RX.findall(raw)
        for index, (first, second) in enumerate(zip(runs, runs[1:])):
            if len(first) == 1 and len(second) == 8:
                cipher = first + second
                variants = []
                for label, target in FIRST.items():
                    for mode, item in outputs(cipher, target).items():
                        variants.append({'first': label, 'mode': mode, **item,
                                         'dictionary_words': sorted(dictionary.get(item['second_word'], []))})
                cases.append({'page': page, 'pair_index': index, 'cipher': cipher,
                              'variants': variants})
    target = next((case for case in cases if case['page'] == 'lp2-54' and case['cipher'] == 'ᚪᛗᛝᛞᛡᚦᛉᛁᛗ'), None)
    if target is None:
        raise ValueError('LP2-54 red prefix was not found as a 1+8 word pair')
    return {'schema': 'liberpedia-lp2-54-header-dictionary-v1',
            'source_manifest_sha256': sha(ROOT / 'experiments/records/word-sum-corpus-control/source/SOURCE-MANIFEST.json'),
            'source_rows': source_rows, 'eight_rune_dictionary_spellings': len(dictionary),
            'eligible_visible_pairs': len(cases),
            'all_pair_dictionary_hits': sum(bool(v['dictionary_words']) for c in cases for v in c['variants']),
            'pairs_with_any_hit': sum(any(v['dictionary_words'] for v in c['variants']) for c in cases),
            'planted_positive_controls': positive,
            'target_pair': target,
            'all_pairs': cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = collect()
    data = canonical(result)
    path = HERE / 'results.json'
    if args.check:
        if path.read_bytes() != data:
            raise SystemExit('Saved results differ from recomputation')
        print('OK: corpus, 56 pages, six modes/cribs per eligible pair and saved results')
    else:
        path.write_bytes(data)
        print(json.dumps({k: result[k] for k in ('eligible_visible_pairs', 'all_pair_dictionary_hits', 'pairs_with_any_hit')}, indent=2))
        print([(v['first'], v['mode'], v['dictionary_words']) for v in result['target_pair']['variants']])


if __name__ == '__main__':
    main()
