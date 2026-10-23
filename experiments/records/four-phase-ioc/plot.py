"""Write a phone-readable SVG of the four-phase comparison."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
lo, hi = 0.0343, 0.03475
x0, x1 = 106, 336


def position(value):
    return x0 + (value - lo) / (hi - lo) * (x1 - x0)


lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="360" viewBox="0 0 360 462" role="img" aria-labelledby="title desc">',
    '<title id="title">Four alternating rune streams and their collision rates</title>',
    '<desc id="desc">Successive rune positions repeat phases zero through three. Each observed LP2 phase is within the middle 95 percent of 1,999 page-shuffled controls. A planted four-stream warning-page control is detected.</desc>',
    '<rect width="360" height="462" fill="#fff"/>',
    '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#26343c}.head{font-size:17px;font-weight:700}.small{font-size:12px;fill:#52616a}.label{font-size:13px;font-weight:600}.tick{font-size:11px;fill:#53616a}</style>',
    '<text x="16" y="28" class="head">Four alternating streams</text>',
    '<text x="16" y="49" class="small">Successive rune positions repeat 0, 1, 2, 3.</text>',
]
for i in range(8):
    x = 17 + i * 40
    phase = i % 4
    fill = "#dfe9ee" if phase in (0, 2) else "#f0f3f5"
    lines.append(f'<rect x="{x}" y="64" width="33" height="32" rx="3" fill="{fill}" stroke="#bcc9cf"/>')
    lines.append(f'<text x="{x+16.5}" y="86" text-anchor="middle" font-size="15">{phase}</text>')
lines += [
    '<text x="16" y="134" class="head">LP2 against page shuffles</text>',
    '<text x="16" y="154" class="small">Dot: manuscript. Line: middle 95% of controls.</text>',
]
for tick in (0.0343, 0.0345, 0.0347):
    x = position(tick)
    lines.append(f'<line x1="{x:.1f}" y1="177" x2="{x:.1f}" y2="316" stroke="#e8edef"/>')
    lines.append(f'<text x="{x:.1f}" y="336" text-anchor="middle" class="tick">{tick:.4f}</text>')
for phase in range(4):
    y = 193 + phase * 36
    observed = saved["observed"]["phase_ioc"][phase]
    left, right = saved["null"]["phase_central_95"][phase]
    lines.append(f'<text x="16" y="{y+5}" class="label">Phase {phase}</text>')
    lines.append(f'<line x1="{position(left):.1f}" y1="{y}" x2="{position(right):.1f}" y2="{y}" stroke="#9caab1" stroke-width="8" stroke-linecap="round"/>')
    lines.append(f'<circle cx="{position(observed):.1f}" cy="{y}" r="6" fill="#21516b" stroke="#fff" stroke-width="2"/>')
lines += [
    '<line x1="16" y1="358" x2="344" y2="358" stroke="#dce4e8"/>',
    '<text x="16" y="383" class="label">Planted control: detected</text>',
    '<text x="16" y="403" class="small">Four shifted copies of a known reading:</text>',
    '<text x="16" y="421" class="small">phase IoC 0.0640; none of 1,999 shuffles higher.</text>',
    '<text x="16" y="447" class="small">A narrow test of concentration, not every cipher.</text>',
    '</svg>'
]
(HERE / "phase-comparison.svg").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("Wrote phase-comparison.svg")
