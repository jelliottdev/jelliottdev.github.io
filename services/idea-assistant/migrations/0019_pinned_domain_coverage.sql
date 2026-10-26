-- Private server journal. Rows describe independently verified persisted sources,
-- never browser-advertised totals. No public endpoint is enabled by this schema.
CREATE TABLE pinned_domain_coverage (
 coverage_id TEXT PRIMARY KEY,
 parent_domain_id TEXT NOT NULL,
 binding_json TEXT NOT NULL,
 source_id TEXT NOT NULL,
 source_binding_sha256 TEXT NOT NULL,
 plan_sha256 TEXT NOT NULL,
 verifier_version TEXT NOT NULL,
 evidence_epoch INTEGER NOT NULL CHECK(evidence_epoch>=0),
 setting_count INTEGER NOT NULL CHECK(setting_count>0),
 page_count INTEGER NOT NULL CHECK(page_count BETWEEN 1 AND 75),
 total_cases INTEGER NOT NULL CHECK(total_cases=setting_count*page_count),
 verified_named_cases INTEGER NOT NULL DEFAULT 0 CHECK(verified_named_cases BETWEEN 0 AND total_cases),
 verified_unique_cases INTEGER NOT NULL DEFAULT 0 CHECK(verified_unique_cases BETWEEN 0 AND total_cases),
 revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0)
);
CREATE INDEX pinned_coverage_parent ON pinned_domain_coverage(parent_domain_id,evidence_epoch);
CREATE TABLE pinned_domain_coverage_commits (
 id TEXT PRIMARY KEY,
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 expected_revision INTEGER NOT NULL,
 evidence_epoch INTEGER NOT NULL
);
CREATE TRIGGER pinned_coverage_commit_guard BEFORE INSERT ON pinned_domain_coverage_commits BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_domain_coverage p JOIN finite_evidence_epoch e ON e.id=1 WHERE p.coverage_id=NEW.coverage_id AND p.revision=NEW.expected_revision AND p.evidence_epoch=NEW.evidence_epoch AND e.epoch=NEW.evidence_epoch) THEN RAISE(ABORT,'stale pinned coverage commit') END;
END;
CREATE TRIGGER pinned_coverage_commit_revision AFTER INSERT ON pinned_domain_coverage_commits BEGIN
 UPDATE pinned_domain_coverage SET revision=revision+1 WHERE coverage_id=NEW.coverage_id;
END;
CREATE TABLE pinned_domain_coverage_sources (
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 receipt_key TEXT NOT NULL,
 source_id TEXT NOT NULL,
 source_sha256 TEXT NOT NULL,
 selector_json TEXT NOT NULL,
 task_id TEXT NOT NULL,
 task_sha256 TEXT NOT NULL,
 result_id TEXT NOT NULL,
 created_at TEXT NOT NULL,
 input_version TEXT NOT NULL CHECK(input_version IN ('raw','reviewed')),
 program_id TEXT NOT NULL,
 PRIMARY KEY(coverage_id,receipt_key)
);
CREATE INDEX pinned_coverage_source_identity ON pinned_domain_coverage_sources(coverage_id,source_id);
CREATE TRIGGER pinned_coverage_source_conflict BEFORE INSERT ON pinned_domain_coverage_sources BEGIN
 SELECT CASE WHEN EXISTS(SELECT 1 FROM pinned_domain_coverage_sources s WHERE s.coverage_id=NEW.coverage_id AND ((s.source_id=NEW.source_id AND (s.source_sha256<>NEW.source_sha256 OR s.task_id<>NEW.task_id OR s.task_sha256<>NEW.task_sha256 OR s.result_id<>NEW.result_id OR s.created_at<>NEW.created_at OR s.input_version<>NEW.input_version)) OR (s.receipt_key=NEW.receipt_key AND (s.source_id<>NEW.source_id OR s.source_sha256<>NEW.source_sha256 OR s.selector_json<>NEW.selector_json OR s.program_id<>NEW.program_id)))) THEN RAISE(ABORT,'conflicting pinned source') END;
END;
CREATE TRIGGER pinned_coverage_source_update BEFORE UPDATE ON pinned_domain_coverage_sources BEGIN SELECT RAISE(ABORT,'immutable pinned source'); END;
CREATE TRIGGER pinned_coverage_source_delete BEFORE DELETE ON pinned_domain_coverage_sources BEGIN SELECT RAISE(ABORT,'immutable pinned source'); END;
CREATE TABLE pinned_domain_coverage_settings (
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 setting_index INTEGER NOT NULL CHECK(setting_index>=0),
 program_id TEXT NOT NULL,
 mask TEXT NOT NULL CHECK(length(mask) BETWEEN 1 AND 75 AND mask NOT GLOB '*[^01]*'),
 verified_count INTEGER NOT NULL DEFAULT 0 CHECK(verified_count>=0),
 PRIMARY KEY(coverage_id,setting_index)
);
CREATE TRIGGER pinned_coverage_setting_guard BEFORE INSERT ON pinned_domain_coverage_settings BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_domain_coverage p WHERE p.coverage_id=NEW.coverage_id AND NEW.setting_index<p.setting_count AND length(NEW.mask)=p.page_count AND NEW.verified_count=0) OR EXISTS(SELECT 1 FROM pinned_domain_coverage_settings s WHERE s.coverage_id=NEW.coverage_id AND s.setting_index=NEW.setting_index AND s.program_id<>NEW.program_id) THEN RAISE(ABORT,'conflicting pinned setting') END;
END;
CREATE TABLE pinned_domain_coverage_unique_cases (
 coverage_id TEXT NOT NULL REFERENCES pinned_domain_coverage(coverage_id),
 program_id TEXT NOT NULL,
 page_id TEXT NOT NULL,
 case_id TEXT NOT NULL,
 PRIMARY KEY(coverage_id,program_id,page_id)
);
CREATE TRIGGER pinned_coverage_unique_conflict BEFORE INSERT ON pinned_domain_coverage_unique_cases BEGIN
 SELECT CASE WHEN EXISTS(SELECT 1 FROM pinned_domain_coverage_unique_cases c WHERE c.coverage_id=NEW.coverage_id AND c.program_id=NEW.program_id AND c.page_id=NEW.page_id AND c.case_id<>NEW.case_id) THEN RAISE(ABORT,'conflicting pinned unique case') END;
END;
CREATE TRIGGER pinned_coverage_unique_count AFTER INSERT ON pinned_domain_coverage_unique_cases BEGIN
 UPDATE pinned_domain_coverage SET verified_unique_cases=verified_unique_cases+1 WHERE coverage_id=NEW.coverage_id;
END;
CREATE TRIGGER pinned_coverage_unique_update BEFORE UPDATE ON pinned_domain_coverage_unique_cases BEGIN SELECT RAISE(ABORT,'immutable pinned unique case'); END;
CREATE TRIGGER pinned_coverage_unique_delete BEFORE DELETE ON pinned_domain_coverage_unique_cases BEGIN SELECT RAISE(ABORT,'immutable pinned unique case'); END;
CREATE TABLE pinned_domain_coverage_cases (
 coverage_id TEXT NOT NULL,
 setting_index INTEGER NOT NULL,
 page_index INTEGER NOT NULL CHECK(page_index BETWEEN 0 AND 74),
 page_id TEXT NOT NULL,
 program_id TEXT NOT NULL,
 case_id TEXT NOT NULL,
 receipt_key TEXT NOT NULL,
 matched INTEGER NOT NULL CHECK(matched IN (0,1)),
 PRIMARY KEY(coverage_id,setting_index,page_index),
 FOREIGN KEY(coverage_id,setting_index) REFERENCES pinned_domain_coverage_settings(coverage_id,setting_index),
 FOREIGN KEY(coverage_id,receipt_key) REFERENCES pinned_domain_coverage_sources(coverage_id,receipt_key)
);
CREATE INDEX pinned_coverage_cases_source ON pinned_domain_coverage_cases(coverage_id,receipt_key);
CREATE TRIGGER pinned_coverage_case_guard BEFORE INSERT ON pinned_domain_coverage_cases BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM pinned_domain_coverage p JOIN pinned_domain_coverage_settings s ON s.coverage_id=p.coverage_id WHERE p.coverage_id=NEW.coverage_id AND s.setting_index=NEW.setting_index AND NEW.page_index<p.page_count AND s.program_id=NEW.program_id) OR EXISTS(SELECT 1 FROM pinned_domain_coverage_cases c WHERE c.coverage_id=NEW.coverage_id AND c.setting_index=NEW.setting_index AND c.page_index=NEW.page_index AND (c.page_id<>NEW.page_id OR c.program_id<>NEW.program_id OR c.case_id<>NEW.case_id OR c.matched<>NEW.matched)) THEN RAISE(ABORT,'conflicting pinned case') END;
END;
CREATE TRIGGER pinned_coverage_case_count AFTER INSERT ON pinned_domain_coverage_cases BEGIN
 UPDATE pinned_domain_coverage SET verified_named_cases=verified_named_cases+1 WHERE coverage_id=NEW.coverage_id;
 UPDATE pinned_domain_coverage_settings SET mask=substr(mask,1,NEW.page_index)||'1'||substr(mask,NEW.page_index+2),verified_count=verified_count+1 WHERE coverage_id=NEW.coverage_id AND setting_index=NEW.setting_index;
 INSERT INTO pinned_domain_coverage_unique_cases(coverage_id,program_id,page_id,case_id) VALUES(NEW.coverage_id,NEW.program_id,NEW.page_id,NEW.case_id) ON CONFLICT(coverage_id,program_id,page_id) DO NOTHING;
END;
CREATE TRIGGER pinned_coverage_case_update BEFORE UPDATE ON pinned_domain_coverage_cases BEGIN SELECT RAISE(ABORT,'immutable pinned case'); END;
CREATE TRIGGER pinned_coverage_case_delete BEFORE DELETE ON pinned_domain_coverage_cases BEGIN SELECT RAISE(ABORT,'immutable pinned case'); END;
