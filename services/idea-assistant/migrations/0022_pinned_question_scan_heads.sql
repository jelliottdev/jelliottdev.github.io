-- Stable logical question heads; attempts and all former journals remain intact.
CREATE TABLE pinned_question_coordinator_heads (
 logical_id TEXT PRIMARY KEY,
 binding_json TEXT NOT NULL CHECK(length(CAST(binding_json AS BLOB))<=131072),
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 active_coordinator_id TEXT NOT NULL UNIQUE REFERENCES pinned_question_coordinator(coordinator_id),
 generation INTEGER NOT NULL CHECK(generation>=0),
 revision INTEGER NOT NULL CHECK(revision>=0)
);
CREATE TRIGGER pinned_question_head_identity BEFORE UPDATE ON pinned_question_coordinator_heads BEGIN
 SELECT CASE WHEN NEW.logical_id<>OLD.logical_id OR NEW.binding_json<>OLD.binding_json OR NEW.coverage_id<>OLD.coverage_id OR NEW.revision<>OLD.revision+1 OR NOT ((NEW.generation=OLD.generation AND NEW.active_coordinator_id=OLD.active_coordinator_id) OR (NEW.generation=OLD.generation+1 AND NEW.active_coordinator_id<>OLD.active_coordinator_id)) THEN RAISE(ABORT,'invalid coordinator head transition') END;
END;
CREATE TRIGGER pinned_question_head_delete BEFORE DELETE ON pinned_question_coordinator_heads BEGIN SELECT RAISE(ABORT,'immutable coordinator logical head'); END;
CREATE TRIGGER pinned_question_active_commit BEFORE INSERT ON pinned_question_coordinator_commits BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_question_coordinator_heads h WHERE h.active_coordinator_id=NEW.coordinator_id) THEN RAISE(ABORT,'stale coordinator attempt') END;
END;
CREATE TRIGGER pinned_question_head_frontier AFTER INSERT ON pinned_question_coordinator_commits BEGIN
 UPDATE pinned_question_coordinator_heads SET revision=revision+1 WHERE active_coordinator_id=NEW.coordinator_id;
END;
CREATE TABLE pinned_question_coordinator_renewals (
 id TEXT PRIMARY KEY,
 logical_id TEXT NOT NULL REFERENCES pinned_question_coordinator_heads(logical_id),
 expected_revision INTEGER NOT NULL CHECK(expected_revision>=0),
 old_coordinator_id TEXT NOT NULL REFERENCES pinned_question_coordinator(coordinator_id),
 new_coordinator_id TEXT NOT NULL REFERENCES pinned_question_coordinator(coordinator_id),
 generation INTEGER NOT NULL CHECK(generation>=1),
 reason TEXT NOT NULL CHECK(reason='authenticated-expiry'),
 UNIQUE(logical_id,generation)
);
CREATE TRIGGER pinned_question_renewal_guard BEFORE INSERT ON pinned_question_coordinator_renewals BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_question_coordinator_heads h JOIN pinned_question_coordinator old ON old.coordinator_id=h.active_coordinator_id JOIN pinned_question_coordinator fresh ON fresh.coordinator_id=NEW.new_coordinator_id JOIN pinned_domain_coverage c ON c.coverage_id=h.coverage_id JOIN finite_evidence_epoch e ON e.id=1 WHERE h.logical_id=NEW.logical_id AND h.revision=NEW.expected_revision AND h.active_coordinator_id=NEW.old_coordinator_id AND NEW.generation=h.generation+1 AND old.phase<>'ready' AND fresh.coverage_id=h.coverage_id AND fresh.phase='discovering' AND fresh.revision=0 AND fresh.next_sequence=0 AND fresh.page_count=0 AND c.evidence_epoch=e.epoch) THEN RAISE(ABORT,'stale coordinator renewal') END;
END;
CREATE TRIGGER pinned_question_renewal_advance AFTER INSERT ON pinned_question_coordinator_renewals BEGIN
 UPDATE pinned_question_coordinator_heads SET active_coordinator_id=NEW.new_coordinator_id,generation=NEW.generation,revision=revision+1 WHERE logical_id=NEW.logical_id;
END;
CREATE TRIGGER pinned_question_renewal_update BEFORE UPDATE ON pinned_question_coordinator_renewals BEGIN SELECT RAISE(ABORT,'immutable coordinator renewal'); END;
CREATE TRIGGER pinned_question_renewal_delete BEFORE DELETE ON pinned_question_coordinator_renewals BEGIN SELECT RAISE(ABORT,'immutable coordinator renewal'); END;

-- Existing attempt-zero rows are retained, including their public revision.
INSERT INTO pinned_question_coordinator_heads(logical_id,binding_json,coverage_id,active_coordinator_id,generation,revision)
 SELECT 'pqh_'||substr(coordinator_id,5),binding_json,coverage_id,coordinator_id,0,revision FROM pinned_question_coordinator WHERE COALESCE(json_extract(binding_json,'$.attemptGeneration'),0)=0;
CREATE TRIGGER pinned_question_head_initialize AFTER INSERT ON pinned_question_coordinator WHEN COALESCE(json_extract(NEW.binding_json,'$.attemptGeneration'),0)=0 BEGIN
 INSERT INTO pinned_question_coordinator_heads(logical_id,binding_json,coverage_id,active_coordinator_id,generation,revision) VALUES('pqh_'||substr(NEW.coordinator_id,5),NEW.binding_json,NEW.coverage_id,NEW.coordinator_id,0,NEW.revision);
END;
