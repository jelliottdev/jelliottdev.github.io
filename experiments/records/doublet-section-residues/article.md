## Finding

**The 86 adjacent equal-rune pairs do not favor a position modulo 2 through 8 within their manuscript sections.** We reproduced the [published section-relative residue counts](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/results/lag_and_parity.txt) exactly. The strongest of seven adjusted concentration scores is **1.168** (modulo 2). In **4,316 of 5,000** controls, at least one of the seven scores is as high. That comparison retains the observed number of doublets in each section.

![For modulo seven, the 86 doublets spread across all seven positions rather than clustering in one group.](experiments/records/doublet-section-residues/residues.svg)

## What was tested

A *doublet* is a pair of consecutive identical runes. The position used here is the **second rune's zero-based position within its section**. The nine unsolved sections are LP2-00–02, 03–07, 08–14, 15–22, 23–26, 27–32, 33–39, 40–53 and 54–55. We scanned every rune in those sections, found 86 doublets and counted their positions modulo 2, 3, 4, 5, 6, 7 and 8. All seven count vectors match the source test; for example, modulo 7 gives **7, 10, 12, 10, 15, 18, 14**.

For each modulus, the expected count accounts for how many eligible adjacent-pair positions of each residue exist in *each* section. The comparison then randomly places that section's **same number of doublet events** among its eligible positions. It repeats this 5,000 times and, in each trial, selects the strongest of the same seven moduli. Using the strongest result on both sides matters: after seeing seven residue plots, one will usually look uneven by chance. The statistic is chi-square divided by its degrees of freedom, so the different moduli can be compared on a common scale.

The control maximum has a median score of **1.858**; the manuscript's strongest score is **1.168**. The saved [results](experiments/records/doublet-section-residues/results.json) include every doublet position, expected count, seven observed score vectors and all 5,000 control maxima. A planted control keeps the nine section event counts but places them all on positions divisible by 7. Its adjusted modulo-7 score is **86.338**, far beyond the control range, confirming that a strong modular placement pattern would be visible.

## Limit of the result

This does **not** rule out block ciphers or any general mechanism for suppressing adjacent repeats. It only finds no **section-position residue concentration** among the observed doublets for moduli 2–8 under this uniform-placement comparison. The comparison does not preserve possible clustering of events within sections, different word boundaries, or a cipher's expected position distribution. It also does not test sentence-relative positions: the public source's sentence-token rules cannot be reproduced exactly from the punctuation retained in this site's transcription. Those counts need a separate, pinned sentence-boundary inventory.

To reproduce offline, run `python experiments/records/doublet-section-residues/run.py --check` and `python experiments/records/doublet-section-residues/check.py`. The independent check extracts doublets again from the page text and verifies all seven residue vectors. No external files or network service are needed during replay.
