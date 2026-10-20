# Experiment records

The registry starts empty. Earlier work is not automatically a published experiment. Write a clear script, retest it, and review its precise claims before publishing.

## Add an idea

1. Run `python scripts/new_experiment.py your-short-id` to create a draft.
2. Write `article.md`: question, rationale, scope, method, results, limitations, and remaining work.
3. Replace `run.py` with a readable reproducible script. Use explicit inputs, deterministic ordering, a documented seed where relevant, and machine-readable output. Include dependency versions. The generated stub deliberately refuses to run.
4. Fill `record.json`. Specify exact pages, transcription choice, transformations, parameter ranges, and exclusions. List every input and output with its SHA-256.
5. Retest from the repository root with the stated command. Compare the output to the stored result. Document thresholds and controls; stochastic tests need a null model, trial count, seed, and uncertainty.
6. Have a human review the record, populate reviewer and retest date, and change `status` to `published`.
7. Run `python scripts/build_experiments.py`, then `python scripts/build_access_exports.py`. Review the generated site before committing.

Drafts never enter the public search index. Files committed to a public repository remain publicly readable; never commit private drafts. The builder validates fields, paths, file hashes, page IDs, and related records. It does not run scripts or certify findings.

## Record vocabulary

`supported`, `not-supported`, and `inconclusive` describe the result within the stated scope. They do not settle a general theory. Record a precise finding and limitations even when a test produces no useful result. Include related work and explain how the new test differs.

## Search and optional AI

The site ranks published records locally with BM25 term matching, including scope and limitations. This is lexical retrieval, not exhaustive detection of equivalent ideas. No hit means no matching **documented** experiment. Compare pages, input representation, and parameter bounds yourself.

Optional AI uses WebLLM 0.2.86 and Qwen2.5-0.5B-Instruct in a browser worker. It receives the query and up to three retrieved records with citation labels. It cannot browse, run scripts, or submit ideas. It is disabled when no matching published records exist.

Inference runs on the visitor's device. Initial runtime/model downloads use jsDelivr, Hugging Face, and the model-library host. No API key or paid inference endpoint is used. The visitor chooses whether to start the large download. WebGPU and sufficient memory are required; search remains usable without them. Generated text is labeled a draft and never changes the recorded result. Citation labels identify provided records, not verified entailment.

The AI needs real-device answer-quality evaluation once records exist. Do not present it as an authority on all prior Cicada research.

References: https://webllm.mlc.ai/docs/user/get_started.html and https://github.com/mlc-ai/web-llm/tree/v0.2.86

## Check the implementation

Run `python scripts/test_experiments.py` for publishing validation. For browser regression tests, install Playwright, serve the repository on port 8765, and run `node scripts/test_interface.cjs`. It uses the Edge browser channel; `PLAYWRIGHT_MODULE` can point to an existing Playwright installation and `WIKI_BASE_URL` can select a different preview server. Synthetic experiment records are intercepted in the test browser only. AI output is mocked in those UI tests; this does not test model answer quality.
