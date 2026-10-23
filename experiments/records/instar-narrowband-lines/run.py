"""Measure two fixed narrowband claims in pinned Cicada audio files.

Run from any directory: python experiments/records/instar-narrowband-lines/run.py --check
Requires numpy, scipy, and soundfile. Does not search for or decode a watermark.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import welch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FILES = {
    "instar": ("exports/sources/cicada-2013-twitter/761.mp3", "83008217439110c3b824898af73b99cb2cf0657dda88cb363c3aa34a4ec0a460"),
    "interconnectedness": ("exports/audio/interconnectedness.mp3", "1ce3839b4a62462d9009c4469acc189b523e1bdcf338cb49cda1cd7bb4efffc6"),
}
NFFT = 65536


def one_file(name, relpath, expected_hash):
    path = ROOT / relpath
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_hash:
        raise ValueError(f"Audio identity changed: {relpath}: {digest}")
    audio, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != 44100 or audio.shape[1] != 2:
        raise ValueError(f"Unexpected sample format: {relpath}")
    mono = audio.mean(axis=1)
    freq, power = welch(mono, sr, window="hann", nperseg=NFFT, noverlap=NFFT // 2)
    measurements = {}
    for label, low, high, margin in (("mains_region", 50, 70, 20), ("horizontal_scan_region", 14000, 17000, 300)):
        target = np.flatnonzero((freq >= low) & (freq <= high))
        peak = int(target[np.argmax(power[target])])
        surrounding = (freq >= low - margin) & (freq <= high + margin) & (np.abs(freq - freq[peak]) > 3)
        baseline = float(np.median(power[surrounding]))
        measurements[label] = {
            "peak_hz": round(float(freq[peak]), 2),
            "peak_db_per_hz": round(float(10 * np.log10(power[peak])), 2),
            "local_median_db_per_hz": round(float(10 * np.log10(baseline)), 2),
            "peak_above_local_median_db": round(float(10 * np.log10(power[peak] / baseline)), 2),
        }
        window_scores = []
        for start in range(0, len(mono) - 20 * sr + 1, 20 * sr):
            wf, wp = welch(mono[start:start + 20 * sr], sr, window="hann", nperseg=NFFT, noverlap=NFFT // 2)
            near_peak = (wf >= freq[peak] - 2) & (wf <= freq[peak] + 2)
            nearby = (wf >= low - margin) & (wf <= high + margin) & (np.abs(wf - freq[peak]) > 3)
            score = 10 * np.log10(float(np.max(wp[near_peak])) / float(np.median(wp[nearby])))
            window_scores.append(round(float(score), 1))
        measurements[label]["twenty_second_window_prominence_db"] = window_scores
    return {
        "source": relpath, "sha256": digest, "sample_rate": sr,
        "channels": audio.shape[1], "samples": len(audio),
        "duration_seconds": round(len(audio) / sr, 3),
        "measurement": measurements,
    }


def calculate():
    return {
        "schema": "liberpedia-instar-narrowband-v1",
        "method": "Stereo channels averaged; full-track Welch PSD, Hann, 65,536 samples per segment, 50% overlap; peak within 50-70 Hz and 14-17 kHz; compare to local median excluding ±3 Hz around selected peak.",
        "tracks": {name: one_file(name, *entry) for name, entry in FILES.items()},
    }


def figure(result):
    bars = []
    labels = (("instar", "The Instar Emergence", "#275a72"), ("interconnectedness", "Interconnectedness", "#687985"))
    for row, (key, label, color) in enumerate(labels):
        item = result["tracks"][key]["measurement"]["horizontal_scan_region"]
        y = 110 + row * 76
        width = round(item["peak_above_local_median_db"] * 8)
        bars.append(f'<text x="20" y="{y-12}" font-size="15">{label} · {item["peak_hz"]:,.2f} Hz</text>')
        bars.append(f'<rect x="20" y="{y}" width="{width}" height="22" fill="{color}"/>')
        bars.append(f'<text x="{29+width}" y="{y+17}" font-size="14" font-weight="700">+{item["peak_above_local_median_db"]:.1f} dB</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 250" role="img" '
            'aria-label="The Instar Emergence has a persistent 15.65 kilohertz line 39.7 decibels above nearby frequencies; Interconnectedness has an 8.9 decibel peak in the same broad band.">'
            '<rect width="520" height="250" fill="#f5f7f8"/>'
            '<g fill="#21313b" font-family="Arial, sans-serif"><text x="20" y="34" font-size="19" font-weight="700">High-frequency line</text>'
            '<text x="20" y="57" font-size="13">Peak above nearby frequencies, 14–17 kHz</text>'
            + ''.join(bars) + '<text x="20" y="235" font-size="12">Same measurement on pinned 2013 and 2014 tracks; not a watermark test.</text></g></svg>\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    if args.check:
        expected = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        if result != expected:
            raise AssertionError("Measured spectrum differs from archived result")
        if figure(result) != (HERE / "lines.svg").read_text(encoding="utf-8"):
            raise AssertionError("Figure differs from measured result")
        print("PASS: pinned audio identities and two full-track narrowband measurements")
    else:
        (HERE / "lines.svg").write_text(figure(result), encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
