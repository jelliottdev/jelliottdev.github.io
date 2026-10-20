# Liberpedia interface

Liberpedia is a manuscript reference for researchers who need to locate a page, inspect exact text and images, trace a claim, or compare a proposed experiment with documented work.

The home page is an editorial index: manuscript releases, reference articles, specific page details, and research records. Its visual identity comes from the manuscript image, serif headings, blue links, a restrained ink palette, and aligned article lists. Avoid ornamental runes, grandiose copy, unrelated illustrations, dashboard statistics, and repeated interface explanations. Clean does not mean visually unfinished.

The sidebar groups browsing, reference articles, and source files. On phones it becomes an overlay drawer; it must not push the article down. Search stays visible and usable while the drawer is open. Focusing a header link or search control closes the drawer; only the underlying article becomes inert. Drawer focus, Escape, close-on-navigation, and recovery from errors must work without a mouse. Main article focus follows route navigation. Original-image inspection remains a separate dialog.

Primary paths:

- Search or page index → manuscript record → reader, original image, source, or download.
- Topic index → exact page or evidence article.
- Have we tried it? → related records → scope, findings, script, output and limitations.

Phone priorities are selecting a page, reading, inspecting an image, downloading the correct file, and searching an idea. Controls must fit at 320 CSS pixels; tables may scroll inside a labeled section without making the whole page scroll sideways. Use legible input fonts and sufficiently large tap targets.

Experiment search is not a novelty oracle. Empty registry, no lexical match, index-load failure, hosted-service loading, cancellation and generation failure need distinct messages. Hosted AI must not download a model onto the visitor’s device or replace source records. Generated comparisons remain drafts with links to retrieved records.

The system currently has no published experiment records. Hosted AI quality and performance evaluation remains required once records are available. Browser tests use isolated synthetic records; these must never be published as research.

Checked during the October 2026 update: home, catalogue, search, reader, downloads, prime-sum article, topics, experiments and manuscript pages at 320, 390, 768 and 1440 CSS pixels; drawer keyboard behavior; original download hash; offline file verification; search deep links; and empty/populated experiment UI using test fixtures.

## Manuscript reader

The reader is a reading workspace rather than an article header followed by a long stack of panels. Its identity comes from the original manuscript sheet on a neutral paper surround, with the transcription alongside on desktop. Blue-grey controls reuse the wiki palette; serif type belongs to headings and readings, while controls remain sans serif. No animation or ornamental graphics are needed.

The first choice is the manuscript page, then image, text, or desktop comparison. On phones the image and transcription occupy the same place in the flow; page navigation and view switches stay available while scrolling. Switching views returns to the top so a long image cannot leave the transcription offscreen. Text version and size persist across page navigation when applicable; unavailable versions fall back to the page's actual text. Visible Latin titles, archived runes, reviewed text and decoded readings remain distinct. Whole-section readings explicitly identify their scope.

Keep original JPEG and checksummed file links together after the reading surface. Page records contain the deeper annotations and sources. Image enlargement supports fit-page, fit-width, zoom and native overflow panning; the dialog fills a phone viewport and closes with Escape or its Close control. Never disable browser zoom.

Reader verification: narrow 320 and 390 CSS-pixel screens, 1440 desktop comparison, release boundaries, first/last pages, title-page mode fallback, persisted text mode, original-image enlargement and panning. This is browser viewport verification, not a physical-device certification.
