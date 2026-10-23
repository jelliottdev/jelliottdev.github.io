# JPEG byte classes after re-encoding

**Finding:** The four LP2 files singled out in the 2023 byte-histogram report have a nonzero most-frequent byte in our archived originals. That four-page grouping **does not survive a fixed JPEG re-encode**. The same decoded page images yield 23 nonzero-mode files at quality 75, 23 at quality 85, and five at quality 95. A file-byte mode is therefore sensitive to JPEG encoding choices; the grouping alone cannot identify a manuscript layer or hidden message.

![Bar chart comparing the number of nonzero-modal-byte LP2 files in originals and three fixed re-encodes.](experiments/records/jpeg-modal-reencode-control/mode-control.svg)

| File set | Nonzero-mode pages | Original four still nonzero-mode |
| --- | ---: | ---: |
| Archived originals | 4 of 58 | 4 of 4 |
| Re-encode at quality 75 | 23 of 58 | 1 of 4 |
| Re-encode at quality 85 | 23 of 58 | 1 of 4 |
| Re-encode at quality 95 | 5 of 58 | 0 of 4 |

The original four are **LP2-00, 04, 24 and 26**. At qualities 75 and 85, only LP2-24 retains a nonzero mode. At quality 95, none does. Re-encoding introduces many different nonzero-mode pages at 75 and 85; it does not simply turn every page into a `00`-mode file.

## What was compared

For each of the 58 archived LP2 JPEGs, the script counts all 256 possible *complete-file byte values* and records the unique most frequent one. It then decodes that original and saves it in memory as a new JPEG at each of three specified quality settings, with chroma subsampling disabled and no resizing. The re-encoded files are **derivatives**, never replacements for the original manuscript images. The [existing byte audit](#/wiki/jpeg-byte-distribution) gives the full original histograms and frame-header checks; this test asks whether their four-page class is stable under a change of JPEG representation.

This is a bounded sensitivity control, **not a randomness test**. The quality settings are illustrative and were not sampled from a model of how Cicada made the original files. Re-encoding can change compressed bytes and decoded pixels, so this result neither explains the original file-production process nor rules out steganography. A proposed extraction must specify its target bytes, algorithm and expected output separately.

## Reproduce

Run `python experiments/records/jpeg-modal-reencode-control/run.py --check` from the repository root with **Pillow 11.3.0**. The [saved report](experiments/records/jpeg-modal-reencode-control/results.json) lists the SHA-256, byte length and mode of every original and all 174 temporary re-encodes. The [plan](experiments/records/jpeg-modal-reencode-control/plan.json) fixes the measurement and settings. The source claim and its 58-page table are summarized in [Reported attempts](#/wiki/reported-attempts?section=jpeg-hex-distribution); the historically linked [image archive](https://github.com/rtkd/iddqd/tree/master/liber-primus__images--unsolved) identifies its earlier image collection, whose 2023 revision has not been pinned.
