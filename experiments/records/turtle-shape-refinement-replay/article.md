The six later turtle-shape checks reproduce the source's empirical tail counts, and none passes its combined flag rule. This is a bounded followup to the existing 72-rule replay. It adds the source's selected 2,000-shuffle refinements, not another drawing family or a plaintext readout.

Each rune becomes a prime value or one-based prime index. The selected rule turns the turtle by that number modulo its stated modulus, either absolutely or relative to the previous heading, then steps by one unit or by the normalized value. The same 12,956-rune stream includes all 55 nonempty LP2 pages, without page resets. The frozen plan records the exact source functions, selected diagnostics, seeds, input hashes and planted controls before this fresh replay; the archived selections and results were already known.

The illustration shows the full ordered path and the first fixed shuffled path (seed 103301), using the prime-value, modulus-8, relative-turn, value-step rule. Both panels use the same drawing scale and the union of their coordinate bounds. The shuffle preserves rune frequencies. This picture illustrates what the detector compares; it does not certify a glyph.

The six selected diagnostics use four distinct path rules. The modulus-8 rule supplies three statistics from the same walk. Computing each shared series once produces 8,000 surrogate walks, rather than treating 12,000 scalar statistic evaluations as independent paths. Including four target paths and 402 planted-control paths, the run evaluates 8,406 walks; all have distinct full-coordinate hashes.

| Stream / modulus / turn / step | Measure | Empirical two-sided frequency | Gaussian tail | Both source gates? |
|---|---|---:|---:|---|
| Prime / 6 / absolute / unit | Symmetry | 0.002 | 0.126810 | No |
| Prime / 8 / relative / value | Raster fill | 0.002 | 0.00112484 | No |
| Prime / 8 / relative / value | Symmetry | 0 | 0.000414295 | No |
| Prime / 8 / relative / value | Components | 0.012 | 0.00000222564 | No |
| Prime / 12 / absolute / unit | Raster fill | 0.006 | 0.0101041 | No |
| Prime index / 6 / relative / unit | Raster fill | 0.012 | 0.00876753 | No |

The source requires an empirical frequency of zero AND a Gaussian tail below 0.01/(72 times 6), approximately 0.0000231481. The modulus-8 symmetry measure reaches the empirical floor but misses the Gaussian threshold. Its component count passes the Gaussian threshold but misses the empirical floor. No selected measure passes both.

All six empirical frequencies and all six false flags match the pinned ledger. Gaussian values are not a bit-exact archived replay: four tails differ beyond floating-point rounding, by at most 0.0000237632 in absolute terms. The frozen source functions and current recorded numerical environment produce the values above. This record does not establish the reason for the archived numerical differences; they do not change the six decisions.

An independent checker recounts all 12,000 selected saved tail samples, recomputes means and sample standard deviations, and checks Gaussian tails using erfc rather than the source's 1-erf expression. A separate existing implementation agrees on coordinates, raster pixels and selected statistics for 30 real, shuffled and control cases. The source's planted square triggers five statistics and its block-comb triggers two, meeting its phase-0 requirement of at least two. These controls establish that the implemented detector can respond to those plants; they do not validate its power for arbitrary hidden shapes.

Zero observed tail hits among 2,000 shuffles is a finite-sample frequency, not probability zero. Nonzero two-sided frequencies have a 0.001 increment, far above the corrected threshold. The Gaussian extrapolation assumes a suitable distribution and is especially questionable for discrete component counts. The source's tied-tail formula can exceed one and its closure/caging measures duplicate a ratio. Selection across 72 rules and six measures is retained in the source correction; this replay supplies no separately validated familywise probability. Other drawing rules and any decryption readout remain untested.

The bundled Python source is from Dukotah/cicada3301 commit f08b20b632d91209ddbaa747e8e2f23df0c78ba1, under its MIT license (included as LICENSE.source). The wrapper extracts and executes the pinned pure functions without running source top-level imports or network code. The source provenance, numerical reproduction and independent checks are distinct evidence.
