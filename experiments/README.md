# Experiment records

The registry contains bounded, reproducible experiments. Earlier work is not automatically a published experiment. Write a clear script, retest it, and review its precise claims before publishing.

## Add an idea

1. Run `python scripts/new_experiment.py your-short-id` to create a draft.
2. Write the question, rationale, scope, and pre-run plan in `article.md`. Declare the success criterion and stopping rule before inspecting results. After running, fill in actual results, changes made after inspection, retest details, and limitations.
3. Replace `run.py` with a readable reproducible script. Use explicit inputs, deterministic ordering, a documented seed where relevant, and machine-readable output. Include dependency versions. The generated stub deliberately refuses to run.
4. Fill `record.json`. Specify exact pages, transcription choice, transformations, parameter ranges, and exclusions. List every input and output with its SHA-256.
5. Retest from the repository root with the stated command. Compare the output to the stored result. Document thresholds and controls; stochastic tests need a null model, trial count, seed, and uncertainty.
6. Retest and review the precise claims, populate the actual reviewer and retest date, and change `status` to `published`. Computational review must identify the agent and explicitly state that human review is pending; never present it as independent human review. Publication means the documented result is available, not that its interpretation is endorsed.
7. Assign the published record's type and method links as described under **Connect a published record to the method map** below. Do not add draft IDs to that map.
8. Run `python scripts/build_experiments.py`, `python scripts/build_articles.py`, `python scripts/build_assistant.py`, then `python scripts/build_access_exports.py`. Review the generated site before committing. The article build refreshes the method map after the experiment registry changes.

Drafts never enter the public search index. Files committed to a public repository remain publicly readable; never commit private drafts. The builder validates fields, paths, file hashes, page IDs, and related records. For a conventional `plan.json`, it also requires the plan and its listed dependencies to be declared hashed inputs, checks their recorded digests, and checks `plan_sha256` when present in a declared `results.json`. This catches stale nested references even when the outer record hashes match. It does not run scripts or certify findings; other plan/report formats still need their own validation.

## Record vocabulary

`supported`, `not-supported`, and `inconclusive` describe the result within the stated scope. They do not settle a general theory. Record a precise finding and limitations even when a test produces no useful result. Include related work and explain how the new test differs.

## Search and optional AI

External tools can start with `data/experiment-index.json`, a compact discovery list of published questions, summaries, tags, families and targets. Follow `record_url` to `reference/experiments/<id>.json` for the complete record, including scope, findings, limitations, review, article and hashed file lists. This object is identical to that record in `data/experiments.json`; relative paths resolve against the site root. Follow `bundle_url` for its reproduction archive. Discovery summaries and family membership are not sufficient evidence that a specific proposal was tested. These static resources require no API key and do not call hosted inference. The builder removes withdrawn records from its generated individual-export directory.

The site ranks published techniques locally with BM25 term matching, including scope and limitations. Page references are removed from the technique query; a page number alone is never a matching experiment. Selected pages provide scope context, not substitute results. This is lexical retrieval, not exhaustive detection of equivalent ideas. No hit means no matching **documented** experiment. Compare pages, input representation, and parameter bounds yourself.

Hosted AI is deployed through Cloudflare Workers AI, using its built-in binding rather than provider or visitor keys. It uses the same form and adds a cited comparison above the records; there is no browser model download or separate AI section. See [deployment and limits](../services/idea-assistant/README.md).

The verified service URL is set in `data/assistant.json`. Empty registries and unmatched techniques do not call inference. Answers use complete experiment scopes; excerpts from explicitly named manuscript pages can supply supporting context. Only pressing Check idea can start inference. Repeated answers are cached against the question and exact evidence; changed source contents invalidate the server cache. The free plan has a daily allowance; when unavailable, ordinary search still works. Generated comparisons are not authoritative findings, and valid citation labels do not prove that a claim follows from the source.

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

## Connect a published record to the method map

Three different fields organize the work:

| Field | Purpose | Example |
| --- | --- | --- |
| `record.json` → `family` and `variant` | Group a baseline and follow-ups addressing the same bounded research question. | One row-sum experiment and a variant changing its boundary policy. |
| `data/method-families.json` → `families[].related` | Link records to broad method guides. Membership is non-exclusive. | A route-plus-key test can link to both route and key families. |
| `data/method-families.json` → `record_kind_by_id` | Describe the role of the evidence. This is not an outcome or confidence rating. | A tree-source alignment is a source audit, not a bounded solving test; a synthetic decoder check is a control. |

When the retested record is ready to publish:

1. Add its exact ID to `related` for at least one relevant method family. Link only families that help describe the actual procedure; a word mentioned in the background is not enough. Do not create a new broad family for every parameter change.
2. Add its ID to `record_kind_by_id` with an existing key from `record_kinds`: `manuscript`, `control`, `alphabet`, `audit`, `historical`, or `replay`. Read the definitions in the same file before choosing. A method replay can reproduce a proposed procedure without confirming its reading.
3. Keep these edits together with the record's publication. The experiment builder requires type assignments to cover exactly the published records. The method-map builder requires linked records to be published. Drafts must therefore remain absent from both structures.
4. Run the build commands above, then `node scripts/test_idea_coverage.cjs` and `python scripts/check_article_links.py`. Inspect the experiment's type label, its method-guide links, and its placement among baseline/variants. These checks validate organization and references; they do not reproduce the scientific calculation.

If withdrawing a record to draft, remove its type assignment and method links in the same change, and review published records that reference it. Do not replace a missing or withdrawn test with a family-level claim that the method failed. If a retest changes only the result of an existing record, keep its identity and update the scope, outputs and explanation as required.
