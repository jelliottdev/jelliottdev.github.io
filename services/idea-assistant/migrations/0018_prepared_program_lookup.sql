-- Read compatible retained mapping evidence without scanning every preparation.
CREATE INDEX prepared_plans_program_lookup ON prepared_plans
 (proposal_id,task_id,input_version,parent_task_id,authority,created_at,id);
