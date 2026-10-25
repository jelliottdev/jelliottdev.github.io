PRAGMA foreign_keys = ON;
-- Internal authorization, separate from idea, task and result identities.
CREATE TABLE prepared_plans (
 id TEXT PRIMARY KEY CHECK(length(id)=69 AND substr(id,1,5)='prep_'),
 binding_hash TEXT NOT NULL CHECK(length(binding_hash)=64),
 proposal_id TEXT NOT NULL REFERENCES proposals(id),
 card_hash TEXT NOT NULL CHECK(length(card_hash)=64),
 task_id TEXT NOT NULL CHECK(length(task_id)=64),
 task_hash TEXT NOT NULL CHECK(length(task_hash)=64),
 input_version TEXT NOT NULL CHECK(input_version IN ('raw','reviewed')),
 parent_task_id TEXT REFERENCES local_tasks(id),
 authority TEXT NOT NULL CHECK(authority IN ('idea','remaining-lp2')),
 controls_hash TEXT NOT NULL CHECK(length(controls_hash)=64),
 basis_hash TEXT NOT NULL CHECK(length(basis_hash)=64),
 basis_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 created_day TEXT NOT NULL
);
CREATE INDEX prepared_plans_binding ON prepared_plans(binding_hash,created_at,id);
CREATE INDEX prepared_plans_day ON prepared_plans(created_day);
CREATE TRIGGER prepared_plans_immutable BEFORE UPDATE ON prepared_plans
BEGIN SELECT RAISE(ABORT,'Prepared plan authorizations are immutable'); END;
