"""Run this feedback suite; pass --manifest to run another compatible suite."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from engines.feedback_suite import main  # noqa: E402


if __name__ == "__main__":
    main(default_manifest=HERE / "manifest.json")
