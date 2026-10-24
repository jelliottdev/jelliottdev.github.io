ALTER TABLE proposal_submissions ADD COLUMN original_idea TEXT NOT NULL DEFAULT ''
  CHECK (length(original_idea) <= 8000);
