-- Private server-owned frontier; no client cursor/completion setters.
CREATE TABLE pinned_question_coordinator (
 coordinator_id TEXT PRIMARY KEY,
 binding_json TEXT NOT NULL CHECK(length(CAST(binding_json AS BLOB))<=131072),
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 phase TEXT NOT NULL CHECK(phase IN ('discovering','importing','verifying','ready')),
 revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0),
 scan_id TEXT,
 next_sequence INTEGER NOT NULL DEFAULT 0 CHECK(next_sequence>=0),
 previous_page_sha256 TEXT,
 cursor TEXT CHECK(cursor IS NULL OR length(CAST(cursor AS BLOB))<=65536),
 completion_token TEXT CHECK(completion_token IS NULL OR length(CAST(completion_token AS BLOB))<=65536),
 pending_json TEXT CHECK(pending_json IS NULL OR length(CAST(pending_json AS BLOB))<=1900000),
 pending_sha256 TEXT,
 import_offset INTEGER NOT NULL DEFAULT 0 CHECK(import_offset>=0),
 page_count INTEGER NOT NULL DEFAULT 0 CHECK(page_count>=0),
 imported_items INTEGER NOT NULL DEFAULT 0 CHECK(imported_items>=0),
 CHECK((phase='importing' AND pending_json IS NOT NULL AND pending_sha256 IS NOT NULL) OR (phase<>'importing' AND pending_json IS NULL AND pending_sha256 IS NULL AND import_offset=0)),
 CHECK(phase NOT IN ('verifying','ready') OR completion_token IS NOT NULL)
);
CREATE TRIGGER pinned_question_coordinator_identity BEFORE UPDATE ON pinned_question_coordinator BEGIN
 SELECT CASE WHEN NEW.coordinator_id<>OLD.coordinator_id OR NEW.binding_json<>OLD.binding_json OR NEW.coverage_id<>OLD.coverage_id THEN RAISE(ABORT,'immutable coordinator binding') END;
END;
CREATE TABLE pinned_question_coordinator_commits (
 id TEXT PRIMARY KEY,
 coordinator_id TEXT NOT NULL REFERENCES pinned_question_coordinator(coordinator_id),
 expected_revision INTEGER NOT NULL CHECK(expected_revision>=0),
 UNIQUE(coordinator_id,expected_revision)
);
CREATE TRIGGER pinned_question_coordinator_commit_guard BEFORE INSERT ON pinned_question_coordinator_commits BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_question_coordinator q JOIN pinned_domain_coverage p ON p.coverage_id=q.coverage_id JOIN finite_evidence_epoch e ON e.id=1 WHERE q.coordinator_id=NEW.coordinator_id AND q.revision=NEW.expected_revision AND p.evidence_epoch=e.epoch) THEN RAISE(ABORT,'stale coordinator revision or evidence epoch') END;
END;
CREATE TRIGGER pinned_question_coordinator_commit_revision AFTER INSERT ON pinned_question_coordinator_commits BEGIN
 UPDATE pinned_question_coordinator SET revision=revision+1 WHERE coordinator_id=NEW.coordinator_id;
END;
CREATE TABLE pinned_question_coordinator_pages (
 coordinator_id TEXT NOT NULL REFERENCES pinned_question_coordinator(coordinator_id),
 sequence INTEGER NOT NULL CHECK(sequence>=0),
 scan_id TEXT NOT NULL,
 page_sha256 TEXT NOT NULL,
 previous_page_sha256 TEXT,
 range_start INTEGER NOT NULL CHECK(range_start>=0),
 range_count INTEGER NOT NULL CHECK(range_count BETWEEN 1 AND 16),
 total_items INTEGER NOT NULL CHECK(total_items BETWEEN 0 AND 192),
 metadata_sha256 TEXT NOT NULL,
 PRIMARY KEY(coordinator_id,sequence)
);
CREATE TABLE pinned_question_coordinator_journal (
 coordinator_id TEXT PRIMARY KEY REFERENCES pinned_question_coordinator(coordinator_id),
 page_count INTEGER NOT NULL DEFAULT 0,
 item_count INTEGER NOT NULL DEFAULT 0,
 last_sequence INTEGER NOT NULL DEFAULT -1,
 scan_id TEXT,
 page_sha256 TEXT,
 previous_page_sha256 TEXT,
 metadata_sha256 TEXT,
 range_start INTEGER,
 range_count INTEGER,
 total_items INTEGER
);
CREATE TRIGGER pinned_question_coordinator_journal_initialize AFTER INSERT ON pinned_question_coordinator BEGIN
 INSERT INTO pinned_question_coordinator_journal(coordinator_id) VALUES(NEW.coordinator_id);
END;
CREATE TRIGGER pinned_question_coordinator_page_order BEFORE INSERT ON pinned_question_coordinator_pages BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_question_coordinator_journal j WHERE j.coordinator_id=NEW.coordinator_id AND j.page_count=NEW.sequence AND ((NEW.sequence=0 AND NEW.previous_page_sha256 IS NULL) OR (j.scan_id=NEW.scan_id AND j.page_sha256=NEW.previous_page_sha256))) THEN RAISE(ABORT,'invalid coordinator page order') END;
END;
CREATE TRIGGER pinned_question_coordinator_journal_update_guard BEFORE UPDATE ON pinned_question_coordinator_journal BEGIN
 SELECT CASE WHEN NEW.coordinator_id<>OLD.coordinator_id OR NEW.page_count<>OLD.page_count+1 OR NEW.last_sequence<>OLD.page_count OR NOT EXISTS(SELECT 1 FROM pinned_question_coordinator_pages p WHERE p.coordinator_id=NEW.coordinator_id AND p.sequence=NEW.last_sequence AND NEW.item_count=OLD.item_count+p.total_items AND NEW.scan_id=p.scan_id AND NEW.page_sha256=p.page_sha256 AND NEW.metadata_sha256=p.metadata_sha256 AND NEW.range_start=p.range_start AND NEW.range_count=p.range_count AND NEW.total_items=p.total_items AND NEW.previous_page_sha256 IS p.previous_page_sha256) THEN RAISE(ABORT,'immutable coordinator journal summary') END;
END;
CREATE TRIGGER pinned_question_coordinator_journal_append AFTER INSERT ON pinned_question_coordinator_pages BEGIN
 UPDATE pinned_question_coordinator_journal SET page_count=page_count+1,item_count=item_count+NEW.total_items,last_sequence=NEW.sequence,scan_id=NEW.scan_id,page_sha256=NEW.page_sha256,previous_page_sha256=NEW.previous_page_sha256,metadata_sha256=NEW.metadata_sha256,range_start=NEW.range_start,range_count=NEW.range_count,total_items=NEW.total_items WHERE coordinator_id=NEW.coordinator_id;
END;
CREATE TRIGGER pinned_question_coordinator_journal_delete BEFORE DELETE ON pinned_question_coordinator_journal BEGIN SELECT RAISE(ABORT,'immutable coordinator journal summary'); END;
CREATE TRIGGER pinned_question_coordinator_page_update BEFORE UPDATE ON pinned_question_coordinator_pages BEGIN SELECT RAISE(ABORT,'immutable coordinator page'); END;
CREATE TRIGGER pinned_question_coordinator_page_delete BEFORE DELETE ON pinned_question_coordinator_pages BEGIN SELECT RAISE(ABORT,'immutable coordinator page'); END;

CREATE TRIGGER pinned_question_coordinator_commit_update BEFORE UPDATE ON pinned_question_coordinator_commits BEGIN SELECT RAISE(ABORT,'immutable coordinator commit'); END;
CREATE TRIGGER pinned_question_coordinator_commit_delete BEFORE DELETE ON pinned_question_coordinator_commits BEGIN SELECT RAISE(ABORT,'immutable coordinator commit'); END;
CREATE TABLE pinned_question_coordinator_completion (
 coordinator_id TEXT PRIMARY KEY REFERENCES pinned_question_coordinator(coordinator_id),
 proof_json TEXT NOT NULL CHECK(length(CAST(proof_json AS BLOB))<=131072),
 proof_sha256 TEXT NOT NULL,
 final_page_sha256 TEXT NOT NULL
);
CREATE TRIGGER pinned_question_coordinator_completion_guard BEFORE INSERT ON pinned_question_coordinator_completion BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_question_coordinator q WHERE q.coordinator_id=NEW.coordinator_id AND q.phase='ready' AND q.previous_page_sha256=NEW.final_page_sha256 AND q.pending_json IS NULL) THEN RAISE(ABORT,'incomplete coordinator receipt') END;
END;
CREATE TRIGGER pinned_question_coordinator_completion_update BEFORE UPDATE ON pinned_question_coordinator_completion BEGIN SELECT RAISE(ABORT,'immutable coordinator completion'); END;
CREATE TRIGGER pinned_question_coordinator_completion_delete BEFORE DELETE ON pinned_question_coordinator_completion BEGIN SELECT RAISE(ABORT,'immutable coordinator completion'); END;
CREATE TRIGGER pinned_question_coordinator_ready_update BEFORE UPDATE ON pinned_question_coordinator WHEN OLD.phase='ready' BEGIN SELECT RAISE(ABORT,'immutable ready coordinator frontier'); END;
