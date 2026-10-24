PRAGMA foreign_keys = ON;

-- Explicit public entries reference the immutable normalized card only.
-- Existing private proposals are never published by applying this migration.
CREATE TABLE research_ideas (
  proposal_id TEXT PRIMARY KEY REFERENCES proposals(id),
  created_at TEXT NOT NULL,
  created_day TEXT NOT NULL
);
CREATE INDEX research_ideas_day ON research_ideas(created_day);
CREATE INDEX local_tasks_idea_page ON local_tasks(proposal_id, created_at DESC, id DESC);
