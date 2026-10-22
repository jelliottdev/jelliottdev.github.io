## What changed from the baseline

The [full-corpus comparison](#/experiments/parallel-languages) used 1,012 evaluation sentences per language. Here we divide that evaluation split into **eight consecutive, disjoint blocks** and compare shorter passages. Each block contains the same sentence IDs in all eight languages. No sentences were chosen because their statistics looked promising.

The first four blocks contain 127 sentences each, and the last four contain 126. Exact one-based sentence ranges are recorded in the results. The tokenization and distance definitions are unchanged.

## Results

**English is the closest of the eight language profiles to the pooled manuscript in all eight blocks, in each of the three representations.** This supports the stability of that relative ranking across these shorter passages. It does not identify the plaintext language.

Using letter units, the block sizes and manuscript distances are:

| Language | Tokens per block, range | Word-length distance, range |
| --- | ---: | ---: |
| English | 2,613–3,002 | 0.0710–0.1035 |
| Finnish | 1,927–2,105 | 0.3726–0.4316 |
| French | 3,047–3,318 | 0.1731–0.2079 |
| German | 2,623–2,927 | 0.1696–0.1961 |
| Italian | 2,880–3,181 | 0.2274–0.2467 |
| Portuguese | 2,818–3,147 | 0.2007–0.2300 |
| Spanish | 3,106–3,467 | 0.2091–0.2402 |
| Welsh | 2,884–3,206 | 0.1416–0.1940 |

The target has 2,896 rune tokens. These are smaller aligned passages, not exactly size-matched samples: their token counts range from **1,927 to 3,467**. Translating the same content changes word counts. Keeping the same sentence ranges preserves the content control; truncating every language at exactly 2,896 words would no longer compare exactly the same passages. This design documents that tradeoff rather than hiding it.

## Does the statistic recognize known languages at this scale?

For each block, we compare its word-length histogram against all eight full development-language histograms. The closest development profile is the corresponding language in **64 of 64 decisions**, separately for letter units, accent-folded letters, and GP grouping. The raw report includes every distance and the full confusion matrices, including zeros.

That is a control on these eight translated languages within FLORES. It is not a success rate for cipher language identification. The corpus shares translation practices and source genre; the manuscript does not. The three representations also reuse the same text and are not independent replications.

## Bounds and limitations

- All 1,012 evaluation sentences are used once per language, with no overlap between blocks. Development text is used only for the reference profiles.
- A source article can cross a block boundary. Blocks are therefore not independent draws, and the 64 decisions are not treated as independent trials. No binomial accuracy interval or language posterior is calculated.
- The manuscript remains pooled LP2-00–55, with headings and the baseline boundary convention. This does not test each section separately.
- Word-length comparison requires preserved boundaries and one ciphertext rune per counted plaintext unit. GP grouping remains an orthographic sensitivity, not a validated phonetic transcription.
- No genre-matched corpus or known decoded LP control is included in this variant. The separate [known-reading control](#/experiments/known-reading-languages) now covers the nine documented LP sections. A genre-matched corpus remains open.

## Reproduce

The experiment download includes the aligned corpus, token ledger, baseline helper, independent tokenizer, frozen plan and result ledger. Python 3 standard library only; no network, API or model is used.

```sh
python experiments/records/parallel-language-blocks/run.py --check
python experiments/records/parallel-language-blocks/check.py
```

The plan was committed before block scoring; its dependency hash was refreshed for a chart-only baseline change before scoring began. The first command verifies input hashes and recomputes the full report. The second independently reconstructs all 192 block profiles with a regex tokenizer and exact rational total-variation distances, checks all nearest-reference decisions, and verifies that the block ranges cover the evaluation sentences exactly once.

[Results and confusion matrices](experiments/records/parallel-language-blocks/results.json) · [Frozen plan](experiments/records/parallel-language-blocks/plan.json) · [Baseline distributions and source attribution](#/experiments/parallel-languages)

FLORES source text and this derived account are offered under CC BY-SA 4.0. See the source attribution included with the baseline files.
