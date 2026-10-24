"""Compact source-versus-fallback planted-control figure."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def draw(d):
    source=d['source_control'];fallback=d['fallback_control']
    assert source['recovered']==fallback['recovered']==40
    rows=[('Source',source['retained'],126,'#285674'),('KJV only',fallback['retained'],160,'#788b98'),
          ('Source',source['ranked_first'],242,'#285674'),('KJV only',fallback['ranked_first'],276,'#788b98')]
    parts=[]
    for name,value,y,color in rows:
        width=value*4.1
        parts.append(f'<text x="16" y="{y+13}" class="label">{name}</text>'
                     f'<rect x="92" y="{y}" width="{width:.1f}" height="18" rx="2" fill="{color}"/>'
                     f'<text x="296" y="{y+14}" class="value" text-anchor="end">{value}/40</text>')
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 348" role="img" aria-labelledby="title desc">
<title id="title">Matching totals can hide a different screen</title>
<desc id="desc">Both models retain 26 of 40 true offsets. The source model ranks 21 first, while the KJV-only fallback ranks 22 first. Five individual trial rankings changed.</desc>
<style>text{font-family:Arial,sans-serif;fill:#1f2c35}.heading{font-size:18px;font-weight:700}.sub{font-size:14px;fill:#52626c}.section{font-size:14px;font-weight:700}.label,.value{font-size:13px}.value{font-weight:700}</style>
<rect width="320" height="348" fill="#fff"/>
<text x="16" y="29" class="heading">Same total, different choices</text>
<text x="16" y="54" class="sub">40 planted messages at hidden offsets</text>
<path d="M16 70H304" stroke="#d8dee2"/>
<text x="16" y="101" class="section">True offset kept for decoding</text>
''' + ''.join(parts[:2]) + '''
<text x="16" y="217" class="section">True offset ranked first</text>
''' + ''.join(parts[2:]) + f'''
<path d="M16 312H304" stroke="#d8dee2"/>
<text x="16" y="335" class="section">{len(d['changed_trial_ids'])} of 40 trial rankings changed</text>
</svg>\n'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    value=draw(data);target=HERE/'comparison.svg'
    if a.check:
        assert target.read_text(encoding='utf-8')==value
    else:
        target.write_text(value,encoding='utf-8',newline='\n')
    print('PASS comparison.svg' if a.check else 'Wrote comparison.svg')


if __name__=='__main__':main()
