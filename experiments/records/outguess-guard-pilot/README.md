# Guarded OutGuess diagnostic pilot

This is research preparation, not a published Have we tried it record. The plan and runner were committed as `4210429` before the fresh 20 October 2026 run. The archived guarded binary's hash matches its build record; both patched source files match their recorded hashes and exact edits after CRLF normalization. A separate clean build now reproduces all 13 pilot results, as described below.

## Fixed scope and result

Ten positive controls ran first, with the runner set to stop on a control failure. All ten matched their expected payload hashes. The same key, original JPEGs and 20-second timeout as the baseline were retained. Three further images were selected from known baseline outcomes, not randomly or as held-out cases.

| Image | Baseline | Guarded pilot | Byte comparison |
| --- | --- | --- | --- |
| LP1-06 | Exit 0, unverified output | Exit 0, unverified output | Same 58,152 bytes |
| LP1-05 | Exit 1, length rejection | Exit 1, length rejection | Same empty output |
| LP1-14 | Exit 3221225620 | Exit 1, explicit iterator guard | Same empty output |

LP1-14 reports `Guard: iterator skipmod zero at off=645437 bits=645682`. The explicit zero check precedes the remainder operation in the recorded iterator patch. This narrows the diagnostic for this guarded run; it is not a baseline crash stack trace, a finding about all 41 abnormal cases, or evidence that the image has no hidden data. LP1-06 remains unverified bytes despite an unchanged successful exit.

## Reproduce and audit

Run `python experiments/records/outguess-guard-pilot/check.py` from the repository to audit saved inputs, payloads and the comparison without executing OutGuess. To repeat retrieval with the exact declared binary, use:

```text
python experiments/records/outguess-guard-pilot/run.py --outguess /path/to/outguess --check
```

The runner requires the planned binary hash. A different binary is a different comparison. It does not fetch or install executable software.

## Build from source and compare

The build specification and comparison runner were committed as `e3921c5` before the clean binary's retrieval run. Using MinGW-W64 GCC 16.1.0 on Windows, `build.py` compiled all 54 C files afresh from upstream commit `24810e14327c2bbeedeaadd3e24491f2a4425c02`. It checks the checkout, applies the recorded portability and diagnostic patches, verifies normalized source hashes, and records compiler identity and commands. It does not download software or execute the resulting program during compilation.

Given a clean checkout of [the upstream source](https://github.com/resurrecting-open-source-projects/outguess/tree/24810e14327c2bbeedeaadd3e24491f2a4425c02) at that commit and an installed compatible GCC toolchain:

```text
python experiments/records/outguess-guard-pilot/build.py --source /path/to/outguess-source --output /path/to/new-build
python experiments/records/outguess-guard-pilot/compare_rebuild.py --outguess /path/to/new-build/outguess.exe --output /path/to/new-comparison
python experiments/records/outguess-guard-pilot/check.py
```

Both output directories must be new. The comparison command requires the exact executable hash recorded in `clean-build-report.json`; if a local build differs, retain its report and treat it as a separate build comparison rather than replacing the expected hash. The last command audits the committed evidence, not the new output directory.

The recorded clean executable has SHA-256 `bdc1810e59cb1152e7c3da88b38eaedfe49eba1656b4a4ab6f8c2b3f40126273`. It is not byte-identical to the archived executable. Nevertheless, all ten positive controls and three selected cases reproduce the same return codes, normalized diagnostics and exact payload byte streams. `clean-results/comparison.json` records those comparisons and binds them to the plan, archived report and clean-build report. The checker independently recomputes equality from the saved files.

This establishes behavior on these 13 inputs for this recorded build. It does not establish bit-for-bit reproducible compilation, behavior on other platforms, or equivalence on every possible input.

## Before publication

Prepare a reviewed experiment record and downloadable reproduction materials. Keep this pilot separate from any later 77-image sweep, and retain its preselected scope. No general success, payload-validity or hidden-data absence claim follows from these 13 cases. Human review remains pending.
