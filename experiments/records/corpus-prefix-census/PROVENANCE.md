# Frozen plan and later test additions

The census plan records the original `scripts/test_corpus_resume.py` hash, `c849872a4a9c68cab0c0cbe6b730c872155e283e4c4e9487368db69f65b4ae1e`. Commit `7499b96512e28873f836da8962ef3da2e1409384` subsequently added 27 lines of checker corruption controls to that test. The current file's hash is `af3fe14f6a6e3b60e6af1c03f0ff0bf0ffd5e71bcfdc00c81631523f93a25611`.

The original bytes from commit `baadf89` are preserved as `frozen-resume-test.py.txt`, with the plan's hash verified. The bundle includes the current executable test and its current hash separately. The frozen plan has not been rewritten to make the later test appear original.

This change adds synthetic validation cases; it does not change the census calculator, source reader, source checker, target, selection rule or statistical definitions. All other census-plan input hashes match the packaged files. All comparison-plan input hashes also match. The two independent receipts bind the actual result files to their checker implementations.

The full run used the five commands documented in the reproduction instructions, with rendering performed after both audits passed. The single-entry wrapper is an orchestration convenience; its failure-path tests do not substitute for the full source and comparison checks.

The plan files retain their preparation-time status strings. Completion is established by `audit-receipt.json` and `comparison-receipt.json`, not by changing those historical strings. Human review remains pending.
