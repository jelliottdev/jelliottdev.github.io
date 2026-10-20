# Reader, downloads, and machine access

Reader routes use `#/reader/lp2-15` (and corresponding page IDs). The original image sits beside explicitly labeled archived, reviewed, literal, and contextual text versions. Whole-section readings list all pages they cover. Zoom, adjustable type size, page selection, previous/next controls, and keyboard navigation are available.

Downloads use a generated file catalog with exact paths, roles, byte lengths, and SHA-256 values. Original images are checked against the page record. Three ZIP bundles include CONTENTS.json; every member is read back and hashed before publication. Reviewed text never replaces the archived file. Browser verification uses Web Crypto locally and makes no upload request.

Machine-readable access does not alter the human interface:

- `/llms.txt`: discovery and evidence conventions.
- `/llms-full.txt`: the complete set of published page references.
- `/data/catalog.json`: exact file URLs, roles, sizes, hashes.
- `/data/pages/{id}.json`: existing structured records.
- `/reference/{id}.md`: plain-text page documents.
- `/reference/{id}.html`: full references readable without JavaScript.
- `/reference/index.html`, `/sitemap.xml`, `/robots.txt`: discovery.

These are ordinary public static resources, not an authenticated API or a promise that every AI provider will ingest them automatically. Snapshot dates, numbering conventions, source links, and evidence limitations are included in the machine-facing text. No private conversations or unpublished experiment logs are exported.

Regenerate after data changes, in this order:

1. `python scripts/build_numeric_notes.py`
2. `python scripts/build_access_exports.py`

The archive importer invokes both steps automatically. Text file line endings must remain LF so served bytes agree with checksums. Verify catalog hashes against the Git blobs before pushing, not just against the working directory. If an exported record changes, rebuild all affected manifests and bundles.

Validation includes a real browser download compared with its original-image hash, local verification of both correct and modified files with zero upload requests, no-JavaScript reading, desktop/mobile reader and downloads, and verification of every bundled member.
