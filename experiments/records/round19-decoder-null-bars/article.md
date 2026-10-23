# How often do wrong keys look promising?

A language score can rise because a decoder has more freedom to choose English-like output. The [pinned Round 19 test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/I1) ran wrong keys through several decoders, then fitted a separate score threshold for each one. We replayed its fit from all **34,000 saved score rows** and checked the arithmetic independently.

## Finding

![Wrong keys crossing the same score line under five decoders.](experiments/records/round19-decoder-null-bars/decoder-null-bars.svg)

The source used **−5.5** as a reading line. With a permissive drift decoder, all **500 of 500** wrong keys in one setting scored above that line; at a stricter drift setting, **230 of 2,000** did. The source's repository decoder yielded **0 of 2,000** above the same line. The chart counts scores, **not readable decipherments**. Its point is that a fixed language-score line has very different behavior under different decoders.

These archived comparisons use 240-rune samples and beam width 400, with the same declared SHA256-counter wrong-key family. They do not calibrate whole-book outputs.

The source therefore fitted wrong-key score tails separately for each of **13 decoder modes** on real ciphertext and synthetic controls: **26 cells** in all. Our full source replay matches every saved fit field. An independent implementation, using the same stated block sizes and random seeds, also matches all 26 cells. For example, the fitted one-percent bar for **one million** wrong-key trials is **−6.02** for the repository mode and **−4.05** for the most permissive drift mode. Those bars are **model projections** from 500–2,000 scores per cell, not observed million-trial error rates.

As a separate check fixed before we computed it, we fitted on alternating rows and compared predictions with the reserved rows at block sizes **10, 25 and 50**. Median absolute score errors were **0.012, 0.015 and 0.016**. This checks short-block behavior inside the saved arrays; it cannot validate the source's million- or billion-trial extrapolation. The source fit was already known when we wrote the replay plan, so this is a retrospective replay with a new internal diagnostic.

## What it means

For this specific language score and decoder family, the threshold must be calibrated **after** the decoder rule and search size are fixed. A score above an unadjusted line is insufficient evidence of a correct key. The saved wrong-key arrays come from the source's beam searches; we did not rerun those 34,000 decodes or test a new LP2 key. The Gumbel model's tail and its independence assumptions remain unverified at million-trial scale. This result does not identify or exclude an LP2 cipher.

## Reproduce

The [plan](experiments/records/round19-decoder-null-bars/plan.json) pins the source revision and exact saved arrays. The downloadable experiment includes the original MIT-licensed source and score data. From the extracted folder, run:

```text
python experiments/records/round19-decoder-null-bars/run.py
python experiments/records/round19-decoder-null-bars/check.py
python experiments/records/round19-decoder-null-bars/plot.py --check
```

The first command executes the original fit script in a temporary folder and compares its entire 26-cell output with the archived source. The second independently recomputes the fits and reserved-row diagnostic, then compares the saved [results](experiments/records/round19-decoder-null-bars/results.json). The chart is generated as responsive SVG from the same pinned rows. The related [known-key decoder control](#/experiments/round19-decoder-baseline-control) tests a different question: whether each decoder can recover planted text at all.
