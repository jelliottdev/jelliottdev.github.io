-- Interest only. Anonymous browser tokens are hashed before persistence.
-- No votes or counts are linked to evidence, tasks, or experimental outcomes.
CREATE TABLE record_upvotes (
 record_id TEXT NOT NULL,
 voter_hash TEXT NOT NULL CHECK(length(voter_hash)=64),
 created_at TEXT NOT NULL,
 PRIMARY KEY(record_id,voter_hash)
);
