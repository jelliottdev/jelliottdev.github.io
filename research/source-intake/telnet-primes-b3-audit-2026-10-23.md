# 2013 telnet missing primes: B3 source audit

This is internal provenance work for the `historical-prime-and-ps-keys` replay. The original 2013 hidden-service command is unavailable. The following are archived copies and source code, not a new live verification of the service.

| Item | Pinned source | SHA-256 of retrieved raw bytes (2026-10-23) | Finding |
| --- | --- | --- | --- |
| Later preserved `primes` command transcript | [2013 first-onion README at `ade9a028`](https://github.com/neuroretransmit/cicada/blob/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2013/004-first-onion/README.md) | `677eb388bb85530e7137e0dea22896dd3ead1a805b11b6a0dece14a05d395a8e` | Output jumps from 71 to 1229; two doubled spaces occur at 29→31 and 3257→3259. |
| Archived CicadaOS `prime_echo` script | [script at `c3127e0e`](https://github.com/cicada-solvers/The-Complete-Cicada3301-Archive/blob/c3127e0e9eb5afbb582d37988d6369fe38429238/2013/additional%20files/Cicada%20OS/cicados/usr_local_bin/prime_echo) | `1ab3a8f4520a3d93784aea137847e0c7f77d9fff4df02d481b62d13280753350` | Prints 73, 79, and all subsequent primes through 1223. It is a different artifact from the telnet command. |
| B3 executable and saved result | [program at `f08b20b6`](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/b3_hints.py) | Exact copies and hashes are in the experiment plan | Generates every prime from 73 through 1223, 180 terms, then their 179 adjacent differences. |

The missing set is **the 21st through 200th primes inclusive: 73–1223, 180 terms**. The phrase “about 200 missing primes” is imprecise. A published secondary note that calls this a CicadaOS gap conflates the telnet and OS outputs; use the separate artifact names when documenting it. `articles/2013-opening.html` and `articles/2013-twitter-gematria.html` do not presently claim that CicadaOS omitted these primes, so no existing article correction was needed in this pass.

The B3 source does not test the 2013 onion-cookie hashes or OpenPGP packets. Its exact grid is nine streams × 55 unsolved rune segments plus their joined stream × two signs × Atbash on/off × F interruption on/off = 4,032 decodes. The source file reports only the maxima; Liberpedia's checker reconstructs the full case ledger. Its score gate is a heuristic and has no full-search null calibration.
