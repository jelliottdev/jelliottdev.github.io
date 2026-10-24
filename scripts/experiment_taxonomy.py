"""Overlay authored record classifications without mutating the taxonomy or records."""
from copy import deepcopy
import re

_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
_MAP_ID = re.compile(r"[a-z][a-z0-9]*(?:[-:/][a-z0-9]+)*\Z")


def apply_classifications(types, records, retired_ids=()):
    """Return effective taxonomy; branch existence belongs to the map validator.

    Existing selected membership order is retained. Missing memberships append in
    records order, so the same input gives the same output and repeated application
    is idempotent. Records without classification make no changes. Only explicitly
    retired IDs are removed; omitted records never imply retirement.
    """
    if not isinstance(types, dict):
        raise ValueError("Taxonomy must be an object")
    kinds = types.get("record_kinds")
    families = types.get("families")
    assignments = types.get("record_kind_by_id")
    if not isinstance(kinds, dict) or not isinstance(families, list) or not isinstance(assignments, dict):
        raise ValueError("Taxonomy needs record_kinds, families and record_kind_by_id")
    by_family = {}
    for family in families:
        if (not isinstance(family, dict) or not isinstance(family.get("id"), str)
                or family["id"] in by_family or not isinstance(family.get("related"), list)):
            raise ValueError("Invalid or duplicate taxonomy family")
        by_family[family["id"]] = family
    if not isinstance(records, (list, tuple)):
        raise ValueError("Records must be a sequence")
    if not isinstance(retired_ids, (list, tuple)):
        raise ValueError("Retired IDs must be a sequence")
    retired = set()
    for identifier in retired_ids:
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier) or identifier in retired:
            raise ValueError("Retired IDs must be distinct safe record IDs")
        retired.add(identifier)
    overlays = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Record must be an object")
        if isinstance(record.get("id"), str) and record["id"] in retired:
            raise ValueError("A record cannot be both active and retired")
        if "classification" not in record:
            continue
        identifier = record.get("id")
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier) or identifier in seen:
            raise ValueError("Invalid or duplicate classified record ID")
        seen.add(identifier)
        classification = record["classification"]
        if not isinstance(classification, dict) or set(classification) != {"kind", "methods", "map_parent"}:
            raise ValueError(f"{identifier}: classification needs exactly kind, methods, map_parent")
        kind, methods, parent = (classification[key] for key in ("kind", "methods", "map_parent"))
        if not isinstance(kind, str) or kind not in kinds:
            raise ValueError(f"{identifier}: unknown record kind")
        if (not isinstance(methods, list) or any(not isinstance(method, str) or method not in by_family for method in methods)
                or len(methods) != len(set(methods))):
            raise ValueError(f"{identifier}: methods must be distinct existing family IDs")
        if not isinstance(parent, str) or len(parent) > 200 or not _MAP_ID.fullmatch(parent):
            raise ValueError(f"{identifier}: invalid map_parent ID")
        overlays.append((identifier, kind, set(methods)))
    effective = deepcopy(types)
    for identifier in retired:
        effective["record_kind_by_id"].pop(identifier, None)
    for family in effective["families"]:
        family["related"] = [member for member in family["related"] if member not in retired]
    for identifier, kind, methods in overlays:
        effective["record_kind_by_id"][identifier] = kind
        for family in effective["families"]:
            related = family["related"]
            if family["id"] not in methods:
                family["related"] = [member for member in related if member != identifier]
            elif identifier not in related:
                related.append(identifier)
    return effective
