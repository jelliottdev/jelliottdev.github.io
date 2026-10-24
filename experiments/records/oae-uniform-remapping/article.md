## What changes when three rune types become one?

Merging every **O, A and AE** into a single rune increases equal neighboring pairs from **89 to 192** in the source's 13,136-rune LP2 stream. On a fixed 29-symbol scale, the index of coincidence rises from **1.00 to 1.22**. This measures how sensitive two statistics are to one particular transcription change. It does not recover plaintext.

The three shapes are easy to confuse. A [public source audit](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/independent-read/FINDINGS.md) therefore merged the family and compared the resulting statistics. We reproduced its arithmetic and checked every uniform assignment of these three labels.

## What the 27 assignments cover

Each input rune type can become O, A or AE: **3 × 3 × 3 = 27 assignments**. The same assignment applies at every occurrence; other rune types stay unchanged. Six assignments merely exchange the three names. These preserve the frequency multiset and every equality relation, so neither statistic can detect such a naming error.

The three assignments that merge the entire family give the largest repeat count and frequency concentration in this finite set. That upper bound applies to these 27 uniform assignments. It does not cover individual glyph corrections, new symbol types, changing word boundaries or context-dependent readings.

## Why the source reports 1.14

The source program multiplies raw IoC by the number of distinct symbols remaining in the stream. Merging three types leaves **27**, so its value is **1.137**. Keeping the original **29-symbol scale** gives **1.221** instead. Both calculations reproduce; the multiplier changed. Comparisons should state which scale they use.

The raw collision probability changes from **0.03448 to 0.04211**. These numbers describe the same before-and-after streams without an alphabet-size multiplier. [How IoC works](#/wiki/index-of-coincidence).

## What this does not settle

This text includes the two solved closing pages. It is a different sample from the 12,956-rune unsolved-only stream used by several other records.

No glyph image was adjudicated here. The source's shape-clustering inputs are not supplied by this replay, and a clustering agreement score cannot itself decide whether a whole class has the correct rune name. More importantly, changes in ciphertext statistics do not bound the effect of transcription errors on an unknown decoder. [Known-key error controls](#/experiments/rune-reading-sensitivity-t3) test that separate question on specified ciphers.

## Reproduce

Run `run.py --check`, then `check.py`. The producer uses frequency and adjacent-pair tables; the independent checker builds all 27 full remapped streams. Both use the frozen source text and standard Python. `plot.py --check` verifies the diagram. No random trials or language-score threshold are used.

The map set, source hash and metrics were frozen before the new census. No target-dependent choices were added afterward. The original source exposure script and findings are preserved for comparison; their broader decryption conclusions are not adopted.
