# Testing a three-rune shift display

The pinned LiberPrayground program displays possible readings **three runes at a time**. For each block it tries all 29 alphabet shifts and ranks them by a rune-trigram frequency table. It repeats the display from three starting positions. Each block chooses its own ranked shift; the program does not require one key to connect adjacent blocks.

We checked that display on **17 already decoded page streams** (15 LP1 pages and solved LP2-56–57). Adding 7 to every known rune gave every block a known correct shift. The original program's block output matched a separate enumeration of all 29 shifts. Yet its first-ranked row recovered only **50.4%** of known runes on average across the 51 page/starting-position displays (range 32.1–64.5%). Five blocks had ties for the top frequency; stable source ordering chooses one displayed alternative without resolving the tie.

![The selected row scores well but falls short of exact recovery](experiments/records/relikd-trigram-shift-control/comparison.svg)

We also scored all 29 displayed rows per starting position with a fixed English quadgram table. Blank source cells broke text into separate runs; a row needed at least 100 scored quadgrams. The best-scoring row was on LP1-06: **129 of 207 runes matched, leaving 78 wrong**. Its score was higher than the maximum of each of 49 complete searches on within-page shuffled controls. That is a finite comparison of this display and score, not a probability that it decoded a page. The scorer's training overlap with these known readings has not been excluded.

The selected row starts **“OANDEDNDEEDWEDTSES…”**; the known reading starts **“OANAMANDECIDEDTOGO…”**. The resemblance is real, but so are the mismatches.

The fixed control rule required both score separation from at least 47 of 49 shuffled maxima **and 70% exact recovery** before screening unsolved LP2. The 70% line is a practical threshold chosen for this control, not a universal decoding standard. The score condition passed; recovery did not. We did **not** run this setup on unsolved LP2. The +7 construction verifies a simple known shift and source arithmetic; it does not test whether an unknown cipher uses an interrupted or changing key. Likewise, plausible-looking fragments can arise because every three-rune block is independently selected from a language table.

This is a control audit of a local-fragment display, not a failed Liber Primus decryption. A proposed decoder would need an explicit rule connecting blocks and a known-reading recovery control for that rule before an unsolved-page result could carry weight.

## Inspect and reproduce

The [frozen control plan](experiments/records/relikd-trigram-shift-control/precontrol-plan.json) fixes the 17 pages, three starts, 29 ranked rows, score eligibility, +7 plant and 49 shared shuffles. [Complete measurements](experiments/records/relikd-trigram-shift-control/results.json) preserve every first-ranked page/start display and every shuffle maximum. The original program is [pinned at revision 719380e](https://github.com/relikd/LiberPrayground/blob/719380ebee0523ad7f2fbf389c6f960d51bea5a4/LP/FailedAttempts.py); it has no license file in that Git tree, so its code is not copied into this record.

With a separate checkout of that exact revision, run Python in UTF-8 mode. This matters on Windows because the original frequency loader does not declare its file encoding.

```text
python -X utf8 experiments/records/relikd-trigram-shift-control/run.py --source-root PATH_TO_LIBERPRAYGROUND --check
python experiments/records/relikd-trigram-shift-control/check.py --source-root PATH_TO_LIBERPRAYGROUND
python experiments/records/relikd-trigram-shift-control/plot.py --check
```

The runner executes the original method from verified Git objects in a temporary directory and compares its entire saved result. The checker separately derives the 29 shifts, all selected rows and all 49 complete-search maxima without importing that method. No manuscript target or external service is needed.
