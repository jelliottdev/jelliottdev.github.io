# Page 49–51 payloads as keys: fixed-opening check

**Finding.** We retested the complete published B-05 candidate grid against a different, narrower question: can any source-defined key produce one of nine fixed, 12-rune known-reading openings at the start of a nonempty LP2-00–55 page? Across **70,680 source configurations**, **none can** under the source's key-skip rule. The longest feasible prefix is five runes.

![B-05 source configurations thin from short opening matches to no complete 12-rune match.](experiments/records/grid-payload-prf-opening-cribs/b05-opening-funnel.svg)

## What was compared

The earlier [B-05 source-grid replay](experiments/records/grid-payload-prf-source-grid/article.md) regenerated the source's 70,680 English-scored cases from the page 49–51 payload bytes. Its four grouped parts include 12 payload representations, 15 PRFs, two byte reductions, direction/sign/Atbash/offset choices, constant shifts, and variants at six contested payload bytes. Those cases reduce to **59,948 distinct effective key streams** for the original 400-rune screen. We reused the exact effective streams and their source case identities, checking every generated key hash against the saved case receipt. In the reverse branch, the original full-length stream is reversed *before* the offset is taken.

For each key, an exact path checker asked whether its first symbols could decode the first 12 runes of any included page as any of the nine independently published reading openings. It permits up to **three rejected key draws** between output runes; each rejected draw must have produced the preceding ciphertext rune. This tests whether a path exists, without English scoring or beam pruning. The earlier replay's null English score and this new fixed-opening failure answer different questions.

| Longest opening prefix | Source configurations |
| --- | ---: |
| 1 rune | 46,041 |
| 2 runes | 22,136 |
| 3 runes | 2,461 |
| 4 runes | 40 |
| 5 runes | 2 |
| 12 runes | **0** |

Several source configurations share effective key bytes, so these are **configuration counts**, not independent keys. The result excludes the specified B-05 keys as producers of these nine exact openings at these 55 page starts. It does **not** show that an unsolved page must begin with one of the known readings, or that payload-derived keys, other offsets, other plaintexts or other page groupings are impossible.

## Repeat it

```bash
python experiments/records/grid-payload-prf-opening-cribs/run.py
python experiments/records/grid-payload-prf-opening-cribs/check.py
python experiments/records/grid-payload-prf-opening-cribs/plot.py --check
```

`run.py` regenerates the source keys from pinned payload bytes, verifies all previously saved case hashes and preserves every original case in a compact digest. `check.py` verifies the four source-part totals and plants both an ordinary and a forced-skip 12-rune opening under a real payload-derived PRF key. All page text and crib CSV inputs are pinned by hash. This is one grouped test of a finite source grid, not a separate experiment for every key.
