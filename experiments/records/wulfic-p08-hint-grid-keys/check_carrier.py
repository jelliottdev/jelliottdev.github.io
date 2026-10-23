"""Cross-check the source's P08 row strings against archived LP1-08 OutGuess bytes."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"experiments/records/outguess-default-key"
PAYLOAD=OUT/"results/lp1-08.bin"
IMAGE=ROOT/"images/lp1-08.jpg"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    plan=json.loads((HERE/"plan.json").read_text(encoding="utf-8"))
    extraction_plan=json.loads((OUT/"plan.json").read_text(encoding="utf-8"))
    report=json.loads((OUT/"results/report.json").read_text(encoding="utf-8"))
    entry=next(x for x in report["records"] if x["image"]=="lp1-08")
    image_row=next(x for x in extraction_plan["images"] if x["id"]=="lp1-08")
    raw=PAYLOAD.read_bytes()
    assert len(raw)==140 and raw.decode("ascii").startswith("\nFor those who have fallen behind:")
    assert entry["returncode"]==0 and entry["bytes"]==len(raw)
    assert entry["sha256"]==sha(PAYLOAD)
    assert entry["image_sha256"]==image_row["sha256"]
    if IMAGE.exists():assert sha(IMAGE)==image_row["sha256"]
    lines=raw.decode("ascii").splitlines()
    assert lines[2]==""
    first=lines[3].split();second=lines[4].split()
    assert first==plan["source_grid"]["row1"]
    assert second==plan["source_grid"]["row2"]
    return {"schema":"wulfic-p08-carrier-audit-v1","carrier":"images/lp1-08.jpg","carrier_sha256":image_row["sha256"],"saved_extraction":"experiments/records/outguess-default-key/results/lp1-08.bin","extraction_sha256":sha(PAYLOAD),"extraction_length":len(raw),"outguess_returncode":entry["returncode"],"source_paired_rows_match_exactly":True,"row1":first,"row2":second,"label_note":"The source's P08 is the current LP1-08 image. The archived OutGuess extraction contains the two rows verbatim."}

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true");a=ap.parse_args()
    audit=build();dest=HERE/"carrier-audit.json"
    if a.check:
        assert audit==json.loads(dest.read_text(encoding="utf-8"))
        print("PASS LP1-08 archived payload, carrier receipt and source grid rows")
    else:
        dest.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8",newline="\n")
        print(audit["extraction_sha256"])
