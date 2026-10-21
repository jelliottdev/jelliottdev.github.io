## Why match the number of tokens?

The [aligned-language baseline](#/experiments/parallel-languages) compares the manuscript with much longer reference texts. This control asks a narrower question: how do those reference languages behave when each sample contains exactly **2,896 tokens**, the size of the unsolved rune-token target?

Every complete reference sample is nearest to its own language profile. However, **the manuscript is farther from every language profile than any of that language's reference samples are**. English is still the nearest of the eight candidates, but nearest does not mean that its profile closely explains the manuscript. These are observed distances, not probabilities or statistical rejection thresholds.

## What is held fixed

The languages, translations, development profiles, three common representations and total-variation distance are inherited from the baseline. There is no fitted classifier or new language selection. Each evaluation translation is tokenized sentence by sentence, then divided in original order into disjoint blocks of 2,896 tokens. Every complete block is retained; the final incomplete remainder is counted and reported but not scored as an equal-size sample.

This produces seven blocks each for English and German, eight each for French, Italian, Portuguese, Spanish and Welsh, and five for Finnish. The three representations reuse the same texts. The resulting 177 profile checks are **not 177 independent trials**, and they are not pooled into a claimed general classification accuracy.

Equal token counts do not preserve identical translated passages: different languages use different numbers of words for the same content. This control addresses size. The [aligned-block variant](#/experiments/parallel-language-blocks) separately preserves sentence ranges across languages. Neither controls for the difference between translated web material and Liber Primus's style.

## Reading the distances

Each sample is compared with all eight full development profiles using length bins 1 through 15 and 16+. Total variation is half the sum of the absolute differences in bin proportions. Zero means matching distributions; larger values mean greater separation. All distances are stored as exact rational numbers, and ties would be retained rather than broken by language order.

| Language | Complete blocks per representation | Largest letter-control distance | Manuscript to letter profile |
| --- | ---: | ---: | ---: |
| English | 7 | 0.0508 | 0.0831 |
| Finnish | 5 | 0.0466 | 0.4051 |
| French | 8 | 0.0514 | 0.1781 |
| German | 7 | 0.0561 | 0.1665 |
| Italian | 8 | 0.0436 | 0.2375 |
| Portuguese | 8 | 0.0426 | 0.2114 |
| Spanish | 8 | 0.0456 | 0.2230 |
| Welsh | 8 | 0.0404 | 0.1650 |

“Largest control distance” means the farthest observed sample from its own language's development profile. It is not a confidence limit. The manuscript lies beyond those observed ranges for all eight languages in all three representations, including GP-style grouping. That grouping is an orthographic sensitivity, not a validated conversion of each language into runes.

Within this corpus, all complete samples have a unique nearest profile matching their known language. The manuscript's nearest profile is English in all three representations. The report preserves every competing distance and the margin over the nearest competing language, so this statement can be checked without relying on a winner-only table.

## A Unicode exception found before scoring

The original follow-up plan assumed that all three representations would preserve token boundaries. The implementation stopped when that check failed. Lowercasing the capital dotted I in “İzmir” creates an i followed by a combining dot; the inherited raw-letter tokenizer treats the mark as a separator. Accent folding removes it, joining the word. Three source sentences are affected.

An amendment was committed after inspecting that tokenization issue and before inspecting follow-up scores. The baseline tokenizer was not silently changed. Each representation is partitioned independently, its endpoint ledger is retained, and the report states whether boundaries agree. Folded letters and GP grouping do share boundaries. The original plan remains available alongside the amendment.

## What this does not establish

The control does not identify the manuscript's language, eliminate the eight languages, or estimate a posterior probability. The sample ranges are small, adjacent blocks can share a source article, and both reference splits come from the same benchmark. The manuscript has different genre, spelling, unit and boundary uncertainties. Even its closest reference profile can therefore be a poor match for reasons other than language.

The [known-reading control](#/experiments/known-reading-languages) supplies a complementary warning: some short, established English sections rank nearest to other language profiles. The [cipher-invariants guide](#/wiki/cipher-invariants) explains which transformations preserve lengths and which change the assumptions behind this comparison.

## Reproduce and inspect

Python 3's standard library is sufficient; no API or model is involved. From the repository or extracted reproduction bundle, choose new output filenames:

```sh
python scripts/run_target_sized_languages.py --output my-language-controls.json
python scripts/check_target_sized_languages.py my-language-controls.json --receipt my-language-audit.json
python -m unittest discover -s scripts -p test_target_sized_languages.py
```

The independent checker imports neither the producer nor the baseline tokenizer. It reconstructs words with a regex tokenizer, calculates distances from integer histogram counts, and checks all sample boundaries, remainders, 177 profiles, competing distances, margins and summary decisions. Its saved receipt records the report and checker hashes. Computational verification has passed; human review remains pending.

FLORES translations and this derived account are provided under CC BY-SA 4.0. The baseline's source attribution is included with the reproduction files.
