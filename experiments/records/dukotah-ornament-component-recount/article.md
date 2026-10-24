The frozen P-9 selection contains all 30 inventory boxes whose original n field is at most 16. A fresh count from 19 JPEGs matches the source's stored n_components in every box. Only 9 boxes match the old n field; 13 have more than 16 connected components. The fresh range is 0 to 341.

This measures a field-definition mismatch. The inventory's old n is an upstream catalogue field, not a validated glyph count. Connected components are also not glyph counts: touching strokes can merge, detached parts can split, and edge selection can omit ink. The measurement does not establish how many runes any box contains.

Before segmentation, plan.json froze all selected IDs, coordinates, expected JPEG hashes, parameters and stop rules. All 19 local images matched the pinned source target_renders SHA-256 values. run.py independently implements whole-page grayscale thresholding below 128, four-connected segmentation, minimum ink area six pixels, and the source's bounding-box overlap selection of at least half the component bounding rectangle area. Coordinates use exclusive component stops exactly as scipy.find_objects does.

check.py uses Python AST selection to execute only page_ink, labelled and comp_table from the bundled hash-verified reader source. It compares every selected component rectangle and pixel area with the independent run, then checks the stored counts. It does not import the full reader, load its missing templates, or run its glyph decoder. A small synthetic topology/minimum-area control is also checked. The source snapshot is pinned to f08b20b632d91209ddbaa747e8e2f23df0c78ba1.

These exact image measurements support the saved component counts and reject treating the old low-n filter as a count of at most sixteen glyphs. They do not support the stronger source verdict that a hidden artwork channel is absent. The separate fresh ornament reader gate reached 83.4%, below its 90% threshold, so no band text reading or decoding is attempted here. A new validated reader and appropriate controls would be needed for a content test.

Reproduce offline from the repository root after supplying the declared original image bundle:

    python experiments/records/dukotah-ornament-component-recount/run.py --check
    python experiments/records/dukotah-ornament-component-recount/check.py
    python experiments/records/dukotah-ornament-component-recount/plot.py --check
