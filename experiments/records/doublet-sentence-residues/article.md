# Do repeated runes favor a sentence position?

## Finding

The 86 adjacent equal-rune pairs show **no unusual concentration at a sentence-relative position modulo 2 through 8** under a control that keeps each section's number of doublets and the visible punctuation fixed. The strongest of the seven patterns is modulo three: **26, 23 and 37** doublets at positions 0, 1 and 2. In **2,068 of 5,000** controls, at least one modulus had a pattern as strong. This is a bounded position test, not a general exclusion of block ciphers or a decryption result.

![Three bars show the strongest observed grouping, 26, 23 and 37 doublets by sentence position modulo three. Expected counts are about 29, 29 and 28. Of 5,000 section-preserving controls, 2,068 found an equal or stronger best grouping across all seven moduli.](experiments/records/doublet-sentence-residues/sentence-residues.svg)

## Counting from a sentence boundary

The [source test](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/lag_and_parity_tests.py) resets the rune-position count after a period, semicolon or section mark; line wraps do not reset it. This site's transcription preserves the 12,956 runes but not all of that punctuation. We therefore took just the reset rune ordinals from the [pinned relikd source text](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4/pages). The [boundary file](experiments/records/doublet-sentence-residues/sentence-boundaries.json) gives the source-text hash and reset ordinals for each of the nine sections, without republishing either repository's source text or code.

All nine section lengths, the 86 doublet locations and **all seven published sentence-relative count vectors** reproduce. For each possible second-rune position, we compute its distance from the latest sentence boundary. The comparison randomly relocates the same number of doublets within each section, preserving sentence boundaries and applying the entire seven-modulus scan to every control. A deliberately concentrated modulo-seven placement scores **82.53**, above every control maximum, so the test detects a strong pattern when one is present.

The result depends on this transcription, its punctuation boundaries, moduli 2–8 and a uniform-placement control. It does not preserve clustering or model a specific cipher's event positions. Other sentence definitions and other position rules need separate tests. The related [section-position test](#/experiments/doublet-section-residues) addresses a different coordinate system.

## Reproduce

Run `python experiments/records/doublet-sentence-residues/run.py --check` and `python experiments/records/doublet-sentence-residues/check.py`. To verify the upstream punctuation extraction as well, fetch relikd/LiberPrayground at commit `719380ebee0523ad7f2fbf389c6f960d51bea5a4` and pass its `pages` folder to `check.py --source-pages PATH`. The checker validates each source file's SHA-256 and reconstructs every reset ordinal before recounting the doublets.
