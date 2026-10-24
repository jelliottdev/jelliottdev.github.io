# Experiment records

The registry contains bounded, reproducible experiments. Earlier work is not automatically a published experiment. Write a clear script, retest it, and review its precise claims before publishing.

## Run a family as a batch

Use a shared engine when proposals change parameters of the same operation. Keep one published account for the common question and attach stable, machine-readable cases. The first engine covers scalar-primed plaintext and ciphertext feedback; its [manifest and engine guide](engines/README.md) defines the exact supported operations.

```text
python scripts/run_experiment_suite.py experiments/suites/feedback-opening-census/manifest.json --check
python experiments/suites/feedback-opening-census/check.py
```

For a new batch, copy the manifest, choose a new suite ID, declare all inputs and parameter values, and run the central command with `--output-dir`. Reuse the engine's controls. An altered recurrence needs a versioned engine and independent check; changing the success criterion also changes what the batch can establish. Statistical searches must apply the same selection procedure to their controls.

The record's optional `batch` field names its suite ID, hashed manifest input, hashed case output, case count and scope note. The builder checks those attachments. `data/experiment-index.json` exposes the manifest and case URLs for other tools. The site presents the finding in the existing experiment format. Count published accounts, historical proposals and parameter configurations separately.

After the calculation and independent checks pass, update declared hashes in one command:

```text
python scripts/refresh_experiment_hashes.py your-record-id --write
```

Without `--write`, this command only reports drift. It does not execute the experiment, certify its interpretation or change review status. Build the site once after the batch is ready, and publish one combined commit.

## Author an experiment once

```text
python scripts/new_experiment.py your-short-id
```

Edit **`experiments/records/your-short-id/record.json`**. This is the only authored content file. The scaffold also creates `run.py`, a deliberately failing stub to replace with the actual experiment. Scripts, input data, frozen plans and measured outputs remain separate evidence files.

The new format uses `schema: "liberpedia-experiment-v2"`:

- `question`: the question a reader can understand.
- `result.finding`: what happened and what it means, in one short paragraph.
- `result.limits`: the qualification needed to interpret that result.
- `result.next_steps`: what remains worth checking.
- `analysis`: the full technical account in Markdown, including the method, controls, planned criteria, results and any decisions made after inspection.
- `scope`, `reproduction`, `review`, `visuals`, `sources`: exact bounds and evidence, as before.
- `classification`: the existing record kind, method-family IDs and research-map parent branch. The build updates those indexes from this field; no separate assignment-file edit is needed. Unknown categories or branches are rejected.

Write the result once. The page, graph preview, search index, checker evidence and ZIP instructions use that same finding and limit. Technical detail belongs in `analysis`; short result fields are limited to 700 characters and are never silently truncated. Duplicate fields such as `reader_finding`, `summary` or a second top-level `finding` are rejected. CI requires the new format for added records and newly published drafts, and prevents downgrading a converted record. `article.md` is a generated compatibility file; do not edit it.

1. Before running, record the hypothesis, exact inputs, bounds, success criterion, controls and stopping rule. Keep the record a draft.
2. Implement and run the experiment. Check its saved output independently, including whether its controls could detect a known answer. A run or schema check alone does not certify the interpretation.
3. Fill in the actual result and limitations, and the reviewer and retest date. Declare every dependency and output with its reviewed hash. Hash refresh reports byte changes; it does not approve them:

   ```text
   python scripts/refresh_experiment_hashes.py your-short-id --write
   python scripts/preflight_experiments.py your-short-id
   ```

4. Set `classification` using existing kinds, methods and the closest existing map branch. Change status to `published` only when the reviewed record is ready.
5. Build all derived views once:

   ```text
   python scripts/build_research.py
   ```

This command builds records, articles, checker data, downloads, the research map and its home preview in dependency order, then checks catalog hashes and map freshness. It does not run experiments, alter findings, commit or push. Batch related records into one build and release.

Existing records and archived bundles remain supported in their original format. They are not automatically rewritten or summarized. For a deliberate migration, embed the exact account bytes in `analysis` and verify every frozen dependency; never refresh an evidence hash just to make a conversion pass. The source schema is stricter for new records, while public export fields remain compatible with existing tools.

Drafts do not enter public indexes, but committed drafts are still public files. Never commit private material. Review metadata must identify the actual computational reviewer; independent human review is complete only when its name, date and findings are recorded. A pending review has no implied assignee or deadline.

## Record vocabulary

`supported`, `not-supported`, and `inconclusive` describe the result within the stated scope. They do not settle a general theory. Record a precise finding and limitations even when a test produces no useful result. Include related work and explain how the new test differs.

## Search and optional AI

External tools can start with `data/experiment-index.json`, a compact discovery list of published questions, summaries, tags, families and targets. Follow `record_url` to `reference/experiments/<id>.json` for the complete record, including scope, findings, limitations, review, article and hashed file lists. This object is identical to that record in `data/experiments.json`; relative paths resolve against the site root. Follow `bundle_url` for its reproduction archive. Discovery summaries and family membership are not sufficient evidence that a specific proposal was tested. These static resources require no API key and do not call hosted inference. The builder removes withdrawn records from its generated individual-export directory.

The site ranks published techniques locally with BM25 term matching, including scope and limitations. Page references are removed from the technique query; a page number alone is never a matching experiment. Selected pages provide scope context, not substitute results. This is lexical retrieval, not exhaustive detection of equivalent ideas. No hit means no matching **documented** experiment. Compare pages, input representation, and parameter bounds yourself.

Hosted AI is deployed through Cloudflare Workers AI, using its built-in binding rather than provider or visitor keys. It uses the same form and adds a cited comparison above the records; there is no browser model download or separate AI section. See [deployment and limits](../services/idea-assistant/README.md).

The verified service URL is set in `data/assistant.json`. Empty registries and unmatched techniques do not call inference. Answers use complete experiment scopes; excerpts from explicitly named manuscript pages can supply supporting context. Only pressing Check idea can start inference. Repeated answers are cached against the question and exact evidence; changed source contents invalidate the server cache. The free plan has a daily allowance; when unavailable, ordinary search still works. Generated comparisons are not authoritative findings, and valid citation labels do not prove that a claim follows from the source.

## Describe reusable results

An optional `materials` note tells the checker what the saved files actually contain. Use `summary` for retained material, `reuse` for questions it can answer without a new transformation run, `limits` for missing content or remaining work, and `evidence` for one to three declared reproduction file paths. Inspect the files and their producer before writing this note. Scores, output hashes, selected candidates and complete decoded streams support different actions; filenames alone do not establish their contents. Keep the same explanation in the experiment account.

The complete note, including paths, must fit 1,200 JSON characters. The builder rejects oversized notes and undeclared references rather than truncating them. It verifies referenced file hashes, not the truth of the interpretation or runtime reproducibility. The note travels unchanged in full and compact checker evidence; absence means reuse availability is unknown. It does not create a new experiment or change its outcome.

## Check the implementation

Run `python scripts/test_experiments.py` for publishing validation. For browser regression tests, install Playwright, serve the repository on port 8765, and run `node scripts/test_interface.cjs`. It uses the Edge browser channel; `PLAYWRIGHT_MODULE` can point to an existing Playwright installation and `WIKI_BASE_URL` can select a different preview server. Synthetic experiment records are intercepted in the test browser only. Hosted responses are mocked in UI tests; this does not test model answer quality.

## Preserve the reviewed script

Each published record receives a reproduction ZIP under `downloads/experiments/`, built from its declared inputs and outputs, script, account, record JSON, and the manifest verifier. Declare every local helper and data dependency; an undeclared dependency will not be supplied by a larger checkout when someone uses this archive. Original image inputs remain in `original-images.zip`; the per-experiment instructions and image-input manifest identify that requirement. External executables and packages are not bundled. Run `python scripts/test_experiment_bundles.py` to check all archive manifests and representative isolated reruns.

Set `reproduction.script_sha256` to the SHA-256 of the exact script used in the retest. The builder compares this declared digest with the current file; changing the script or leaving the digest empty prevents publication. The generated draft leaves it empty deliberately.

For example, from the repository root:

```sh
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('experiments/records/your-short-id/run.py').read_bytes()).hexdigest())"
```

Replace `your-short-id` with the record ID. Copy the digest only after the retest, along with the corresponding input/output hashes and review details. If the script changes, retest it before updating the recorded hash. Hash verification establishes byte identity, not that a retest occurred or that the findings are correct. List local helper modules and configuration files used by the script among the hashed inputs as well.

## Links in the full account

Use ordinary Markdown links for HTTPS sources and wiki routes, for example `[Atbash](#/wiki/atbash)`. Links to local files must name the exact script, article, input, or output path declared in the record; `[Input](text/lp2-31.txt)` works when that path is in `reproduction.inputs`. Unsafe or undeclared file destinations remain visible as text. Inline and fenced code stay literal. This renderer is for reviewed experiment articles; the AI answer renderer has separate evidence-link restrictions.

Simple pipe tables render in the full account. Give a header row, a separator row (`| --- | --- |`), and one row per result; leave a blank line afterward. Use the surrounding prose to state units, scope, and whether values are observed or expected. Tables scroll within the article on narrow screens. Put examples containing literal pipe characters in fenced code blocks rather than inside table cells.

If header, separator, or data rows have different cell counts, the full table is shown as escaped text with an explanation. Extra cells are never discarded to make the table fit. Correct the Markdown before publishing.

## Experiment families and variants

Group tests by a shared scientific question and method, not merely a keyword or page. Every new record has `family` (`id`, `title`, `question`, `baseline`) and `variant` (`label`, `changes`). All members repeat identical family metadata; the baseline names a published record. Older independent records remain readable.

To start a separate follow-up page in an existing family:

```sh
python scripts/new_experiment.py my-row-sum-variant --baseline lp2-row-prime-sums
```

This creates a new draft folder with the baseline's family and scope, plus a link back to it. It does not inherit results, input hashes, output files, review, or published status. Replace the variant label, change the intended scope fields, and record their exact differences before running. The command accepts a published family baseline; if you are following up on a sibling variant, use its family's baseline here and explain the sibling connection in the article. Add that sibling to `related` as appropriate.

The baseline has an empty `changes` list. For a variant, list every changed scope field once: `pages`, `representation`, `procedure`, `parameters`, or `exclusions`. Each entry has `field`, the exact `before` and `after` values from the two records, and a `reason`. The builder rejects missing, invented, or inaccurate differences. Changing several variables is permitted but must be visible; it cannot isolate the effect of one variable.

An identical rerun belongs in the original record's retest history. A new parameter sweep belongs in one planned record with its full result table, not dozens of records selected after seeing favorable values. Preserve the original plan and outputs when recording exploratory follow-ups. A fundamentally different question or method needs a new family; use `related` for connections across families.

Each variant retains its own findings and limitations. Search groups matching members by family but does not treat an untested sibling as tested. The full record compares all published family members. A baseline alone is explicitly labeled as having no completed variants.

Standalone Markdown images may reference declared local SVG, PNG, JPG, or WebP outputs, with descriptive alt text. Generate analytical charts from the stored results and include the plotting script among the hashed inputs. Do not use an illustrative diagram as experimental evidence.

## Source-file scopes

Experiments on historical clues or editions need not invent a manuscript page association. Set `scope.pages` to an empty list and list exact source paths in `scope.artifacts`; every artifact must also be a declared hashed input. At least one page or artifact is required. State explicitly whether the record is a known-result control or an unsolved-page test. Source-file matches do not establish that the method was tried on any manuscript page.

## Updating metadata-bound inputs

A checksum can be repeated in a record, a plan's input list, and a saved report's `plan_sha256`. Updating the record alone leaves a bundle that verifies its files but cannot reproduce its calculation. After an input changes, inspect the actual difference, update dependent plans, and rerun the affected producer and checker. If the change is provenance-only, compare every result field and confirm that only the plan digest changed; do not infer that from the input's filename or from a passing file manifest.

Run `python scripts/test_experiment_bundles.py` after rebuilding downloads. It checks declared bundle files, plan input hashes and saved plan digests, then runs selected producers and checkers from isolated extractions. It does not rerun every experiment or establish the correctness of every hypothesis. Image prerequisites remain separate from the small experiment ZIPs.


## Editorial coverage notes

`data/idea-coverage.json` records common proposals and missing bounds. These notes are not experiments, are not included in completed-record counts, and are not sent to the hosted AI as experimental evidence. The local checker matches explicit phrases and displays up to three related notes; the browse view exposes all notes.

Each note has a coverage status, an explanation, the information needed to make the proposal testable, a proposed extension explicitly marked not run, and links to narrower published experiments. Partial coverage never means that an entire cipher family was excluded. Keep these notes current when a new experiment is published. Run `node scripts/test_idea_coverage.cjs` after edits.


The solving-method directory is built from `data/method-families.json` by `scripts/build_method_map.py`, called during the article build. When publishing a result, assign it to at least one relevant method family. These links are editorial associations, not claims that a whole family has been tested. The directory copies each linked record's question and exclusions so changes to scope do not leave stale summaries.

## Choose existing categories in the experiment file

`classification` belongs in the same authored record:

```json
"classification": {
  "kind": "method",
  "methods": ["feedback"],
  "map_parent": "method:feedback"
}
```

`kind` describes the evidence: use an existing key from `record_kinds` in `data/method-families.json`. It is not a confidence rating. A reproduced proposed method is a `replay`; a synthetic decoder check is a `control`; artwork provenance is an `audit`.

`methods` names existing broad family IDs from that file. These links are non-exclusive: a route-plus-key experiment may belong to two methods. Choose families describing the tested procedure, not words mentioned only in its background.

`map_parent` names the closest existing branch ID in a solving or analysis tree in `data/research-map.json`. A baseline draft inherits its existing placement. The build adds the record to that branch and updates ancestor counts; it does not infer a method from the title or create a new category.

For new-format records, do not separately edit `families[].related` or `record_kind_by_id`: those assignments are derived. Existing legacy records retain their current assignments. Adding an entirely new category remains an explicit taxonomy decision, not a side effect of publishing a record.

`family` and `variant` remain separate: they group a baseline and follow-ups addressing one bounded question. Use them when only specific scope variables change, rather than creating a new method family for each parameter change.

## Parallel work and publication

Before choosing a source test, compare the pinned ledger entry and decoding rule with both published records and unfinished record directories. Claim its exact source ID with the integrating agent; a shared source file is not sufficient to establish equivalence. Keep work in a separate directory and leave `status` as `draft` until the calculation, independent checker and interpretation are ready. The integrating agent publishes completed records together and owns shared indexes and builds. Before handoff, run `python scripts/preflight_experiments.py your-record-id` (or several IDs together). It uses the publication validators on drafts without changing status, generating site files or executing scripts. It checks declared bytes, plan/report provenance, related IDs and exact family differences; it does not certify the scientific result.

Use LF newlines for newly generated text. Preserve archived source bytes with explicit Git attributes when their exact hashes matter. After staging a release, run `python scripts/check_staged_catalog.py --all` before committing. This reads all indexed blobs in one Git process and catches files whose working bytes match the catalog but whose published bytes were normalized. Run `git diff --cached --check` and review the staged file list; do not stage another agent's unfinished directory.
