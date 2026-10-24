# Numeric skip controls: source gates and recovery are different outcomes

No manuscript target was decoded in this intake. The frozen plan, exact key arrays and source hashes precede the synthetic run. The 54 source-labelled streams are one method family, not 54 solving ideas.

## Executed controls

The unchanged source `encipher_keyskip` and `sweep.beam` ran 1,080 cells: all 54 labels, both signs, both Atbash states and offsets 0–4. The two complete known readings have 184 and 85 runes; their assignment was fixed before execution. Atbash cells test the inverse preprocessing branch and duplicate the underlying decoded problem, so these are not 1,080 independent trials.

All cases use the first eligible seed from the frozen range 3301–3332 whose planted path has no more than three skipped keys at any step. Of 1,080 cells, 1,034 used the first seed, 24 used the third, 20 the tenth and two the fourth. No case was omitted. There are 1,036 plants with genuine skips and 44 without skips. The seed conditioning establishes representable-path controls; it does not characterize an unrestricted stochastic encryptor.

| Source branch | Cells | Exact entire reading | Exact first 50 runes | Passed source short gate | Passed short and full gates | Wrong key passed both |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Numeric without Fibonacci | 660 | 634 | 610 | 660 | 660 | 0 |
| Numeric2 Part A | 420 | 402 | 394 | 420 | 420 | 0 |

The 44 complete-reading mismatches are **all strictly higher cumulative-score alternatives**, with no ties and no lower-score returned alternatives. Every true path is valid under the source suppressed-doublet constraint and the maximum-three-skip rule; all 44 mismatch cases have genuine skips. Atbash duplicates remain in the receipt: 44 cells represent 22 underlying sign/key/offset/reading cases. `failure-diagnosis.json` lists every case, changed rune positions, cumulative scores and normalized scores. This demonstrates that passing both English gates does not establish exact plaintext recovery. It does not establish that any particular manuscript target must fail or succeed.

An independent ordinary Python encoder in `summarize.py` reconstructed all 1,080 planted ciphertexts and their skip lists. The stored ciphertext hash covers the original NumPy int64 byte representation; reconstruction explicitly packs little-endian signed 64-bit values. `diagnose.py` independently checks each suppressed-key validity constraint and reruns every mismatched source decode. No accelerated decoder is proposed, and no source/native parity claim is needed.

## Exact proposed target scope

Retain both complete source grids, with one grouped report, if the next target run is authorized:

- Numeric: 33 streams, **1,176 key values**, 36,300 screens. This is the source's explicit no-Fibonacci branch, not its full 874-stream campaign.
- Numeric2: **Part A only**, 21 streams, **1,172 key values**, 23,100 screens. Parts B/C are excluded. `partition_rev` reverses this exact 1,172-value sequence; regenerating at another length changes that key.
- Both: 55 source text segments; signs −1/+1; Atbash off/on; offsets 0–4; first 50 runes at beam 60; full confirmation only when the short score is strictly greater than −6.5. Full widths are 200 and 300 respectively; confirmation bar is strictly greater than −5.5. Maximum skipped keys remains three, including all source path ordering, pruning and validity behavior.
- Score coverage and full-decoding coverage must be reported separately. Failed short screens do not receive complete-page decoding. Preserve every labelled setting and explicitly mark phase duplicates, rather than inflating independent scope.

The fixed arrays already freeze source quirks: the numeric e construction uses a finite 299-term approximation and diverges from high-precision e at digit 612 (counting the integer digit). Its digits/pairs remain historical source-generated streams, not a claim of exact e throughout. The BBS-labelled streams retain the historical constructor even for seeds 503 and 311, which are not coprime to its modulus. Numeric2's magic-square row-sum stream is constant 24 modulo 29, so all five phases alias; repeated 3301 digits have period four, so phases zero/four alias. All 54 base arrays have distinct first-50 prefixes. Five artifact constructions overlap values in the existing fixed-numeric record; the changed decoder and phase grid are the additional scope.

Only direct numeric branch functions and `sweep.beam` are needed. Never call `prefilter`, `attack_page` or numeric2 main. Optional missing `campaign12/walden.txt` affects only unused bigram/monogram setup, not this decoder or either numeric grid; no substitute is permitted. `source_hashes` pins the existing solved/self-reliance files imported for that unused setup. The source MIT license and attribution must accompany any bundled code and inputs.

## Measured cost

The complete control run, including wrong-key full decodes, took **38.345 seconds**. Numeric mean source screen/full costs were **0.730 ms / 21.244 ms**; Numeric2 costs were **0.694 ms / 24.083 ms**. Mean screen projections are **26.49 s + 16.04 s** for the two proposed target grids. Applying the slowest observed screen to every setting gives **141.82 s + 95.33 s**. At a hypothetical 1% survivor rate, mean confirmation costs add **7.71 s + 5.56 s**. These are synthetic timing projections, not measured manuscript runtime or validated upper bounds; manuscript survivor counts and branching remain unknown. A deliberately pessimistic all-settings-confirm, longest-page scaled estimate exceeds two hours, so stream-level progress and a recorded time budget are appropriate. No optimization may replace variable streams with constant-seed equivalence.

Recommend executing the unchanged two-stage grids, retaining all screen scores and each survivor's full result, with the above power limits stated. This is a finite English-score replay, not a blanket exclusion of the numeric methods. Additional controls or a control-only publication would not complete the manuscript search.

## Reproduce controls

With the exact public source checkout at the frozen relative path:

```text
python research/source-intake/numeric-skip-controls-2026-10-24/probe.py probe
python research/source-intake/numeric-skip-controls-2026-10-24/summarize.py
python research/source-intake/numeric-skip-controls-2026-10-24/diagnose.py
```

The first command regenerates control results, including new timing fields; it is not a byte-stable `--check` CLI. Preserve the frozen receipt when reproducing. No build, shared data file, target record or publication was changed here.
