"""Audit a reported STUDY HERE pointer and GP block sums on 464 LP1 words."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/464-pointer.json'
SECTIONS = [
    ('warning', ['lp1-01']),
    ('welcome', ['lp1-03', 'lp1-04']),
    ('first-koan', ['lp1-06', 'lp1-07', 'lp1-08', 'lp1-09']),
    ('second-koan', ['lp1-14', 'lp1-15']),
]


def factors(n):
    out = []
    divisor = 2
    while divisor * divisor <= n:
        while n % divisor == 0:
            out.append(divisor)
            n //= divisor
        divisor += 1
    if n > 1:
        out.append(n)
    return out


def report():
    inputs = ['data/index.json', 'experiments/records/lp1-word-length-balance/words.json']
    inputs += [f'text/{page}.txt' for _, pages in SECTIONS for page in pages]
    inputs += [f'data/pages/{page}.json' for _, pages in SECTIONS for page in pages]
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs}
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    primes = {entry['rune']: entry['prime'] for entry in alphabet}
    ledger = json.loads((ROOT / 'experiments/records/lp1-word-length-balance/words.json').read_text(encoding='utf-8'))
    rune_pattern = re.compile('[' + ''.join(primes) + ']+(?:\'[' + ''.join(primes) + ']+)*')
    cipher_words, reading_words, section_counts = [], [], {}
    for section, pages in SECTIONS:
        cipher = ''.join((ROOT / f'text/{page}.txt').read_text(encoding='utf-8') for page in pages)
        unknown = {c for c in cipher if '\u16a0' <= c <= '\u16ff'} - set(primes)
        if unknown:
            raise ValueError('Unrecognized rune in ' + section)
        cipher = cipher.replace('/', '').replace('\r', '').replace('\n', '')
        cwords = rune_pattern.findall(cipher)
        reading = ''.join(json.loads((ROOT / f'data/pages/{page}.json').read_text(encoding='utf-8'))['reading']['literal'] for page in pages)
        reading = reading.replace('/\n', '').replace('\r', '').replace('\n', '')
        rwords = re.findall("[A-Z]+(?:'[A-Z]+)?", reading)
        if len(cwords) != len(rwords):
            raise ValueError('Known reading and ciphertext word counts differ in ' + section)
        section_counts[section] = len(cwords)
        cipher_words.extend(cwords)
        reading_words.extend(rwords)
    if len(cipher_words) != 464 or len(ledger) != 464:
        raise ValueError('Expected exactly 464 words')
    if cipher_words != [row['ciphertext'] for row in ledger]:
        raise ValueError('Independent ciphertext tokenization differs from word ledger')
    sums = [sum(primes[c] for c in word if c in primes) for word in cipher_words]
    upper, lower = sum(sums[:331]), sum(sums[331:])
    return {
        'schema': 'liberpedia-464-pointer-audit-v1',
        'input_sha256': hashes,
        'section_counts': section_counts,
        'total_words': len(cipher_words),
        'forward_331': {'one_based_index': 331, 'reading': reading_words[330], 'cipher_gp_sum': sums[330]},
        'reverse_133': {'reverse_one_based_index': 133, 'forward_one_based_index': 464 - 133 + 1,
                        'reading': reading_words[331], 'cipher_gp_sum': sums[331]},
        'observed': {'first_331_gp_sum': upper, 'last_133_gp_sum': lower,
                     'total_gp_sum': sum(sums), 'first_331_factors': factors(upper),
                     'last_133_factors': factors(lower)},
        'reported': {'first_331_gp_sum': 71963, 'last_133_gp_sum': 26893},
        'matches_report': {'first_331': upper == 71963, 'last_133': lower == 26893},
        'word_prime_sums': sums,
        'word_readings': reading_words,
        'limits': 'Checks archived ciphertext and known reading, not source images. The supplied transcript omits its exact 464-word list; a different historical list could yield a different sum.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        if result != json.loads(OUTPUT.read_text(encoding='utf-8')):
            raise SystemExit('Recomputed pointer or sums differ from saved audit')
        print('464-word pointer, all word sums and input hashes reproduce.')
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'forward_331': result['forward_331']['reading'],
                      'reverse_133': result['reverse_133']['reading'],
                      'first_331_gp_sum': result['observed']['first_331_gp_sum'],
                      'last_133_gp_sum': result['observed']['last_133_gp_sum']}))
