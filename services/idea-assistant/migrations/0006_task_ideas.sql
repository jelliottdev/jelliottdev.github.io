PRAGMA foreign_keys = ON;

-- A computation keeps its content identity and original provenance. Additional
-- ideas link to it without copying the task or its verified results.
CREATE TABLE local_task_ideas (
  task_id TEXT NOT NULL REFERENCES local_tasks(id),
  proposal_id TEXT NOT NULL REFERENCES proposals(id),
  input_version TEXT NOT NULL CHECK (input_version IN ('raw','reviewed')),
  parent_task_id TEXT REFERENCES local_tasks(id),
  created_at TEXT NOT NULL,
  created_day TEXT NOT NULL,
  PRIMARY KEY (task_id, proposal_id)
);
INSERT INTO local_task_ideas (task_id, proposal_id, input_version, parent_task_id, created_at, created_day)
SELECT id, proposal_id, input_version, parent_task_id, created_at, created_day FROM local_tasks;
CREATE INDEX local_task_ideas_day ON local_task_ideas(created_day);
CREATE INDEX local_task_ideas_proposal ON local_task_ideas(proposal_id, created_at DESC, task_id DESC);
