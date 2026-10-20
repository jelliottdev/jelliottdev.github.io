# Experiment records

The registry starts empty. Earlier work is not automatically a published experiment. Write a clear script, retest it, and review its precise claims before publishing.

## Add an idea

1. Run `python scripts/new_experiment.py your-short-id` to create a draft.
2. Write the question, rationale, scope, and pre-run plan in `article.md`. Declare the success criterion and stopping rule before inspecting results. After running, fill in actual results, changes made after inspection, retest details, and limitations.
3. Replace `run.py` with a readable reproducible script. Use explicit inputs, deterministic ordering, a documented seed where relevant, and machine-readable output. Include dependency versions. The generated stub deliberately refuses to run.
4. Fill `record.json`. Specify exact pages, transcription choice, transformations, parameter ranges, and exclusions. List every input and output with its SHA-256.
5. Retest from the repository root with the stated command. Compare the output to the stored result. Document thresholds and controls; stochastic tests need a null model, trial count, seed, and uncertainty.
6. Have a human review the record, populate reviewer and retest date, and change `status` to `published`.
7. Run `python scripts/build_experiments.py`, `python scripts/build_assistant.py`, then `python scripts/build_access_exports.py`. Review the generated site before committing.

Drafts never enter the public search index. Files committed to a public repository remain publicly readable; never commit private drafts. The builder validates fields, paths, file hashes, page IDs, and related records. It does not run scripts or certify findings.

## Record vocabulary

`supported`, `not-supported`, and `inconclusive` describe the result within the stated scope. They do not settle a general theory. Record a precise finding and limitations even when a test produces no useful result. Include related work and explain how the new test differs.

## Search and optional AI

The site ranks published techniques locally with BM25 term matching, including scope and limitations. Page references are removed from the technique query; a page number alone is never a matching experiment. Selected pages provide scope context, not substitute results. This is lexical retrieval, not exhaustive detection of equivalent ideas. No hit means no matching **documented** experiment. Compare pages, input representation, and parameter bounds yourself.

Hosted AI is deployed through Cloudflare Workers AI, using its built-in binding rather than provider or visitor keys. It uses the same form and adds a cited comparison above the records; there is no browser model download or separate AI section. See [deployment and limits](../services/idea-assistant/README.md).

The verified service URL is set in `data/assistant.json`. Empty registries and unmatched techniques do not call inference. Answers use complete experiment scopes; excerpts from explicitly named manuscript pages can supply supporting context. Only pressing Check idea can start inference. Repeated answers are cached against the question and exact evidence; changed source contents invalidate the server cache. The free plan has a daily allowance; when unavailable, ordinary search still works. Generated comparisons are not authoritative findings, and valid citation labels do not prove that a claim follows from the source.

## Check the implementation

Run `python scripts/test_experiments.py` for publishing validation. For browser regression tests, install Playwright, serve the repository on port 8765, and run `node scripts/test_interface.cjs`. It uses the Edge browser channel; `PLAYWRIGHT_MODULE` can point to an existing Playwright installation and `WIKI_BASE_URL` can select a different preview server. Synthetic experiment records are intercepted in the test browser only. Hosted responses are mocked in UI tests; this does not test model answer quality.

## Preserve the reviewed script

Set `reproduction.script_sha256` to the SHA-256 of the exact script used in the retest. The builder compares this declared digest with the current file; changing the script or leaving the digest empty prevents publication. The generated draft leaves it empty deliberately.

For example, from the repository root:

```sh
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('experiments/records/your-short-id/run.py').read_bytes()).hexdigest())"
```

Replace `your-short-id` with the record ID. Copy the digest only after the retest, along with the corresponding input/output hashes and review details. If the script changes, retest it before updating the recorded hash. Hash verification establishes byte identity, not that a retest occurred or that the findings are correct. List local helper modules and configuration files used by the script among the hashed inputs as well.
