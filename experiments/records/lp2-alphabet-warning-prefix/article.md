# Fixed alphabet transformations and the warning opening

## Why test this?

A newcomer can reasonably try reusing the warning's Atbash method, shifting the rune alphabet, or reversing the text. These are small, finite searches. The difficult part is deciding what counts as success without picking an attractive fragment after looking at the output.

This test uses one deliberately narrow criterion: the first 12 decoded rune indices must equal the first 12 decoded runes of LP1-01's warning. The criterion is motivated by an existing reading, but there is no evidence that an unsolved page must repeat that opening. This is not an English detector.

## Plan and scope

The plan and runner were committed as `faab48f` before the first execution. All 56 archived pages LP2-00–55 are included, corresponding to their unsolved status in the source snapshot. This is not a claim about their present-day solving status.

For every page, keep all recognized runes, including headings, and remove other characters. Use indices 0–28. Try both original and whole-stream reversed order. For each order, evaluate both multipliers a = 1 and a = -1 with every additive offset b = 0–28, using `(a * index + b) % 29`.

The positive multiplier covers all constant shifts. The negative multiplier covers alphabet reversal with every shift; ordinary Atbash is a = -1, b = 28. The identity is included. Reversing a complete stream is not the same as reversing individual rows or words.

| Transformation class | Orders | Offsets | Pages | Cases | Exact matches |
| --- | --- | --- | --- | --- | --- |
| Constant shift | 2 | 29 | 56 | 3248 | 0 |
| Reversed alphabet plus offset | 2 | 29 | 56 | 3248 | 0 |
| Total |  |  |  | 6496 | 0 |

These are parameter cases, not a promise that every resulting string is distinct.

## Result and interpretation

All 6496 cases completed. No output began with the specified 12-rune warning prefix. Every full candidate sequence is retained in the JSON output, not only its prefix or an attractive excerpt. Each case records the page, order, multiplier, offset, output indices, and exact-match flag.

This finding is negative only for the declared opening at position zero. It does not rule out meaningful text beginning differently, a heading that needs separate treatment, another region, or an arbitrary substitution. There is no significance estimate because this is an exhaustive exact-match query, not a statistical test of whether the text is English.

## Reproduce and inspect

Use Python 3.12.10 and the repository checkout:

```
python experiments/records/lp2-alphabet-warning-prefix/run.py --check
python experiments/records/lp2-alphabet-warning-prefix/check.py
```

The first command regenerates and compares every candidate, input hash, and match flag. The second uses a separately constructed alphabet-walk lookup to verify all output indices and confirms that every parameter tuple is unique. It also checks the known warning's opening A,W,A against indices 24,7,24. Neither command uses a network service.

[Download all candidate outputs](experiments/records/lp2-alphabet-warning-prefix/results.json). To save a fresh report, run the runner with `--output my-prefix-scan.json`; it refuses to overwrite an existing file. Read `alphabet` to map output indices back to runes. Latin transliteration involves additional conventions and is not applied here.

## Retest and changes after inspection

Codex reran the complete scan and the separate oracle on 20 October 2026. All 6496 candidates reproduced exactly. No input-selection rule, prefix length, transformation, or stopping rule changed after the first result. The independent oracle was added after the first run as a verification step, not used to select results. Human review remains pending.

## Next variants

A different known opening, prefix position, heading convention, or transformation range must be declared as a new variant with the changes visible. Do not append extra guesses to this baseline and report only the final combined search. An exact match in any later variant would still require checking the rest of the page.
