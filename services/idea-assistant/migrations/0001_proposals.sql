PRAGMA foreign_keys = ON;

CREATE TABLE proposals (
  id TEXT PRIMARY KEY,
  card_hash TEXT NOT NULL UNIQUE,
  card_json TEXT NOT NULL,
  fragment TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'accepted', 'duplicate', 'declined')),
  reviewed_at TEXT,
  review_reason TEXT,
  record_id TEXT
);

CREATE TABLE proposal_submissions (
  request_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES proposals(id),
  request_hash TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '' CHECK (length(note) <= 1200),
  source_url TEXT NOT NULL DEFAULT '' CHECK (length(source_url) <= 1500),
  received_at TEXT NOT NULL,
  received_day TEXT NOT NULL
);

CREATE INDEX proposal_submissions_day ON proposal_submissions(received_day);
CREATE INDEX proposal_submissions_card ON proposal_submissions(proposal_id);
CREATE INDEX proposals_review_queue ON proposals(status, created_at);
