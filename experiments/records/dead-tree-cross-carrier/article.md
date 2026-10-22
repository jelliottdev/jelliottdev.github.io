## One source family, two different treatments

The [LP2-55 source comparison](#/experiments/dead-tree-alignment) favored a horizontally reflected version of R. Neil Marshman’s [DeadTree.jpg](https://commons.wikimedia.org/wiki/File:DeadTree.jpg). Two related images remain: a broad, soft tree on [LP2-32](#/reader/lp2-32), and a faint tree behind text in the [2016 message](images/message-2016.jpg). This record measures them separately. The first comparison uses LP2-55 as the reference image; the second returns to the Commons photograph. It does not assume identical blur, brightness or scale across carriers.

The result supports the shared tree artwork under the declared comparisons. It does not recover how the author processed any image, prove a decryption step or assign a probability of chance resemblance across other photographs.

## LP2-55 → LP2-32: same orientation

The script compares the tree region of two original 2,400 × 3,600 JPEGs. It maps their differently rendered dark and pale shapes to grayscale responses, blurs with sigma 15 and searches scales 0.650–1.225 in 0.025 steps. It searches every integer translation keeping the source crop fully inside the LP2-32 crop. Both the original LP2-55 orientation and its horizontal reflection are scored.

![LP2-55 tree aligned to LP2-32, with target and overlay](exports/figures/dead-tree-manuscript.png)

The displayed panels are contrast-mapped and blurred for this comparison; open the [unmodified LP2-55](images/lp2-55.jpg) and [LP2-32](images/lp2-32.jpg) images to inspect the real artwork. The unchanged orientation aligns the broad top forks and carries more of that alignment into the lower trunk. The figure shows its upper-region fit and a half-opacity overlay, not an original image layer.

| LP2-55 orientation | Whole-region best | Upper 60% fit | Lower 40% at upper fit |
| --- | ---: | ---: | ---: |
| Same | **0.623** | **0.704** | **0.600** |
| Horizontally reflected | 0.483 | 0.514 | 0.353 |

The same-orientation upper fit uses scale 0.900 and translation `(123,186)` inside the LP2-32 crop. This says that the two *manuscript treatments* preserve orientation relative to each other. It does not contradict the preceding experiment, where both were compared with an originally unreflected photograph.

## Commons photograph → 2016: reflected orientation

The 2016 JPEG is only 563 × 569 pixels and puts pale message text over a very dark tree. The script crops the central tree, maps pixel brightness above the black background to a response, and masks pixels brighter than 100 to reduce the white lettering. It uses Gaussian sigma 1.5 and searches 26 scales from 0.065 to 0.140. The source photograph’s original and horizontally reflected orientations are both compared.

![Mirrored Commons tree aligned to the faint 2016 background tree, with target and overlay](exports/figures/dead-tree-message.png)

This figure increases contrast and removes much of the bright text **for inspection only**; it is not the original message. The source photograph is R. Neil Marshman / Brookie, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), cropped, mirrored, resized and contrast-mapped here. [Original Commons JPEG](exports/sources/commons/DeadTree.jpg) · [original 2016 message](images/message-2016.jpg).

| Photograph orientation | Whole-region best | Upper 60% fit | Lower 40% at upper fit |
| --- | ---: | ---: | ---: |
| Original | 0.566 | 0.644 | 0.442 |
| Horizontal reflection | **0.854** | **0.826** | **0.858** |

The reflected upper fit uses scale 0.089 and translation `(69,29)` within the message crop. The lower region matches at that fixed transform despite not setting the transform in the declared search. The photograph, crop, text mask and response were still chosen after seeing the images, so these correlations are descriptive, **not** a calibrated chance probability.

## Bounds, files and next checks

The [complete result JSON](exports/dead-tree-cross-carrier.json) records both orientations, 24 and 26 scale values, crops, settings, coordinates and scores. This is one family of related source-image comparisons, not a blanket assertion that every tree image was made with the same filter. Fine branches and the amount of visible trunk vary. No source was inferred from manuscript text or rune values.

The lower 40% check is useful but not fully independent: all preprocessing choices and the two target images were selected during exploration. A stronger source-identification test would score a preregistered set of unrelated tree photographs under the same search budget and report the winner and gap. An exact production reconstruction would need to explain the tonal treatment and branch omissions as well as geometry. Those questions remain open.

Download the [experiment bundle](downloads/experiments/dead-tree-cross-carrier.zip); it contains the Commons photograph, plan, script, report and figures. Place the original LP2-55, LP2-32 and 2016 JPEGs in its `images/` directory, or extract the site’s original-images ZIP there. Install Python 3, NumPy and OpenCV (the recorded run used OpenCV 5.0.0), verify the bundled files and image hashes using the `START-HERE` instructions, then run:

```text
python experiments/records/dead-tree-cross-carrier/run.py --check
```

The [plan](experiments/records/dead-tree-cross-carrier/plan.txt) lists every input and preprocessing choice. Edit a copy and save separate results for any changed crop, mask, threshold, scale range or image set. The [script](experiments/records/dead-tree-cross-carrier/run.py) does not access a network or AI service.
