# LP2 red-initial source audit

The [Round 22 illustration experiment](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/D-illustration-dropcap/RESULTS.md) reports red drop-caps on 15 of 58 LP2 pages. Its [extractor](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/D-illustration-dropcap/extract_illustration.py) decides `has_dropcap` solely from the **total** number of red pixels on a page. The threshold is 30,000 pixels. The same script computes connected components but does not use them for that decision.

We measured the same red predicate on Liberpedia's 58 original LP2 JPEGs. All **58 red-pixel totals match** the pinned source's [feature table](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/D-illustration-dropcap/features.json) (SHA-256 `9c75e8b21c38aba614fb83fc8911f3e1b6febccd16b6489a950f7313568f6bb0`). The source rule again selects the same 15 pages. We independently measured four-connected red components at half resolution and multiplied component areas by four to give full-resolution-equivalent areas. A 10,000-pixel component threshold selects **13 pages**. In this archived image set, the largest component on a nonselected page is 3,208 pixels; the smallest selected component is 24,764. The 10,000-pixel cut falls inside that observed gap. It was chosen after inspection and is an exploratory classification rule, not a preregistered cipher test.

| Page | Total red pixels | Largest red component, approximate | Visual inspection |
| --- | ---: | ---: | --- |
| [LP2-07](../images/lp2-07.jpg) | 30,160 | 2,988 | Small red closing line; no large initial. |
| [LP2-53](../images/lp2-53.jpg) | 100,933 | 3,208 | Three lines of small red runes; no large initial. |

The 13 pages with large connected red initials are **00, 03, 06, 08, 15, 23, 27, 33, 39, 40, 54, 56 and 57**. A contact-sheet visual check confirms all 13 show a large red initial. LP2-03 and LP2-33 each show **two** large initials. LP2-06, LP2-15 and LP2-39 show an initial below earlier page content. Thus a single “first rune of the page” does not completely encode the visible large-initial channel even after repairing its page list.

This finding concerns the **feature extractor**, not whether a red-initial sequence encodes a message. The source's 15-page bitstring, gap statistics, and quoted initial-rune string depend on its misclassified inputs or incomplete one-initial-per-page representation. Its reported shuffle calculations may be reproducible for that **selected data**; they cannot be carried over unchanged to the corrected set. The [separate corrected page-order record](../experiments/records/red-initial-presence-order/article.md) now tests placement of the 13 pages under its own declared control. A replacement initial-identity or large-shape-centroid test still needs a rule for multiple and later initials.

Reproduce the image audit from the repository root with Python 3 and `Pillow`, `numpy`, and `opencv-python-headless`:

```sh
python scripts/audit_red_initials.py > research/red-initials-audit.csv
```

The [58-row CSV](red-initials-audit.csv) records each archived JPEG's SHA-256, total red count, largest red component, large-component count and both classification rules. The [audit script](../scripts/audit_red_initials.py) uses the source's exact red predicate but an independently implemented component measurement at half resolution. The image bytes and their provenance are available through the [original-image downloads](../downloads/original-images.zip). The half-resolution component area is an approximation; it is sufficient to separate these two groups by a factor of over seven.

The source's four hand-check controls cover pages 00, 08 and 15 as positive and 09 as negative. They do not include 07 or 53. This is a concrete example of why a positive control must probe the failure mode of the detector, not merely confirm examples far from its decision boundary.
