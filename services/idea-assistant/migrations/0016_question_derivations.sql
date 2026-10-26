PRAGMA foreign_keys = ON;
-- A variation is a different canonical question, with independently retained origins.
-- Published source receipts need not exist in local_tasks.
CREATE TABLE question_derivations (
 id TEXT PRIMARY KEY CHECK(length(id)=64),
 parent_proposal_id TEXT NOT NULL REFERENCES research_ideas(proposal_id),
 child_proposal_id TEXT NOT NULL REFERENCES research_ideas(proposal_id),
 origin_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 created_day TEXT NOT NULL,
 CHECK(parent_proposal_id<>child_proposal_id)
);
CREATE INDEX question_derivations_parent ON question_derivations(parent_proposal_id,created_at DESC,id DESC);
CREATE INDEX question_derivations_child ON question_derivations(child_proposal_id,created_at DESC,id DESC);
CREATE INDEX question_derivations_day ON question_derivations(created_day);
CREATE TRIGGER question_derivations_immutable BEFORE UPDATE ON question_derivations
BEGIN SELECT RAISE(ABORT,'Question derivations are immutable'); END;
