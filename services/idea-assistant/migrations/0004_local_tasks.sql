PRAGMA foreign_keys = ON;

CREATE TABLE local_tasks (
  id TEXT PRIMARY KEY,
  task_hash TEXT NOT NULL,
  create_hash TEXT NOT NULL,
  proposal_id TEXT NOT NULL REFERENCES proposals(id),
  card_json TEXT NOT NULL,
  task_json TEXT NOT NULL,
  input_version TEXT NOT NULL CHECK (input_version IN ('raw','reviewed')),
  parent_task_id TEXT REFERENCES local_tasks(id),
  created_at TEXT NOT NULL,
  created_day TEXT NOT NULL
);
CREATE INDEX local_tasks_day ON local_tasks(created_day);
CREATE TABLE local_task_results (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES local_tasks(id),
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  created_day TEXT NOT NULL
);
CREATE INDEX local_task_results_day ON local_task_results(created_day);
CREATE INDEX local_task_results_task ON local_task_results(task_id, created_at, id);
