"""Reproduce the manifest-driven feedback family census."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('feedback_suite', ROOT / 'experiments/engines/feedback_suite.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.main(default_manifest=ROOT / 'experiments/suites/feedback-opening-census/manifest.json')
