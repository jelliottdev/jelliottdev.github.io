-- A verified opening can answer its exact prefix question before all cases run.
-- Keep repeated progress reads independent of the number of checked cases.
CREATE INDEX pinned_coverage_verified_opening
 ON pinned_domain_coverage_cases(coverage_id,matched);
