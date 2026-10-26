PRAGMA foreign_keys = ON;
-- A reservation and its full public origin are committed in one D1 batch.
-- Deferral permits the gate to reserve the budgets before any later INSERT.
CREATE TABLE question_derivation_submissions (
 request_id TEXT PRIMARY KEY REFERENCES proposal_submissions(request_id) DEFERRABLE INITIALLY DEFERRED,
 request_hash TEXT NOT NULL CHECK(length(request_hash)=64),
 origin_id TEXT NOT NULL REFERENCES question_derivations(id) DEFERRABLE INITIALLY DEFERRED,
 receipt_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 created_day TEXT NOT NULL
);
CREATE INDEX question_derivation_submissions_day ON question_derivation_submissions(created_day);
CREATE TRIGGER question_derivation_submissions_immutable BEFORE UPDATE ON question_derivation_submissions
BEGIN SELECT RAISE(ABORT,'Question derivation submissions are immutable'); END;
