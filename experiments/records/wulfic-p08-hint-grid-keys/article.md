# Keys made from the P08 hint grid

The source calls its hint page **P08**; this is today's [LP1-08](#/wiki/2014-stage05), not LP2-08. An earlier [OutGuess extraction](#/wiki/outguess) from the original LP1-08 JPEG saved a 140-byte message. All **28 two-character groups** in its two grid rows match the [archived Wulfic script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p08_grid_analysis.py) in order. We checked the stored extraction against its recorded image and output hashes; this verifies the grid's provenance without treating the subsequent key idea as established.

The script converts each row's characters to Gematria Primus values and treats their differences or raw values as repeating keys. For example, its first `TL` / `SL` pair contributes **28, 0** to one 28-value key. We tested the script's seven fixed keys and the five keys it rotates through every phase.

**The threshold hits do not establish a reading.** The source's full old P08–54 range includes nine solved LP1 pages. Of **103** rotated-key hits above its index-of-coincidence cutoff, **99** are on those solved pages. The remaining **four** are on LP2-00–37, all on LP2-32. Three share one frequency relation: `KEY_A` subtraction and `KEY_B` addition give the same text, while `KEY_A` Beaufort reflects its alphabet and therefore has the same frequency score. The fourth uses a different raw-row key.

![Of 103 source cutoff hits, 99 occur on solved LP1 pages and 4 on unsolved LP2 pages. The strongest LP2 frequency score is a retrospective diagnostic, not a reading.](experiments/records/wulfic-p08-hint-grid-keys/comparison.svg)

Index of coincidence measures how often two rune positions carry the same rune; here it is scaled by 29. A high score measures concentration, not whether the rune order forms a readable message.

The strongest LP2 case is **1.382** on LP2-32, a 121-rune page. Its first 30 decoded runes transliterate as `LTHIOWRDBEOBNGTHJLBDOEWONJEAMFLBSEBTHF`. The reflected variant begins `NIOTHOEAEGEOBEOHIOENEOGWOEYLEUIFNEOXJEOIOF`; the other key begins `DCCYJNGUXSBTHCDNGPNGDDLBTHHGEOMHCNGCO`. These are candidate outputs for inspection, not verified plaintext. The source's own word score operates mostly on letter bigrams after removing the manuscript's word boundaries; it supplies no independent whole-page reading or held-out prediction.

The source's cutoff can detect the kind of text it seeks: we encrypted **17 established LP1 readings** with each of the five rotated keys at two phases and three directions. All **510** controls decrypted exactly and passed the same IoC cutoff. That tests the cutoff on those known-reading lengths, not on every possible language or layered cipher.

After seeing that the solved pages dominated, we examined LP2 separately using the **same 199 page shuffles** specified for the full sweep. None of the 199 shuffled LP2 maxima reached 1.382; **7 of 199** had at least four cutoff hits. This is explicitly a **post-observation subset diagnostic**. The shuffles preserve each page's rune counts but destroy position order. They do not model the full historical search over clues, keys and scoring choices, and zero observed shuffle exceedances does not imply zero chance or identify an encryptor.

The original script's page loader resolves to `tools/pages`, which contains no page files at the pinned commit. We corrected only that path and loaded the **47 committed `pages/page_08`–`page_54` Git blobs**. Under the modern page names these are LP1-08–16 and LP2-00–37. The corrected-path run has **987 fixed-key cases** (20 cutoff hits, all on solved LP1) and **17,766 rotated-key cases**. Its raw-input snapshot, all candidate scores, controls and both null readouts are bundled; it is an adaptation of the source's fixed arithmetic, not a claim that the legacy command itself ran as written.

This test covers the specified 14/28-value keys, three GP29 directions, and all source key phases on those pages. It leaves aside the same script's separate bigram-substitution, Koan-key and free arithmetic ideas, later LP2 pages, other hint encodings and other reading criteria. See the [carrier comparison](experiments/records/wulfic-p08-hint-grid-keys/carrier-audit.json), [frozen plan](experiments/records/wulfic-p08-hint-grid-keys/plan.json), [complete results](experiments/records/wulfic-p08-hint-grid-keys/results.json), and [LP2-only diagnostic plan](experiments/records/wulfic-p08-hint-grid-keys/diagnostic-plan.json).

To reproduce from the experiment ZIP or a full Liberpedia checkout with Python and NumPy:

```text
python experiments/records/wulfic-p08-hint-grid-keys/run.py --check
python experiments/records/wulfic-p08-hint-grid-keys/diagnostic.py --check
python experiments/records/wulfic-p08-hint-grid-keys/check.py
python experiments/records/wulfic-p08-hint-grid-keys/check_carrier.py --check
python experiments/records/wulfic-p08-hint-grid-keys/plot.py --check
```

The independent checker rebuilds every observed key from the source's paired rows, checks every source page array against its preserved raw bytes, and reevaluates all 18,753 observed cases and 510 planted controls. The seeded full-null replays are checked by the two complete run commands.
