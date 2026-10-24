# Authored browser follow-ups

This extends the community research loop. A follow-up is a proposed bounded
experiment, not a new finding and not evidence that all other variants are open.
It is authored once in the originating `record.json`, under `browser_followups`.

Each array item has exactly:

- `id`: stable lowercase hyphenated ID.
- `title`, `question`, `scope_change`, `limitation`: plain authored text.
- `card`: the active `ClaimShare.cardData` v1 shape, without source/history.
- `inputs`: `{version, alphabet_sha256, pages:[{id,text_sha256}]}`. Page order
  matches the card; hashes cover UTF-8 text and `LocalExperiment.stable(alphabet)`.
- `control`: `{label, task, expected_result_sha256}`. The synthetic positive
  control uses the exact same ordered steps, alphabet and criterion as the
  proposed target task. Its bounded fixture is labeled synthetic, never an
  archived manuscript transcription. The expected digest covers the complete
  stable result. For a prefix criterion every stated position must match. For a fixed-pair measurement every planted pair must match, there must be at least one opportunity, and the exact random-order expectation must be smaller than that planted count.

The card explicitly specifies input version, GP29 representation and evaluation.
Steps come only from the existing deterministic `planCard`; no AI mapping or
default measurement is permitted for an authored follow-up. Supported evaluations are exact-prefix recovery and a fixed within-word affine-pair count with an exact conditional expectation. A valid declaration does not make an unsupported
method executable.

`POST /record-plans` accepts `{recordId,followupId}`. Current clients add
`includeExisting:true` to opt into saved-task lookup; legacy two-field requests
retain their original response shape and perform no database lookup. The service fetches only the
fixed canonical record URL and official alphabet/page sources. It checks the
published record, recipe, input hashes and control before returning a plan.
The response is `{state:'plan-ready', origin, card, task, inputVersion, control,
question, scopeChange, limitation, existingTask?}`. No writes or target execution occur here.
An exact registered task can be returned as `existingTask:{id,state}` so the
visitor continues an unfinished experiment or opens its saved computation.
The lookup requires the exact task and immutable recipe, not a similar title;
unregistered contexts and revised protocols are not exposed.

`origin` has `{recordId,followupId,recordSha256,protocolSha256}`; hashes pin the
exact fetched record bytes and stable complete follow-up object. The client
reviews this proposal before saving the card and creating a task. The optional
`origin` on `POST /tasks` must be revalidated against the server-loaded recipe,
exact proposal card and exact task, never trusted as visitor attribution.

Store the validated origin and recipe/control snapshot on the task–idea
association, separately from computation identity. Identical computations may
have multiple legitimate published origins. Project only registered entries'
origins. Old results remain reproducible when the source record later changes.
Generic later scope extensions must not silently inherit authored-origin status.

The browser runs the declared control before the target. A failed control stops
the target. Results still require an explicit submission and independent replay.
They do not inherit the parent record's outcome or update published evidence.

Map actions, validation and execution consume this declaration. Do not maintain
parallel handwritten button text or per-record UI branches. Nodes without a
declared runnable follow-up continue to show authored bounds and next checks;
they must not advertise that arbitrary variants can already run.

## Large manuscript scopes

Scopes over 40 pages load the generated `data/local-run-inputs.json` in one
fixed official request. The bundle contains exact raw/reviewed text for all 75
archived pages and the ordered alphabet; CI checks it against the original
page JSON files. Authored follow-ups still verify every selected text hash and
the alphabet pin. Invalid or missing bundles fail without per-page fallback.
This bounds external requests on the free Worker plan.

## Authoring and controls

`scripts/browser_followups.py:construct_followup` builds the card, exact source
pins and full synthetic recovery control from one explicit ordered program.
It independently inverses the supported primitives, then checks the complete
known Warning text with the Python runner; JavaScript parity is tested. It
never decodes manuscript targets while preparing a recipe. Noninvertible or
incomplete methods are rejected. Existing-record exclusions and prior results
must be checked before calling a setting new or open. A longer prefix cannot
rescue a setting already rejected on the same initial positions.

Multiple settings stay grouped under their originating record. The map uses
one accessible selector and review action instead of repeating full cards.

## Shared record actions

`record-followup-view.js` renders and binds the same canonical declarations in
both the research-map preview and full library record. It provides one setting
selector and one review link, with no creation or execution on selection.
Missing or malformed declarations expose no runnable action. Source and control
validation still happens at plan review; view validation is not execution proof.

## Remaining execution boundaries

The current prepared follow-ups do not make every research record runnable.
Do not equate an exclusion or next-step paragraph with an executable open test:
it may be covered elsewhere, lack a precise rule, or require another runner.

Finite, non-repeating streams now use the distinct reviewed primitive
`{op:'finite-shift',key:[...],direction:'add'|'subtract',reset:'page'|'line'|'word'}`.
The engine accepts 1–20,000 explicit GP29 residues and validates every complete
segment before any execution or progress. Separators do not consume terms;
word boundaries are any non-rune character, line boundaries are CR/LF, and each
page starts fresh. No wrapping, inferred continuation, skip or cross-page carry
is allowed. The canonical operation is `finite_key`, with label `Finite key
stream` and the same key/direction/reset fields. Both independent runners and
the authoring inverse support it. Authoring checks target lengths without
transforming target text, as well as complete synthetic recovery.

Existing standardized-card limits (12,000 bytes and structural budgets) remain
in force. Engine capacity does not promise that a 20,000-value array can be
shared or saved as a card. Current complete pages need at most 277 terms, which
fit; oversized cards fail rather than truncating or silently raising limits.
The source-bound phrase mapper accepts only fully written arrays and explicit
arithmetic/reset wording, within its existing quote/response limits. It never
invents prime, Fibonacci or totient values from a sequence name. Numeric schedule
provenance and existing-prefix exclusions must be checked before a new recipe
is declared. The plan view shows stream length and behavior first; complete
values are available in one optional disclosure and reproduction files.

The fixed word-pair adapter uses criterion
`{kind:'word-affine-count',lag,a,b,boundaries}` with lag 1–12, coefficients
0–28 and `non-rune` or `hyphen-period` boundaries. The latter splits only at
literal ASCII hyphens and periods, ignoring other layout marks. It never joins
across pages. Canonical cards use one `word_affine_count` operation and an
identical explicit evaluation. It does not accept transformation compounds.

The null comparison is the exact average obtained by uniformly permuting each
word's existing rune multiset. For a word length n and lag l, it is
`(n-l) * sum_i m_i*(m_j-[i=j]) / (n*(n-1))`, where j=(a*i+b) modulo29.
Counts and expected values are returned per page and in aggregate. Fractions
are reduced exact numerator/denominator strings; rounding is display-only.
This is not a permutation-tail probability, a full-search adjustment, or a
cipher model. Other statistical records still need their own adapters for
shuffle constraints, search correction, generators or held-out predictions.
An exact-prefix comparison cannot substitute for those experiments.

`local-control.js` supplies the same criterion-specific positive-control
property to plan preparation, browser execution and package construction.
Every use still checks the complete replayed control hash. The independent
Python package guard checks the corresponding property before any target run.
 The current
authoring constructor also restricts criteria to documented Warning prefixes;
other reading criteria need explicit source pins and independent controls.

The word-pair authoring constructor is `construct_word_pair_followup`. Its
synthetic control contains layout separators and complete planted words, and
must change its measured opportunities if the alternate boundary rule is used.
This checks the boundary distinction as well as arithmetic. Existing fixed
relation counts do not make an expanded test significant or identify a generator.
