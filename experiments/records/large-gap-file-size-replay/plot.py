"""Responsive source arithmetic and archive comparison chart."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
reported = r["reported_arithmetic"]
actual = r["archived_image_bytes"]
perm = r["fixed_label_permutation_reference"]
rows = [
    ("Big-gap list", reported["big_mean_kb"], "#31566e", 101),
    ("Comparison list", reported["regular_mean_kb_corrected"], "#74838b", 166),
]
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;")
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 350" role="img" aria-labelledby="title desc">',
    '<title id="title">Reported page groups differ by about 40 KiB, not 74 KiB</title>',
    '<desc id="desc">The post listed 16 big-gap pages averaging 582.8 KiB and 15 comparison pages averaging 542.9 KiB. Its printed comparison mean of 508.9 is an arithmetic error. The same archived JPEGs yield 39.8 KiB difference.</desc>',
    '<rect width="360" height="350" fill="#f7f8f9"/>',
    '<text x="18" y="33" font-family="system-ui,sans-serif" font-size="18" font-weight="650" fill="#24343d">The file-size comparison</text>',
    '<text x="18" y="57" font-family="system-ui,sans-serif" font-size="12" fill="#50626c">31 reported size labels match the archive.</text>',
]
for label, value, color, y in rows:
    width = value * .45
    parts += [f'<text x="18" y="{y}" font-family="system-ui,sans-serif" font-size="14" fill="#24343d">{esc(label)}</text>',
              f'<text x="340" y="{y}" text-anchor="end" font-family="system-ui,sans-serif" font-size="14" font-weight="650" fill="#24343d">{value:.1f} KiB</text>',
              f'<rect x="18" y="{y+10}" width="{width:.1f}" height="17" fill="{color}"/>']
parts += [
    '<path d="M18 209H342" stroke="#ccd3d6"/>',
    f'<text x="18" y="240" font-family="system-ui,sans-serif" font-size="15" fill="#24343d">Corrected difference <tspan font-weight="700">{reported["difference_kb_corrected"]:.1f} KiB</tspan></text>',
    f'<text x="18" y="267" font-family="system-ui,sans-serif" font-size="14" fill="#50626c">Published claim: <tspan text-decoration="line-through">{reported["difference_kb_claimed_approx"]} KiB</tspan></text>',
    f'<text x="18" y="302" font-family="system-ui,sans-serif" font-size="12" fill="#50626c">Archive: {actual["mean_difference"]/1024:.1f} KiB difference.</text>',
    f'<text x="18" y="320" font-family="system-ui,sans-serif" font-size="12" fill="#50626c">Fixed-label shuffle: {perm["one_sided_fraction"]*100:.1f}% at least as large.</text>',
    '<text x="18" y="338" font-family="system-ui,sans-serif" font-size="10" fill="#50626c">Neither comparison verifies the gap classification.</text>',
    '</svg>',
]
payload = '\n'.join(parts) + '\n'
target = HERE / 'file-size-comparison.svg'
if args.check:
    assert target.read_text(encoding='utf-8') == payload
else:
    target.write_text(payload, encoding='utf-8')
print(f'Chart {"checked" if args.check else "written"}.')
