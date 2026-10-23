## Finding

If I and M act as local markers for F interruptions, one simple prediction is that they should occur close to F more often than page composition alone would suggest. Among **458 F runes** on LP2-00–55, **132** have an I or M within two rune positions on either side. Shuffling rune order separately within each page gives a middle 95% range of **96–133**, with **34 of 999** shuffles at or above 132.

![Observed F neighborhoods against page-preserving shuffles.](experiments/records/im-near-f-markers/proximity.svg)

The observed count sits near the upper edge of this particular reference. It is **not evidence of a reset rule**. The proposed I/M pair and proximity radius were chosen after discussion of the manuscript, and the reported stream-skip idea did not specify a distance or direction. Testing other rune pairs, distances and sections would create more chances for a high count.

## Exactly what was counted

For each F, the script looks up to two rune positions before and two after it, staying on the same page. It scores one exposure if any of those positions contains I or M. Punctuation and word breaks are omitted, just as they are in the rune-only stream. The 999 reference trials retain each page's length and exact counts of every rune, including F, I and M, while shuffling their order.

This does not insert or remove F, model skipped key slots, detect doublet avoidance, or decode a message. A proposed stream cipher needs a fixed key generator and a deterministic transition for F, collisions and I/M before its full output can be compared with a held-out page.

## Reproduce

Run `python experiments/records/im-near-f-markers/run.py --check` from the repository root. The [results](experiments/records/im-near-f-markers/results.json) preserve page counts, the shuffle seed and all 999 comparison counts.
