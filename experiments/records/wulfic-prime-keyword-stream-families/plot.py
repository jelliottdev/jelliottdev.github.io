"""Phone-readable comparison of full-search IoC peaks against shuffled pages."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE=Path(__file__).resolve().parent
OUT=HERE/'comparison.svg'


def figure():
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    rows=[
        ('Repeated keywords',data['observed']['keyword_only']['max_ioc']['ioc'],
         [x['keyword_only_max_ioc'] for x in data['null']],data['null_ge']['keyword_only_max_ioc']),
        ('Prime streams',data['observed']['prime_stream']['max_ioc']['ioc'],
         [x['prime_stream_max_ioc'] for x in data['null']],data['null_ge']['prime_stream_max_ioc']),
        ('Keyword-stepped primes',data['observed']['keyword_stepped']['max_ioc_after_singleton_gate']['ioc'],
         [x['keyword_stepped_max_ioc'] or 0 for x in data['null']],data['null_ge']['keyword_stepped_max_ioc']),
    ]
    left,right=32,309
    scale=lambda value:left+(value-1.0)/.35*(right-left)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 340 356">',
           '<title id="title">Three source searches compared with complete shuffled controls</title>',
           '<desc id="desc">Each row shows the observed maximum index of coincidence and the minimum-to-maximum range of 49 complete-search shuffles. Prime streams reached a higher maximum than 48 of 49 shuffles, but did not produce a reading.</desc>',
           '<rect width="340" height="356" fill="#fff"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#23313a;font-size:13px} .small{fill:#53636f}.bold{font-weight:700}</style>',
           '<text x="16" y="27" class="bold" font-size="17">Highest IoC in each search</text>',
           '<text x="16" y="49" class="small">Blue: manuscript  ·  Gray: 49 shuffled runs</text>']
    for index,(label,observed,null,ge) in enumerate(rows):
        y=84+index*88
        lo,hi=min(null),max(null)
        parts.extend([
            f'<text x="16" y="{y}" class="bold">{escape(label)}</text>',
            f'<line x1="{left}" y1="{y+19}" x2="{right}" y2="{y+19}" stroke="#d5dde2" stroke-width="2"/>',
            f'<line x1="{scale(lo):.1f}" y1="{y+19}" x2="{scale(hi):.1f}" y2="{y+19}" stroke="#8d9ca6" stroke-width="7" stroke-linecap="round"/>',
            f'<circle cx="{scale(observed):.1f}" cy="{y+19}" r="7" fill="#236080" stroke="#fff" stroke-width="2"/>',
            f'<text x="16" y="{y+45}" class="small">Observed {observed:.3f}  ·  matched by {ge} of 49</text>',
        ])
    parts.extend(['<text x="24" y="336" class="small">1.00</text>',
                  '<text x="276" y="336" class="small">1.35 IoC</text>',
                  '</svg>'])
    return '\n'.join(parts)+'\n'


if __name__=='__main__':
    rendered=figure()
    if '--check' in sys.argv:assert OUT.read_text(encoding='utf-8')==rendered
    else:OUT.write_text(rendered,encoding='utf-8',newline='\n')
    print('PASS: comparison figure')
