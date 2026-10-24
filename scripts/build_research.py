"""Build all experiment-dependent views once, in dependency order. No Git push.

Edit record.json, run/review its experiment separately, then use this command.
A failed stage stops the build; this never runs experiments or changes outcomes.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    ('build_experiments.py',),
    ('build_articles.py',),
    ('build_assistant.py',),
    ('build_access_exports.py',),
    ('build_research_map.py',),
    ('build_home_clusters.py', '.'),
    ('check_download_catalog.py',),
    ('build_research_map.py', '--check'),
)


def build(root=ROOT, run=subprocess.run):
    for script, *args in STAGES:
        print('Research build: ' + script, flush=True)
        run([sys.executable, str(root / 'scripts' / script), *args], cwd=root, check=True)


if __name__ == '__main__':
    build()
