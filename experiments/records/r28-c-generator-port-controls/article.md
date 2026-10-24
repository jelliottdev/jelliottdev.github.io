# Can the compiled generator ports reproduce their reference streams?

**Finding.** The pinned Round 28 C generator code matches all **144,000 symbols** in a finite Python-model comparison, and all **8,192 symbols** in the earlier Round 27 archived reference vectors. A separate checker reproduces every symbol using independently constructed expectations. This validates the extracted generator code on this finite grid.

![All finite C generator comparisons match exactly.](experiments/records/r28-c-generator-port-controls/port-checks.svg)

We compiled the unmodified generator and reducer region of [the pinned source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round28/L4/grind28.c) in a small portable harness. The full sweep engine requires POSIX functions and an unavailable language-panel file; this harness only calls its generator functions.

The grid contains nine output modes and eight fixed seeds: 0, 1, 777, 3301, 123456789, 2147483647, 2147483648 and 4294967295. Each emits 2,000 symbols, crossing MT's 624-word state reload several times. The modes are Python 2.7 single-word MT with random29, five-bit modulo, five-bit rejection and shuffle29; canonical and historical PHP MT with scaling or modulo; and glibc's additive generator modulo 29. The archived comparison separately tests the first 128 random29 symbols for all 64 Round 27 reference seeds.

Both PHP twist modes produce different streams for every tested seed. This matters because checking the canonical twist does not establish that the historical PHP generator was implemented correctly. The independent checker uses the standard-library MT engine with an explicitly constructed state for canonical PHP, a separate historical-twist implementation, and an unbounded history recurrence for glibc rather than the source's ring buffer. The familiar MT19937 seed-5489 reference also passes.

This is a **generator-port control**, not a decoding control or a manuscript result. It does not rerun native PHP, native glibc or Python 2.7; the native-runtime assertions in the source remain source-reported evidence. It does not reproduce the language scores, plant-recovery gates, full seed spaces, checkpoint behavior or the source's LP2 negatives. In particular, no fresh coverage is assigned to the orphaned Round 28 run.

Run offline from the repository root with Python 3 and GCC:

```bash
python experiments/records/r28-c-generator-port-controls/run.py
python experiments/records/r28-c-generator-port-controls/check.py
python experiments/records/r28-c-generator-port-controls/plot.py --check
```

All source files and the MIT license are bundled. Generated executables live only in a temporary directory. The checker recompiles the C region and checks every emitted symbol and saved digest.
