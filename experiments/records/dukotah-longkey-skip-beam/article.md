# A long running key with skipped positions

A pinned Campaign VII program tried three candidate books or prose texts as long keys. At every manuscript rune, its decoder searched paths that advance **one or two key positions**, keeping the 120 paths it scored highest. The source tested 54 page/key/offset combinations; none reached its −5 English-score bar. We reproduce its best score, **−6.086 on LP2-17**, and all 54 complete outputs.

The decisive qualification is the decoder's **known-message test**. We encrypted documented text with the same key texts and a rule that skips a key position only when the ordinary draw would repeat the previous ciphertext rune. All **18** planted skip cases passed the source's English-score bar, yet **zero recovered the complete original text**. The score can therefore say “English-like” about a *different* path. The archived no-hit result is a bounded search result, not an exclusion of this cipher mechanism.

![A comparison shows all 18 planted collision-skip cases pass the score bar but none recover exact plaintext; all 54 manuscript searches stay below the bar.](experiments/records/dukotah-longkey-skip-beam/comparison.svg)

| Input to the same decoder | Above source score bar | Complete exact reading |
| --- | ---: | ---: |
| Known text, ordinary key advance | 18/18 | 11/18 |
| Known text, collision-triggered skips | 18/18 | **0/18** |
| Unsolved LP2 pages | 0/54 | Unknown |

The first collision-skip control in the fixed test order uses the Tao Te Ching key at offset zero, the 85-rune known reading, and two planted skips. It returns a *higher* English score than the known text (−4.335 versus −4.462), but its **19th rune** is `TH` where the known text has `B`:

```text
Known     ...INTHEDEEPWE|BTHEREEXISTSAP...
Returned  ...INTHEDEEPWE|THTHEREEXISTSAP...
```

These are continuous rune transliterations, with no added word spaces. The vertical bar marks the first differing rune boundary; the dots mark omitted runes. Both readings clear the source's −5 bar, so that bar alone cannot tell the correct path from the wrong one.

The controls use the 85-rune documented `AN END` reading and a deterministic 273-rune repetition of it, at each of the three source offsets for each of the three keys. The longer sample is close to the tested page lengths of 273–277 runes. Repetition makes it a detector check, not a second independent natural passage. Several planted paths without a collision-triggered skip also lose the correct text because the beam is allowed to choose a higher-scoring path.

## What the source actually searches

The fixed key texts are a Tao Te Ching file, a Gospel of Thomas file, and Cicada PGP prose from the pinned repository. The source selects the six longest rune-bearing unsolved segments: LP2-29, 43, 47, 11, 17 and 21. Each key is tried at its beginning, one-quarter point and halfway point. That is **3 texts × 6 pages × 3 offsets = 54 searches**. The source's saved top result and our complete output ledger agree.

The source description calls this a *doublet-avoiding* running-key search. Its executable beam, however, permits either advance at **every** rune; it does **not** check whether the extra advance would prevent a doublet. We replay the executable rule exactly and use collision-triggered encryption only for the planted control. That distinction is why this result cannot be generalized to a decoder that enforces the collision condition.

The English score ranks transliterated rune output by a pinned four-letter frequency model. It is a useful search heuristic, but choosing the best of many beam paths can give a convincing score to an incorrect reconstruction. The planted control measures that failure directly. Other keys, starting points, pages, beam widths, and a collision-constrained decoder are outside the test.

## Reproduce

The [frozen plan](experiments/records/dukotah-longkey-skip-beam/plan.json) pins all three key files, the source grid and control construction. [Results](experiments/records/dukotah-longkey-skip-beam/results.json) include every manuscript score and all 36 planted cases. Run from a Liberpedia checkout:

```text
python experiments/records/dukotah-longkey-skip-beam/run.py --check
python experiments/records/dukotah-longkey-skip-beam/check.py
python experiments/records/dukotah-longkey-skip-beam/plot.py --check
```

The runner executes the [unmodified source program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/c1_skipkey.py) in a temporary copy and matches its saved result. The independent checker reconstructs the beam, all 54 outputs, all 36 plants and the source-to-site rune mapping. The source program and exact key files are bundled with their hashes. Its archived report predates our planted controls; the control findings are new to this replay.
