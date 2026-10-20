# Reader, downloads, and machine access

Reader routes use `#/reader/lp2-15` (and corresponding page IDs). The original image sits beside explicitly labeled archived, reviewed, literal, and contextual text versions. Whole-section readings list all pages they cover. Zoom, adjustable type size, page selection, previous/next controls, and keyboard navigation are available.

Downloads use a generated file catalog with exact paths, roles, byte lengths, and SHA-256 values. Original images are checked against the page record. Three ZIP bundles include CONTENTS.json; every member is read back and hashed before publication. Reviewed text never replaces the archived file. Browser verification uses Web Crypto locally and makes no upload request.

Machine-readable access does not alter the human interface:

- `/llms.txt`: discovery and evidence conventions.
- `/llms-full.txt`: the published page references and authored guide text.
- `/data/catalog.json`: exact file URLs, roles, sizes, hashes, and descriptive labels for research scripts.
- `/data/guide-index.json`: compact guide titles, summaries, aliases, and direct HTML/text URLs. Fetch the selected guide instead of the full text collection when possible.
- `/data/articles.json`: complete authored guide records, including HTML bodies.
- `/data/article-search.json`: the browser's lighter search index, with the same searchable text and metadata but without HTML bodies.
- `/data/evidence/editorial-page-notes.json`: selected visual observations, their original-image hashes, and the observation record's review date.
- `/data/pages/{id}.json`: existing structured records.
- `/reference/{id}.md`: plain-text page documents.
- `/reference/{id}.html`: full references readable without JavaScript.
- `/reference/index.html`, `/sitemap.xml`, `/robots.txt`: discovery.

These are ordinary public static resources, not an authenticated API or a promise that every AI provider will ingest them automatically. Snapshot dates, numbering conventions, source links, and evidence limitations are included in the machine-facing text. No private conversations or unpublished experiment logs are exported.

Regenerate affected sources before the access exports. These steps are conditional; a copy edit does not require replaying every calculation:

1. `python scripts/build_page_notes.py` when editorial visual observations change. See [the editing procedure](EDITORIAL.md#adding-or-correcting-visual-observations).
2. `python scripts/build_numeric_notes.py` when numerical source data changes.
3. `python scripts/build_reading_guides.py` when known-reading controls or their guide template change.
4. `python scripts/build_articles.py` when authored guides, search metadata, or generated reading guides change.
5. `python scripts/build_assistant.py` when page notes, readings, or other inputs used by the background excerpts change. This rebuilds static context; it does not call hosted inference or publish experiments.
6. `python scripts/build_access_exports.py` last, to rebuild the catalog, standalone page references, guide discovery index, checksums, and ZIP bundles.

Experiment registry changes have their own validation and build sequence in [experiments/README.md](../experiments/README.md). A background page excerpt is not evidence that a technique has been tested.

The archive importer invokes the numeric-note, editorial-page-note, and access-export steps. It does not replace the other conditional steps above. In particular, rebuild affected reading guides and assistant excerpts after changing their source records, then finish with access exports again.

Text file line endings must remain LF so served bytes agree with checksums. Verify catalog hashes against the Git blobs before pushing, not just against the working directory. If an exported record changes, rebuild all affected manifests and bundles. `python scripts/test_reference_bundle.py` checks that the advertised reproduction commands work from an isolated extraction; run it when scripts or bundle contents change materially.

Validation includes a real browser download compared with its original-image hash, local verification of both correct and modified files with zero upload requests, no-JavaScript reading, desktop/mobile reader and downloads, and verification of every bundled member.

Authored wiki guides use the Python article builder above. When the six rendered reference routes (spelling, conventions, alphabet, readings, topics, or sources) change, run `node scripts/export_articles.cjs` against the local preview before rebuilding access exports. It requires Playwright (or an absolute `PLAYWRIGHT_MODULE` path) and installed Edge; `WIKI_BASE_URL` defaults to `http://127.0.0.1:8765/`. It expands details sections before extracting text, so machine readers receive the same full content available to human readers. Page-record exports themselves need only Python.
