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
  stable result. Its exact-prefix criterion must match.

The card explicitly specifies input version, GP29 representation and evaluation.
Steps come only from the existing deterministic `planCard`; no AI mapping or
default measurement is permitted for an authored follow-up. Initial support is
exact-prefix evaluation only. A valid declaration does not make an unsupported
method executable.

`POST /record-plans` accepts `{recordId,followupId}`. The service fetches only the
fixed canonical record URL and official alphabet/page sources. It checks the
published record, recipe, input hashes and control before returning a plan.
The response is `{state:'plan-ready', origin, card, task, inputVersion, control,
question, scopeChange, limitation}`. No writes or target execution occur here.

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
