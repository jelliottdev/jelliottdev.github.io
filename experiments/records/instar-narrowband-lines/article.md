# Instar's high-frequency line and low hum

The archived *Instar Emergence* has a narrow line at **15,645.89 Hz**. It rises **39.72 dB above the nearby median** in a fixed full-track spectrum and remains prominent in all eight nonoverlapping 20-second windows. A separate low-frequency peak appears at **59.22 Hz**, 14.89 dB above its nearby median. These measurements make the reported spectral features inspectable; they do not identify a recording device, geographic location, encoded message, or watermark.

![Two pinned Cicada tracks compared in the 14–17 kHz band](experiments/records/instar-narrowband-lines/lines.svg)

## What was tested

A discussion of the music described an approximately 15 kHz “CRT hum” and 60 Hz hum in *Instar*. We checked the exact archived `761.mp3` and used the separately preserved *Interconnectedness* recording as a comparison. Both files are pinned by SHA-256 in the downloaded record. The *Interconnectedness* carrier already has a documented OpenPuff branch, so it is a comparison of frequency spectra, **not** a clean “no-hidden-content” control.

We averaged the stereo channels, measured a Hann-windowed Welch spectrum over the complete 44.1 kHz track, and selected the largest bin in two bands fixed from the report: 50–70 Hz and 14–17 kHz. The FFT segment length is 65,536 samples with 50% overlap. Each peak is compared with the median of a local band, excluding 3 Hz around that peak. The same peak frequencies were checked in consecutive 20-second windows.

| Track | Peak in 14–17 kHz | Above nearby spectrum | 20-second windows above 10 dB |
| --- | ---: | ---: | ---: |
| The Instar Emergence | 15,645.89 Hz | +39.72 dB | 8 of 8 |
| Interconnectedness | 14,497.23 Hz | +8.93 dB | 3 of 13 |

The low band also has prominent peaks in both tracks, though at different frequencies: Instar at 59.22 Hz and Interconnectedness at 69.98 Hz under this rule. “Near 60 Hz” is a useful description of the first measured peak. It is **not** proof of North American mains pickup: instruments, processing and MP3 artifacts are not excluded by a spectral peak alone.

## What this leaves open

The source did not specify a watermark algorithm, payload or detector. A narrow spectral line is a property of the sound file, not an extraction of hidden data. The proposed ~500 Hz time-localized gaps were not tested here; they need a fixed event interval and a defined gap statistic. A later watermark test should pin a detector and decision threshold, then measure false positives on matched audio.

## Reproduce

Download this experiment ZIP and the reference-data bundle, extract both into one folder and run:

```sh
python -m pip install numpy scipy soundfile
python experiments/records/instar-narrowband-lines/run.py --check
python experiments/records/instar-narrowband-lines/check.py
```

The first script checks the two MP3 hashes, recomputes the Welch measurements and checks the figure. The independent check uses a single FFT per 20-second window, without Welch, and confirms both Instar peaks persist. The saved [results](experiments/records/instar-narrowband-lines/results.json) include every window score. Decoding may vary in last-place floating-point digits across library versions; the archived output was produced with the versions stated in the record.
