## Why test readings whose language is already known?

A language comparison should be checked on Liber Primus itself, not only on ordinary translated web text. This control uses **all nine documented reading sections, spanning 17 runic pages**. Their English readings are reproduced with the existing fixed cipher parameters before any statistical comparison. The method is not asked to discover their plaintext.

The result is useful precisely because it is imperfect: **the pooled readings rank closest to English in every tested representation, but several individual sections have a different nearest language profile.** A nearest statistical match is not a dependable language label for a short section.

## What was fixed before scoring

The original plan selects every documented section and the pool, includes headings, and uses the same eight FLORES development-language profiles and length-distance definition as the [baseline](#/experiments/parallel-languages). Within each section, page text is concatenated in order and slash/newline wraps are removed. Sections remain separate when their token lists are pooled.

We compare the literal Latin rune labels using the three corpus representations: letters, accent-folded letters, and GP-style grouping. We also compare native rune-token lengths with each corpus representation. Expanding a rune label into letters changes the counting unit: TH can be two letters but one rune. GP grouping is still a mechanical orthographic sensitivity, not a validated phonetic conversion.

## An input problem found in the first run

LP2-56's published literal field includes its hexadecimal target. A general letter tokenizer interprets the hash's letter fragments as extra words. The unfiltered field produces **50 apparent tokens**, while the rune-derived prose has **25**. All **38 excluded non-rune alphabetic characters** in this control come from LP2-56. The other eight sections have none under the same rule.

We retained that first report and froze a separate amendment before calculating the amended results. For every section—not just LP2-56—the added comparison constructs Latin labels from the verified decoded rune trace, preserves nonalphabetic delimiters, and replaces any alphabetic source character that is not a GP rune with a separator. This gives a consistently defined rune-derived text profile. The original unfiltered results remain in the download as a diagnostic, not a clean prose-language control. The amendment was made after inspecting the first run and is not described as part of the original predeclared design.

## Reading the results

The chart names the nearest language profile for each known-English section. Every language uses identical styling. Its first column compares rune-derived letter lengths with corpus letter lengths; the next uses GP grouping on those labels; the final compares native rune lengths with the GP-grouped corpus. The raw report also contains the accent-folded and additional unit-comparison results.

- The pool contains **739 native rune tokens** and ranks closest to English in all nine comparisons. It is still much shorter than the 2,896-token unsolved target.
- The second koan has 87 native tokens. Its letter profile ranks closest to English, but its GP-grouped and native-rune profiles rank closest to a different candidate. The established English reading has not changed; the counting model has.
- The final parable has only 20 native tokens. Its nearest profile changes between letter, GP-label, and native-rune representations.
- For LP2-56, removing hash fragments changes the literal-profile result. This illustrates an input-selection effect rather than new evidence about the plaintext language.

These results do not prove that the corpus method is useless. They show what its successful pooled comparison does and does not establish. None of the nine sections is a random draw, the pool reuses them, and the representations reuse the same text. Do not turn these outcomes into an independent-trial accuracy estimate or a posterior probability for the unsolved manuscript.

## Reproduce and inspect

Download this experiment's bundle and extract the folder structure intact. It contains the corpus references, archived traces, source transcriptions, reading parameters, original plan, amendment, diagnostic report, current report and scripts. Python 3 standard library only; no API or network.

```sh
python experiments/records/known-reading-languages/run.py --check
python scripts/check_known_reading_language_control.py experiments/records/known-reading-languages/results.json
```

The replay first reproduces the literal readings exactly against the stored page records. The independent checker reconstructs profiles from the separately archived CSV traces and a regex tokenizer; it checks all **70 profiles and 90 rankings** using exact rational distances, and verifies the excluded-character counts. This is computational review, not human review or a new authentication of the readings.

[Current results](experiments/records/known-reading-languages/results.json) · [Original diagnostic](experiments/records/known-reading-languages/diagnostic-original.json) · [Original plan](experiments/plans/known-reading-language-control.json) · [Amendment](experiments/plans/known-reading-language-control-amendment.json)

See [known readings](#/readings), [word-length conventions](#/wiki/word-lengths), and the [shorter aligned-passage controls](#/experiments/parallel-language-blocks). Genre-matched parallel material, per-section unsolved analysis and exact target-size calibration remain separate work.

FLORES translations and this derived account are provided under CC BY-SA 4.0; source attribution is included in the bundle. Manuscript/source provenance remains documented separately in the page records.
