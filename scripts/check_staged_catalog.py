"""Check catalog hashes against bytes Git will publish, not working-tree line endings."""

import hashlib
import json
import subprocess


def staged(path):
    return subprocess.check_output(["git", "show", f":{path}"])


catalog = json.loads(staged("data/catalog.json"))
changed = set(
    subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"])
    .decode("utf-8")
    .strip("\0")
    .split("\0")
)
checked = 0
for entry in catalog["files"]:
    path = entry["path"]
    if path not in changed:
        continue
    content = staged(path)
    assert len(content) == entry["bytes"], f"Staged size differs: {path}"
    assert hashlib.sha256(content).hexdigest() == entry["sha256"], f"Staged hash differs: {path}"
    checked += 1
print(f"PASS: {checked} changed catalogued files match the staged Git bytes")
