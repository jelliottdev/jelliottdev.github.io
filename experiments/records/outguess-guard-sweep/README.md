# Guarded OutGuess: full baseline comparison

This plan extends the 13-case diagnostic pilot to the complete original 77-image baseline. It retains all original image hashes, the literal default key and 20-second timeout. The ten known positive controls run first; a failed control stops the sweep. This is not a new key search or authentication of candidate output.

The executable is the recorded clean build in `../outguess-guard-pilot/clean-build-report.json`; its source build instructions are in that directory. The pilot cases are included, not treated as unseen validation.

Run from the repository root, with a new output directory:

```text
python experiments/records/outguess-guard-sweep/run.py --outguess /path/to/outguess.exe --output experiments/records/outguess-guard-sweep/results
```

Retain every output and diagnostic, including differences from the baseline. Compare payload bytes directly. Do not count an explicit guard rejection as proof that an image contains no hidden data. The original baseline executable is unmodified; a changed guarded diagnostic does not establish a baseline crash stack trace.
