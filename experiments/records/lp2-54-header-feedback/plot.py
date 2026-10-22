"""Render the six declared header openings as a compact SVG comparison."""
import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    chosen = [x for x in data["cases"] if x["first_plain_rune"]]
    assert len(chosen) == 6
    rows = [("Source", [plan["labels"][i] for i in data["header_cipher_indices"]], "source")]
    rows += [(('CT' if x['mode'] == 'ciphertext_feedback' else 'PT') + ' · ' + x['first_plain_rune'], x['header_labels'], x['mode']) for x in chosen]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 400" role="img" aria-labelledby="title desc">',
           '<title id="title">LP2-54 red header under two feedback recurrences</title>',
           '<desc id="desc">Nine source rune positions and six decrypted rows for A, I and O first-rune cribs. The boundary after the first rune is marked. Ciphertext feedback gives the same final eight runes for all three primers; plaintext feedback changes them.</desc>',
           '<rect width="820" height="400" fill="#fff"/>',
           '<text x="20" y="32" font-family="Georgia,serif" font-size="24" fill="#202a30">LP2-54 · nine-rune red header</text>',
           '<text x="20" y="55" font-family="Arial,sans-serif" font-size="13" fill="#59656b">All 29 primers were enumerated; rows show the proposed A, I and O openings.</text>']
    x0, step = 154, 71
    for i in range(9):
        x = x0 + i * step
        out.append(f'<text x="{x}" y="80" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#607078">{i+1}</text>')
    out.append('<line x1="188" y1="87" x2="188" y2="365" stroke="#ad7e57" stroke-width="2"/>')
    for row, (name, cells, mode) in enumerate(rows):
        top = 91 + row * 42
        bg = '#f3f5f4' if row % 2 == 0 else '#fff'
        out.append(f'<rect x="12" y="{top}" width="796" height="40" fill="{bg}"/>')
        label_color = '#8f3940' if mode == 'source' else '#294b5e'
        out.append(f'<text x="20" y="{top+26}" font-family="Arial,sans-serif" font-size="17" font-weight="600" fill="{label_color}">{html.escape(name)}</text>')
        for i, item in enumerate(cells):
            x = x0 + i * step
            out.append(f'<text x="{x}" y="{top+26}" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" fill="#202a30">{html.escape(item)}</text>')
    out += ['<text x="20" y="392" font-family="Arial,sans-serif" font-size="12" fill="#59656b">CT: previous ciphertext rune · PT: previous plaintext rune · indices are modulo 29</text>', '</svg>']
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render()
    target = HERE / 'header-feedback.svg'
    if args.check:
        assert target.read_text(encoding='utf-8') == text
        print('PASS: header figure matches the saved 58-case census')
    else:
        target.write_text(text, encoding='utf-8', newline='\n')
        print('Wrote', target)


if __name__ == '__main__':
    main()
