# Measuring the reported large line gaps

A supplied analysis reports **109 blank pixels** in a large gap between rune rows, against **73** in an ordinary gap, with a **129-pixel** exception on the parable page. We measured fixed rune-text regions on two of its listed large-gap pages (LP2-04 and LP2-35), the named exception (LP2-57), and one of its ordinary-gap comparison pages (LP2-14). This is a check of the visible spacing claim, not a whole-book census.

![Gap widths in four fixed page regions; three listed large-gap pages each have one wide gap, while the comparison region does not.](experiments/records/large-gap-pixel-replay/gap-measurements.svg)

The [original LP2-04 image](#/reader/lp2-04) has one **109-pixel** clear gap among eleven measured gaps; the others are **73–75**. [LP2-35](#/reader/lp2-35) has one **110-pixel** gap among eleven, and [LP2-57](#/reader/lp2-57) has the reported **129-pixel** exception among four. The [LP2-14 comparison region](#/reader/lp2-14) has six gaps, all **73–75**. These are counts of wholly blank horizontal pixel rows, not baseline distances. The full [results](experiments/records/large-gap-pixel-replay/results.json) include every ink-row coordinate. Repeating the measurement at grayscale cutoffs 100, 160 and 200 leaves all four gap lists unchanged.

This supports the *existence and scale* of the exceptional spacing on the selected archived images. The one-pixel difference on LP2-35 shows why a single exact width should not be applied to every page. The forum text does not include the original screenshot coordinates, so our rectangles and pixel rule are a declared independent measurement, not a reconstruction of the author's Canva selections.

The reason for the extra space remains open. The selected pages have different content and layouts. This measurement neither verifies the post's full 16-page classification nor shows that punctuation, numbers, a particular font or a cipher caused the gap. It also supplies no bit-reading rule.

Reproduce from the repository root with `python experiments/records/large-gap-pixel-replay/run.py --check`, `python experiments/records/large-gap-pixel-replay/check.py`, and `python experiments/records/large-gap-pixel-replay/plot.py --check`. The second script independently reduces flat pixel rows and compares every box at all three thresholds.
