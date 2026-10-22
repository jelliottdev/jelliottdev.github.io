## What this comparison tells us

**English has the closest word-length distribution among the eight reference languages tested.** This comparison is useful only if the manuscript's separators correspond to plaintext word boundaries and the encryption preserves one counted unit per rune. Those conditions are unverified for unsolved LP2. The ordering of other close candidates changes when a fixed GP-style grouping is applied to all eight. A nearest distribution is not a plaintext identification or a decoded word.

The experiment uses translations of the **same 997 development sentences and 1,012 evaluation sentences** from FLORES-200. The languages were fixed before scoring: English, Welsh, German, French, Spanish, Italian, Portuguese and Finnish. They give a manageable Latin-script comparison without adding a transliteration model for other scripts. They are not a shortlist inferred from the manuscript, and the ranking is not a search across all languages.

The plan and source files were committed in `738a812` before any scores were calculated. It is a predeclared comparison within this project, not an external preregistration. Human review is pending.

## Word-length results

The distance is **total variation** between word-length distributions: half the sum of their absolute frequency differences. Zero means identical distributions; one means no overlap. We count lengths 1 through 15 separately and put longer words in a final 16+ bin. A value of 0.084 is a distance, not an 8.4% chance of anything.

| Language | Letters | GP grouping sensitivity |
| --- | ---: | ---: |
| English | 0.0840 | 0.1148 |
| Welsh | 0.1721 | 0.1731 |
| German | 0.1757 | 0.1708 |
| French | 0.1827 | 0.1759 |
| Portuguese | 0.2131 | 0.2058 |
| Spanish | 0.2240 | 0.2127 |
| Italian | 0.2359 | 0.2311 |
| Finnish | 0.4022 | 0.3927 |

[Open the comparison chart](experiments/records/parallel-languages/comparison.svg). The chart shows the same results with article-resampling ranges. The JSON also contains the accent-folded letter comparison, which keeps the same language order.

The ordering depends on the counting convention. A language ranking is conditional on both the corpus and the assumed relationship between plaintext units and ciphertext runes. The full table keeps every tested candidate visible.

## Why the rankings differ

The manuscript has a pronounced peak at length three: **24.86% of its tokens contain three runes**. The language profiles differ in how much mass they place at each length. The distribution chart shows the manuscript first, followed by all eight languages alphabetically, using identical scales and the same styling for every language.

The first-place result still has a visible mismatch: English has 19.07% three-letter words, below the manuscript's three-rune share. A ranking measures relative closeness among the tested profiles; it does not establish that the nearest profile is a good explanation of the ciphertext.

[Open all nine distribution panels](experiments/records/parallel-languages/distributions.svg). Lengths 9 and above are combined only for display; scoring retains the original 16 bins. Every full distribution is also available in the results JSON.

## The assumptions that make lengths useful

This comparison requires manuscript word boundaries to preserve plaintext word boundaries, and one counted plaintext unit to correspond to one ciphertext rune. A position-dependent substitution can preserve lengths even when letter frequencies change. Inserted nulls, deleted symbols, word splitting, different spacing, or units representing syllables can break the comparison.

The manuscript target is the existing [rune-token ledger](exports/unsolved-word-tokens.json): **2,896 tokens and 12,956 runes from LP2-00–55**, including headings. Line wraps and slash wraps are removed; tokens can continue across page boundaries. Internal apostrophes count zero, and decimal labels are excluded. See [word lengths](#/wiki/word-lengths) for the exact boundary convention and its historical alternatives. Pooling the pages assumes their aggregate is meaningful; it does not establish that every section has one language or cipher.

For FLORES, letters are lowercased and normalized to NFC. Alphabetic runs are words; internal straight or curly apostrophes are removed without splitting the word. Hyphens and other nonletters separate words. Numbers contribute no letters. Each sentence is tokenized independently. This is an explicit mechanical convention, not a linguist's definition of a word. The comparison retains every aligned sentence; it does not truncate each language to a different passage to equalize word totals.

The GP sensitivity folds combining accents and greedily groups ING, TH, EO, NG, OE, AE, IA, IO and EA, longest first. ING/NG, IO/IA, K/C and Z/S share symbols. Other letters remain. **This is not a validated translation into Gematria Primus.** Pronunciation, ambiguous segmentation and unsupported letters remain unresolved. A supplementary mechanical Welsh-digraph calculation is retained in the raw data as a representation check, not as a separate candidate category or a preferred model. It groups CH, DD, FF, NG, LL, PH, RH and TH and gives a length distance of 0.1466; it does not resolve morphological parsing. The raw-letter and GP profiles can contain more than 29 distinct symbols, so they cannot be literal bijective mappings into a 29-rune alphabet as written. This inventory mismatch is reported in the downloadable results rather than silently repaired by deleting rare letters.

## Repetition gives a different test

IoC is the probability that two different sampled positions contain the same symbol. Adjacent repetition here counts equal neighbors **within words only**. Both require stronger assumptions than lengths: equality must survive a fixed one-to-one substitution. They are not preserved by a general polyalphabetic cipher.

| Text, using letter units | IoC | Equal adjacent pairs |
| --- | ---: | ---: |
| Unsolved rune target | 0.03448 | 0.63% |
| English | 0.06597 | 2.42% |
| Welsh | 0.06387 | 5.74% |
| German | 0.07344 | 2.33% |
| French | 0.06912 | 2.42% |
| Portuguese | 0.07072 | 1.00% |
| Spanish | 0.07111 | 0.77% |
| Italian | 0.07305 | 4.57% |
| Finnish | 0.07282 | 9.31% |

The language profiles have letter IoCs between **0.06387 and 0.07344**, far from the target's **0.03448**. None of these profiles supplies a close single-substitution explanation of the pooled manuscript. The GP sensitivity does not remove that discrepancy. Spanish is closest on the adjacent-repeat measure, yet has a much poorer word-length match. These conflicting rankings are why we do not blend the measures into an unexplained “language likelihood.”

This does not eliminate Welsh, English or any other language under a different cipher. It weakens the proposed fixed-substitution comparison under these text and unit conventions. See [cipher invariants](#/wiki/cipher-invariants) for what different transformations preserve.

## Controls and sampling sensitivity

Each development-language word-length profile was compared with each evaluation-language profile. The nearest development profile identified the corresponding evaluation language **8 out of 8 times in each of the three representations**. That is a useful check that this dataset and statistic can distinguish the chosen languages at this sample size. It is not 100% accuracy on unknown manuscripts: there are only eight whole-document controls, drawn from the same benchmark, and they are much longer than the target.

For the error bars we resample the **281 source-article URL groups** in the evaluation split, with replacement, 200 times using seed 3301. All sentences from a sampled article are kept. The same article draw is used for all eight languages, preserving the matched-content comparison and avoiding treating every sentence as independent. English has the smallest length distance in all 200 draws in all three representations. This is stability to this corpus resampling—not a 100% probability that the manuscript is English. The target transcription is held fixed; these intervals omit uncertainty about its boundaries, genre and cipher.

FLORES contains translated web material. It controls subject matter across languages, but not the difference between that material and Liber Primus's philosophical style, historical spelling or possible nonstandard prose. Translation practices can also affect lengths. A separately fixed, genre-matched parallel corpus remains a follow-up. The [exact-token control](#/experiments/target-sized-languages) now checks complete 2,896-token samples: all reference samples identify their own language profile, but every manuscript-to-profile distance exceeds the corresponding observed control range. Those ranges are descriptive, not confidence limits or rejection thresholds. The [known-LP reading control](#/experiments/known-reading-languages) is now complete as a computational comparison, with human review pending. A separate [shorter aligned-block variant](#/experiments/parallel-language-blocks) now checks eight disjoint evaluation blocks per language; it preserves matching sentences rather than enforcing exactly equal word counts.

## Reproduce it

Download this experiment's bundle. It includes the source translations, source-article metadata, plan, token ledger, scripts, result JSON and chart. No API, account, model download or network request is needed to rerun the analysis; Python 3's standard library is enough.

```sh
python experiments/records/parallel-languages/run.py --check
python experiments/records/parallel-languages/check.py
python experiments/records/parallel-languages/distribution_figure.py --check
```

The first command verifies input hashes, recomputes the comparisons and the 200 resamples, and checks the saved report and chart. Without `--check`, it writes those two outputs. The second uses a separate regex tokenizer and integer-count formulas to verify the 24 language profiles, additional digraph sensitivity, manuscript profile, IoC, repeated neighbors, distances and ordering. It does not independently reimplement the bootstrap. The final command checks that the distribution chart matches the saved counts; it does not perform another experiment. The ledger itself has a separate [transcription/word-length reproduction](#/wiki/word-lengths).

[Raw results](experiments/records/parallel-languages/results.json) · [Frozen plan](experiments/records/parallel-languages/plan.json) · [Source attribution](experiments/records/parallel-languages/SOURCE.txt)

## Sources and reuse

- [FLORES-200 documentation](https://github.com/facebookresearch/flores/blob/main/flores200/README.md): aligned translation benchmark and language list.
- [Original archive](https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz): exact extracted translation and metadata files; archive and extracted-file hashes are recorded in the plan.
- [Dataset card and license](https://huggingface.co/datasets/facebook/flores): Creative Commons Attribution-ShareAlike 4.0 International. Source translations are redistributed unchanged. This derived analysis and its article are also offered under CC BY-SA 4.0.

## Check against known LP readings

The [known-reading control](#/experiments/known-reading-languages) now tests all nine established reading sections and their pool. The pool ranks closest to English, while some individual sections do not. It also documents how LP2-56's embedded hash distorts an unfiltered letter-token count. This supplies a manuscript-specific caution beyond the within-FLORES controls.
