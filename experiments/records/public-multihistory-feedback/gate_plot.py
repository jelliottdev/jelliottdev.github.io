"""Compact chart of the source search's recovery on its own planted controls."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
summary = json.loads((HERE / "gate-results.json").read_text(encoding="utf-8"))["summary"]
labels = (("ct", "Visible-rune history"), ("pt", "Decoded-rune history"), ("mix", "Mixed history"))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="287" viewBox="0 0 360 287" role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif;background:#f7f8f9">',
       '<title id="title">Actual source search recovers seven of seven ciphertext-history plants but none of the fourteen plaintext or mixed-history plants</title>',
       '<desc id="desc">The source plants use seed 7,11,2. Ciphertext history ignores the seed after its first three runes. Plaintext and mixed history search only equal-symbol seeds and recover zero planted examples.</desc>',
       '<rect width="360" height="287" fill="#f7f8f9"/>',
       '<text x="18" y="29" font-size="19" font-weight="700" fill="#202b35">Can the search recover its plants?</text>',
       '<text x="18" y="52" font-size="15" fill="#4d5d68">Each row: seven planted feedback rules</text>']
for i, (key, label) in enumerate(labels):
    y = 85 + i * 57
    n = summary[key]["search_gate_pass"]
    svg += [f'<text x="18" y="{y}" font-size="16" fill="#26343f">{label}</text>',
            f'<rect x="18" y="{y+10}" width="255" height="14" rx="2" fill="#dbe4e9"/>',
            f'<rect x="18" y="{y+10}" width="{255*n/7:.1f}" height="14" rx="2" fill="#346b86"/>',
            f'<text x="340" y="{y+23}" font-size="16" font-weight="700" fill="#26343f" text-anchor="end">{n} / 7</text>']
svg += ['<text x="18" y="251" font-size="15" fill="#4d5d68">True seed: 7, 11, 2</text>',
        '<text x="18" y="272" font-size="15" fill="#4d5d68">Plain/mixed: only constant seed triples</text>',
        '</svg>']
(HERE / "search-domain-gate.svg").write_text("\n".join(svg) + "\n", encoding="utf-8", newline="\n")
