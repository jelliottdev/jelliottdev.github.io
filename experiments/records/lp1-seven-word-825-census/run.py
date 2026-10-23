"""Run the LP1 seven-word census from its experiment folder."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_lp1_825_window  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = audit_lp1_825_window.report()
    output = audit_lp1_825_window.OUTPUT
    if args.check:
        if json.loads(output.read_text(encoding="utf-8")) != result:
            raise SystemExit("Saved census differs from source traces")
        print("PASS LP1 seven-word GP-825 census")
    else:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        print("Wrote", output.relative_to(ROOT))
