-- Canonical saved task JSON already contains these fields. An expression index
-- admits historical tasks without rewriting their immutable IDs or receipts.
-- Discovery also checks the public association's input version; the original
-- version here is a deliberately conservative additional lookup constraint.
CREATE INDEX local_tasks_protocol_lookup ON local_tasks (
  input_version,
  json_extract(task_json, '$.engine'),
  json_extract(task_json, '$.alphabet'),
  json_extract(task_json, '$.steps'),
  json_extract(task_json, '$.criterion')
);

-- Store a frozen requested computation, not a mutable claim that it is covered.
-- Every read derives coverage afresh from public verified source results.
CREATE TABLE idea_computation_evidence (
  proposal_id TEXT NOT NULL REFERENCES proposals(id),
  requested_task_id TEXT NOT NULL,
  requested_task_json TEXT NOT NULL,
  requested_task_hash TEXT NOT NULL,
  input_version TEXT NOT NULL CHECK (input_version IN ('raw','reviewed')),
  created_at TEXT NOT NULL,
  PRIMARY KEY (proposal_id, requested_task_id)
);
CREATE INDEX idea_computation_evidence_latest ON idea_computation_evidence(proposal_id,created_at DESC,requested_task_id DESC);
