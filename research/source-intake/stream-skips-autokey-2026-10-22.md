# Stream skips and autokey: supplied leads

This is an intake note, not a completed experiment or a claim about the encryption mechanism. The three supplied screenshots contain discussion, not a fixed program, source-position trace or complete output. Their exact image hashes are below; no public post URL was supplied. Preserve these as distinct questions and do not report them as historical failures.

| Submitted image | SHA-256 |
| --- | --- |
| `1-16562.jpg` | `96cafc31bbf0e590ec71b65443abd6a590211534dd140306dc7a928a65a36556` |
| `2-16564.jpg` | `f12241581443a6328e687444c8ca138592f30eaeb72b97f3a516948bd5dcf2e4` |
| `3-16570.jpg` | `4f21c361d7a0f6e2ed16144face87503d9faef5bcfc61f8e57dfc9c3ecc52e16` |

## 1. Collision-driven skipping and resynchronization

The proposed mechanism rejects a key slot when its output would repeat the previous rune, treats some F runes as skips, and uses I and M runes as possible markers to restore alignment. These are three separate state transitions. The supplied description does not say whether F is copied, removed or consumes a key slot; whether I and M are separate markers or a joint pattern; or how a marker determines the new key position. Fix those rules before attempting a manuscript decode. Without a key generator and a deterministic resynchronization rule, arbitrary advances can fit a chosen reading.

Already related, but narrower: [`decoder-skip-controls`](../../experiments/records/decoder-skip-controls/record.json) tests planted collision skips and an unrelated advance with known plaintext. [`lp2-54-55-autokey-reset`](../../experiments/records/lp2-54-55-autokey-reset/record.json) and its skip sibling test six F positions on two pages with ciphertext feedback. None tests I/M resynchronization or the complete combined proposal on LP2. A useful next test would first verify exact recovery on planted ciphertext with a frozen transition table and then apply that same table to a held-out manuscript span. Record both recovery and how many alignments the rule permits.

## 2. Short-window lag patterns

The same discussion reports repeated rune patterns in selected 10–15-rune windows, including lag 13, but gives no window coordinates, match definition or denominator. At lag 13, a window of length 10–13 has no internal pair 13 positions apart, and a 15-rune window has only two. The claimed lag therefore needs a longer comparison span or a different meaning of “window.” Do not encode the ambiguous claim as a positive result. A bounded measurement should state the exact start positions and pair rule, scan all declared windows and lags, and compare the **largest** score with controls that repeat the same scan. Existing doublet and lag records do not establish this claim.

## 3. Cumulative-sum autokey

The supplied formula is `P[k] = C[k] − sum(P[0] ... P[k−1]) mod 29`. With an empty initial sum, define `S[k] = sum(P[0] ... P[k]) mod 29`. Then `S[k] = C[k]`, so `P[0] = C[0]` and `P[k] = C[k] − C[k−1] mod 29` for every `k > 0`. This is exactly first-differencing of the ciphertext, with its first rune retained. We should search and assess it under that name, not count the recurrence as a new independent method. The [differential guide](../../articles/method-differences.html) now shows the reduction. Existing difference measurements and the LP2-54–55 feedback tests overlap, but no record claims a full-manuscript plaintext recovery under this exact proposal.

## 4. Fibonacci autokey on the LP2-40 header

A participant reports interesting patterns on the page-40 header using a Fibonacci autokey, and to a lesser degree a sum version. “Interesting” supplies no fixed plaintext, recurrence, seeds, offsets, stop rule or full-header output. The published [`lp2-fibonacci-openings`](../../experiments/records/lp2-fibonacci-openings/record.json) test uses a **precomputed Fibonacci shift sequence** against nine fixed page-opening cribs. It is not a plaintext-feedback Fibonacci autokey and does not adjudicate the header observation. A fair targeted test should freeze both autokey recurrence and seeds, include the whole red header, enumerate the declared small parameter set, and compare the best outcome with controls that receive the same search. Report page-40 results separately from any broader LP2 claim.

Priority: the exact cumulative-sum reduction is settled algebraically. The remaining items are queued for rule specification and bounded replay; do not increment the completed-experiment count for this note.
