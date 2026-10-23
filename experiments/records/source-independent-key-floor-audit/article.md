## Finding

The published D2 audit asks whether the unusual rune statistics were caused by counting the wrong text or joining pages incorrectly. Its source script runs from the pinned files here, and its planted-English scoring control passes. An independent Unicode-rune count confirms **12,956 runes** and **86 equal adjacent pairs among 12,901 within-page pairs**. None of the 54 extra pairs made by joining pages is equal. Its index of coincidence (multiplied by 29) is **0.9999** and entropy is **4.8565 bits**.

That supports the *measurements*. It does not reproduce the report's stronger statement that the low doublet rate excludes **every plaintext-independent key**. D2's `recompute.py` never calculates the cited plaintext-difference floor. The separate B4 script requires four English corpus files absent from the pinned repository, so its corpus numbers cannot be regenerated from this source package. We retain those numbers as reported results, not measurements made in this replay.

## What the bound actually says

Let `Δp` be a plaintext difference and `Δk` a key difference modulo 29. If their distributions are independent under the specified sampling model, then the **expected** ciphertext repeat rate is

```text
P(Δp + Δk = 0) = Σ P(Δp = d) P(Δk = −d) ≥ min P(Δp = d).
```

The inequality is correct under that factorization. It is not a minimum imposed on *each finite ciphertext*. A small complete example makes the distinction visible. In an alphabet of three symbols, take plaintext `0, 0, 1, 0`: its three successive differences are `0, 1, 2`, so the minimum difference frequency is **1/3**. Enumerate all **81** four-symbol keys drawn independently and uniformly, without looking at that plaintext. The expected ciphertext repeat rate is **1/3**, yet **24 keys (8/27)** yield **zero** repeats. No plaintext-aware choice was needed for those outcomes to be possible.

![The count of adjacent repeats across all 81 keys in the finite example.](experiments/records/source-independent-key-floor-audit/finite-key-control.svg)

This logical distinction does **not** make an independent uniform additive key a good explanation for LP2. The separate [exact uniform-key test](#/experiments/uniform-additive-doublets) assigns 86 or fewer repeats among 12,901 positions a probability near **1.07 × 10⁻⁹⁸** under its precisely defined model. The source's corpus floors may also help specify useful language models. What they cannot do without a declared stochastic model and error threshold is turn one observed manuscript rate into an impossibility proof for every independent key generator or every possible plaintext.

## Source coverage and limits

The [B4 preregistration](experiments/records/source-independent-key-floor-audit/source/liber-primus/analysis/round10b/B4-otp-steelman/PREREG.md) required **at least five independent English encodings of at least 100,000 runes each**. Its [G3 implementation](experiments/records/source-independent-key-floor-audit/source/liber-primus/analysis/round10b/B4-otp-steelman/b4_identifiability.py) names **four** large external corpora, plus a 180-rune solved-page sample explicitly excluded from the large-corpus minimum. None of the four corpus text files is present in the pinned Git tree; `git ls-tree -r --name-only f08b20b -- liber-primus/data/kjv.txt liber-primus/data/moby.txt liber-primus/data/pride.txt liber-primus/data/war.txt` returns no paths. The earlier [saved B4 output](experiments/records/source-independent-key-floor-audit/source/liber-primus/analysis/round10b/B4-otp-steelman/b4_results.json) reports a KJV minimum of **1.5025%**. A [later source audit](experiments/records/source-independent-key-floor-audit/source/liber-primus/analysis/round18/L7-redteam/RESULTS.md) calls that figure stale and reports **1.386%** using a longer KJV sample. This replay verifies the provenance and revision, but neither source corpus is available here to recalculate the revised value.

D2 also labels the `p* ≈ 400` period-detection threshold reproduced in its saved report. The D2 script prints column IoC for selected periods; it does not rerun the separate detection-power simulation behind that threshold. This record therefore does not validate that claim. The page inventory is based on the pinned rune text, not a new inspection of each manuscript image.

## Reproduce

The [pinned source inventory](experiments/records/source-independent-key-floor-audit/source-manifest.json), [D2 output](experiments/records/source-independent-key-floor-audit/source-replay.txt), [result data](experiments/records/source-independent-key-floor-audit/results.json), and [finite control](experiments/records/source-independent-key-floor-audit/finite-key-control.svg) are included. Python 3 and the standard library suffice:

```text
python experiments/records/source-independent-key-floor-audit/run.py --check
python experiments/records/source-independent-key-floor-audit/check.py
python experiments/records/source-independent-key-floor-audit/plot.py --check
```

The first command reruns the source D2 code and makes its printed positive control a hard gate. The second extracts rune characters with an independent parser, verifies source hashes and counts, and checks the finite-key example by enumerating ciphertexts directly. Neither command fills in the absent four corpora.
