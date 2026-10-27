-- Canonical proposal JSON remains the sole retained method-parent declaration.
-- Public membership is joined at read time; no private proposal is published here.
CREATE INDEX proposals_method_parent_lookup ON proposals(
 json_extract(card_json,'$.rules.searchProtocol.value.parentId'),created_at DESC,id DESC
) WHERE json_extract(card_json,'$.rules.searchProtocol.value.kind')='method-design'
 AND json_extract(card_json,'$.rules.searchProtocol.value.version') IN (1,2);
