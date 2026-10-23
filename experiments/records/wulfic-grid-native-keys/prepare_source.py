"""Export numerical Stage N inputs from a pinned external checkout; no source code is bundled."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
STAGE_SHA = "b3445d5e04eea89865898f8eafa40b2d5abd7948fb1f4e1b2b667a63a5f1a5c4"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == COMMIT
    assert hashlib.sha256((source / "tools/run_stage_n.py").read_bytes()).hexdigest() == STAGE_SHA
    program = '''
import json
from itertools import islice
from tools.lpcore import detect, keys
from tools.lpcore.ciphers import primes
from tools.lpcore.corpus import load_corpus
from tools.lpcore.solved import DIVINITY, FIRFUMFERENFE
from tools.lpcore.verify import load_translation
from tools.run_stage_n import byte_keys
c=load_corpus()
q=detect.unigram([r for w in keys.solved_plaintext_words(c,load_translation()) for r in w])
profile={"grid_bytes":keys.grid_bytes(c),"grid_digits":keys.grid_digits(c),"byte_keys":byte_keys(c),"rune_keys":{"phi(prime)":[p-1 for p in islice(primes(),800)],"DIVINITY":list(DIVINITY)*100,"FIRFUMFERENFE":list(FIRFUMFERENFE)*60},"unigram":q}
print(json.dumps(profile,separators=(',',':')))
'''
    result = subprocess.check_output([sys.executable, "-c", program], cwd=source, text=True)
    profile = json.loads(result)
    assert len(profile["grid_bytes"]) == 256 and len(profile["grid_digits"]) == 512
    assert len(profile["byte_keys"]) == 12 and len(profile["rune_keys"]) == 3
    assert len(profile["unigram"]) == 29
    (HERE / "source-profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
