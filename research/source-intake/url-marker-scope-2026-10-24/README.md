# Literal web-marker affine readout

Draft ready for root review: `experiments/records/url-marker-affine-census/record.json`.

This completes one fixed literal readout within the already published 812-map GP29 affine key grid. It does not add a new keyspace, a URL recognizer or a new source-entry count. The original page/input plan was frozen before target counting; its SHA256 remains 335c2e6829eae6ae03a54acdeb28c37f5b7e959430b889f174328824915ee1f5.

The sole underlying window/key is LP2-36, rune start 226, `a=24,b=28`: indices 4,14,14,3,20 decode to HTTPS. HTTP is the same window's prefix, so the two token rows are not independent candidates. WWW 0 and ONION 0. Exact match rows include all page/key/start coordinates, cipher and decoded indices, source line/raw-column locations, and eight-rune-flank snippets. All non-rune separators are explicitly removed, and no punctuation or hostname syntax is inferred. A lone five-rune marker confirms neither URL nor plaintext.

Original streams contain no equal-symbol triples. Since every bijective substitution preserves equality, literal WWW is impossible under any static bijective single-rune map in these page streams. This invariant does not exclude addresses lacking WWW, changing maps, hidden layers or transpositions. ONION's absence extends only across the 812-map affine grid.

The source scanner and independently implemented complete decoded-stream substring checker both pass 3248 planted map/token controls at fixed offset 8. The independent checker covers 45,472 page/map streams, including 812 empty LP2-50 cases (44,660 nonempty outputs), and agrees on every tuple and saved field. Hashes for index+56 pages, result/match integrity, standalone completed-record validation and SVG size/font constraints pass. Retest date uses local 2026-10-23; plan/path naming uses UTC 2026-10-24.

The white/gray 580-pixel SVG has minimum 20-pixel labels. It shows the actual five cipher rune indicesâ†’HTTPS, decoded neighboring rune-slot context, overlapping HTTP-prefix count and zero-WWW invariant. It was rasterized and visually inspected; the preview stays here, outside the public record's numerical outputs.

For integration, retain the queue's unresolved URL grammar/continuation scope. `scope-receipt.json` states the exact coverage and relationship to `wholepage-affine-gp29` and `monoalphabetic-crib-capacity`. No shared catalogues, generated site files, queue data, builds or commits were changed.
