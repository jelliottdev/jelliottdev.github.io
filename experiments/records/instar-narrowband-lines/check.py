"""Independent single-FFT check of the persistent Instar peaks (no Welch)."""
import hashlib
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
PATHS = {
    "instar": ("exports/sources/cicada-2013-twitter/761.mp3", "83008217439110c3b824898af73b99cb2cf0657dda88cb363c3aa34a4ec0a460"),
    "interconnectedness": ("exports/audio/interconnectedness.mp3", "1ce3839b4a62462d9009c4469acc189b523e1bdcf338cb49cda1cd7bb4efffc6"),
}
N = 131072


def window_peaks(relpath, expected_hash):
    path = ROOT / relpath
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
    data, sample_rate = sf.read(path, dtype="float32", always_2d=True)
    assert sample_rate == 44100 and data.shape[1] == 2
    mono = data.mean(axis=1)
    taper = np.hanning(N)
    hz = np.fft.rfftfreq(N, 1 / sample_rate)
    result = []
    for start in range(0, len(mono) - 20 * sample_rate + 1, 20 * sample_rate):
        excerpt = mono[start + 5 * sample_rate:start + 5 * sample_rate + N]
        power = abs(np.fft.rfft(excerpt * taper)) ** 2
        peaks = []
        for low, high in ((50, 70), (14000, 17000)):
            band = np.flatnonzero((hz >= low) & (hz <= high))
            peaks.append(float(hz[band[np.argmax(power[band])]]))
        result.append(peaks)
    return result


def main():
    instar = window_peaks(*PATHS["instar"])
    other = window_peaks(*PATHS["interconnectedness"])
    assert len(instar) == 8 and len(other) == 13
    assert all(abs(low - 59) < 1 and abs(high - 15646) < 1 for low, high in instar)
    assert sum(abs(high - 15646) < 1 for _, high in other) == 0
    print("PASS: independent FFT finds both Instar lines in all eight 20-second windows; 15.646 kHz is not the comparison track's strongest high-band line")


if __name__ == "__main__":
    main()
