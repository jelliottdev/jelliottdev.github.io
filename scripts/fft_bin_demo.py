"""Synthetic FFT demonstration. No Cicada recording is loaded or analyzed.

Requires NumPy; --plot also requires Matplotlib. Prints measured grid maxima.
"""
import argparse
import json
from pathlib import Path
import numpy as np

RATE = 44100
TONE = 1042.85
CASES = [(1024, 1024), (1024, 16384), (16384, 16384)]


def spectra():
    for samples, nfft in CASES:
        time = np.arange(samples) / RATE
        signal = np.sin(2 * np.pi * TONE * time)
        amplitude = np.abs(np.fft.rfft(signal * np.hanning(samples), n=nfft))
        frequencies = np.fft.rfftfreq(nfft, d=1 / RATE)
        peak = int(np.argmax(amplitude))
        yield dict(samples=samples, fft_length=nfft,
                   duration_seconds=samples / RATE, bin_spacing_hz=RATE / nfft,
                   peak_bin=peak, peak_bin_hz=float(frequencies[peak])), frequencies, amplitude


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plot', action='store_true', help='Write the guide SVG')
    args = parser.parse_args()
    cases = list(spectra())
    # Separate exact bin arithmetic checks the frequency-array convention.
    for row, frequencies, amplitude in cases:
        assert row['peak_bin_hz'] == row['peak_bin'] * RATE / row['fft_length']
        assert row['peak_bin'] == int(np.argmax(amplitude))
    assert cases[0][0]['peak_bin'] == 24
    assert cases[0][0]['peak_bin_hz'] == 1033.59375
    assert all(case[0]['peak_bin'] == 387 for case in cases[1:])
    print(json.dumps({'scope': 'Synthetic sine only; not a historical audio result',
                      'sample_rate_hz': RATE, 'tone_hz': TONE,
                      'window': 'numpy.hanning(samples), symmetric Hann',
                      'numpy_version': np.__version__,
                      'cases': [row for row, _, _ in cases]}, indent=2))
    if args.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'svg.hashsalt': 'liberpedia-fft-demo', 'font.size': 11})
        fig, axes = plt.subplots(3, 1, figsize=(5, 7), sharex=True, layout='constrained')
        names = ['1,024 samples Â· 1,024-point FFT',
                 'Same samples Â· padded to 16,384',
                 '16,384 actual samples Â· no padding']
        for ax, (row, frequency, amplitude), title in zip(axes, cases, names):
            ax.plot(frequency, amplitude/amplitude.max(), '.-', color='#315b70',
                    markersize=3, linewidth=1)
            ax.axvline(TONE, color='#9c4c2f', linestyle='--', linewidth=1)
            ax.set(xlim=(850, 1200), ylim=(0, 1.12), title=title)
            ax.set_yticks([0, 0.5, 1])
            ax.grid(alpha=0.2)
        axes[-1].set_xlabel('Frequency (Hz)')
        fig.supylabel('Magnitude / maximum in each panel')
        fig.suptitle('Synthetic 1042.85 Hz sine\nDashed line: generated tone', fontsize=13)
        path = Path(__file__).resolve().parents[1] / 'exports/figures/fft-bins.svg'
        fig.savefig(path, metadata={'Date': None})
        path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
        plt.close(fig)


if __name__ == '__main__':
    main()
