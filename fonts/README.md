# Rune font

Liberpedia bundles **Noto Sans Runic Regular, version 2.002** so manuscript text remains readable when a visitor's device has no Runic font. The CSS loads it only for Unicode's Runic block (U+16A0–U+16FF). Latin text keeps the site's existing typefaces. This font is a display aid for the transcription; the original page image remains the source for inspecting ambiguous marks.

- Font: [`NotoSansRunic-Regular.ttf`](https://github.com/google/fonts/blob/cc75b7d0ac3515f034d1b9740edff62942ac7cf9/ofl/notosansrunic/NotoSansRunic-Regular.ttf) from the [Google Fonts Noto Sans Runic directory](https://github.com/google/fonts/tree/cc75b7d0ac3515f034d1b9740edff62942ac7cf9/ofl/notosansrunic).
- Copyright: 2022 The Noto Project Authors. License: [SIL Open Font License 1.1](OFL-NotoSansRunic.txt), bundled alongside the font.
- Source commit: `cc75b7d0ac3515f034d1b9740edff62942ac7cf9`.

Run `python scripts/check_rune_font.py` to check that every Gematria Primus rune and every Runic character in the manuscript transcription has a glyph in the bundled file. The CSS font URL and license file are checked too.
