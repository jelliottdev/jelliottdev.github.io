"""Prove the grid radix bound under explicit positional-digit/byte assumptions.

Python 3 standard library. --write saves the report; --check verifies it.
Reads page records directly, not a previously converted byte stream.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/grid-radix-bound.json'
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def report():
    rows, hashes = [], {}
    for n in [49,50,51]:
        relative = f'data/pages/lp2-{n}.json'
        blob = (ROOT / relative).read_bytes()
        hashes[relative] = hashlib.sha256(blob).hexdigest()
        page = json.loads(blob)
        grid_row = 0
        for line in page['raw'].splitlines():
            if not re.fullmatch(r'[0-9A-Za-z]{2}(?:-[0-9A-Za-z]{2})+/?', line):
                continue
            grid_row += 1
            tokens = line.removesuffix('/').split('-')
            assert len(tokens) == 8
            for column, token in enumerate(tokens,1):
                rows.append(dict(page=page['id'],grid_row=grid_row,column=column,token=token))
    assert len(rows) == 256
    digits = [(ALPHABET.index(x['token'][0]),ALPHABET.index(x['token'][1])) for x in rows]
    lower = max(max(pair) for pair in digits) + 1
    upper = min((255-b)//a for a,b in digits if a)
    assert lower == upper == 60
    witnesses = [x for x in rows if 'x' in x['token'] or x['token'] == '4F']
    alternatives = []
    for base in [59,60,61,62]:
        values = [a*base+b for a,b in digits]
        alternatives.append(dict(base=base,valid_digits=all(max(pair)<base for pair in digits),
                                 minimum=min(values),maximum=max(values),over_byte=sum(v>255 for v in values)))
    reversed_values = [b*lower+a for a,b in digits]
    return dict(assumptions=['One common integer base, positional two-digit numerals.',
                            'Digit values follow 0–9, A–Z, a–z, starting at zero.',
                            'Every entry represents one unsigned byte, 0–255.'],
                source_sha256=hashes,entries=len(rows),digit_alphabet=ALPHABET,
                lower_bound=lower,upper_bound=upper,witnesses=witnesses,
                alternatives=alternatives,reversed_order_maximum_at_minimum_base=max(reversed_values),
                reversed_order_over_byte=sum(v>255 for v in reversed_values),
                limits=['Conditional uniqueness does not prove the byte assumption.',
                        'Different digit values, nonpositional codes and larger values are outside the proof.',
                        'No row traversal, multi-byte endianness, cipher or payload interpretation follows.'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args(); result=report()
    if args.write:
        OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    elif args.check:
        assert json.loads(OUTPUT.read_bytes())==result
        print('PASS: 256 entries force base 60 under the stated assumptions; saved report matches.')
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
