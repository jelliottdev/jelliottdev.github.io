# Liberpedia interface direction

Liberpedia is a reference work and research archive. The first decision on each screen should be whether to read, inspect a source page, or check a prior test. Keep the original artifact and the interpretation visibly distinct.

- Use white for reading surfaces and cool gray for navigation, figure grounds, and secondary panels. Blue identifies links and active controls; manuscript red is reserved for source features or a specific data meaning. Do not add a warm paper tint or color filter to original images.
- Keep typography editorial and restrained: serif page and section titles, readable sans-serif prose, monospace only for exact data and commands. No decorative hero language, oversized cards, or long process explanations in primary UI.
- Put frequent destinations first. Group secondary navigation, and automatically reveal the group containing the current page. On phones, keep search and the primary action reachable before deep directories.
- Keep idea checking and archive browsing separate. The Research map combines Graph and List modes over the same current records, filters and selection; individual experiments and source-family comparisons remain directly linked.
- Let the site header and reader controls scroll away so a phone keeps its full reading area. Experiment records lead with the finding, limit, bounds and reproduction action; group secondary research material in labeled disclosures.
- Use native HTML/CSS for symbolic mappings, small diagrams, sequences, comparisons, and tables so they reflow and remain selectable. Use source images for manuscript evidence, artwork, archival captures, and geometry that cannot be faithfully represented as code. A downloadable SVG may supplement an inline explanation.
- Every figure must remain understandable without color. Put the variables, bounds, and conclusion beside the visual; place provenance and reproduction details after the finding or in a disclosure.
- Check the rendered page at 320, 390, 768, and at least one wide desktop width. Verify focus, disclosure states, no sideways scrolling, image loading, and direct links to hidden sections.

- Wiki articles end with their authored content. Use relevant links in context; do not append the same tools, related-links, process or provenance panels to every article. Keep full methods and reproduction files on the linked research records.

## October 2026 implementation handoff

The supplied implementation handoff sets the direction for dedicated manuscript and idea workspaces. Keep their quiet white and cool-gray surfaces, compact named controls, and clear hierarchy. The manuscript gets the available screen area; source text and contextual readings remain distinct. Preserve public links into these workspaces.

Idea checking follows input, clarification when necessary, confirmation, and comparison with actual research. Keep original wording separate from the confirmed interpretation. Missing parameters remain unknown, never automatic wildcards. Show findings and meaningful differences before supporting detail. A saved or printed comparison must use the same confirmed idea and evidence snapshot. Do not import prototype example findings as research or advertise attachment interpretation that is not implemented.

The research index remains separate. Optional research maps help discover related approaches; their editorial groupings do not establish that procedures are equivalent or covered. Use current record content even when a map began from an older archive snapshot.

### Shared specification vocabulary

Organize an idea as outcome, ordered methods, scope, and bounds or rules. Reuse the small maintained outcome and method-family vocabularies; spelling or phrasing changes do not create categories. Keep the exact objective and output-changing settings alongside the shared labels. A readable passage and a complete solution can share a deciphering outcome without sharing a success criterion.

Show the exact objective beneath its outcome category on review cards, results
and printed packets. Suppress only a repeated category label, never a different
objective that happens to belong to that category. Editing another field must
not silently rewrite an unchanged objective.

Free text can clarify an existing category or remain unclassified. It cannot add categories automatically. Expand the maintained vocabulary only when an existing category cannot describe the distinction. Scope and parameter changes belong in the specification, not in new method names. A broad method label helps find related work; it never establishes that an exact configuration was executed. An outcome alone is not a method and must not retrieve arbitrary experiments.

### Home composition (24 October)

Use the supplied Liberpedia-home-current composition as the home reference. The standalone home shares one frame between the manuscript preview, idea entry and research-map preview. Keep source imagery on cool gray, functional headings in sans-serif and the serif Liberpedia wordmark. Secondary reference destinations remain quiet direct links below. Home styles are isolated from articles and reader styles; the home must render without loading the experiment registry.

The file picker currently keeps originals in this browser for preview only. Show that boundary in file review; transfer only the confirmed text into the checker. Do not imply that attached files, linked repositories or scripts have been interpreted or executed.

Home text handoff uses `investigate.html#input=…`, preserving whitespace and
Unicode without placing the idea in the HTTP request target. Both entry pages
share `idea-input.js` and its 1,500-character limit. Existing `?q=` links and
standardized `#idea=` cards remain supported. Opening an input never submits it.

The confirmed standardized idea is the intake. Do not add a second “Suggest a test” form. Preserve original wording beside its standardized interpretation internally; checking overlap and designing a bounded test are maintainer work. Exact duplicate storage does not establish semantic novelty. Sharing remains an optional card action. No automatic experiment result or public untested page is implied by saving.

The later community-loop request supersedes the maintainer-only queue boundary:
confirmed uncovered ideas should lead to persistent untested entries, prepared
bounded plans, optional local execution and returned evidence. Use
`docs/community-research-loop.md` as the implementation contract. Keep the one
idea intake; do not ask visitors to design and submit a second test. An AI plan
is proposed work, and an accepted computation is not a cipher solution. Until
the persistent entry/download/return journey is implemented and verified, do not
replace the existing saved receipt with a claim that this loop is available.

Browser execution is the primary path: review a plan, Run in browser, inspect
the result and submit it from the same entry. Run the site's engine in a
cancellable background worker; never require a download or Python installation.
Downloads and results-file uploads belong to optional reproduction. Put a
completed finding and its save state above plan details, not below a long form.

Show authored findings before comparison prose. A direct comparison backed by
reviewed execution metadata should use those recorded conditions and limits
without a model rewrite or an AI label. It still describes only the matched
operation, not unprovided settings or success at the visitor's whole objective.
Keep the same evidence and attribution in the printed research note.

The comparison explains the matching operation, input treatment and evaluation.
Do not repeat the findings, limits or saved-file descriptions underneath them.
Keep complete source details available without making unrelated page exceptions
part of a comparison about one page.

## Complete current handoff (24 October)

The complete-current package supersedes older global navigation and separate research-directory layouts. Use a closed-by-default native drawer on every viewport, with one menu button and the Liberpedia wordmark in a scrolling header. Search lives inside the drawer. Five primary destinations are Home, Read the manuscript, Have we tried it?, Research map, and Guides & methods. Do not restore a separate global Experiments or Research index destination: Graph and List are modes of the same research browser.

Guide pages use a readable article column and section navigation, with mobile contents in a dialog. Experiment records lead with their finding and visual; Scope, Reproduce, Analysis and Sources remain direct tabs. Current records and original files are authoritative; prototype snapshots and illustrative claims must never replace them. Preserve specialist interactives and old section links. Source-family comparisons compare exact recorded fields, not inferred semantic equivalence.

Keep interpretation loading and errors beside the editable idea input. Preserve wording and cursor position; only move to clarification/review after a usable draft exists. Editing cancels a pending interpretation. A service failure must not become a separate error page or automatically submit an unverified claim. Straightforward, fully recognized phrases can ask local clarification without a model call.

### Research traversal and zoom

Graph and List are two views of the same branch. List shows only immediate children, with matching branch colors and counts; opening a branch advances exactly one level. It does not flatten the whole archive into a result list. Filters narrow matching counts within the same hierarchy.

Graph zoom changes the space available for detail. Keep markers, strokes and touch areas stable in screen pixels; reveal labels when they fit without collisions. Dense branches need wider geometry. Render label touch targets above marker targets so tapping a title selects that title's record. Pinch and button zoom share the same limits. Preserve the current branch, filters and record when changing views.

Resizing or opening a preview must preserve map zoom. Keep the inspected area in view; entering Graph from List should reveal its selected record. A sort change returns keyboard focus to the replacement sort control. Reader options requested for an earlier page must not open after navigation or another dialog takes focus. Shared-card URLs use the same current checker entry as navigation without copying source-query parameters.

On phones, a Graph record selection replaces the canvas with a reading panel; do not float a short scrolling card over the map or List. Give it one Back to map action and show its authored result, exact tested page ranges and a plain-language limit. The map is inert while that panel is visible, and returning restores its camera. List remains hierarchical navigation: branches drill one level and terminal records are native links to the full record, with no duplicate preview/open controls. Explain outcomes before raw scores; preserve all original scientific findings and bounds in the source record. Revalidate published data on first load while retaining the app's in-memory cache.
