"""Build small, deterministic reproduction archives from published record dependencies."""
import hashlib
import json
from pathlib import PurePosixPath
import zipfile


def build(root, record):
    experiment_id = record["id"]
    directory = f"experiments/records/{experiment_id}"
    names = {
        record["article_path"], record["reproduction"]["script"],
        f"{directory}/record.json", "scripts/verify_bundle.py",
        *(item["path"] for item in record["reproduction"]["inputs"]),
        *(item["path"] for item in record["reproduction"]["outputs"]),
    }
    omitted = []
    members = {}
    for name in sorted(names):
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise ValueError("Unsafe bundle member: " + name)
        source = (root / name).resolve()
        if not source.is_relative_to(root.resolve()):
            raise ValueError("Bundle member escapes repository: " + name)
        data = source.read_bytes()
        if name.startswith("images/") and path.suffix.lower() in (".jpg", ".jpeg", ".png"):
            omitted.append({"path": name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
        else:
            members[name] = data
    manifest = f"EXPERIMENT-{experiment_id}-CONTENTS.json"
    instructions = (
        f"{record['title']}\n\n"
        "Extract this ZIP with its folders intact. Run commands from the extracted folder.\n"
        "This archive contains the published record, account, scripts, declared non-image\n"
        "inputs, and recorded results. It is not an executable installer or a whole website.\n\n"
        f"Verify the files:\n  python scripts/verify_bundle.py {manifest}\n\n"
        f"Environment and external prerequisites:\n{record['reproduction']['environment']}\n\n"
    )
    if omitted:
        image_manifest = f"EXPERIMENT-{experiment_id}-IMAGE-INPUTS.json"
        members[image_manifest] = (json.dumps(omitted, indent=2) + "\n").encode("utf-8")
        instructions += (
            "Original image inputs are NOT included in this ZIP.\n"
            "Download https://jelliottdev.github.io/downloads/original-images.zip\n"
            "and extract it into the same folder, preserving images/.\n"
            f"Then verify the images required by this experiment:\n"
            f"  python scripts/verify_bundle.py {image_manifest}\n\n"
        )
    instructions += (
        f"Reproduce:\n  {record['reproduction']['command']}\n\n"
        f"Read the complete account in {record['article_path']} before running.\n"
        "A successful reproduction checks the published calculation; it does not\n"
        "automatically support the hypothesis. Keep findings and limitations together.\n"
        "External tools and Python packages are not installed or bundled.\n"
    )
    members[f"START-HERE-{experiment_id}.txt"] = instructions.encode("utf-8")
    contents = [{"path": name, "bytes": len(data),
                 "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in sorted(members.items())]
    members[manifest] = (json.dumps(contents, indent=2) + "\n").encode("utf-8")
    destination = root / "downloads/experiments" / f"{experiment_id}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    reusable = False
    if destination.exists():
        with zipfile.ZipFile(destination) as archive:
            reusable = (set(archive.namelist()) == set(members)
                        and all(archive.read(name) == data for name, data in members.items()))
    if not reusable:
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(members.items()):
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
    with zipfile.ZipFile(destination) as archive:
        assert len(archive.namelist()) == len(members)
        assert all(archive.read(name) == data for name, data in members.items())
    return destination.relative_to(root).as_posix(), len(members), len(omitted)
