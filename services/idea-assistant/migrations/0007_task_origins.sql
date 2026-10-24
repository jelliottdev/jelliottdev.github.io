PRAGMA foreign_keys = ON;
-- Reviewed origins belong to an idea association, never to computation identity.
CREATE TABLE local_task_origins (
 task_id TEXT NOT NULL,
 proposal_id TEXT NOT NULL,
 origin_id TEXT NOT NULL CHECK(length(origin_id)=64),
 origin_json TEXT NOT NULL,
 snapshot_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 created_day TEXT NOT NULL,
 PRIMARY KEY(task_id,proposal_id,origin_id),
 FOREIGN KEY(task_id,proposal_id) REFERENCES local_task_ideas(task_id,proposal_id)
);
CREATE INDEX local_task_origins_day ON local_task_origins(created_day);
CREATE TRIGGER local_task_origins_immutable BEFORE UPDATE ON local_task_origins
BEGIN SELECT RAISE(ABORT,'Reviewed task origins are immutable'); END;
