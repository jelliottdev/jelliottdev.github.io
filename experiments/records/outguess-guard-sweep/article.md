# Original JPEGs: guarded OutGuess build comparison

## What this test asks

The original default-key sweep had 41 abnormal exits. Those failures leave an important question: did the retrieval reach an identifiable error condition, and would a more explicit check change the extracted bytes?

This variant uses a clean build with three diagnostic guards. A guard checks a condition before an operation that would otherwise be invalid and stops with an explanatory message. Here the checks concern the retrieval bit position, iterator capacity, and a zero iterator value used by a remainder operation. They are diagnostic changes, not a new decryption method.

The [original baseline](#/experiments/outguess-default-key) remains available with its unchanged results. Both records belong to the same experiment family.

## What stayed fixed

The inputs are all 75 manuscript JPEGs plus the 2014 opening image and compasses cover, in their original bytes. Image hashes, the literal key `Default key`, and the 20-second timeout match the baseline. No image was recompressed or edited. The ten known payload controls run first; a control failure would stop the sweep.

The scope and runner were committed as `40890c5` before execution. The earlier 13-case pilot helped establish the build procedure; those cases are included here and are not presented as unseen validation. This is one complete 77-image comparison, not a search over keys or build settings.

## What changed

The recorded executable was compiled afresh from upstream commit `24810e14327c2bbeedeaadd3e24491f2a4425c02`, with the documented Windows portability changes and explicit guard patches. All 54 C files were compiled; object files from the original build were not reused. The build specification records compiler identity, source hashes and commands.

The clean guarded Windows executable has SHA-256 `bdc1810e59cb1152e7c3da88b38eaedfe49eba1656b4a4ab6f8c2b3f40126273`.

The clean executable differs in hash from the archived pilot executable, although it reproduced all 13 pilot results exactly. The full comparison below uses the clean executable. This does not establish bit-for-bit reproducible compilation across toolchains.

## Results

| Baseline outcome | Guarded outcome | Images |
| --- | --- | ---: |
| Successful exit | Same successful exit, diagnostic and bytes | 31 |
| Existing rejection | Same rejection, diagnostic and bytes | 5 |
| Abnormal exit | Explicit zero-iterator guard; unchanged empty output | 41 |

All ten positive controls match. The 31 successful exits consist of those ten controls and 21 unverified outputs. Every one of the 77 payload byte streams matches the baseline exactly; no new candidate output appeared.

All 41 changed cases report `Guard: iterator skipmod zero`, with their individual bit counts and offsets retained in the saved report. For example, LP1-14 reports `Guard: iterator skipmod zero at off=645437 bits=645682`. The guarded build checks this zero value before the iterator's remainder operation.

The [comparison graphic](experiments/records/outguess-guard-sweep/results/comparison.svg) summarizes the counts. The [per-image comparison](experiments/records/outguess-guard-sweep/results/comparison.json) and [complete diagnostics](experiments/records/outguess-guard-sweep/results/report.json) retain the underlying evidence.

## What the result means

The new build gives a specific diagnostic for all 41 previously abnormal cases. This is useful for investigating the implementation and for preventing those failures from being mistaken for clean negative results.

It does not authenticate the 21 candidate outputs. It does not prove any image lacks hidden data. Both executables share the same upstream source and Windows port, so this is not validation by an independent implementation or another platform. The guarded run is also not a captured stack trace from the original executable.

## Reproduce the saved comparison

Download this experiment's bundle and the original-images archive, then extract both into the same folder, preserving their paths. Follow the bundle's START-HERE file to verify the archive and required image hashes. From that folder run:

```text
python experiments/records/outguess-guard-sweep/compare.py --check
```

This needs Python and the supplied data, but does not execute OutGuess. It verifies the plan dependencies and image hashes, checks both sets of saved outputs, and compares bytes and diagnostics directly. It recomputes the saved comparison instead of trusting its reported equality flags.

To regenerate the chart after that audit:

```text
python experiments/records/outguess-guard-sweep/figure.py
```

## Repeat retrieval from a source build

Supply a clean checkout of the pinned upstream source and a compatible MinGW-W64 GCC toolchain. The included build script does not fetch or install these dependencies. Choose an output directory that does not yet exist:

```text
python experiments/records/outguess-guard-pilot/build.py --source /path/to/outguess-source --output /path/to/new-build
python experiments/records/outguess-guard-sweep/run.py --outguess /path/to/new-build/outguess.exe --output /path/to/new-results
```

The runner requires the recorded executable hash. If compilation produces a different hash, preserve its build report and define a separate comparison; do not overwrite the expected hash to make the check pass. The new-results directory must not already exist. The saved-evidence audit above checks the committed results, not this new directory. To rerun retrieval and compare directly with the committed results, use `run.py --outguess /path/to/new-build/outguess.exe --check`.

## Remaining work

Human review is pending. An independently documented platform or implementation would address a different uncertainty from the guard comparison. Candidate-payload analysis should be a separate bounded experiment, retaining all outputs and avoiding the assumption that process success implies a message.
