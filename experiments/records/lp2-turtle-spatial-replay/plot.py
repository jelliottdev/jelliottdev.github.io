"""Create a compact, responsive visual of the planted and observed paths."""
import hashlib
import json
import random
from pathlib import Path

from run import HERE, ROOT, load_stream, walk


def trace(x, y, left, top, width, height, world=None):
    if world is None:
        world = (float(x.min()), float(x.max()), float(y.min()), float(y.max()))
    xmin, xmax, ymin, ymax = world
    scale = min((width - 20) / max(xmax - xmin, 1e-9), (height - 20) / max(ymax - ymin, 1e-9))
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    px = left + width / 2 + (x - cx) * scale
    py = top + height / 2 - (y - cy) * scale
    return "M" + " ".join(f"{a:.2f},{b:.2f}" for a, b in zip(px, py))


def main():
    _, _, indices, primes = load_stream()
    source = [primes[i] for i in indices]
    shuffled = source.copy()
    random.Random(3301).shuffle(shuffled)
    real = walk(source, 4, "relative", "unit")
    null = walk(shuffled, 4, "relative", "unit")
    plant = walk([0, 1, 2, 3] * 800, 4, "absolute", "unit")
    world = (min(float(real[0].min()), float(null[0].min())),
             max(float(real[0].max()), float(null[0].max())),
             min(float(real[1].min()), float(null[1].min())),
             max(float(real[1].max()), float(null[1].max())))
    panels = [
        ("Planted square", plant, None, "#235d75"),
        ("LP2 prime-value path", real, world, "#234e68"),
        ("Shuffled control", null, world, "#667b88"),
    ]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 360" role="img" aria-labelledby="title desc">',
           '<title id="title">Turtle paths: detectable square and two manuscript-stream renders</title>',
           '<desc id="desc">A planted square closes; the LP2 value path and a histogram-preserving shuffle are irregular. Both manuscript panels use the same coordinate scale.</desc>',
           '<style>text{font:16px system-ui,sans-serif;fill:#202b31}.sub{font-size:13px;fill:#5c6870}.border{fill:#f3f5f6;stroke:#c9d1d6}</style>']
    for i, (label, points, bounds, color) in enumerate(panels):
        left = 16 + i * 316
        out.append(f'<rect class="border" x="{left}" y="16" width="300" height="326" rx="4"/>')
        out.append(f'<text x="{left + 14}" y="44">{label}</text>')
        if i == 0:
            out.append(f'<text class="sub" x="{left + 14}" y="64">known shape · absolute, mod 4</text>')
        else:
            out.append(f'<text class="sub" x="{left + 14}" y="64">relative turns · unit steps · mod 4</text>')
        d = trace(*points, left + 12, 82, 276, 246, bounds)
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="0.95" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append('</svg>')
    (HERE / 'paths.svg').write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')
    print('wrote paths.svg', hashlib.sha256((HERE / 'paths.svg').read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
