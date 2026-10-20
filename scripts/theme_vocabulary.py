"""Map four selected words across contextual readings; no semantic or significance test."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
from reading_concordance import concordance

ROOT = Path(__file__).resolve().parents[1]
TERMS = ('truth', 'self', 'divinity', 'instar')
LABELS = {'warning': 'Warning', 'welcome': 'Welcome', 'some-wisdom': 'Some Wisdom',
          'first-koan': 'First koan', 'loss-of-divinity': 'Loss of Divinity',
          'second-koan': 'Second koan', 'instruction': 'Instruction',
          'lp2-56': 'LP2-56', 'lp2-57': 'Parable · LP2-57'}


def measure():
    source = ROOT / 'data/evidence/known-readings.json'
    raw = source.read_bytes()
    controls = json.loads(raw)['controls']
    rows = []
    for control in controls:
        counts, hits = {}, {}
        for term in TERMS:
            found = concordance([control], term, context=8)
            # Separate regex check of exact matches and source offsets.
            direct = list(re.finditer(r"(?<![A-Za-z0-9'’])" + term + r"(?![A-Za-z0-9'’])",
                                      control['reading'], re.I))
            assert [(h['source_start'], h['source_end']) for h in found] == [m.span() for m in direct]
            counts[term] = len(found)
            hits[term] = found
        rows.append({'section': control['id'], 'label': LABELS[control['id']],
                     'pages': control['pages'], 'counts': counts, 'hits': hits})
    return {'schema': 'liberpedia-theme-vocabulary-v1', 'source': source.relative_to(ROOT).as_posix(),
            'source_sha256': hashlib.sha256(raw).hexdigest(), 'terms': list(TERMS),
            'method': 'Exact case-insensitive whole words in each stored contextual reading, once per section including stored headings; no prefix, stemming, possessive expansion or semantic classification.',
            'limits': 'Editorially selected terms. Raw counts, not normalized frequencies, rune counts, source attributions or significance estimates. A zero does not mean the theme is absent.',
            'sections': rows}


def figure(report):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="440" viewBox="0 0 360 440" role="img" aria-labelledby="title desc">',
           '<title id="title">Selected words across the known readings</title>',
           '<desc id="desc">A count matrix for truth, self, divinity and instar across nine contextual reading sections. Counts indicate exact wording, not the presence or importance of a theme.</desc>',
           '<rect width="360" height="440" fill="white"/><g font-family="Arial,sans-serif" fill="#243d4a">',
           '<text x="10" y="22" font-size="16" font-weight="bold">Where the wording recurs</text>',
           '<text x="10" y="44" font-size="12">Contextual English; stored headings included</text>']
    for i, term in enumerate(TERMS):
        svg.append(f'<text x="{166+i*52}" y="72" text-anchor="middle" font-size="11">{term.capitalize()}</text>')
    for row_index, row in enumerate(report['sections']):
        y = 84 + row_index * 31
        svg.append(f'<text x="10" y="{y+20}" font-size="12">{escape(row["label"])}</text>')
        for i, term in enumerate(TERMS):
            value = row['counts'][term]
            fill = '#d8e7ed' if value else '#f4f4f1'
            svg.append(f'<rect x="{142+i*52}" y="{y}" width="48" height="27" fill="{fill}"/>')
            svg.append(f'<text x="{166+i*52}" y="{y+19}" text-anchor="middle" font-size="14">{value}</text>')
    svg += ['<text x="10" y="385" font-size="12">Shading marks presence; numbers give counts.</text>',
            '<text x="10" y="407" font-size="12">A zero is not evidence that the idea is absent.</text>',
            '<text x="10" y="427" font-size="12">Read each passage before interpreting a connection.</text>', '</g></svg>']
    return '\n'.join(svg) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = measure()
    files = {'exports/theme-vocabulary.json': json.dumps(report, ensure_ascii=False, indent=2)+'\n',
             'exports/figures/theme-vocabulary.svg': figure(report)}
    for name, content in files.items():
        path = ROOT / name
        if args.write:
            path.write_text(content, encoding='utf-8', newline='\n')
        else:
            assert path.read_text(encoding='utf-8') == content, name + ' differs'
    print('PASS: nine sections, four exact words, every source offset, report and figure')
