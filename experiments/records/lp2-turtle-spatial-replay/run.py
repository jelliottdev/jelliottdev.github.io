"""Independent replay of Dukotah round 22 lane B's finite turtle render.

The 55 nonempty source segments equal Liberpedia LP2-00..49 and LP2-51..55.
No English score or discretionary picture reading enters this calculation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE_SHA = "79b14e630946b64cdca838f328e73904f506df576d15e21fcb46271d4b4c8040"
MODULI = (4, 6, 8, 12, 29, 360)
STATS = ("closure", "self_intersections", "bbox_fill", "caging", "symmetry", "components")


def load_stream():
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = index["alphabet"]
    by_rune = {row["rune"]: i for i, row in enumerate(alphabet)}
    page_ids = [f"lp2-{i:02}" for i in list(range(50)) + list(range(51, 56))]
    chunks = []
    for page in page_ids:
        raw = (ROOT / "text" / f"{page}.txt").read_text(encoding="utf-8")
        chunks.append("".join(ch for ch in raw if ch in by_rune))
    runes = "".join(chunks)
    digest = hashlib.sha256(runes.encode("utf-8")).hexdigest()
    if digest != SOURCE_SHA or len(runes) != 12956:
        raise ValueError(f"Input differs from pinned source stream: {len(runes)} / {digest}")
    indices = [by_rune[ch] for ch in runes]
    primes = [row["prime"] for row in alphabet]
    return page_ids, digest, indices, primes


def walk(values, modulus, turn, step):
    values = np.asarray(values, dtype=np.float64)
    angles = np.mod(values, modulus) * (360.0 / modulus)
    if turn == "relative":
        angles = np.cumsum(angles)
    angles = np.deg2rad(angles)
    lengths = np.ones(len(values)) if step == "unit" else values / max(float(values.max()), 1.0)
    x = np.concatenate(([0.0], np.cumsum(lengths * np.cos(angles))))
    y = np.concatenate(([0.0], np.cumsum(lengths * np.sin(angles))))
    return x, y


def raster(x, y, resolution=128):
    xmin, ymin = float(x.min()), float(y.min())
    scale = (resolution - 1) / max(float(np.ptp(x)), float(np.ptp(y)), 1e-9)
    t = np.linspace(0.0, 1.0, 8)
    sx = x[:-1, None] + (x[1:] - x[:-1])[:, None] * t
    sy = y[:-1, None] + (y[1:] - y[:-1])[:, None] * t
    col = np.clip(((sx - xmin) * scale).astype(int).ravel(), 0, resolution - 1)
    row = np.clip(((sy - ymin) * scale).astype(int).ravel(), 0, resolution - 1)
    image = np.zeros((resolution, resolution), dtype=bool)
    image[row, col] = True
    return image


def overlap(a, b):
    both = np.logical_and(a, b).sum()
    either = np.logical_or(a, b).sum()
    return float(both / either) if either else 1.0


def crossings(x, y, seed=3301):
    n = len(x) - 1
    if n < 4:
        return 0.0
    rng = np.random.default_rng(seed)
    sampled = min(60000, int(n * (n - 1) / 2))
    left = rng.integers(0, n, sampled)
    right = rng.integers(0, n, sampled)
    keep = np.abs(left - right) >= 2
    left, right = left[keep], right[keep]
    ax, ay = x[left], y[left]
    bx, by = x[left + 1], y[left + 1]
    cx, cy = x[right], y[right]
    dx, dy = x[right + 1], y[right + 1]

    def orientation(px, py, qx, qy, rx, ry):
        return (ry - py) * (qx - px) > (qy - py) * (rx - px)

    first = orientation(ax, ay, cx, cy, dx, dy) != orientation(bx, by, cx, cy, dx, dy)
    second = orientation(ax, ay, bx, by, cx, cy) != orientation(ax, ay, bx, by, dx, dy)
    return float(np.count_nonzero(first & second) / len(left) * n * (n - 1) / 2)


def measure(x, y, seed=3301):
    distance = float(np.hypot(np.diff(x), np.diff(y)).sum()) or 1e-9
    closure = math.hypot(float(x[-1] - x[0]), float(y[-1] - y[0])) / distance
    cells = raster(x, y)
    _, components = ndimage.label(cells)
    return {
        "closure": closure,
        "self_intersections": crossings(x, y, seed),
        "bbox_fill": float(cells.mean()),
        "caging": closure,
        "symmetry": max(overlap(cells, np.fliplr(cells)), overlap(cells, np.flipud(cells)), overlap(cells, np.rot90(cells))),
        "components": float(components),
    }


def empirical_two_sided(observed, samples):
    arr = np.asarray(samples)
    return float(2 * min(np.count_nonzero(arr <= observed), np.count_nonzero(arr >= observed)) / len(arr))


def plant_control(values, modulus=4):
    x, y = walk(values, modulus, "absolute", "unit")
    observed = measure(x, y)
    samples = {key: [] for key in STATS}
    for k in range(200):
        shuffled = list(values)
        import random
        random.Random(3301 + k).shuffle(shuffled)
        sx, sy = walk(shuffled, modulus, "absolute", "unit")
        result = measure(sx, sy, 3301 + k)
        for key in STATS:
            samples[key].append(result[key])
    return {"observed": observed,
            "p": {key: empirical_two_sided(observed[key], samples[key]) for key in STATS}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--full-null", action="store_true", help="Run 200 source-matched shuffles for all 72 constructions")
    args = parser.parse_args()
    page_ids, digest, indices, primes = load_stream()
    streams = {
        "value": [primes[i] for i in indices],
        "pi": [i + 1 for i in indices],
        "phi": [primes[i] - 1 for i in indices],
    }
    source = json.loads((HERE / "source-ledger.json").read_text(encoding="utf-8"))
    source_by_id = {row["combo"]: row for row in source["rows"]}
    rows = []
    for name, values in streams.items():
        for modulus in MODULI:
            for turn in ("absolute", "relative"):
                for step in ("unit", "value"):
                    case_id = f"{name}_M{modulus}_{turn}_{step}"
                    x, y = walk(values, modulus, turn, step)
                    observed = measure(x, y)
                    baseline = source_by_id[case_id]["real"]
                    maximum_difference = max(abs(observed[s] - baseline[s]) for s in STATS)
                    row = {"id": case_id, "stream": name, "modulus": modulus, "turn": turn,
                           "step": step, "observed": observed, "source_max_absolute_difference": maximum_difference}
                    if args.full_null:
                        import random
                        nulls = {key: [] for key in STATS}
                        for k in range(200):
                            shuffled = list(values)
                            random.Random(3301 + k).shuffle(shuffled)
                            sx, sy = walk(shuffled, modulus, turn, step)
                            sample = measure(sx, sy, 3301 + k)
                            for key in STATS:
                                nulls[key].append(sample[key])
                        row["null_p"] = {key: empirical_two_sided(observed[key], nulls[key]) for key in STATS}
                        row["null_mean"] = {key: float(np.mean(nulls[key])) for key in STATS}
                        row["source_null_p_difference"] = max(abs(row["null_p"][s] - source_by_id[case_id]["null_p"][s]) for s in STATS)
                        row["source_null_mean_difference"] = max(abs(row["null_mean"][s] - source_by_id[case_id]["null_mean"][s]) for s in STATS)
                    rows.append(row)
    square = plant_control([0, 1, 2, 3] * 800)
    comb = plant_control([1, 0, 3, 0] * 500)
    output = {"schema": "liberpedia-turtle-spatial-replay-v1", "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
              "source_stream_sha256": digest, "source_segment_pages": page_ids,
              "rune_count": len(indices), "case_count": len(rows), "rows": rows,
              "controls": {"square": square, "blockcomb": comb},
              "source_report_flags": source["flagged_for_oracle"]}
    target = HERE / "results.json"
    if args.check:
        previous = json.loads(target.read_text(encoding="utf-8"))
        if not args.full_null:
            # Check the deterministic constructions and controls against the full saved run.
            for key in ("source_stream_sha256", "source_segment_pages", "rune_count", "case_count", "controls"):
                assert output[key] == previous[key], key
            for now, then in zip(rows, previous["rows"]):
                assert now["id"] == then["id"] and now["observed"] == then["observed"]
        else:
            assert output == previous
        print("PASS: source stream, 72 constructions, controls, and saved results")
    else:
        target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Saved {len(rows)} cases; max source difference {max(r['source_max_absolute_difference'] for r in rows):.3g}")


if __name__ == "__main__":
    main()
