CREATE TABLE proposal_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_id TEXT NOT NULL REFERENCES proposals(id),
  changed_at TEXT NOT NULL,
  old_status TEXT NOT NULL,
  new_status TEXT NOT NULL,
  old_reviewed_at TEXT,
  new_reviewed_at TEXT,
  old_review_reason TEXT,
  new_review_reason TEXT,
  old_record_id TEXT,
  new_record_id TEXT
);

CREATE INDEX proposal_reviews_card ON proposal_reviews(proposal_id, id);

CREATE TRIGGER proposals_review_history
AFTER UPDATE OF status, reviewed_at, review_reason, record_id ON proposals
WHEN NEW.status IS NOT OLD.status
  OR NEW.reviewed_at IS NOT OLD.reviewed_at
  OR NEW.review_reason IS NOT OLD.review_reason
  OR NEW.record_id IS NOT OLD.record_id
BEGIN
  INSERT INTO proposal_reviews (
    proposal_id, changed_at,
    old_status, new_status,
    old_reviewed_at, new_reviewed_at,
    old_review_reason, new_review_reason,
    old_record_id, new_record_id
  ) VALUES (
    NEW.id, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    OLD.status, NEW.status,
    OLD.reviewed_at, NEW.reviewed_at,
    OLD.review_reason, NEW.review_reason,
    OLD.record_id, NEW.record_id
  );
END;
