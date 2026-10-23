## Finding

The eight saved LiberPrayground autokey databases contain **2,412 candidate rows**. Every saved score reproduces to its five-decimal display precision. That confirms the score calculation for these rows; it does **not** show a decoded LP2 passage. The files preserve candidate interruption choices and starting values, but provide no independent execution log for the search that selected them.

![A known 96-rune message recovers in all eight variants when the three inserted interruptions are supplied.](experiments/records/relikd-autokey-interrupt-database/control.svg)

On a constructed **96-rune known reading**, each of the eight rules recovers every rune after three inserted interruptions are removed. With those positions fixed, the correct starting value has the highest coincidence score in **six of eight** rules. The other two place it second. This is a useful check of the arithmetic, but the test **supplies** the interruption locations. It does not establish that the saved search can find them in a real ciphertext.

## The rule that was checked

At each accepted rune, the previous decoded rune sets the next shift. The shift is either its GP **index** or its GP **prime value**. The saved filenames specify adding or subtracting that shift; `_inv` first maps each ciphertext index `c` to `28 − c`. Candidate F positions are deleted before feedback runs. The source examines only the first **16 occurrences** of its interruption rune and may stop the section at the 17th. A row's `keylen` field is its starting value, except that the source computes field **0 using starting value 1**.

The pinned [source function](https://github.com/relikd/LiberPrayground/blob/719380ebee0523ad7f2fbf389c6f960d51bea5a4/LP/InterruptDB.py) actively calls only the **subtract-prime, non-inverted** file. Its adjacent comment describes the other signs, index values and inversion switch, and seven other database files are committed. We reproduced their saved scores under those stated variants, but cannot verify from this revision that those seven branches were executed by its active entry point.

The plain previous-plaintext-prime recurrence overlaps the [GP-prime feedback test](#/experiments/gp-prime-plaintext-feedback). This record's added scope is the source's selected interruptions, inverted input and saved alternative value/sign variants. It does not retest the full unskipped page search.

## How much of the manuscript entered a score

We matched all nine source section streams to the site transcription, then mapped the **actual runes used** by the saved rows back to pages. Across all eight files, **13 pages** entered completely, **8 pages** partly and **35 pages** not at all. In the one actively called source file, **12 complete and 8 partial pages** entered. The long section filenames do not mean every page in those sections was tested: the first-16-interruption cutoff often stops early.

The saved scores are normalized coincidence counts (random-uniform reference near 1). They are selected maxima over starting values and interruption choices. We have not calibrated that whole selection against a matched null or found readable output, so a high row score is **not evidence of a cipher or a solution**. The [complete row data](experiments/records/relikd-autokey-interrupt-database/results.json) and [page coverage](experiments/records/relikd-autokey-interrupt-database/coverage.json) let readers inspect precisely what was checked.

## Reproduce

The [frozen plan](experiments/records/relikd-autokey-interrupt-database/plan.json) pins the source revision, Git-blob hashes, interpretation and control. The original project has no license in the pinned revision, so its source and corpus remain an explicit external prerequisite rather than being repackaged. Obtain that revision of [LiberPrayground](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4), then from this repository root run:

```text
python -X utf8 experiments/records/relikd-autokey-interrupt-database/control.py --source-root PATH_TO_LIBERPRAYGROUND --check
python -X utf8 experiments/records/relikd-autokey-interrupt-database/target.py --source-root PATH_TO_LIBERPRAYGROUND --check
python -X utf8 experiments/records/relikd-autokey-interrupt-database/coverage.py --source-root PATH_TO_LIBERPRAYGROUND --check
python -X utf8 experiments/records/relikd-autokey-interrupt-database/check.py --source-root PATH_TO_LIBERPRAYGROUND
```

The independent checker re-reads the pinned Git objects, recalculates every score and decoded-output digest, and reconstructs all eight known-message controls. It does not infer a new skip pattern or verify the historical search process.
