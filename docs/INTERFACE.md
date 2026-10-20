# Liberpedia interface

The experiment index browses published records through native, keyboard-operable family disclosures. Families sort by title; each family shows its baseline before variants and retains one direct link to every separate experiment. Keep summaries and variant labels here, with full review metadata on the result page. Search matches remain expanded scope comparisons rather than inheriting collapsed browse controls. Check narrow 320px and 390px layouts when changing this browser; generic summary-span float styles must not reposition family titles or counts.

Liberpedia is a manuscript reference for researchers who need to locate a page, inspect exact text and images, trace a claim, or compare a proposed experiment with documented work.

The home page is an editorial index: manuscript releases, reference articles, specific page details, and research records. Its visual identity comes from the manuscript image, serif headings, blue links, a restrained ink palette, and aligned article lists. Avoid ornamental runes, grandiose copy, unrelated illustrations, dashboard statistics, and repeated interface explanations. Clean does not mean visually unfinished.

The sidebar groups browsing, reference articles, and source files. On phones it becomes an overlay drawer; it must not push the article down. Search stays visible and usable while the drawer is open. Focusing a header link or search control closes the drawer; only the underlying article becomes inert. Drawer focus, Escape, close-on-navigation, and recovery from errors must work without a mouse. Main article focus follows route navigation. Original-image inspection remains a separate dialog.

Primary paths:

- Search or page index → manuscript record → reader, original image, source, or download.
- Topic index → exact page or evidence article.
- Have we tried it? → related records → scope, findings, script, output and limitations.

Phone priorities are selecting a page, reading, inspecting an image, downloading the correct file, and searching an idea. Controls must fit at 320 CSS pixels; tables may scroll inside a labeled section without making the whole page scroll sideways. Use legible input fonts and sufficiently large tap targets.

Experiment search is not a novelty oracle. Empty registry, no lexical match, index-load failure, hosted-service loading, cancellation and generation failure need distinct messages. Hosted AI must not download a model onto the visitor’s device or replace source records. Generated comparisons remain drafts with links to retrieved records.

The registry contains published, bounded experiment records. Hosted AI answer quality still needs separate evaluation; deterministic retrieval and browser tests do not establish model quality. Browser regression fixtures must never be published as research.

Checked during the October 2026 update: home, catalogue, search, reader, downloads, prime-sum article, topics, experiments and manuscript pages at 320, 390, 768 and 1440 CSS pixels; drawer keyboard behavior; original download hash; offline file verification; search deep links; and empty/populated experiment UI using test fixtures.

## Manuscript reader

The reader is a reading workspace rather than an article header followed by a long stack of panels. Its identity comes from the original manuscript sheet on a neutral paper surround, with the transcription alongside on desktop. Blue-grey controls reuse the wiki palette; serif type belongs to headings and readings, while controls remain sans serif. No animation or ornamental graphics are needed.

The first choice is the manuscript page, then image, text, or desktop comparison. On phones the image and transcription occupy the same place in the flow; page navigation and view switches stay available while scrolling. Switching views returns to the top so a long image cannot leave the transcription offscreen. Text version and size persist across page navigation when applicable; unavailable versions fall back to the page's actual text. Visible Latin titles, archived runes, reviewed text and decoded readings remain distinct. Whole-section readings explicitly identify their scope.

Keep original JPEG and checksummed file links together after the reading surface. Page records contain the deeper annotations and sources. Image enlargement supports fit-page, fit-width, zoom and native overflow panning; the dialog fills a phone viewport and closes with Escape or its Close control. Never disable browser zoom.

Reader verification: narrow 320 and 390 CSS-pixel screens, 1440 desktop comparison, release boundaries, first/last pages, title-page mode fallback, persisted text mode, original-image enlargement and panning. This is browser viewport verification, not a physical-device certification.

## Wiki search

Initial loading uses `data/article-search.json`, which preserves article text and discovery metadata but omits HTML bodies. Opening a guide loads its authored HTML once per visit; concurrent requests share the load, failed loads can be retried, and stale route responses must not replace the current page. Keep the complete `data/articles.json` export for external consumers. Both indexes are generated together from the same article sources.

Header suggestions and submitted results share local ranking. Exact identifiers lead to manuscript records; guide titles and title prefixes outrank incidental body mentions. A query such as Atbash must put its method article ahead of general introduction pages. The results page has one query field (the header), a ranked list with explicit content types, optional type tabs, and collapsed manuscript filters. Page filters do not suppress unrelated guide results. Search suggestions link directly to destinations and offer all results; Escape, Tab, arrow keys and pointer dismissal remain usable. Suggestion height follows the visible viewport when the phone keyboard appears. The ordinary wiki search remains separate from evidence of completed experiments.


## Illustrated discovery

The home page starts with reader/page/quick-start links and a six-subject image index with compact links to further visual subjects, then separates readings and interpretation, decoding and measurement, and experiments. Sidebar groups follow those tasks. Release page grids stay collapsed until requested.

Article metadata owns curated `aliases`, optional `alias_sections` and `alias_pages`, and `feature_pages`. The last field lists pages where the feature is illustrated, not every page in a named section. `alias_pages` narrows a particular phrase: five-dot and three-dot searches must not inherit each other’s page lists. Exact feature-page matches outrank duplicate topic entries, while the dedicated article remains first. Exact aliases outrank incidental prose and expose those manuscript pages directly; prefix matching supports typing. Accent normalization accepts Möbius, while deliberate spelling variants accept cuniform. Do not silently equate descriptive names with deciphered meanings. Header and submitted search use the same ranking; preserve the mobile composition and pointer-gesture handling.

The illustrated index uses lazy-loaded existing thumbnails. Detail articles link complete original images with captions and downloads. Never change original image bytes to make a feature easier to see. Page comparisons state when previews are cropped and distinguish observed placement from interpretation.

## Article section links

Guide contents links carry the complete wiki route and section parameter, so copied links and new tabs preserve the destination. Normal activation scrolls without rerendering the article, updates the current URL, and moves keyboard focus to the heading. Mobile contents closes before scrolling to avoid a layout shift. Reloading a section URL restores that heading below the sticky header. Modifier clicks keep native browser behavior.

## Guide directory

The directory begins with getting started and complete readings, followed by methods, arithmetic, analysis, hidden content, page studies, philosophy, and artwork. Category descriptions explain the reader's task. Artwork belongs in one category; page-specific studies are distinct from arithmetic references. Metadata assigns each guide one primary category, while article links provide cross-subject connections.

Category destinations use stable names rather than their display position. Preserve the original nine `guide-group-0` through `guide-group-8` bookmarks as aliases; both former artwork categories now lead to the consolidated artwork section. Unconfigured categories must remain visible rather than silently dropping new articles.

`data/guide-categories.json` owns the category order, descriptions, stable IDs, and legacy aliases. Both the wiki and the generated standalone reference index use this file. The standalone index uses native fragment links and must remain navigable without JavaScript.


Guide navigation highlights the exact sidebar link when present. Otherwise, authored categories retain the corresponding subject context (getting started, known readings, analysis, philosophy, or artwork); other guides use All guides & methods. Category context uses aria-current="location", while an exact destination uses aria-current="page".

Region inspection keeps the page name and selected feature in the viewer heading. Inspection controls have descriptive accessible names; opening the whole image clears the feature context. The toolbar must grow for wrapped headings without hiding controls or removing the image viewport.

Direct section and topic URLs scroll to the destination and move keyboard focus to its heading (or the destination itself when it has no heading). A missing destination leaves the normal page available. Focusing must not trigger a second scroll or move the content behind the sticky header.

Authored manuscript images and thumbnails must include their native width and height attributes. CSS controls their displayed size and cropping; the attributes preserve the aspect ratio before lazy images load, preventing section destinations from shifting on phones. Do not resize or recompress original image files for this purpose.

Region inspection fits the recorded rectangle within both viewport dimensions and outlines its original-image bounds. The surrounding original remains visible with a light shade; the outline scales with zoom and clears when opening an image without a selected region.

Guide contents include authored H2 sections and H3 subsections in a nested list. The desktop list scrolls within the viewport; the mobile list remains a collapsed disclosure and closes after selecting a destination.

## Literal tokens and code sizing

Article and standalone-reference code uses an explicit monospace font stack. Inline tokens inherit the surrounding text size; script blocks stay at 14px on phones as well as desktop. Wrapped blocks must fit a 320px viewport, and unwrapped blocks scroll horizontally within their container. Runic transcription blocks retain their larger historic-script typography.

Transcription row links scroll the selected row into view, highlight it, and move programmatic focus to that row. The row uses tabindex="-1" so it does not add a stop to ordinary Tab navigation; Tab continues from the linked row. A nonexistent row must leave the page usable.

Literal reading search joins archived slash/newline wraps and treats hyphens as word separators for typed phrases. Original notation remains searchable as a separate field. Preserve literal spelling (including U/V conventions); a page-specific literal match outranks the shared contextual reading of its section. Search excerpts may show joined text, while page records retain the source line breaks.

Within one guide, alias-section and alias-page keys that normalize to the same search phrase must name the same destination. Case, accents, repeated whitespace, and supported dash variants cannot distinguish two destinations. The guide-index check validates authored and generated metadata; equivalent page lists may differ in order. Different guides may legitimately share a subject alias.

Article breadcrumbs name the authored subject category and link to its subject index when available. A subject index itself links to its category in All guides rather than back to itself. Unconfigured categories fall back to All guides. Keep the standalone-page and text-download actions separate from this navigation.

Scoped download URLs (`#/downloads/<query>`) open at Individual files with the query already applied. General Downloads opens at the bundle introduction. Explicit section parameters take precedence. Preserve the focused heading below the sticky header so keyboard and phone users can reach filtered files without crossing the bundle instructions.

Experiment discovery groups matching records by scientific family without merging findings. Full records compare published variants against the declared baseline, naming every changed scope field. Preserve visible computational-versus-human review status. One baseline must not imply that planned variants have been completed. Family comparisons use full-width entries with exact before/after scope in disclosures, so long methods do not become narrow text columns on phones.

Experiment detail pages put the finding and limitations before the exact scope. Keep computational review visible. Reproduction offers the reference bundle, relevant original-image bundle, and direct individual plan, checker and result downloads. A lone run script must not be presented as sufficient to reproduce a test. Keep every declared file and checksum available, including binary outputs, but do not bury the primary results inside the checksum disclosure. Family comparisons follow the record itself; do not repeat family siblings again under Related experiments.

Idea-checker matches show the actual procedure, bounds and exclusions before expandable page/input detail. Lexical overlap does not establish that the submitted variant was tested. If any explicitly requested page is outside a record, name that page even when another requested page overlaps. Browser regression setup must intercept assistant configuration and block the production inference endpoint before loading a page or submitting a form.
