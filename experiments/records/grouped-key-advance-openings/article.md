# Fixed-size grouped key advance

What if one key rune covers several ciphertext runes before the key advances?

## Finding

**No exact opening match.** We held each of the 43 archived keys for groups of **two, three, four or five runes**, testing every key phase and every possible group-boundary offset. The **4,326 settings** across 55 rune-bearing pages produced **2,141,370 comparisons** with nine fixed, 12-rune known-reading openings. None matched; the longest shared prefix was three runes.

![With groups of three, one key position serves three consecutive ciphertext runes; an offset shifts the boundary.](experiments/records/grouped-key-advance-openings/clock.svg)

The diagram shows the key slots for a group of three. At offset zero, slot 0 serves ciphertext positions 0–2, slot 1 serves 3–5, and so on. Offset one moves that boundary, so position 2 already uses slot 1. We tested all offsets for each group size. Each page restarts the schedule, and plaintext is ciphertext minus the chosen key-rune index modulo 29.

## Scope and reproduction

The 43 keys are pinned in the [public wordlist replay](#/experiments/public-wordlist-vigenere). This is a **new test of fixed group sizes**, not a reproduction of that source's ordinary one-step Vigenère output. It does not cover variable group lengths, other keys, interruptions, word resets or unknown opening readings. Planted plaintext recovers under every group size; an independent checker rebuilds the page starts from page JSON and applies the clock rule separately.

The [manifest](experiments/suites/classical-key-schedules/manifest.json) fixes every size, phase and offset. [Results](experiments/records/grouped-key-advance-openings/results.json) include per-size totals and all-case output digest. From the repository root, run `python experiments/records/grouped-key-advance-openings/run.py --check` and `python experiments/suites/classical-key-schedules/check.py grouped-key-advance-openings`.
