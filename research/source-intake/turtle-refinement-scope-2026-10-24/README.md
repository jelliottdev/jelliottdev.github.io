This intake completes the six later R22 turtle refinements only. The baseline already covers the 72-rule, 200-shuffle screen. The new draft is experiments/records/turtle-shape-refinement-replay/record.json, grouped under the existing lp2-turtle-spatial-replay family.

Frozen plan: plan.json; exact pinned source pure functions and MIT license are bundled. Benchmark: 40 full walk/detector cases in 0.466 seconds, estimating 93 seconds for 8,000 null walks. The full run then completed. The six diagnostics share four seeded surrogate series (three diagnostics use the identical M8 walk), giving 8,000 null paths, four target paths and 402 control paths, all 8,406 coordinate digests distinct.

All six empirical tails and false source flags agree with the pinned ledger. Four Gaussian tails differ beyond rounding, max absolute difference 0.0000237632; no exact numerical Gaussian parity is claimed. Both plants pass. Thirty independent path/raster/selected-stat checks pass, and check.py independently recounts the 12,000 selected sample values and Gaussian decisions. Empirical p=0 is not probability zero. Source multiple-selection correction and Gaussian assumptions remain explicit.

The SVG compares a full actual selected path and the first fixed shuffle, on the same coordinate scale. Preview PNG is for visual QA only. It is an illustration, not glyph recognition.

Isolated artifact: isolated-reproduction.zip includes the declared dependencies and record; isolated-reproduction/ is its extracted scratch. check.py and plot.py pass there. Full target replay is not rerun solely for packaging. From extraction root:

python experiments/records/turtle-shape-refinement-replay/run.py
python experiments/records/turtle-shape-refinement-replay/check.py
python experiments/records/turtle-shape-refinement-replay/plot.py

Only the draft record directory and this intake were authored. No shared catalogue, build or commit was changed. Root adds identical family metadata to the baseline. Intake ZIP and extracted scratch are QA artifacts, not public record dependencies; exclude them from publication if unnecessary.
