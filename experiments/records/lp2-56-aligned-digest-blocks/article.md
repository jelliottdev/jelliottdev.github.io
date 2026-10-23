## Finding

**No tested digest equals a complete aligned block of the 256-byte grid payload from LP2-49–51.** We reused the exact artifact corpus fixed for the [LP2-56 printed-hash check](#/experiments/lp2-56-internal-artifact-hashes): 412 named variants representing **324 distinct byte strings**. Seven hash algorithms produced **16,848 exact block comparisons** and zero matches. This tests one possible structure for the grid bytes; it does not identify what they mean.

![The 256-byte payload divided into 16-, 32- and 64-byte blocks, with seven digest algorithms and no exact matches.](experiments/records/lp2-56-aligned-digest-blocks/blocks.svg)

The question is whether the grid might contain whole hashes of already preserved puzzle material. A hash has a fixed byte length, so we cut the payload from **byte zero** into non-overlapping blocks of that length and compared complete digest bytes. The test used neither a sliding window nor the hexadecimal *text* of a digest.

| Block size | Complete blocks | Hashes checked | Comparisons |
| --- | ---: | --- | ---: |
| 16 bytes | 16 | MD5 | 5,184 |
| 32 bytes | 8 | SHA-256, SHA3-256, BLAKE2s-256 | 7,776 |
| 64 bytes | 4 | SHA-512, SHA3-512, BLAKE2b-512 | 3,888 |

The inputs were the **75 original page JPEGs**, four exact newline forms of each of the **75 stored raw page strings**, four forms of each of **nine stored literal sections**, and the resolved payload itself. Duplicate byte strings were hashed once. The [candidate map](experiments/records/lp2-56-aligned-digest-blocks/candidate-map.json) retains all 412 names and their byte hashes; the [input plan](experiments/records/lp2-56-aligned-digest-blocks/plan.json) pins the earlier corpus and payload by SHA-256. The payload comes from the [LP2-49–51 grid extraction](#/experiments/rsa-window-54-source-replay), not from the printed 512-bit value on LP2-56.

## Why the zero is bounded

For each of the seven algorithms, a synthetic 256-byte container held a known candidate digest in its **first and last aligned blocks**. The same scanner found both positions and did not mistake reversed digest bytes for a match. Standard `abc` digest vectors also passed. These controls check the scanner's boundaries, byte order, and hash API; they do not show that a real grid block should be a hash.

Other origins, overlapping or bit-shifted windows, changed input bytes, padding, hash truncation, and different algorithms were outside this test. The result rejects only the precise claim that **one of these 324 candidate byte strings hashes to one of these complete aligned blocks under these seven algorithms**. It cannot rule out a digest embedded elsewhere in the grid or a different interpretation of the payload.

## Reproduce

From the repository root, run:

```text
python experiments/records/lp2-56-aligned-digest-blocks/run.py --check
python experiments/records/lp2-56-aligned-digest-blocks/check.py
```

The runner computes each candidate digest once per algorithm and fans it out to the matching block size. The independent checker rebuilds the input bytes and searches in the opposite direction: it indexes candidate digests, then asks which payload blocks appear in that index. Both verify the pinned source files. The [result summary](experiments/records/lp2-56-aligned-digest-blocks/results.json) includes the block counts, comparisons, matches and all seven planted-control outcomes.
