# How distinctive is LP2-16–22's 59×59 fit?

**Finding:** Counting decimal digits of Gematria Primus prime values across LP2-16–22 gives **3,481 = 59²**, exactly as reported. Among all **50 contiguous seven-page windows** from LP2-00–55, this is the only exact square under that same representation. This supports the arithmetic and distinguishes the chosen window within a narrow comparison; it does not establish a grid route or a decryption.

![Decimal prime-digit totals across all 50 seven-page windows, highlighting LP2-16–22.](experiments/records/lp2-seven-page-square-fits/windows.svg)

The rule is fixed before the sweep: count every archived rune, including red runes; replace each rune with its GP prime *written in decimal*; count the resulting digits; take every consecutive span of seven pages. There is no reshuffling, route or inserted number. An independent checker reconstructs the totals from the page records rather than the producer's text files.

| Representation, same 50 windows | Exact-square windows |
| --- | --- |
| Rune count | None |
| Decimal digits of zero-based rune indices | None |
| Decimal digits of one-based rune indices | LP2-41–47: 3,249 = 57² |
| Decimal digits of GP prime values | LP2-16–22: 3,481 = 59² |

These nearby alternatives show why the representation matters. They also show why **one in 50 is not a chance probability**: the page span, width, representation and square criterion were considered after the manuscript was inspected. Other widths, subdivisions, inclusion rules and number encodings greatly expand that search space. A 59×59 placement itself has many possible orientations and traversals; this count alone does not choose one. The [Stage 1/2 replay](#/experiments/cc-roman-matrix-replay) checks one proposed continuation separately.

## Reproduce

Run `python experiments/records/lp2-seven-page-square-fits/run.py --check` and `python experiments/records/lp2-seven-page-square-fits/check.py` from the repository root. The [plan](experiments/records/lp2-seven-page-square-fits/plan.json) pins the alphabet and 56 page text files. The [result table](experiments/records/lp2-seven-page-square-fits/results.json) gives all 50 windows and the per-page counts. The source proposal is identified in [reported attempts](#/wiki/reported-attempts?section=cc-section-matrix-fits).
