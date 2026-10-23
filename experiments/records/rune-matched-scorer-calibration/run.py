"""Execute the pinned R16 scorer calibration and retain exact solved texts.

The original result path is generated transiently inside our bundled source
copy; top-level results and texts are written with LF line endings.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE / "source" / "liber-primus"
MOD = LP / "analysis" / "round16" / "scorer"
sys.dont_write_bytecode = True
sys.path.insert(0, str(LP / "src"))
sys.path.insert(0, str(MOD))


def main():
    spec = importlib.util.spec_from_file_location("pinned_r16_measure", MOD / "measure.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main() == 0
    old = module.eng_score.default()
    solved = [{"page": name, "file": file, "text": txt}
              for name, file, txt in module.get_solved_page_texts(old)]
    generated = MOD / "results.json"
    result = json.loads(generated.read_text(encoding="utf-8"))
    pinned = json.loads((MOD/"original_results.json").read_text(encoding="utf-8"))
    # The source report contains a narrative note with an arithmetic typo;
    # the operational measurements and gates must agree exactly.
    for key in ("matched_model", "solved_pages", "null", "separation", "gates", "verdict"):
        assert result[key] == pinned[key], key
    generated.unlink()
    (HERE/"solved_texts.json").write_text(
        json.dumps(solved, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    (HERE/"results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print("Pinned scorer replay: five solved texts, 200 random-key nulls; source measurements agree.")


if __name__ == "__main__":
    main()
