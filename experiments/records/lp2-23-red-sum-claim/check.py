"""Independent integer-prime and span check; does not import the producer."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    rune_order = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
    primes = [n for n in range(2,110) if all(n%d for d in range(2,int(n**.5)+1))]
    assert len(primes) == 29
    by_rune = dict(zip(rune_order,primes))
    text = (ROOT / 'text/lp2-23.txt').read_text(encoding='utf-8')
    span = re.match(r'([^.]*)[.]',text).group(1)
    actual = [by_rune[c] for c in span if c in by_rune]
    expected = [3,97,19,79,17,47,89,17,31,61,31,41,59,61,31,103]
    assert actual == expected and sum(actual) == 786
    report = json.loads((HERE / 'results.json').read_bytes())
    assert report['header']['values'] == actual
    assert report['header']['word_lengths'] == [2,6,3,5]
    # Independent, explicitly written phrase encoding; K is GP C.
    phrase = [59,67,53,59,5,67,13,29,7,19,73,67,89,17,67]
    assert sum(phrase) == 691 and len(phrase) == 15
    assert report['phrase_th_rune']['values'] == phrase
    assert report['phrase_split_th']['sum'] == 691-5+59+23 == 768
    assert report['difference'] == 95 and report['same_sum'] is False
    assert report['a_to_f_sensitivity']['sum'] == sum(actual)-97+2 == 691
    assert report['a_to_f_sensitivity']['is_transcription_correction'] is False
    print('PASS: archived header786; phrase691 under TH-rune encoding; splitting TH gives768; no source glyph corrected.')


if __name__ == '__main__':
    main()
