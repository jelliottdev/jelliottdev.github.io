## The comparison

The pale tree on [LP2-55](#/reader/lp2-55) resembles the photograph [DeadTree.jpg](https://commons.wikimedia.org/wiki/File:DeadTree.jpg), credited to R. Neil Marshman / Brookie. This test asks a narrower, checkable question: when the source photograph is scaled and translated over the manuscript tree, does a horizontal reflection fit better than its original orientation? It does **not** seek a decryption rule or recover the original image-editing steps.

The published [Commons original](exports/sources/commons/DeadTree.jpg) is 1,894 × 2,606 pixels. Its local SHA-256 is `608288991f92b8ab901a9fbb39937f93ebdfeb5fd84edeecfa637d5262ff7b29`; its SHA-1 matches the checksum on the [Commons file record](https://commons.wikimedia.org/wiki/File:DeadTree.jpg). The LP2-55 JPEG is the archived 2,400 × 3,600-pixel page. The script rejects either image if its bytes change.

![Mirrored source, pale manuscript tree and their half-opacity overlay](exports/figures/dead-tree-alignment.png)

The figure shows the selected mirrored fit at left, the LP2-55 tree region in the middle and a 50% overlay at right. Both source and manuscript are converted to grayscale response maps, enlarged for inspection; this is **not** an unmodified image or a reconstruction of the author’s layer. The source is R. Neil Marshman / Brookie, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), horizontally reflected, cropped, resized, threshold-mapped and blurred here. [Open the original photograph](exports/sources/commons/DeadTree.jpg) · [Open the unmodified manuscript page](images/lp2-55.jpg).

## Frozen comparison rule

The source crop is `[100, 500, 1750, 1950]`; the LP2-55 crop is `[550, 1300, 1850, 2550]`, with right and bottom edges excluded. In each grayscale crop, values darker than the chosen brightness level become a stronger tree response. The source uses `clip((170−L)/130,0,1)` and the manuscript `clip((250−L)/45,0,1)`. Gaussian blur with sigma 7 tolerates differences in stroke width and some missing twigs. Those values were chosen after inspecting the images, so the following scores are descriptive rather than a blind significance test.

For each orientation, the script checks 23 scales from 0.370 through 0.700 in increments of 0.015, plus every integer translation that keeps the whole template inside the manuscript crop. The fit score is normalized cross-correlation. In a second run, only the upper 60% of the source template chooses the transform; the lower 40% is scored at that fixed transform. This lower-region check tests whether the upper-branch fit extends further down the same image. It is not a wholly independent holdout because the photograph, crops and processing were selected after viewing both images.

| Orientation | Best whole-crop correlation | Upper 60% fit | Lower 40% at that fit |
| --- | ---: | ---: | ---: |
| Original | 0.377 | 0.564 | −0.095 |
| Horizontal reflection | **0.623** | **0.813** | **0.456** |

The reflected upper fit uses scale 0.550 and translation `(230,94)` relative to the LP2-55 crop. Its major forks, central branch structure and rightward lower limb overlap in the visualization. The unreflected comparison does not carry its upper fit into the lower region. [Download every scale, coordinate and score](exports/dead-tree-alignment.json).

## What this establishes and what remains open

The two declared alignments favor a horizontally reflected source photograph, including the lower region that did not choose the fit. This supports a specific image-source relationship more strongly than a general resemblance between bare trees. The test does not calculate a chance probability against a collection of other tree photographs. It does not establish the exact crop, layer opacity, drawing/filter steps or software used to make LP2-55. Fine branches and the lower trunk differ visibly in the overlay.

The [branches guide](#/wiki/branches?section=shared-tree) compares the related treatments on LP2-32 and in the 2016 message. Those carriers are **not** fit by this script; each would need its own frozen crop and control comparison. Nothing in this image alignment implies a rune operation.

## Reproduce

Download the [experiment bundle](downloads/experiments/dead-tree-alignment.zip) and extract it preserving folders. It contains the [Commons original](exports/sources/commons/DeadTree.jpg). Download the [LP2-55 original](images/lp2-55.jpg) separately or extract the original-images ZIP into the same folder. Install Python 3, NumPy and OpenCV (`opencv-python`); the recorded run used OpenCV 5.0.0. Verify the files using the bundled `START-HERE` instructions, then run:

```text
python experiments/records/dead-tree-alignment/run.py --check
```

To regenerate a report and figure under other settings, edit a **copy** of the script and save separate outputs. Report altered crops, thresholds, blur, scale range and orientation choices. The exact source file, [plan](experiments/records/dead-tree-alignment/plan.txt), [script](experiments/records/dead-tree-alignment/run.py), [results](exports/dead-tree-alignment.json) and [visualization](exports/figures/dead-tree-alignment.png) are linked here for inspection.
