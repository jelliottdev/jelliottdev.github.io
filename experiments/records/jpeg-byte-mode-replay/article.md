# JPEG byte histograms: the four-page split

**Finding:** The reported LP2 split is present in the archived JPEGs. Of 58 files, **54 have `00` as their most frequent byte**. The four exceptions—LP2-00, 04, 24 and 26—have `44` as their mode. Both groups contain one-component and three-component JPEGs, so component count does not explain the split. Nothing in this measurement extracts a hidden message or shows that any file is random.

![LP2 modal bytes crossed with JPEG component counts, with a shorter LP1 comparison.](experiments/records/jpeg-byte-mode-replay/modes.svg)

The test counts the **stored file bytes**, including headers and compressed data. It does not count visible pixel values or the individual digits in a hexadecimal display. The source called the common group “null” and the exceptions “random”; here those terms are replaced with the exact byte modes. Even on the page with the most zeros, `00` is only 20.1% of the file, not a majority. Byte `44` is hexadecimal for decimal 68 (ASCII `D`), consistent with the source’s display label.

| LP2 most frequent byte | One-component JPEG | Three-component JPEG |
| --- | ---: | ---: |
| `00` | 22 | 32 |
| `44` | 1 | 3 |

The same fixed rule gives 15 `00`-mode files and two `28`-mode files in the 17 archived LP1 images. Those exceptions are LP1-00 and LP1-02, corresponding to the source’s one-based “Page 1” and “Page 3.” This extends its sixteen-page list to the full local archive; it does not recreate the missing historical histogram screenshots. In all 75 archived files, at least 92.6% of the zero bytes occur **after the first scan header**. This locates the bytes within the stored JPEG stream but does not isolate every later marker or explain how its encoder produced them.

The [fixed re-encoding control](#/experiments/jpeg-modal-reencode-control) tests whether the byte class survives different JPEG settings. The four page numbers alone do not specify a date, a cipher or a payload. For a fuller explanation of the byte-versus-pixel distinction, see the [JPEG distribution guide](#/wiki/jpeg-byte-distribution).

## Reproduce

Download the [original images](#/downloads) alongside this experiment, then run `python experiments/records/jpeg-byte-mode-replay/run.py --check` from the repository root. The script checks all 75 image hashes and re-counts their byte modes and JPEG frame components using Python's standard library. [The plan](experiments/records/jpeg-byte-mode-replay/plan.json) fixes the rule; [the results](experiments/records/jpeg-byte-mode-replay/results.json) list every page's checksum, byte length, mode, zero count and component count. The historical [source file repository](https://github.com/rtkd/iddqd/tree/master/liber-primus__images--unsolved) is not pinned to its October 2023 revision, so equality with that exact historical input remains unverified.
