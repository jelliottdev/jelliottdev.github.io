CREATE TABLE family_case_results (
  family_id TEXT NOT NULL,
  revision TEXT NOT NULL,
  case_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  task_json TEXT NOT NULL,
  result_hash TEXT NOT NULL,
  result_json TEXT NOT NULL,
  matched INTEGER NOT NULL CHECK (matched IN (0,1)),
  created_at TEXT NOT NULL,
  created_day TEXT NOT NULL,
  PRIMARY KEY (family_id, revision, case_id)
);
CREATE INDEX family_case_results_day ON family_case_results(created_day);
-- D1 batches are transactions. This also closes the concurrent preflight race:
-- exceeding the quota aborts the whole submission, never a partial batch.
CREATE TRIGGER family_case_results_quota BEFORE INSERT ON family_case_results
WHEN (SELECT COUNT(*) FROM family_case_results WHERE created_day=NEW.created_day)>=1000
BEGIN SELECT RAISE(ABORT, 'family daily result limit'); END;
