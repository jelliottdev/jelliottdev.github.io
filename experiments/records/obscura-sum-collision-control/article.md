# How much does an OBSCURA word-sum match narrow the search?

**A GP-sum match is common in the LP2 text.** The sixteen fixed candidate words from the [OBSCURA table audit](#/experiments/mixed-square-word-sums) have thirteen distinct prime totals. Those totals match **104 of 2,928** visible words on LP2-00–55. A sum match can nominate a word for inspection, but it does not pick a unique key or operation.

![The observed 104 matches lie inside the 77–114 central range of page-preserving shuffled controls.](experiments/records/obscura-sum-collision-control/sum-collisions.svg)

To test whether 104 is unusual, the script shuffles rune prime values **within each page** while leaving its rune inventory and every visible word length fixed. Across 2,000 seeded shuffles, the mean is **95.2 matches** and the central 95% of counts is **77–114**. In **375** trials, the count was at least 104. The observed count is therefore not an unusually selective signal under this control.

For example, the supplied candidates `BUFFERS` and `MOURNFUL` both have target total 199. A ciphertext word totalling 199 cannot distinguish those proposed words on the basis of the sum. The count also ignores whether either candidate has the same length, punctuation, or rune pattern as the ciphertext word. Those checks would need to be fixed before a word-level decoding attempt.

## What this does and does not test

This measures the **first selection step** of a reported idea: pick encrypted words whose GP sums equal one of the table-word totals. It does not reproduce a word-specific cipher, because the discussion did not save one exact transformation or its complete output. The control preserves page rune frequencies and word lengths; it is a reference for match abundance, not a model of the manuscript's encryption.

The observation does not rule out a fully specified key scheme. Such a scheme would need a deterministic rule for choosing among equal-sum words, an exact transformation, and held-out words or pages it predicts without adjustment.

## Reproduce

Download this experiment's ZIP or run from the repository root:

```text
python experiments/records/obscura-sum-collision-control/run.py --check
python experiments/records/obscura-sum-collision-control/check.py
```

The [results](experiments/records/obscura-sum-collision-control/results.json) retain every target total's observed count and all 2,000 control counts. The second script independently recounts the original matches from page records.
