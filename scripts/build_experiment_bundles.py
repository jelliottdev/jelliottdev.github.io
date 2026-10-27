"""Build small, deterministic reproduction archives from published record dependencies."""
import hashlib
import json
from pathlib import PurePosixPath
import re
import zipfile
from reproduction_sources import read_pinned


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
    expected = {item['path']: item['sha256']
                for role in ('inputs', 'outputs') for item in record['reproduction'][role]}
    expected[record['reproduction']['script']] = record['reproduction']['script_sha256']
    for name in sorted(names):
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise ValueError("Unsafe bundle member: " + name)
        source = (root / name).resolve()
        if not source.is_relative_to(root.resolve()):
            raise ValueError("Bundle member escapes repository: " + name)
        if name in expected:
            # Resolve the pin again; compiled source_path is a presentation hint,
            # never authority. Keep the original member name for old scripts.
            try:
                data, _ = read_pinned(root, {'path': name, 'sha256': expected[name]})
            except ValueError as error:
                raise ValueError('Bundle dependency differs from reviewed hash: ' + name) from error
        else:
            data = source.read_bytes()
        shared_original = (name.startswith("images/") or
                           re.fullmatch(r"exports/sources/cicada-2014-seventh-onion/\d+\.jpg", name))
        if shared_original and path.suffix.lower() in (".jpg", ".jpeg", ".png"):
            omitted.append({"path": name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
        else:
            members[name] = data
    manifest = f"EXPERIMENT-{experiment_id}-CONTENTS.json"
    instructions = (
        f"{record['title']}\n\n"
        f"Experiment: {experiment_id}\n"
        f"Published account: https://jelliottdev.github.io/#/experiments/{experiment_id}\n\n"
        f"Question:\n{record['question']}\n\n"
        f"Reported outcome: {record['outcome']}\n"
        f"Finding:\n{record['finding']}\n\n"
        f"Limits:\n{record['limitations']}\n\n"
        f"Review:\n{record['review']['reviewer']}\n"
        f"Recorded retest date: {record['review']['retested_on']}\n\n"
        "Extract this ZIP with its folders intact. Run commands from the extracted folder.\n"
        "This archive contains the published record, account, scripts, declared non-image\n"
        "inputs, and recorded results. It is not an executable installer or a whole website.\n\n"
        "The bundled file verifier requires Python 3.9 or later. Individual experiments\n"
        "may have further requirements listed below.\n\n"
        f"Verify the files:\n  python scripts/verify_bundle.py {manifest}\n\n"
        f"Environment and external prerequisites:\n{record['reproduction']['environment']}\n\n"
    )
    if omitted:
        image_manifest = f"EXPERIMENT-{experiment_id}-IMAGE-INPUTS.json"
        members[image_manifest] = (json.dumps(omitted, indent=2) + "\n").encode("utf-8")
        instructions += (
            "Original image inputs are NOT included in this ZIP.\n"
            "Download https://jelliottdev.github.io/downloads/original-images.zip\n"
            "and extract it into the same folder, preserving every original path.\n"
            f"Then verify the images required by this experiment:\n"
            f"  python scripts/verify_bundle.py {image_manifest}\n\n"
        )
    instructions += (
        f"Reproduce:\n  {record['reproduction']['command']}\n\n"
        f"Read the complete account in {record['article_path']} before running.\n"
        "A successful reproduction checks the published calculation; it does not\n"
        "automatically support the hypothesis. Keep findings and limitations together.\n"
        "External tools and Python packages are not installed or bundled.\n\n"
        "If verification fails, retain the error and compare against a fresh extraction.\n"
        "Do not overwrite the expected results to turn a mismatch into a pass.\n"
        "Record your Python version, full command, terminal output and any changed inputs.\n"
        "A missing dependency or abnormal exit is not a negative result for the hypothesis.\n"
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
            reusable = (len(archive.namelist()) == len(members)
                        and set(archive.namelist()) == set(members)
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
