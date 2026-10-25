-- Family rows are intrinsically public, fixed reviewed computations. Keep the
-- same canonical protocol lookup as the generic task store, without copies or
-- synthetic proposals. Raw source context is fixed by this family definition.
CREATE INDEX family_case_protocol_lookup ON family_case_results (
 family_id,
 json_extract(task_json,'$.engine'),
 json_extract(task_json,'$.alphabet'),
 json_extract(task_json,'$.steps'),
 json_extract(task_json,'$.criterion')
);
CREATE INDEX family_case_result_lookup ON family_case_results(task_id,result_hash,created_at DESC,revision DESC,case_id);
