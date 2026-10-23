"""Small-screen diagram of the full source varint matrix's strongest comparisons."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["rows"]
names = (("canon_256", "Canonical bytes"),
         ("canon_256_decpref", "Decimal-preferred"),
         ("payload_resolved", "Resolved variant"))
bars = [(label, max(abs(x["rho"]) for x in rows if x["variant"] == key)) for key, label in names]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="298" viewBox="0 0 360 298" role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif;background:#f7f8f9">',
       '<title id="title">Strongest varint gap match by byte version</title>',
       '<desc id="desc">Each of three byte versions has a strongest absolute rank correlation near 0.12, well below the source gate of 0.5. Each bar summarizes eight source comparisons.</desc>',
       '<rect width="360" height="298" fill="#f7f8f9"/>',
       '<text x="18" y="28" font-size="19" font-weight="700" fill="#202b35">Payload as gap values</text>',
       '<text x="18" y="51" font-size="15" fill="#4d5d68">Strongest of 8 comparisons per version</text>']
for i, (label, value) in enumerate(bars):
    y = 80 + i * 60
    svg += [f'<text x="18" y="{y}" font-size="16" fill="#26343f">{label}</text>',
            f'<rect x="18" y="{y+9}" width="264" height="13" rx="2" fill="#dce3e8"/>',
            f'<rect x="18" y="{y+9}" width="{264*value/.5:.1f}" height="13" rx="2" fill="#346b86"/>',
            f'<text x="340" y="{y+20}" font-size="15" fill="#26343f" text-anchor="end">{value:.3f}</text>']
svg += ['<line x1="282" y1="67" x2="282" y2="218" stroke="#7a3030" stroke-width="2" stroke-dasharray="4 3"/>',
        '<text x="18" y="249" font-size="15" fill="#7a3030">Red line: source gate 0.5</text>',
        '<text x="18" y="272" font-size="15" fill="#4d5d68">No comparison reached it.</text>',
        '</svg>']
(HERE / "varint-gap-matrix.svg").write_text("\n".join(svg) + "\n", encoding="utf-8", newline="\n")
