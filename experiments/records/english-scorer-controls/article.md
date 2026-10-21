## Would our scorer recognize a real answer?

A search can recover meaningful text and still discard it if its scoring rule expects the wrong language. This experiment isolates that last step: give a fixed English four-letter scoring model known text in eight languages, then shuffle the same letters as a control. No cipher or decoder is involved.

The model accepts all English and French samples in this run, some German, Italian, Portuguese and Spanish samples, and none of the Finnish or Welsh samples. It accepts none of the 7,680 shuffled controls. That is useful separation from these shuffles, but **acceptance is neither English identification nor proof of a decryption**. Rejection also cannot rule out meaningful plaintext in another language.

## Source and scope

The idea follows the scorer-language investigation in [Dukotah's repository](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/PAPER.md). We pin that revision and reuse its English quadgram count file and −5.5 threshold. We run a new, narrower control on our existing aligned FLORES translations; we do not reproduce the repository's full decoder benchmark or import its conclusions about the unsolved cipher.

The [language comparison experiments](#/experiments/parallel-languages) ask which reference profiles resemble manuscript statistics. This experiment instead asks what a candidate-selection tool accepts when the input is already known text. There are no unsolved-page inputs here.

## Fixed procedure

Divide each of the eight 1,012-sentence translations into the same eight consecutive sentence blocks: four of 127 sentences and four of 126. Join sentences with spaces. Apply each of two rules: uppercase and retain A–Z only; or uppercase, canonically decompose Unicode, remove combining marks, and then retain A–Z. The second rule folds many accented letters but is not a general transliteration system. Uppercasing can expand characters, such as ß to SS. The report records retained lengths and discarded alphabetic characters for each block.

Take the first 120, 240 and 400 retained letters from every block. These are nested samples, not three independent passages. Aligned sentence blocks preserve source content boundaries, but equal character prefixes do not necessarily end at the same translated idea. Generate 20 deterministic shuffles of each excerpt, preserving its exact letter counts. Keep all 384 original cells and all 7,680 controls; there is no selection by score.

For each overlapping group of four letters, use log₁₀(count / total model count). An unseen group receives log₁₀(0.01 / total). Average over the length minus three groups. Accept a sample when this average is at least −5.5. This threshold belongs to this model and preprocessing; it is not portable to an arbitrary language scorer.

## All conditions

Each cell below is accepted originals out of eight blocks. Every condition also has 160 shuffles per language; all have zero accepted shuffles. The figure shows individual original scores and the full observed shuffled range, not a confidence interval.

| Language | A–Z 120 | A–Z 240 | A–Z 400 | Folded 120 | Folded 240 | Folded 400 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| English | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| Finnish | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| French | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| German | 6/8 | 6/8 | 6/8 | 6/8 | 6/8 | 8/8 |
| Italian | 7/8 | 8/8 | 8/8 | 7/8 | 8/8 | 8/8 |
| Portuguese | 5/8 | 7/8 | 7/8 | 6/8 | 7/8 | 7/8 |
| Spanish | 6/8 | 7/8 | 7/8 | 8/8 | 7/8 | 7/8 |
| Welsh | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |

## What this does and does not establish

This scorer can reject intact language while accepting a different non-English language. A successful candidate therefore needs more than crossing a threshold: a reproducible decoding rule, declared choices, coherent extended output and checks against controls appropriate to the whole search.

The shuffles preserve single-letter frequencies but destroy order. They are not wrong-key outputs from a specified cipher. Zero acceptances in this finite collection does not imply zero false positives, especially after searching millions of candidates and keeping the maximum. The overlapping sample lengths, reused translations and shared model also prevent treating these cells as independent trials or a general accuracy estimate. Model-training overlap with the benchmark has not been independently excluded.

This is not decoder recovery power: it bypasses decoding entirely. A later planted-cipher variant should separately measure exact recovery and score acceptance under fixed encoder, key, skip rules and search budget. A search-size control should score the maximum from each complete null search rather than individual null strings alone.

## Reproduce and inspect

Download the experiment bundle and extract it with its directory structure. No network access, API key or third-party Python package is required.

```text
python experiments/records/english-scorer-controls/run.py --check
python scripts/check_english_scorer_controls.py experiments/records/english-scorer-controls/results.json --receipt my-scorer-audit.json
python experiments/records/english-scorer-controls/plot.py
```

The producer checks every pinned input hash. The independent checker reconstructs the source excerpts and shuffles, calculates scores by counting four-letter groups rather than importing the producer, and checks every decision within an absolute numerical tolerance of 10⁻¹². Both computations passed; human review remains pending. The saved JSON includes excerpts, hashes, seeds, individual scores and normalization diagnostics, so every plotted mark can be traced back to its input.
