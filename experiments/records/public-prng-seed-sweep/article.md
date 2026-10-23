# Seven public PRNG constructions against LP2

Could a seeded software random-number generator supply LP2's 29-symbol key stream? This reruns a [published seven-generator screen](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/prng/RESULTS.md) against the first 120 runes of the unsolved text.

## Finding

**No candidate in the executed grid reached the source's required English score.** The replay screened **52,556 decodes**: seven generator implementations, 1,877 fixed seeds, two addition signs and two key directions. The best candidate scored **−6.347**; a candidate needed at least **−5.500** to advance. A planted English message encoded with the source's PHP-style generator scored **−4.155** and was recovered exactly. The same program can therefore find one of its own planted signals under this setup.

These are English quadgram scores: they measure how much a four-letter pattern resembles the training text. **Higher is better**, but even a high score would still require a readable continuation and independent checks before it could count as a solution.

![Three scores on the same scale: planted control clears the bar; the manuscript's best candidate does not.](experiments/records/public-prng-seed-sweep/score.svg)

The winning seed, generator, sign and direction match the archived run. This is evidence about the **specific seeded generators and seed slice below**, not evidence that LP2 uses no PRNG or no stream cipher.

## What was tested

The seven source implementations are PHP-5-style `mt_rand`, .NET-4-style `System.Random`, a simplified single-integer-seeded ISAAC, Blum–Blum–Shub at two fixed moduli, a 32-bit LFSR and a Geffe combination of three LFSRs. Every stream is reduced modulo 29. The key-skip beam searches up to three rejected key symbols at each rune, using the source's English quadgram scorer. Its first-stage ciphertext is exactly the source's 120-rune LP2 prefix, regenerated from the pinned runic transcription.

The 1,877 seeds are **1,828 daily-spaced Unix seconds from 2011–2015 plus 49 fixed number/string-derived seeds**. The source's earlier plan described hourly sampling and an additional rejection reduction; the actual executable and result cover daily sampling and `mod29` only. That difference matters. The test also fixes key offset at zero and does not check other starting positions.

The source calls all seven generators “validated,” but most reference vectors in this script are computed by the same implementation being tested. Self-consistency and a planted decode show that the local program works consistently; they do **not** independently verify exact PHP, .NET or standard ISAAC runtime compatibility. The ISAAC variant expressly uses a simplified seed procedure. We therefore name them as the **source implementations**, not all production runtimes bearing those names.

## Reproduce

Download this experiment's ZIP and run from its extracted folder:

```sh
python experiments/records/public-prng-seed-sweep/run.py
```

The command executes the archived test program, then independently checks the reconstructed ciphertext, case count, control, winning configuration and score against the separately archived original result. It takes several minutes. For a quick integrity check of saved results, run `python experiments/records/public-prng-seed-sweep/check.py`.

The packaged source files are pinned to [Dukotah/cicada3301 revision f08b20b](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/prng). The original generator code, documented plan and result are retained with this record. The only regenerated source input is `ct.bin`, constructed byte-for-byte from that revision's `krisyotam_runes.txt`; the checker confirms its 12,956 rune indices and SHA-256.
