# Liberpedia interface

Liberpedia is a manuscript reference for researchers who need to locate a page, inspect exact text and images, trace a claim, or compare a proposed experiment with documented work.

The home page is an editorial index: manuscript releases, reference articles, specific page details, and research records. Its visual identity comes from the manuscript image, serif headings, blue links, a restrained ink palette, and aligned article lists. Avoid ornamental runes, grandiose copy, unrelated illustrations, dashboard statistics, and repeated interface explanations. Clean does not mean visually unfinished.

The sidebar groups browsing, reference articles, and source files. On phones it becomes an overlay drawer; it must not push the article down. Search stays visible. Drawer focus, Escape, close-on-navigation, and recovery from errors must work without a mouse. Main article focus follows route navigation. Original-image inspection remains a separate dialog.

Primary paths:

- Search or page index → manuscript record → reader, original image, source, or download.
- Topic index → exact page or evidence article.
- Have we tried it? → related records → scope, findings, script, output and limitations.

Phone priorities are selecting a page, reading, inspecting an image, downloading the correct file, and searching an idea. Controls must fit at 320 CSS pixels; tables may scroll inside a labeled section without making the whole page scroll sideways. Use legible input fonts and sufficiently large tap targets.

Experiment search is not a novelty oracle. Empty registry, no lexical match, index-load failure, unsupported WebGPU, model loading, cancellation and generation failure need distinct messages. Optional AI must never silently download a model or replace source records. Generated comparisons remain drafts with links to retrieved records.

The system currently has no published experiment records. Real-device AI quality and performance evaluation remains required once records are available. Browser tests use isolated synthetic records; these must never be published as research.

Checked during the October 2026 update: home, catalogue, search, reader, downloads, prime-sum article, topics, experiments and manuscript pages at 320, 390, 768 and 1440 CSS pixels; drawer keyboard behavior; original download hash; offline file verification; search deep links; and empty/populated experiment UI using test fixtures.
