"""Draw a phone-readable summary of strict full-stream decoder outcomes."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
labels = [('zlib', 'zlib'), ('gzip', 'gzip'), ('raw-deflate', 'Raw DEFLATE'),
          ('bzip2', 'bzip2'), ('xz', 'XZ')]
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 354" role="img" aria-labelledby="title desc">',
    '<title id="title">Complete compression decodes of rune-packed streams</title>',
    '<desc id="desc">Five formats tested on each of 168 byte streams. Every one of the 840 strict complete-stream attempts was invalid; no stream reached the output limit.</desc>',
    '<rect width="340" height="354" fill="#fff"/>',
    '<text x="16" y="29" font-family="sans-serif" font-size="18" fill="#202b32">Compression check</text>',
    '<text x="16" y="53" font-family="sans-serif" font-size="13" fill="#53616a">168 fixed streams · 5 formats</text>',
]
for i, (key, name) in enumerate(labels):
    y = 76 + i * 49
    counts = result['by_format'][key]
    assert counts == {'invalid': 168}
    parts += [
        f'<rect x="16" y="{y}" width="308" height="40" fill="#edf0f2"/>',
        f'<text x="28" y="{y+26}" font-family="sans-serif" font-size="14" fill="#202b32">{name}</text>',
        f'<text x="215" y="{y+26}" font-family="sans-serif" font-size="14" fill="#365d71">0 / 168 valid</text>',
    ]
parts += [
    '<path d="M16 329H324" stroke="#c7d0d5"/>',
    '<text x="16" y="347" font-family="sans-serif" font-size="13" fill="#53616a">Synthetic valid and error controls passed.</text>',
    '</svg>',
]
(HERE / 'summary.svg').write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
print('Wrote summary.svg')
