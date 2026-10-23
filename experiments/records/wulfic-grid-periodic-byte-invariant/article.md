# Does the number grid retain a repeating alphabet's pattern?

The 256 printed cells on LP2-49–51 can be read as bytes. Wulfic's Stage X2 asks whether those bytes could come from a plaintext stream through a **different one-to-one byte substitution at each position of a repeating period**. A one-to-one substitution changes byte values, but it cannot change whether two bytes encrypted with the *same* substitution are equal. That gives a test without guessing any of the substitutions.

**Finding:** across both declared ways to traverse the grid and every period **1–128**, no equality count exceeds the maximum from 100,000 uniform-byte controls. The source's lower-tail rule excludes **241 of 256 reading/period cells** under its English control, **247** under solved LP1 runes, **247** under hexadecimal digits, and **78** under Base64. These are conditional exclusions of this one model; many Base64 cells remain open, and no byte stream has been decoded.

![Conditional exclusions by plaintext control class among 256 grid-reading and period cells](experiments/records/wulfic-grid-periodic-byte-invariant/comparison.svg)

The [full table](experiments/records/wulfic-grid-periodic-byte-invariant/source-stage_x_periodic.tsv) gives the observed pair count, uniform-null maximum, control cutoff and verdict for each of the 256 cells. A cell is one reading order and one period, **not a separate puzzle idea**.

## What was compared

The two reading orders are the printed row order of the 32 × 8 grid and a column-major traversal of the same cells. For each period `p`, the test groups positions by their remainder after division by `p` and counts equal-byte pairs *within* those groups. If a fixed, one-to-one alphabet is reused at each residue, that count is unchanged by encryption.

The source compares the observed count with 100,000 seeded blocks of uniform random bytes. It calls a structural hit only when the grid exceeds **every** such block at the same period. It also compares with 256-byte plaintext windows from Emerson, the solved LP1 rune stream, and generated hexadecimal and Base64 streams. Its exclusion rule asks whether the grid falls below a class's **lower 0.1% control cutoff**. English and LP1 therefore test specific source representations, not every possible language, text encoding or symbol frequency.

The source supplies 9,024 Emerson windows, 2,646 LP1 windows, and 10,000 each of the hexadecimal and Base64 controls. Our independent checker rebuilds the grid bytes from Liberpedia's printed-token export, recalculates **all 256 observed equality counts and pair capacities**, checks every reported decision against its cutoff, and plants residue-specific bijections to verify the invariant. That planted test is a **post-replay mathematical diagnostic**; it is not an original source power study.

## What remains open

An exclusion only applies if the bytes really represent the proposed plaintext class and every residue uses a fixed bijection with no extra processing. It does not rule out a changing alphabet, non-bijective mapping, transposition, compression, keyed stream or a different grid traversal. The uniform-null maximum is a finite-control threshold, not a decryption score. This record replays **Stage X2 only**; the source's X1 byte-uniformity, X3 integer and X4 decompression screens are separate questions.

## Reproduce

From the repository root, Python's standard library checks the bundled source result and rebuilds the figure:

```text
python experiments/records/wulfic-grid-periodic-byte-invariant/run.py --check
python experiments/records/wulfic-grid-periodic-byte-invariant/plot.py --check
```

The [plan](experiments/records/wulfic-grid-periodic-byte-invariant/plan.json) pins the exact source revision, grid export, control counts and rules. The 256-row table was generated with the unmodified [pinned Stage X program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_x.py), calling only its X2 component. To repeat the full 100,000-draw source calculation from a matching external checkout, run:

```text
python experiments/records/wulfic-grid-periodic-byte-invariant/replay_source.py PATH_TO_WULFIC_CLONE
```

The optional source replay requires NumPy, verifies the checkout revision and its four input hashes, then compares its regenerated table **byte-for-byte** with the bundled one. Source code stays in its original repository.
