## Finding

The published semantic-seed sweep tried **4,274 combinations** of candidate seeds, generators and decoders. Its saved screening scores can be reproduced. But **none of those candidates could reach the stated full hit test**, even if one decrypted the page perfectly.

![The source sweep, a perfectly recovered planted key, and the unreachable promotion rule.](experiments/records/semantic-seed-screen-gate-audit/gate.svg)

The code promotes a candidate only if its *screen score is at least +5*. That score is an average of log-probabilities; it cannot exceed **0**. The best actual score was **−6.58**. More decisively, a planted key recovered **all 120 test runes** and scored **−4.35**. The screen discarded it too. The separate published control called the later hit test directly, bypassing this screen.

This changes the interpretation of the reported zero survivors. It is a consequence of the promotion rule, **not evidence that these seeds and generators failed the full test**. The 4,274 saved scores still describe what the source code produced; they do not close the method family.

## What was replayed

The source's seed builder regenerated all **323** committed seeds exactly. The Py2.7 random-generator self-test passed, all seven generator functions ran, and the original sweep reproduced **4,274 rows** against the source's 12,956-rune LP2 transcription. The row count is lower than 323 × 7 × 2 because **31 phrase strings** are used with only three generators. The reproduced best score, −6.5781, matches the published summary.

The nine-register language model used by the later hit test is absent from the pinned repository, as are three exact training corpora needed to rebuild it. We therefore did **not** rerun that test or replace it with a different scorer. The pinned `control.json` is retained as a source artifact, not treated as an independently reproduced control result.

## Reproduce

From the repository root, Python 3 with NumPy runs the fast audit in about a second:

```text
python experiments/records/semantic-seed-screen-gate-audit/run.py --check
python experiments/records/semantic-seed-screen-gate-audit/check.py
```

To rerun all 4,274 upstream screening rows in a temporary copy, use `python experiments/records/semantic-seed-screen-gate-audit/run.py --replay`. This takes roughly three minutes. The [saved rows](experiments/records/semantic-seed-screen-gate-audit/rows.jsonl) and [machine-readable result](experiments/records/semantic-seed-screen-gate-audit/results.json) are bundled with the pinned source and its MIT license. The full source hit test would require its original model and exact corpus bytes, then a corrected, predeclared promotion rule and an end-to-end planted control.
