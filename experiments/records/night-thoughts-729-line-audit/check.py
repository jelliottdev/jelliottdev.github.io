"""Independent spot verification of the six edition-specific line pointers."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    lines = (ROOT / plan["inputs"][0]["path"]).read_text(encoding="utf-8-sig").splitlines()
    # Text location, preceding numbered marker, following numbered marker.
    # These were read independently from the edition; the producer does not
    # supply the coordinates to this checker.
    evidence = [
        ("FOURTH", 3387, 3378, 720, 3388, 730, 729, "Hold her sacred still"),
        ("FIFTH", 4247, 4238, 720, 4258, 740, 729, "thunder scarce obtains your ear"),
        ("SIXTH", 5405, 5404, 728, 5410, 734, 729, "Eternal; or in man the series ends"),
        ("SEVENTH", 6348, 6339, 720, 6349, 730, 729, "blind Passion! drive us on"),
        ("EIGHTH", 7849, 7840, 720, 7860, 740, 729, "the Muse, to win thine ear"),
        ("NINTH", 9293, 9290, 728, 9302, 740, 731, "deep reception, in th' intender'd heart"),
    ]
    assert len(evidence) == len(result["candidates"]) == 6
    for row, (night, target_line, before_line, before_number, after_line, after_number, number, phrase) in zip(result["candidates"], evidence):
        assert phrase in lines[target_line - 1]
        assert lines[before_line - 1].strip().endswith(str(before_number))
        assert lines[after_line - 1].strip().endswith(str(after_number))
        assert before_number + target_line - before_line == number
        assert after_number - (after_line - target_line) == number
        assert (row["night"], row["comparison_edition_file_line_one_based"], row["comparison_edition_verse_line"]) == (night, target_line, number)
    counts = []
    for item in plan["inputs"][1:]:
        counts.append(sum(0x16A0 <= ord(c) <= 0x16FF for c in (ROOT / item["path"]).read_text(encoding="utf-8")))
    assert counts == [262, 266, 201]
    assert result["rune_total"] == sum(counts) == 729
    assert result["line_matches"] == 5
    print("Independent Night Thoughts markers, six lines, and three rune counts checked")


if __name__ == "__main__":
    main()
