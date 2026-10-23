"""Run a registered family engine from a declared suite manifest."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINES = {"gp29-feedback-v1": "experiments/engines/feedback_suite.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    config = json.loads(manifest.read_text(encoding="utf-8"))
    engine = config.get("engine")
    if engine not in ENGINES:
        parser.error(f"Unregistered engine: {engine!r}")
    spec = importlib.util.spec_from_file_location("suite_engine", ROOT / ENGINES[engine])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    argv = ["--manifest", str(manifest)]
    if args.check:
        argv.append("--check")
    else:
        argv.append("--write")
    if args.output_dir:
        argv.extend(["--output-dir", str(args.output_dir.resolve())])
    module.main(argv=argv)


if __name__ == "__main__":
    main()
