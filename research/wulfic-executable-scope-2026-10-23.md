# Wulfic executable-source scope after the stage runner queue

Pinned tree: [`bf89d3d13aad2b8f2c95ab195cf1b092f250775c`](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c). This is an internal intake note, not a claim that all public Liber Primus experiments have been replayed. The tree contains **20 `tools/run_stage_*.py` programs**, **27 Python test files**, and **107 archived `tools/legacy/*.py` scripts** (`git ls-tree`, including files absent from the sparse checkout).

The stage-runner queue is reconciled at the stated executable scope: AA, AB, AC, AD, AE, AF, AG, AH, I, M, N, R, T, U, V, W, X1–X4, Y and Z have published bounded records. Stage S's full 200-setting source replay is recorded in `research/wulfic-stage-s-receipt-2026-10-23.md`; its original negative-control gate is void. A family may be only partly excluded; a source runner's presence in a record does not imply every model variant is ruled out. X1 and X3 share `wulfic-grid-rsa-modulus-screen`. S's 50 raw-byte LP2 scores already overlap the valid W record.

**Earlier executable analyses outside `run_stage_*.py` still require source-specific reconciliation:**

| Source stage / location | Existing finite method | Intake status |
| --- | --- | --- |
| H, O · `tests/test_leak.py`, `tools/lpcore/leak.py` | Surviving adjacent doublets, period/line controls, key-switch and skip-next rule (C6–C8, C14) | Grouped draft `wulfic-doublet-leak-h-o`: sixteen source assertions and all 12,947 pair rows independently checked; not yet published. |
| J, K, L · `tests/test_keyspace.py`, `tools/lpcore/stats.py` | English running-key distribution (C10), ciphertext-autokey lags 2–1000 (C11), ciphertext-selected alphabets/transition χ² (C12), key alphabets (C13) | Published `wulfic-early-keyspace-diagnostics`: thirteen source assertions and all 3,029 manuscript results independently checked. AC/AD use distinct statistics. |
| Q · `tests/test_leak.py` (`TestC3MarkerLetter`), `tests/test_stats.py` (`TestHomophonic`), `reference/findings/lp2_logic_findings_2026-09-29.md` | Constraint register, including rune-letter exclusions C3 and homophonic-substitution bound C15 | Published `wulfic-letter-encoding-bounds`: six source tests, 29 marker checks and an independent homophone-allocation calculation. |
| A–D, F–G · canonical loader, rebuild utility and documentation | Corpus, provenance and corrections rather than additional solving sweeps | Treat as reference/source checks, not extra failed experiments. |

The **107 archived scripts are not a replayed set**. `tools/legacy/README.md` says many read pre-2026-09-29 misaligned page data; a static scan finds 78 with literal old page paths and 50 with parent-directory assumptions (overlapping sets), and most are optimizers with outputs archived separately. They require an individual method-and-input audit, canonical input migration, declared success rule, and controls before any result can be used. Their file count is neither 107 independent ideas nor evidence that their historical outcomes hold. The two other top-level `tools/*.py` programs, `rebuild_page_files.py` and `add_contributor.py`, are respectively a corpus maintenance and contributor utility, not decryption campaigns.

J/K/L is published; the H/O draft awaits release review. Legacy scripts should be triaged for runnable exact methods, without turning archived optimizer output into negative evidence.
