"""Time original one-process T3 versus the level-isolated two-worker helper."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from check_fullbook import same

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[4]
ROOT = WORK / "research-wiki"
BENCH = WORK / "t3-kjv-fullbook-20261023" / "original-benchmark"
T3 = BENCH / "liber-primus/analysis/round19/T3"
OUT = WORK / "t3-kjv-fullbook-20261023" / "benchmark-parallel.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timed(command, cwd=None, env=None):
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return {"seconds": round(time.perf_counter() - start, 3),
            "command": command, "output": result.stdout}


def main():
    plan = json.loads((HERE / "fullbook-benchmark-plan.json").read_text(encoding="utf-8"))
    assert sha(T3 / "t3_decode.py") == plan["source_script_sha256"]
    assert sha(BENCH / "liber-primus/data/kjv.txt") == plan["kjv_sha256"]
    env = os.environ.copy()
    env["T3_KBOOK"] = "0,50"
    source = timed([sys.executable, "t3_decode.py", "12956", "1", "KJV"], cwd=T3, env=env)
    helper = timed([sys.executable, str(ROOT / "experiments/records/rune-reading-sensitivity-t3/replay_fullbook_parallel.py"),
                    "--length", "12956", "--reps", "1", "--register", "KJV", "--levels", "0,50",
                    "--jobs", "2", "--compare", str(T3 / "out_decode_L12956_KJV.json"), "--output", str(OUT)], cwd=ROOT)
    original = T3 / "out_decode_L12956_KJV.json"
    same(json.loads(original.read_text(encoding="utf-8")), json.loads(OUT.read_text(encoding="utf-8")))
    receipt = {"schema": "liberpedia-t3-parallel-benchmark-receipt-v1",
               "plan_sha256": sha(HERE / "fullbook-benchmark-plan.json"),
               "source_script_sha256": sha(T3 / "t3_decode.py"),
               "kjv_sha256": sha(BENCH / "liber-primus/data/kjv.txt"),
               "helper_sha256": sha(ROOT / "experiments/records/rune-reading-sensitivity-t3/replay_fullbook_parallel.py"),
               "logical_cpu_count": os.cpu_count(), "grid": plan["grid"],
               "original_one_process": {"seconds": source["seconds"], "output_sha256": sha(original)},
               "helper_jobs2": {"seconds": helper["seconds"], "output_sha256": sha(OUT)},
               "scientific_fields_equal_except_seconds": True,
               "source_stdout": source["output"], "helper_stdout": helper["output"]}
    dest = HERE / "fullbook-benchmark-receipt.json"
    dest.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"original_seconds": source["seconds"], "helper_jobs2_seconds": helper["seconds"],
                      "scientific_fields_equal_except_seconds": True, "receipt": str(dest)}))


if __name__ == "__main__":
    main()
