# Do marked lines sit above the large gaps?

One report links unusually tall spaces between LP2 rune lines to an apostrophe, quotation mark or numeral on the line **above**. That is more specific than saying the marked pages have unusual spacing somewhere. We aligned text rows with measured image rows on five pages named by the report and one comparison page. The regions were fixed in the [plan](experiments/records/large-gap-mark-alignment/plan.json); this is a selected, local check rather than a whole-book survey.

![Six source-guided marked lines are each followed by a 108–110 pixel gap; 28 unmarked lines in the measured regions have 73–75 pixel gaps.](experiments/records/large-gap-mark-alignment/mark-gap-alignment.svg)

The six marked lines in the reviewed page text are LP2-04 line 8 (apostrophe), LP2-07 line 1 (quotation mark), LP2-10 line 8 (the numeral 7), LP2-35 line 4 (apostrophe), and LP2-42 lines 3 and 6 (quotation marks). Each has a **108–110-pixel** blank interval directly below it. The other **28** measured gaps on those pages and the LP2-14 comparison are **73–75 pixels**. The same row boxes and widths reproduce at three grayscale thresholds: 100, 160 and 200. [Results](experiments/records/large-gap-mark-alignment/results.json) give every line and gap coordinate.

LP2-35 shows why the text version matters. Its original image has a small upright punctuation mark on line 4, and the stored **reviewed** text records an apostrophe there. The archived **raw** text omits it. A literal search of the raw text would therefore find five of the six marked wide-gap lines and classify LP2-35 as an unexplained wide gap. The correction is already documented in the [transcription decisions](#/wiki/transcription-decisions?section=review-lp2-35); this experiment measures its effect on a concrete image/text alignment.

![Original LP2-35 line-four crop showing the narrow upright punctuation mark among the runes.](experiments/records/large-gap-mark-alignment/lp2-35-apostrophe.png)

This alignment is strong **within the six selected regions**, but it does not establish why the extra space appears. The pages and marker lines came from a report proposing the association; they were not sampled blindly. Letter shapes, font fallback or manual layout could produce the same observation without encoding a message. The 129-pixel parable exception and number-panel spacing are outside this test, as are punctuation marks elsewhere in the book.

Reproduce from the repository root with `python experiments/records/large-gap-mark-alignment/run.py --check`, `python experiments/records/large-gap-mark-alignment/check.py`, and `python experiments/records/large-gap-mark-alignment/plot.py --check`. The checker independently reads the archived and reviewed page records and reduces flat grayscale pixel rows.
