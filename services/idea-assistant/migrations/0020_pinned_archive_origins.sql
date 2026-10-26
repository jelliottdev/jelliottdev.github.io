-- Preserve v1 rows as immutable historical generations. New journal generations
-- retain exact typed archive provenance instead of copying sources into tasks.
ALTER TABLE pinned_domain_coverage_sources ADD COLUMN origin_json TEXT;
DROP TRIGGER pinned_coverage_source_conflict;
CREATE TRIGGER pinned_coverage_source_conflict BEFORE INSERT ON pinned_domain_coverage_sources BEGIN
 SELECT CASE WHEN NEW.origin_json IS NULL OR NOT json_valid(NEW.origin_json) THEN RAISE(ABORT,'missing pinned archive origin') END;
 SELECT CASE WHEN json_type(NEW.origin_json)<>'object' OR COALESCE(json_extract(NEW.origin_json,'$.kind'),'') NOT IN ('local','family','published') THEN RAISE(ABORT,'invalid pinned archive origin') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM pinned_domain_coverage_sources s WHERE s.coverage_id=NEW.coverage_id AND ((s.source_id=NEW.source_id AND (s.origin_json IS NOT NEW.origin_json OR s.source_sha256<>NEW.source_sha256 OR s.task_id<>NEW.task_id OR s.task_sha256<>NEW.task_sha256 OR s.result_id<>NEW.result_id OR s.created_at<>NEW.created_at OR s.input_version<>NEW.input_version)) OR (s.receipt_key=NEW.receipt_key AND (s.origin_json IS NOT NEW.origin_json OR s.source_id<>NEW.source_id OR s.source_sha256<>NEW.source_sha256 OR s.selector_json<>NEW.selector_json OR s.program_id<>NEW.program_id)))) THEN RAISE(ABORT,'conflicting pinned source') END;
END;
