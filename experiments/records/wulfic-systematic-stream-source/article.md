# Prime streams and a short feedback key

An [archived solver script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/stream_cipher_attack.py) searches two ways of generating a rune-by-rune key: fixed sequences drawn from primes, and a key in which each new value depends on the previous two. We replayed its complete *executed* grids on the corresponding manuscript pages.

**The script's threshold admits many outputs, but does not identify a reading.** On rune-shuffled versions of the same pages, complete searches also find thousands of hits. The observed best scores sit within the ranges of 19 shuffled searches. These controls show why crossing the source threshold is insufficient; shuffling is not a model of every possible cipher.

![Source-threshold hit counts in the manuscript compared with complete searches on 19 shuffled versions](experiments/records/wulfic-systematic-stream-source/comparison.svg)

| Source branch | Exact search | Manuscript threshold hits | Nineteen complete shuffled searches |
| --- | ---: | ---: | ---: |
| Prime-derived streams | 2,964 settings on 38 pages | 644 | 625–702 hits; median 662 |
| Two-value LFSR | 6,365,529 settings on 3 pages | 38,826 | 33,694–44,833 hits; median 38,452 |

The stream branch's highest index of coincidence is **1.140**, exceeded by **16 of 19** shuffled searches. Its best combined score is exceeded by **5 of 19**. The LFSR branch's best combined score is exceeded by **11 of 19**. Nineteen controls give a coarse comparison, not a precise probability. There is no independently predicted longer passage or untouched page in the source rule.

The script calls its target list “all unsolved pages,” but its old folder names resolve differently. After its exclusions and empty-page checks, it actually reads archived `page_18` through `page_55`, corresponding to **LP2-01–38**. The two older files `page_00` and `page_02` contain no runes. The source then selects the three pages with the most visible one-rune words for the LFSR search: **LP2-28, LP2-10 and LP2-17**. Of these, LP2-28 overlaps the earlier [singleton-LFSR test](#/experiments/wulfic-lfsr-singleton-constraints), which used a different constraint solver and page set.

## What the screens measure

The script tries **26 named prime-derived streams** in subtraction, addition and Beaufort directions. They include prime values, prime minus one, prime gaps and two cumulative sequences. Each begins at page position zero. The separate feedback search tries every initial pair and coefficient pair modulo 29: **29⁴** tuples on each of three pages, again in three directions. Zero coefficients and degenerate sequences are included. These parameter combinations are settings inside two method branches, not millions of independent ideas.

Each decoded output receives an index of coincidence, a count of ten favored rune pairs, and credit when a visible one-rune word becomes **I** or **A**. That last component can dominate: on LP2-38, where the source parser finds only one one-rune word, matching it adds **five points** to a stream score whose hit threshold is two. The best LFSR setting on LP2-17 makes **6 of 10** one-rune words I or A; its index of coincidence is **0.976**. A partial crib fit and a selected score are not a sentence.

The source defines a Fibonacci-prime generator but never adds it to the search table. Its later Berlekamp–Massey section has a `pass` where a full key would be reconstructed. Neither is counted here as an executed decoder. Other prime streams and other feedback lengths remain outside this test.

## How the replay was checked

Before scoring manuscript text, all 26 generators matched the pinned source functions at four lengths. A sample of 107 feedback tuples, including zero states and taps, matched the source's key, decoded runes, and complete score in all three directions. A synthetic known plaintext recovered exactly and passed each source screen. The optimized search then tested every declared setting. An independent scalar checker recalculates all retained winners and their full-decoding hashes and repeats one entire shuffled feedback search.

The [frozen plan](experiments/records/wulfic-systematic-stream-source/plan.json), [pinned input snapshot](experiments/records/wulfic-systematic-stream-source/inputs.json), and [results](experiments/records/wulfic-systematic-stream-source/results.json) give the exact bounds and counts. Run `python experiments/records/wulfic-systematic-stream-source/check.py` to check the saved result. Run `python experiments/records/wulfic-systematic-stream-source/run.py --check` to repeat all grids and controls; this requires Python, NumPy and Numba. With a checkout of the pinned source revision, `gate.py --source-root PATH --check` and `snapshot_inputs.py --source-root PATH --check` verify source parity and original inputs.

The historical outputs in the archived repository are not treated as verified. This is a corrected-input replay of its finite callable branches, not an exclusion of prime-based keys or LFSRs generally.
