## Finding

**No 54-byte window passed the specified strict RSA-structure checks.** The source proposed that the 256-byte payload spread over LP2 pages 49–51 might contain a 432-bit RSA signature or encrypted block inside it, rather than as the whole payload. A 432-bit block is 54 bytes, so there are exactly **203 contiguous positions** to inspect.

![A sliding 54-byte window across each 256-byte payload reading, with the fixed directions and exponents.](experiments/records/rsa-window-54-source-replay/windows.svg)

We independently ran the pinned test on **three source payload readings**. For each window, it checks both byte orders as an encoded block and, when the numeric value is below the published 2013 modulus, raises it to exponents **65,537, 3 and 17**. That made **1,218 direct-block inspections** and **2,493 modular exponentiations** across the three readings. All three returned **zero strict PKCS#1 v1.5 or PSS structural matches**, exactly as the source reported.

There is one weaker PSS-shaped row per reading: window **62**, forward byte order, exponent **17**. It lacks the required eight zero-padding bytes, so the predeclared recognizer labels it *loose*, not a hit. The three payload readings differ at a few bytes, but none of those differences lies inside this particular window.

## What makes the negative meaningful

The runner first planted **ten PKCS#1 v1.5–SHA-1 and five PSS–SHA-1 signatures** under a fresh 432-bit test key. It recovered all **15** at their planted windows. It then found **zero strict matches** in 200 random 256-byte buffers. Our separate checker verifies the pinned input bytes against their Git blob identities, recalculates every real-data window and match tier without importing the runner, and compares the totals to the source's saved result.

This is a bounded structural screen, **not** verification of a signature over a known message. In particular, the source's recognizer checks a known DigestInfo prefix or PSS block shape; it cannot check a message digest when no signed message is specified. The result applies to these three 256-byte readings, the published **2013 432-bit modulus**, 54-byte contiguous windows, both byte orders and those three exponents. It says nothing about other moduli, noncontiguous or bit-shifted selections, different block sizes or non-PKCS constructions.

## Reproduce

Run from the Liberpedia repository root with Python 3:

```text
python experiments/records/rsa-window-54-source-replay/run.py
python experiments/records/rsa-window-54-source-replay/check.py
```

The [machine-readable result](experiments/records/rsa-window-54-source-replay/results.json), [pinned source file list](experiments/records/rsa-window-54-source-replay/source-manifest.json) and original MIT-licensed inputs are included. The local `source/results.json` is the published source result; the top-level `results.json` is our independent replay.
