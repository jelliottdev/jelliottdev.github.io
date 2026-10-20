"""Apply selected editorial observations without replacing archive measurements."""
import hashlib
import json
from pathlib import Path

ROOT = Path(globals().get("OUTPUT_ROOT", Path(__file__).resolve().parents[1]))
SOURCE = "data/evidence/editorial-page-notes.json"


def apply_notes(root=ROOT):
    evidence = json.loads((root / SOURCE).read_text(encoding="utf-8"))
    index = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
    updates = []
    for entry in evidence["records"]:
        pid = entry["page"]
        summary = next(p for p in index["pages"] if p["id"] == pid)
        path = root / "data/pages" / (pid + ".json")
        page = json.loads(path.read_text(encoding="utf-8"))
        digest = hashlib.sha256((root / "images" / (pid + ".jpg")).read_bytes()).hexdigest()
        if digest != entry["image_sha256"] or digest != page["image_sha256"]:
            raise ValueError(f"{pid}: original image differs from reviewed evidence")
        width, height = page["image_dimensions"]
        for note in entry["notes"]:
            if "rect" in note:
                x, y, w, h = note["rect"]
                if not all(type(v) is int for v in [x,y,w,h]) or min(x,y)<0 or min(w,h)<=0 or x+w>width or y+h>height:
                    raise ValueError(f"{pid}: invalid inspection rectangle")
        page["notes"] = [n for n in page["notes"] if n.get("source") != SOURCE]
        page["notes"].extend(dict(n, source=SOURCE) for n in entry["notes"])
        summary["notes_text"] = " ".join(n["title"] + " " + n["text"] for n in page["notes"])
        updates.append((path, page))
    for path, value in [*updates, (root / "data/index.json", index)]:
        path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    print(f"Applied original-image observations to {len(updates)} page records.")


if __name__ == "__main__":
    apply_notes()
