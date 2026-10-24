# Numeric2 Parts B/C: bounded scope assessment

Read-only source/input analysis; no controls or manuscript targets executed. This is not an execution preregistration. Source revision: `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`; source code and preserved inputs are available under the repository's MIT license.

## Part B: payload phase extension

The exact source branch is `sweep_payload_all_offsets`, not main and not the broader claim suggested by its “all offsets” name. It reads both 256-byte files, adds their reversals, reduces each byte modulo 29, then tiles each stream **seven times to 1,792 values** for the 55-page corpus whose longest page has 277 runes. For page length L the executable offset range is:

`range(max(1, 256 - L + 12))`

Thus long pages may receive only offset zero; LP2-49 (66 runes) receives offsets 0–201. Summed over the 55 pages there are **1,882 page/offset pairs**. Four stream labels × two signs × two Atbash states gives **30,112 short screens**. There are 880 offset-zero labels and 29,232 labels with nonzero offsets. This does not cover every phase 0–255 on every page.

Inputs are already available:

| Input | SHA-256 |
| --- | --- |
| `analysis/pp49_51/canon_256.bin` | `4c8dc85531d256793a6d0d318b8845869b4983e672077b094ed955bde92226d5` |
| `analysis/pp49_51/canon_256_decpref.bin` | `0a3aa3c813eddcf7f99ef9794c0e790f2a3fd86ea810a100d7113eb1beebacbd` |

The two readings differ at byte indices 25, 175, 182, 199, 215 and 237, and every difference remains a difference modulo 29. Independently enumerating all 256 phases of the four streams with both signs gives **2,048 distinct complete 256-value cycles**: no exact phase/sign aliases among them. Every page is at least 66 runes, so its maximum reachable key prefix spans at least 261 values, longer than one entire period. This rules out a general full-search alias between these signed phase arrays. Particular ciphertexts can still create coincident outputs, which are outcomes rather than a pretarget equivalence proof. Atbash remains a separate transformation.

The maximum phase is 201, the largest consumed index is at most `201 + 4×276 = 1305`, and the largest padding guard is at most `201 + 4×277 + 8 = 1317`, both below 1,792. These conservative combined maxima suffice to show no finite-tail zero padding is reached. Tiling differs from the old offset-zero payload record's limited allocation/padding behavior.

**Overlap:** `dukotah-payload-key-skip` already ran four payload streams, both signs and Atbash at offset zero on every page: 880 full-page decodes, beam 320, without the short screen. The new branch changes width to 300, adds the 50-rune selection stage, changes available repeated-key allocation, and adds 29,232 nonzero-phase labels. Therefore even its 880 zero-phase settings are overlapping rules/inputs, not an identical byte-for-byte rerun of the previous implementation. The new work is a bounded phase extension of the same payload-key idea, not 30,112 ideas.

## Part C: assigned page-number ramps

`sweep_page_seeded` supplies each source page index i with three exact streams, all of length **1,124**:

- `prime`: `(prime[i mod 29] + j) mod 29`, primes through 109.
- `totient`: `(φ(i+2) + j) mod 29`.
- `3301xor`: `(3301j + i) mod 29 = (24j+i) mod 29`; despite the label, no XOR occurs.

Each key is tested only on its assigned page, both signs and Atbash, offset zero: **660 screens**. The source index is the nonempty-segment index 0–54; it maps to LP2-00–49,51–55, so source index 50 is LP2-51. Do not seed later keys with the image-page number by accident. Guard `4×277+8 = 1116 < 1124`; the largest consumed index is 1104.

Among 165 page-assigned base labels there are **56 distinct arrays**: prime contributes 24 distinct intercepts, totient 19, with 16 shared between those sets; the 3301-labelled slope-24 family contributes all 29 intercepts. There is **no prime/totient coincidence on the same assigned page**, so all 660 actual settings remain distinct by target and transformation. Repeated arrays assigned to different pages cannot remove those page tests. Negative signs produce slopes 28 and 5; no signed-array collision with the positive slopes 1 and 24.

**Overlap:** `wholepage-progressive-caesar` already includes every rigid linear ramp and starting offset of the form `P=C+k*i+b` on all pages. With no skips, the **330 Atbash-off labels** here are a subset of that family. The **330 Atbash-on labels** instead have ciphertext coefficient −1 and are not covered by that record; they require their own overlap check against other affine records. The additional question for the overlapping half is specifically conditional skip paths under this source's beam and short/full gates. This must not be described as a wholly untested numerical construction or a general test of page-number significance. Neither `numeric-stream-skip-grid` nor `artifact-stream-skip-grid` ran Part C. Controls differing only by ramp intercept are related translations, not independent power samples.

## Common gates and required control work

Both branches use the existing engine, unchanged: first 50 runes, beam 60, strict short score greater than −6.5; only survivors receive full-page beam 300, strict full score greater than −5.5; maximum three admissible skipped keys per transition. There is no running-text prefilter or missing Welsh dependency. The historical source log reports Part B in 26.3 seconds and Part C in 0.9 seconds; those are source-host logs, not newly measured local runtimes. Existing local numeric screens suggest a modest grid, but branch-specific synthetic benchmarking and actual survivor cost remain necessary before execution.

Reusable evidence includes the pinned model/source decoder, independently verified source/site arrays, two audited known readings, max-three-skip seed-selection convention, source/native equivalence work and scorer-preference diagnosis. The old payload record's 16 complete-reading controls support its zero-offset, width-320 procedure only. The recent 1,080 controls cover other arrays and offsets 0–4; they do not certify this payload phase domain or page-assigned ramps. Reuse control infrastructure and input hashes, not unearned power claims.

Before either target run, freeze a branch-specific plan and run unchanged-source known-reading controls with genuine skip events. For Part B, cover all tested phase values 0–201 with each of the four payload streams and both signs, using a fixed known-reading assignment; Atbash equivalence may be proved and spot-checked rather than treated as independent power evidence. Include representative long-message plants to exercise period boundaries and finite allocation. For Part C, the 112 distinct signed arrays can be planted directly, with known-reading assignments fixed before target. If both readings are tested for each array there are 224 underlying full controls, not 660 independent tests of every page assignment. Report all bounded-seed attempts, no-eligible and zero-skip cases rather than selecting successful decodes.

Check **exact whole-reading recovery and short-gate passage separately**. The existing source score thresholds should stay fixed for a source replay; any retuned gate becomes a separately planned method. Wrong-key controls are useful diagnostics but do not calibrate the maximum over the entire manuscript grid. For every observed full survivor, independently reconstruct and rescore the source-selected path. Preserve the known cumulative-ranking/normalized-gate distinction and, as a separately labelled audit, inspect retained terminal candidates for normalized crossings. No score-only result establishes a correct reading, full-search significance, language-independent exclusion or OTP explanation.

Recommended order: Part B first because it extends an already published payload-key experiment with exact available inputs and a meaningful new phase range. Part C is very cheap but should be framed narrowly as skip-aware re-evaluation of already-covered rigid ramps. Keep both within the existing method family rather than counting individual settings as ideas.
