PRAGMA foreign_keys = ON;

-- Preserve every existing snapshot byte. Classify old rows once, rather than
-- parsing complete family controls during every subsequent quota check.
CREATE TABLE local_task_origin_kinds (
 task_id TEXT NOT NULL,
 proposal_id TEXT NOT NULL,
 origin_id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('fixed','finite-settings')),
 created_day TEXT NOT NULL,
 PRIMARY KEY(task_id,proposal_id,origin_id),
 FOREIGN KEY(task_id,proposal_id,origin_id) REFERENCES local_task_origins(task_id,proposal_id,origin_id) ON DELETE CASCADE
);
INSERT INTO local_task_origin_kinds
 SELECT task_id,proposal_id,origin_id,
 CASE WHEN json_valid(snapshot_json) AND json_extract(snapshot_json,'$.kind')='finite-settings' THEN 'finite-settings' ELSE 'fixed' END,
 created_day FROM local_task_origins;
CREATE INDEX local_task_origin_kinds_day ON local_task_origin_kinds(kind,created_day);
CREATE TRIGGER local_task_origins_classify AFTER INSERT ON local_task_origins
BEGIN
 INSERT INTO local_task_origin_kinds VALUES(NEW.task_id,NEW.proposal_id,NEW.origin_id,
 CASE WHEN json_valid(NEW.snapshot_json) AND json_extract(NEW.snapshot_json,'$.kind')='finite-settings' THEN 'finite-settings' ELSE 'fixed' END,
 NEW.created_day);
END;
CREATE TRIGGER local_task_origin_kinds_immutable BEFORE UPDATE ON local_task_origin_kinds
BEGIN SELECT RAISE(ABORT,'Origin classification is immutable'); END;

CREATE TABLE authored_finite_snapshots (
 protocol_sha256 TEXT PRIMARY KEY CHECK(length(protocol_sha256)=64),
 snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json) AND json_extract(snapshot_json,'$.kind')='finite-settings'),
 created_at TEXT NOT NULL
);
CREATE TRIGGER authored_finite_snapshots_immutable BEFORE UPDATE ON authored_finite_snapshots
BEGIN SELECT RAISE(ABORT,'Finite source snapshots are immutable'); END;
CREATE TRIGGER authored_finite_snapshots_no_delete BEFORE DELETE ON authored_finite_snapshots
BEGIN SELECT RAISE(ABORT,'Finite source snapshots are immutable'); END;

CREATE TABLE local_task_finite_origins (
 task_id TEXT NOT NULL,
 proposal_id TEXT NOT NULL,
 origin_id TEXT NOT NULL CHECK(length(origin_id)=64),
 origin_json TEXT NOT NULL CHECK(json_valid(origin_json)),
 protocol_sha256 TEXT NOT NULL REFERENCES authored_finite_snapshots(protocol_sha256),
 created_at TEXT NOT NULL,
 created_day TEXT NOT NULL,
 PRIMARY KEY(task_id,proposal_id,origin_id),
 FOREIGN KEY(task_id,proposal_id) REFERENCES local_task_ideas(task_id,proposal_id)
);
CREATE INDEX local_task_finite_origins_day ON local_task_finite_origins(created_day);
CREATE TRIGGER local_task_finite_origins_immutable BEFORE UPDATE ON local_task_finite_origins
BEGIN SELECT RAISE(ABORT,'Finite task origins are immutable'); END;

CREATE VIEW local_task_all_origins AS
 SELECT task_id,proposal_id,origin_id,origin_json,snapshot_json,created_at,created_day,'legacy' AS storage_kind FROM local_task_origins
 UNION ALL
 SELECT o.task_id,o.proposal_id,o.origin_id,o.origin_json,s.snapshot_json,o.created_at,o.created_day,'shared' AS storage_kind
 FROM local_task_finite_origins o LEFT JOIN authored_finite_snapshots s ON s.protocol_sha256=o.protocol_sha256;
