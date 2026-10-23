# Stage S complete source replay: matching rows, void gate

Pinned source: [`Wulfic/Cicada3301-Liber_Primus` at `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c), `tools/run_stage_s.py`. Frozen [plan](wulfic-stage-s-replay-plan-2026-10-23.md), internal [machine-readable receipt](wulfic-stage-s-receipt-2026-10-23.json), and [verifier](wulfic-stage-s-verify.py). The six-worker replay wrote only to an external temporary directory and did not change source methods or files.

All **200 candidate rows** (20 key classings × 10 alignments) and **260 control rows** (120 planted positives, 120 negatives, 20 LP2 shuffled-key nulls) match their pinned Git objects **byte-for-byte**. The two SHA-256 digests are in the JSON receipt. The source control file is absent from the sparse working checkout but present as a pinned Git object; the verifier compared against that object directly. The original script finished normally and printed `PASS ... 0` for scores reaching +30.

The largest LP2 candidate score is **+0.84**, below the source's **+30** screen. However, one 12,956-rune **negative** using `liber_al_vel_legis letters`, seed 0, scored **+53.49**. This violates the source's declared negative-control gate. Consequently the complete run is **void**, and **zero model exclusions** can be taken from it, regardless of how low individual LP2 scores are. This reproduces the source's own Run 2 warning; it does not repair its calibration or support a broader negative conclusion. The smallest planted-positive score was −1.44, which also shows that some settings lacked power. Stage W's separately calibrated 50 raw-byte settings remain the valid overlapping result and are already documented publicly.

Reproduction from the Liberpedia checkout, with a pinned source checkout and an output directory outside either checkout:

```text
python research/wulfic-stage-s-replay.py --source PATH_TO_WULFIC --output PATH_TO_TEMP_OUTPUT
python research/wulfic-stage-s-verify.py --source PATH_TO_WULFIC --output PATH_TO_TEMP_OUTPUT --receipt research/wulfic-stage-s-receipt-2026-10-23.json
```

The wrapper changed only worker count and output paths. The second command checks both full TSV files byte-for-byte, validates the 20 × 10 and 260-row grids, and recomputes the void control independently. No additional public record is needed: the existing [Stage W experiment](../experiments/records/wulfic-position-alphabet-long-keys/article.md) explains the S/W distinction, and a separate page would imply a usable negative result where the control gate failed.
