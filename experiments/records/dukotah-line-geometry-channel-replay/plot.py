"""Compact, phone-sized view of the source gate and observed control recovery."""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE / 'independent-controls.json'
OUT = HERE / 'control-gates.svg'

def make():
    d = json.loads(AUDIT.read_text(encoding='utf-8'))
    fill = d['C3a_highest_recovery']
    c3b = d['C3b']
    assert not d['C3a_gate_pass'] and not c3b['planted_message_recovered']
    start, width = 24, 270
    gate_x = start + width * d['C3a_required_recovery']
    fill_x = start + width * fill
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 266" role="img" aria-labelledby="t d" style="font-family:Arial,sans-serif">
<title id="t">The planted-message gate was not met</title>
<desc id="d">The strongest fill-ratio plant recovered 85.9 percent of bits, below its required 95 percent. A separate ASCII plant was labeled pass by a four-gram score, but reproduced only 29 of 77 intended characters.</desc>
<rect width="320" height="266" fill="#fff"/>
<text x="24" y="28" fill="#222b33" font-size="17" font-weight="700">Did the test recover its plants?</text>
<text x="24" y="58" fill="#304e61" font-size="14" font-weight="700">Line-fill plant</text>
<text x="24" y="77" fill="#4c5862" font-size="13">Best of seven planted separations</text>
<rect x="{start}" y="92" width="{width}" height="24" fill="#e8edf0"/>
<rect x="{start}" y="92" width="{fill_x-start:.2f}" height="24" fill="#54788b"/>
<line x1="{gate_x:.2f}" y1="85" x2="{gate_x:.2f}" y2="125" stroke="#38434b" stroke-width="2"/>
<text x="24" y="139" fill="#35414a" font-size="14">Recovered <tspan font-weight="700">{100*fill:.1f}%</tspan> of bits</text>
<text x="294" y="139" text-anchor="end" fill="#35414a" font-size="14">Needs 95%</text>
<line x1="24" y1="157" x2="294" y2="157" stroke="#dce3e7"/>
<text x="24" y="181" fill="#304e61" font-size="14" font-weight="700">Separate ASCII plant</text>
<text x="24" y="204" fill="#35414a" font-size="14">Source label: “PASS” by four-gram score</text>
<text x="24" y="226" fill="#35414a" font-size="14">Actual text: <tspan font-weight="700">{c3b['character_matches']} of {c3b['characters']} letters</tspan> matched</text>
<text x="24" y="249" fill="#62707a" font-size="13">This gate cannot establish a negative result.</text>
</svg>'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    svg = make()
    if args.check:
        assert OUT.read_text(encoding='utf-8') == svg
    else:
        OUT.write_text(svg, encoding='utf-8', newline='\n')
    print(OUT.name)

if __name__ == '__main__':
    main()
