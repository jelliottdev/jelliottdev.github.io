# Liberpedia interface direction

Liberpedia is a reference work and research archive. The first decision on each screen should be whether to read, inspect a source page, or check a prior test. Keep the original artifact and the interpretation visibly distinct.

- Use white for reading surfaces and cool gray for navigation, figure grounds, and secondary panels. Blue identifies links and active controls; manuscript red is reserved for source features or a specific data meaning. Do not add a warm paper tint or color filter to original images.
- Keep typography editorial and restrained: serif page and section titles, readable sans-serif prose, monospace only for exact data and commands. No decorative hero language, oversized cards, or long process explanations in primary UI.
- Put frequent destinations first. Group secondary navigation, and automatically reveal the group containing the current page. On phones, keep search and the primary action reachable before deep directories.
- Keep idea checking and archive browsing separate. The Research map combines Graph and List modes over the same current records, filters and selection; individual experiments and source-family comparisons remain directly linked.
- Let the site header and reader controls scroll away so a phone keeps its full reading area. Experiment records lead with the finding, limit, bounds and reproduction action; group secondary research material in labeled disclosures.
- Use native HTML/CSS for symbolic mappings, small diagrams, sequences, comparisons, and tables so they reflow and remain selectable. Use source images for manuscript evidence, artwork, archival captures, and geometry that cannot be faithfully represented as code. A downloadable SVG may supplement an inline explanation.
- Prepared checks must explain the action before naming a cipher, key or source. Introduce unfamiliar texts in context, and distinguish a text used as a key from a short numeric pattern that merely shares its name. State what changes from earlier work and what the visitor should inspect; keep literal settings in the exact details.
- Every figure must remain understandable without color. Put the variables, bounds, and conclusion beside the visual; place provenance and reproduction details after the finding or in a disclosure.
- Check the rendered page at 320, 390, 768, and at least one wide desktop width. Verify focus, disclosure states, no sideways scrolling, image loading, and direct links to hidden sections.

- Wiki articles end with their authored content. Use relevant links in context; do not append the same tools, related-links, process or provenance panels to every article. Keep full methods and reproduction files on the linked research records.

## October 2026 implementation handoff

The supplied implementation handoff sets the direction for dedicated manuscript and idea workspaces. Keep their quiet white and cool-gray surfaces, compact named controls, and clear hierarchy. The manuscript gets the available screen area; source text and contextual readings remain distinct. Preserve public links into these workspaces.

Idea entry starts with related research: accept questions, informal hypotheses and pasted discussions without requiring an outcome, method, scope or evaluation. Searching does not create an experiment or save an idea. Offer precise test definition separately; only that path requires clarification and confirmation before preparing a calculation. For a confirmed specification, compare with actual research. Keep original wording separate from the confirmed interpretation. Missing parameters remain unknown, never automatic wildcards. Show findings and meaningful differences before supporting detail. A saved or printed comparison must use the same confirmed idea and evidence snapshot. Do not import prototype example findings as research or advertise attachment interpretation that is not implemented.

The Research map is the shared research index. Graph and List traverse the same immediate children, with the same grouping, colors and counts. Grouping helps visitors explore related approaches; it does not establish that procedures are equivalent or covered. Use current record content even when a map began from an older archive snapshot.

### Comparing an idea and defining a check

A visitor may compare prior work before choosing how a future experiment should judge its output. Keep an undecided evaluation unspecified; never turn it into a measurement, language score, wildcard or execution permission. A comparison-first choice applies only to the current draft revision. Consequential interpretation ambiguities require clarification before defining or running a test, not before showing related reading. Explicit supplied criteria remain intact.

A saved exploratory question is not an experiment waiting to run. A selected evaluation does not make a described hypothesis an executable method. Without a defined rule or saved calculation, show related research and original context before offering precise test definition. Preserve verified calculations and coverage when they exist; display classification must not rewrite the saved card. For a deciphering question with no evaluation, no calculations and no retained evidence, show its method and offer exploration or deliberate check definition. Do not automatically prepare a task on opening it. Prepared source checks and explicitly specified tests retain their reviewed Run flow. Saving, preparation, execution and scientific support are distinct states.

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

### Saved-idea experiment preview

For a saved idea with no experiments and a complete task list, load the proposed
plan automatically. Preparation may save an internal authorization binding the
reviewed card, exact plan and runner checks. Never create a public experiment,
execute a worker or submit a result during page load. Show the exact plan before the
creation action. Keep the full confirmed card and preparation notes available
below it; the outcome and its specific objective remain visible above it.
Existing experiments come first on return visits. A truncated list does not
establish that no experiment exists. Retry preparation explicitly after errors;
late responses must not replace another idea's workspace.

### Contribution entry (25 October)

A visitor need not bring a theory. Home and the research map offer **Help with
an existing check**, which leads directly to maintained browser calculations.
The chooser uses each record's validated follow-ups; its plain headings describe
the declared calculation, with the source question and research link retained.
Do not hand-maintain a separate task catalogue or label a recipe as unfinished.
The chooser verifies saved evidence for each selected rule before describing
remaining work; the review page checks it again before Run. Keep unknown or
incomplete lookups visibly distinct from missing results. A verified opening can
answer its exact question before every page is checked. Complete measurements
are saved results, not a claim that the manuscript is deciphered. Limit chooser
lookups to two at once, load verification tools only on entry, and discard late
updates after a selection change or closing the chooser.

Offer one verified starting point for visitors who do not know which check to
choose. It is a convenient contribution, not a ranking of theories. Keep its
source question, purpose and destination together; never swap it for a different
check after it appears. The full chooser remains one direct disclosure below.
If a visitor opens that chooser while evidence is loading, do not insert a new
recommendation above their place. Unknown availability must stay explicit.

A saved calculation comes before an unfinished comparison. Explain the next
change in ordinary words, and derive its action label from the other verified
grouping. A small illustration may show the same rune order inside different
group boundaries; label it as an illustration, never as measured evidence.
Reviewing the other grouping must still lead to an explicit Run decision and
reuse any pages that already have verified results.

Explain the sequence in ordinary words: review, run in this browser, choose
whether to save. Say how saving updates the question's checked work. Keep exact
rules available before Run, and distinguish a completed calculation from a
decipherment. Learning exercises must not imply that practice adds new evidence.

### Worked plan examples

The shared plan review can illustrate a maintained numeric criterion with one
small rune strip or word calculation before Run. Derive its numbers from the
reviewed criterion and alphabet; label it as an illustration and keep it
distinct from manuscript results. Preserve the exact rule, word boundaries and
limit before Run. Do not add another review step or a separate lesson panel.

### Why a prepared check matters

An authored browser follow-up may declare `motivation`: a short, plain-language
explanation of earlier work and the question this check changes. Store it once
in the experiment source. The chooser and unfinished plan review use that exact
text; the original technical question stays with the full plan. Completed
answers take priority, with this background in the original-plan details.

This text is editorial context, not a task condition, calculation or result.
It must not enter immutable task/origin/receipt schemas. The service returns it
only to clients that explicitly request the optional projection.

### Review and contribution completion

Saved-idea workspaces name the current action: reviewing a runnable check,
choosing missing settings, continuing existing work, or inspecting saved results.
Storage is not a workflow stage. Only verified complete evidence or an answered
opening check permits the saved-results heading; an existing task alone does not.
Keep the heading node stable through asynchronous preparation and inline errors.

After a local calculation, show its unsaved state and explicit Save action before
the detailed findings. State the actual executed pages and what saving contributes.
A failed save retains local results and the retry action. Source questions and
scientific limits remain available; never make a visitor judge significance before
they can contribute a calculation.

### Space for the map and readable test descriptions

Keep Graph/List, contribution access and Filters in one compact row on phones.
Default discovery shortcuts must not create extra rows above the graph. Show
filter chips only for applied filters and omit the root-only breadcrumb; ancestor
navigation remains visible inside branches. Keep controls at least 44px high.

A recorded finding needs context: what the test used, what it changed, and what
it checked. Author this once as reader_test in the canonical record and reuse it
in the record page and map preview. It describes the original experiment, never
a different prepared follow-up. Keep exact methods and bounds available; do not
invent a simplified description when source-authored text is absent.

### Research discovery language

Visitors should recognize a question before learning a cipher name. Keep one
research object across Graph, List, search and its full page. Source-authored
`reader_title` and `reader_intro` supply its plain name and a short account of
what was tried. Preserve the technical title, source names, exact procedure and
original findings; search both names. Never derive an explanation from a title
or turn a broad family label into a claim of coverage.

List introduces each record before its page/status metadata. A record with an
authored introduction shows that introduction, then the finding; the complete
Used/Tried/Checked description follows rather than delaying the finding. Avoid
deictic introductions such as “those texts” and define unfamiliar source names
where they first appear. Stable branch IDs keep their hierarchy and colors while
the visible label describes the action in ordinary words.

The product path is recognize a question, understand the test, inspect its result,
and choose a useful next check. Consistent interactions and honest saved state
serve that path; additional terminology, controls or explanation must earn their
space. Keep technical depth available without making it the entrance exam.

Research browsing starts in List for a first visit so every immediate option is
named. Explicit links and saved Graph/List preferences retain priority. Both
views traverse the same branches, membership and colors; Graph remains available
without forcing visitors to identify unlabeled points before choosing a question.

### Ordinary question overview

Use the concrete method as the stable page title. Keep workflow messages secondary;
show scope, what the check measures, and supplied conditions before the verified
finding. Do not hide the method in the confirmed-card disclosure. Show saved
measurement output directly, then one primary route to inspect its calculation.
Repeated calculation links and source bookkeeping belong below that result.

A saved result is not coverage of an arbitrary question. Bind its requested
program, criterion, complete ordered scope, edition and source bytes to the
original canonical card before displaying a coverage verdict. A subset receipt
can support part of a verified full request, but cannot define what remains
unchecked by itself. Missing or mismatched bindings leave the question visible
and offer recovery; they cannot authorize preparation or execution.

### Variations from a saved question

Offer maintained variations directly beneath a saved question’s finding. Review one concrete change with an example, the pages it will check, and the comparison that stays unchanged. If the earlier saved result covers fewer pages, state both ranges. Opening or reviewing a variation does not run or save it.

A question-level variation uses the original question’s complete ordered scope. Keep its declared program separate from the actual saved calculation and receipt that supplied the starting point. Never present that program as an executed result. Retain the original question and link the variation back to it; preserve the selected review when evidence refreshes.

### Comparing saved variation results

When a variation and its retained starting calculation both have saved outputs, show what changed beside the finding. For output-only checks with shared saved pages, use this comparison as the main finding instead of repeating the generic output preview. Keep scored, opening-match and numerical findings visible; retain the original preview when comparison evidence is missing. Compare only shared saved pages from the same source edition and verified programs. Show short paired excerpts with differences marked without relying on color, and label Latin rune names as labels rather than translation. State when additional pages have no earlier saved output. A changed count is an observation, never a readability score or a claim that the variation improved the answer. Missing or invalid comparison evidence must leave the current question’s finding usable.

### Choosing a check after inspecting output

A saved deciphering question that only recorded transformed runes can offer maintained output checks before further method variations. Explain what each check looks for, its limit, the complete intended page scope, and any smaller earlier saved scope. Keep the original aim, ordered transformations and source edition unchanged. Review and creation are explicit; opening the page never runs or publishes a follow-up. A follow-up is a separate canonical question linked to its source, not a new method family or a retroactive verdict on the original measurement.

Opening checks may derive exact matches from independently verified saved outputs. A language comparison can also assess compatible saved output with the pinned language models without another transformation run. Keep this descriptive assessment separate from the original receipt and finding. Preserve the reviewed choice across redraws and link the original evidence. An explicit Save comparison action retains the public question and its source relationship; sharing requires its own tap.

Language bars count how many of 32 shuffles scored as high as or higher than the selected page. Explain both ends of that scale beside the chart: a longer bar does not mean a stronger language match, and a zero count is not proof of readable text. Keep all eight references in the same order and color. Summarize compared, too-short and unchecked pages separately; a selected page never stands for the whole manuscript. Keep exact scores and model details available below the chart, with the maintained inspection guidance beside the complete output.

Uncovered source prose is an unresolved note, not an invented exception rule. During explicit test definition, let the visitor identify it as background or a condition. Retain the exact wording and clarification history in the draft; only active test content belongs to the canonical public card. A retained condition continues to block unsupported execution. Casual research search never requires this clarification.

Reading a saved question uses structural card validation, not the current interactive confirmation flow. Older unresolved wording remains readable and cannot become execution permission. New confirmations, task preparation and result admission retain their independent review and verification gates.


### Published calculations and setting changes

Discover saved calculations from the generated program directory, rather than
copying them into per-record browser follow-up recipes. The directory is
navigation only: keep the record finding first, preserve the exact selected
source reference, and leave the record readable if the directory is unavailable.
Do not rank cases by an attractive score or imply that listed variations remain
untested. Authenticate the archived output before offering a supported setting
change. Keep its full scope, source edition and output check; reconstructing a
literal program question does not establish the original author's wider aim.
Reuse the shared variation review and evidence lookup before creation or running.

### Record finding order

All record surfaces place the authored result before the method description, regardless of whether the record has an introductory sentence. Full records keep the result, its limit and its visual together before the Used / Tried / Checked explanation. An optional introduction must never change this hierarchy. Missing reader metadata stays missing; do not infer a method or a finding from a title, filename or future check. Verify this with rendered real records, including introductions present, absent and malformed, rather than source-text position checks alone.

### Returning to saved work

A saved question shows verified question-wide evidence first. When no stronger answer is available, show a plain summary of one selected saved calculation: its check, finding, exact pages and text edition. Generate that summary through the shared saved-check verifier and view, never from a task count, task title, copied prose or a record-specific override. A selected calculation is not coverage of the entire question. Unknown coverage and a verified individual result can coexist; label those states separately. Preserve the chosen saved check across redraws, cancel stale reads on navigation, and share the same associated task response with the comparison and variation tools. A revisit or successful-save refresh must read current evidence again.


### Follow-up readiness and recovery

A validated published plan remains readable when saved-work checks fail. Replace the run action and ready-to-run copy with one inline recovery state; a plan being defined does not establish current readiness. A retry revalidates current evidence and never starts or publishes work. Coalesce repeated loads, honor bounded service retry hints, clear timers on departure, and never let stale responses or old callbacks restore Run. Read-only plan inspection has its own bounded service budget, separate from creating work.


### Developing a hypothesis into a method

A standardized method describes a procedure, not just a topic or a renamed hypothesis. New methods are welcome. Use a short broad category name, usually four or five words or fewer; this is a writing guideline, not a hard validation limit. Keep parameters, scope and procedural detail in the test specification rather than its method name. A proposed test needs defined inputs, concrete steps, finite choices, observable outputs, a decision rule and appropriate controls. Keep the original hypothesis distinct from AI-proposed assumptions and from an executable test. Interpretation extracts what the visitor actually supplied; method design is a separate capability and must not pretend its choices came from the original text. A saved label, a method category or an untested idea is not evidence that this design work has happened.
