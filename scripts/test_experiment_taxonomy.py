"""Authored classification overlays: no exports or scientific execution."""
import copy
import json
from pathlib import Path
import unittest
from experiment_taxonomy import apply_classifications


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.types = {
            "description": "Retain this metadata",
            "record_kinds": {"method": {"label": "Method"}, "measurement": {"label": "Measurement"}},
            "record_kind_by_id": {"old": "method", "legacy": "measurement"},
            "families": [
                {"id": "feedback", "related": ["before", "old", "after"], "title": "Feedback"},
                {"id": "number-keys", "related": ["legacy", "old"], "title": "Numbers"},
                {"id": "routes", "related": ["legacy"], "title": "Routes"}],
        }

    def record(self, identifier="old", methods=None, kind="measurement", parent="method:feedback"):
        return {"id": identifier, "classification": {"kind": kind,
                "methods": ["feedback", "routes"] if methods is None else methods,
                "map_parent": parent}}

    def test_pure_overlay_preserves_unrelated_and_existing_order(self):
        records = [self.record()]
        original, original_records = copy.deepcopy(self.types), copy.deepcopy(records)
        result = apply_classifications(self.types, records)
        self.assertEqual(self.types, original)
        self.assertEqual(records, original_records)
        self.assertEqual(result["record_kind_by_id"], {"old": "measurement", "legacy": "measurement"})
        self.assertEqual([f["related"] for f in result["families"]],
                         [["before", "old", "after"], ["legacy"], ["legacy", "old"]])
        result["record_kinds"]["method"]["label"] = "Changed"
        self.assertEqual(self.types, original)

    def test_legacy_records_unchanged_and_empty_methods_remove_only_owner(self):
        self.assertEqual(apply_classifications(self.types, [{"id": "legacy"}]), self.types)
        result = apply_classifications(self.types, [self.record(methods=[])])
        self.assertEqual([f["related"] for f in result["families"]],
                         [["before", "after"], ["legacy"], ["legacy"]])

    def test_new_records_append_deterministically_and_application_idempotent(self):
        records = [self.record("new-b"), self.record("new-a")]
        result = apply_classifications(self.types, records)
        self.assertEqual(result["families"][0]["related"], ["before", "old", "after", "new-b", "new-a"])
        self.assertEqual(result, apply_classifications(result, records))

    def test_categories_are_references_never_created(self):
        for field, value in [("kind", "invented"), ("methods", ["invented"]),
                             ("methods", ["feedback", "feedback"]), ("methods", "feedback"),
                             ("methods", [{}]), ("kind", True)]:
            with self.subTest(field=field, value=value):
                record = self.record(); record["classification"][field] = value
                with self.assertRaises(ValueError):
                    apply_classifications(self.types, [record])

    def test_classification_exact_keys_and_record_identity(self):
        for invalid in [None, {}, {"kind": "method", "methods": []},
                        {"kind": "method", "methods": [], "map_parent": "solve-lp2", "extra": True}]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                apply_classifications(self.types, [{"id": "old", "classification": invalid}])
        for records in [[self.record(), self.record()], [self.record("../bad")]]:
            with self.assertRaises(ValueError):
                apply_classifications(self.types, records)

    def test_map_id_shape_only_existence_deferred(self):
        for value in ["solve-lp2", "method:feedback/operation/d5ab54cbb832027d", "not-yet-validated"]:
            apply_classifications(self.types, [self.record(parent=value)])
        for value in ["", " bad", "../bad", "a//b", "https://example.test", "a" * 201, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                apply_classifications(self.types, [self.record(parent=value)])

    def test_current_taxonomy_self_overlay_is_exact_noop(self):
        types = json.loads((Path(__file__).resolve().parents[1] / "data/method-families.json").read_text(encoding="utf-8"))
        records = [{"id": identifier, "classification": {
            "kind": kind,
            "methods": [family["id"] for family in types["families"] if identifier in family["related"]],
            "map_parent": "solve-lp2"}}
            for identifier, kind in types["record_kind_by_id"].items()]
        self.assertEqual(apply_classifications(types, records), types)

    def test_error_in_later_record_does_not_partially_mutate_input(self):
        original = copy.deepcopy(self.types)
        with self.assertRaises(ValueError):
            apply_classifications(self.types, [self.record("new"), self.record(kind="unknown")])
        self.assertEqual(self.types, original)


if __name__ == "__main__":
    unittest.main()
