-- Malformed historical/nonpublic payloads must not make unrelated inserts fail.
DROP INDEX proposals_method_parent_lookup;
CREATE INDEX proposals_method_parent_lookup ON proposals(
 CASE WHEN json_valid(card_json) THEN json_extract(card_json,'$.rules.searchProtocol.value.parentId') ELSE NULL END,
 created_at DESC,id DESC
) WHERE CASE WHEN json_valid(card_json) THEN
 json_extract(card_json,'$.rules.searchProtocol.value.kind')='method-design'
 AND json_extract(card_json,'$.rules.searchProtocol.value.version') IN (1,2)
 ELSE 0 END;
