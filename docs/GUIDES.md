# Guide and payload maintenance

Authored guide bodies live in `articles/*.html`, with titles and summaries in
`articles/index.json`. These are trusted repository content, not user-submitted
HTML. `scripts/build_articles.py` builds the searchable index and standalone
HTML/text. Keep explanations, links, and reproduction commands in the authored
files; do not edit generated copies.

The ordinary wiki search searches guides. The idea checker does not treat them
as experiment records. No record was added to the experiment registry by this
content expansion.

The entry journey is home → Start solving → a known control → a method guide →
an exact manuscript record and its files. A reader encountering an unfamiliar
term should have an inline link. Each guide has a table of contents and incoming
guide links. Phone layouts use a collapsed contents list, wrapping commands,
and internally scrolling wide tables.

## Payload layers

`data/evidence/embedded-payloads.json` records eight fresh default-key OutGuess
extractions checked on 2026-10-19 against pinned archive controls. The exported
public key and signed messages were verified in an isolated GnuPG keyring.
The reconstructed cover-chain signature required the recorded legacy SHA-1
compatibility flag. These checks are positive controls, not an exhaustive search
for steganography.

Preserve full extracted bytes, separated signed blocks, message bodies, and
decoded derivatives as distinct files. `.gitattributes` disables newline
conversion for this directory. Never silently replace a preserved source with
a cleaned derivative.

The cover-chain column permutation is applied **within each of the five rows**;
read the reordered rows in order. Reading whole columns top-to-bottom is a
different operation. Preserve the literal `ONIO` ending and label the restored N
in the historical address.

## Rebuild and verification

```sh
python scripts/build_reading_guides.py
python scripts/build_articles.py
python scripts/build_assistant.py
python scripts/build_access_exports.py
python scripts/reproduce_reading.py --check-all
python scripts/reproduce_cover_chain.py
python scripts/verify_downloads.py
```

The extraction wrapper additionally requires OutGuess. The reading and chain
scripts use Python's standard library and make no network or inference calls.
After committing, `python scripts/verify_downloads.py --git` checks the actual
published Git bytes rather than the working tree's newline conventions.

For this expansion, 17 literal page controls, the 991-byte reconstructed signed
message, eight payload manifests, 135 authored links, and all 425 catalog entries
were checked. Brave checks covered guide navigation, the chapter-title payload,
search discovery, and a 390-pixel phone viewport. No live inference was used for
this content batch.

## Complete-section guides

`build_reading_guides.py` generates `articles/readings/` from the nine published controls and page records. Never hand-edit these generated bodies. The builder asserts that all pages agree on section membership, order, and contextual text. Literal outputs retain their page boundaries; contextual English stays a separate whole-section rendering. The ordinary guide builder then includes these records in navigation, backlinks, search, and standalone exports.
