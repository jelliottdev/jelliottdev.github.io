# Editorial scope

The manuscript reference remains evidence-based. A separate experiment registry accepts newly written, retested and human-reviewed records; it starts empty. Never import earlier runs as completed records without that process.

- Preserve original images and their SHA-256 checksums.
- Distinguish archived transcriptions, documented corrections, known readings, and visual measurements.
- Date all reading-status claims to the source snapshot.
- Label unreviewed details. Do not call a page exhaustively documented merely because it has a record.
- Do not import experimental outputs, private communications, unsupported plaintexts, or internal research reports wholesale.
- Every page must link to pinned public source images. Pixel coordinates use original-image coordinates.
- Keep original transcriptions available when displaying a corrected derivative.

## Adding or correcting visual observations

Edit `data/evidence/editorial-page-notes.json` for selected observations of the preserved page images. Do not hand-edit generated `data/pages/*.json` files. The separate record keeps these observations distinct from imported archive measurements.

Each entry contains:

- `page`: the exact release ID, such as `lp2-33`.
- `image_sha256`: the hash of the original JPEG that was inspected. Compare it with the page record and file; do not use a thumbnail hash.
- `notes`: objects with a short `title` and explanatory `text`.
- Optional `rect` within a note: `[x, y, width, height]` in original-image pixels. A display window can include whitespace; do not describe it as an exact ink boundary unless measured as such.

Describe placement, shape, color, and other visible features before interpretation. A statement about an exact count needs a clear inclusion rule. A claim about pixel identity, reflection, or a source artwork needs the corresponding comparison; similar subjects alone are insufficient. Use a guide for the longer explanation and connect it to the page through `articles/index.json`.

The record's `reviewed` date identifies the current observation record. Preserve history in Git and explain changed observations in the commit. This editorial record is not a human-reviewed experiment result.

After editing, run from the repository root:

```text
python scripts/build_page_notes.py
python scripts/build_assistant.py
python scripts/build_access_exports.py
```

The first command checks original-image hashes and rectangle bounds before writing page notes and search summaries. It replaces only notes carrying this record's source path. Removing an entry withdraws its notes on the next build; imported measurements remain. Invalid or duplicate page IDs stop the build. Validation occurs before any page-record writes.

If the edit also changes a guide or its search metadata, run `python scripts/build_articles.py` before the final access-export command. That updates both browser indexes and the standalone articles. Do not edit `articles/readings/` directly: those guides are generated from the known-reading controls.

Inspect the affected page and any region buttons in the local site, check the resulting diff, and confirm that the prose and image agree. Relevant automated checks are `python scripts/test_page_notes.py` for builder changes and `node scripts/test_search.cjs` for search changes. The build checks file identity and data structure; it cannot certify the visual interpretation.

# Interface

## Explanatory writing

Keep the technical depth, but write for a reader learning the subject.

- Begin with the question the article answers and why it matters to a solver.
- Explain unfamiliar terms when they first become necessary. A link supplements an explanation; it does not replace one.
- Develop an example from input to operation to result. Show how the result supports the claim instead of presenting commands and conclusions without the steps between them.
- Introduce a command's purpose before showing it, then explain the output the reader should expect.
- Put the main path first. Follow it with field definitions, edge cases, alternative setups and detailed provenance.
- Use limitations where they change how a result should be interpreted. Avoid repeating generic disclaimers in every paragraph.
- Prefer connected explanations over compressed strings of technical nouns. Concision is useful only while the relationship between ideas remains clear.
- Review articles for flow and contradictions after adding material. Do not accumulate introductory patches that leave older instructions inconsistent.

## Appearance

Plain reference-wiki styling: serif article headings, compact sans-serif navigation, blue links, neutral borders, white reading surface. Red is reserved for manuscript-specific emphasis. No decorative hero, card dashboard, gradients, or speculative status badges.

Primary journey: page index or search → page record → source image and transcription → citations. Mobile prioritizes page selection and reading. Full-resolution inspection uses a keyboard-accessible dialog.

# Validation

Check 75 image hashes, record cardinality, page links, desktop/mobile overflow, search, filters, transcription modes, image controls, invalid routes, and absence of experimental records before publication.

For guide or topic-index links, run `python scripts/check_article_links.py`. It checks guide destinations and section anchors, manuscript IDs, local files, and duplicate topic IDs across the authored and generated reading guides. The check does not fetch external URLs or validate other application routes. Use `python scripts/test_article_links.py` when changing the checker itself. Both commands also run in the repository validation workflow.
