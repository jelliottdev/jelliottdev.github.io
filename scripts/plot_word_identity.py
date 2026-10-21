"""Draw positions uniquely identifiable by exact word form in the LP1 object."""
import json
from pathlib import Path
from audit_word_identity import calculate

ROOT = Path(__file__).resolve().parents[1]


def render():
    report = json.loads((ROOT / 'exports/word-identity.json').read_bytes())
    assert report == calculate()
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 330" role="img" aria-labelledby="title desc">',
             '<title id="title">Can a word identify one position?</title>',
             '<desc id="desc">Of 464 positions, 248 ciphertext words occur only once and 216 occur more than once. In decoded rune text, 116 occur only once and 348 occur more than once.</desc>',
             '<rect width="380" height="330" fill="white"/>',
             '<style>text{font:15px Arial,sans-serif;fill:#25343a}.small{font-size:13px}</style>',
             '<text x="20" y="28">Can a word identify one position?</text>',
             '<text x="20" y="51" class="small">Same 464 positions · exact rune-word equality</text>']
    for i, (key, label) in enumerate([('ciphertext', 'Ciphertext'), ('decoded_runes', 'Decoded rune text')]):
        counts = report['summaries'][key]
        unique = counts['singleton_forms_and_positions']
        repeated = counts['positions_with_nonunique_form']
        width = 340 * unique / counts['positions']
        y = 84 + i * 90
        parts.extend([f'<text x="20" y="{y}">{label}</text>',
                      f'<rect x="20" y="{y + 12}" width="{width:.3f}" height="24" fill="#42687b"/>',
                      f'<rect x="{20 + width:.3f}" y="{y + 12}" width="{340-width:.3f}" height="24" fill="#bfccd2"/>',
                      f'<text x="20" y="{y + 57}" class="small">{unique} unique positions · {repeated} nonunique positions</text>'])
    parts.extend(['<rect x="20" y="256" width="12" height="12" fill="#42687b"/>',
                  '<text x="40" y="267" class="small">This word form occurs once</text>',
                  '<rect x="20" y="281" width="12" height="12" fill="#bfccd2"/>',
                  '<text x="40" y="292" class="small">This word form occurs at several positions</text>',
                  '</svg>'])
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    (ROOT / 'exports/figures/word-identity.svg').write_text(render(), encoding='utf-8', newline='\n')
