# Does the pair-skip decoder preserve a known correct key?

The [Round 19 source test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/I1) creates readable rune text, encrypts it with a known key, and sometimes discards a key draw to avoid repeating the last ciphertext rune. It then gives the correct key to six decoders. A decoder that expects skipped draws in **pairs** is intentionally mismatched to this one-draw construction.

## Finding

![With the correct key, the matching decoder recovers all runes at 240 and 400 positions; the pair-skip decoder recovers 37.9 and 41.2 percent.](experiments/records/round19-decoder-baseline-control/decoder-baseline.svg)

At the source's 0.83 suppression setting, the matching decoder recovers **100%** of the planted runes at both 240 and 400 positions. The pair-skip decoder recovers **37.9%** and **41.2%**, respectively. At 240 positions its median language score falls from **−4.303** to **−6.631**, below the source's −5.5 reading bar. The correct key is present throughout: changing the permitted alignment rule alone causes the failure.

We replayed the source's entire **336-decoding G-BASE grid**: four suppression settings, two lengths, six decoder modes and seven seeds. Every non-timing row matches the pinned output; an independent recount matches all 48 cell summaries. A separate [36-case decoder-equivalence receipt](research/control-preflights/i1-2026-10-23.json) finds the same plaintext paths as the two earlier implementations, with scores agreeing within 1.1 × 10⁻¹⁴. Those 36 cases are an instrument control and are not included in the 336.

## What this establishes

A negative search using one skip rule does not exclude a different skip rule. The pair decoder fails **this particular one-draw plant**, not every pair-skip cipher. These are synthetic known-key controls, with English-derived text and a source-selected language threshold. **No LP2 ciphertext or unknown key is tested here.** A high language score can also coexist with poor exact rune recovery, so both measurements matter.

## Reproduce

The [plan](experiments/records/round19-decoder-baseline-control/plan.json) pins the source revision, inputs and original 336-case grid. It was written after the source outcome was known, so it is a retrospective replay specification. A later packaging amendment bundled the exact source code with its MIT license, plus the pinned text and score model, without changing the grid; the [original plan](experiments/records/round19-decoder-baseline-control/original-plan-before-bundle.json) is retained. From the extracted experiment ZIP, run:

```text
python experiments/records/round19-decoder-baseline-control/run.py --nproc 6
python experiments/records/round19-decoder-baseline-control/run.py --check
python experiments/records/round19-decoder-baseline-control/plot.py --check
```

The full run stages the bundled source in a temporary folder and compares each result with the [archived source output](experiments/records/round19-decoder-baseline-control/source/liber-primus/analysis/round19/I1/out_base.json). `--check` independently recounts the saved 336 rows and 48 summaries without running the decoder or changing files. Only wall times are excluded from parity. This is a decoder-power control, not an LP2 solve result.
