"""Build all experiment-dependent views once, in dependency order. No Git push.

Edit record.json, run/review its experiment separately, then use this command.
A failed stage stops the build; this never runs experiments or changes outcomes.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    ('build_local_run_inputs.py',),
    ('build_experiments.py',),
    ('build_articles.py',),
    ('build_assistant.py',),
    ('build_access_exports.py',),
    ('build_research_map.py',),
    ('build_home_clusters.py', '.'),
    ('check_download_catalog.py',),
    ('build_research_map.py', '--check'),
)


PREVIEW_STAGES = (('build_experiments.py',), ('build_research_map.py',), ('build_home_clusters.py', '.'))


def build(root=ROOT, run=subprocess.run, preview=False):
    for script, *args in (PREVIEW_STAGES if preview else STAGES):
        print('Research build: ' + script, flush=True)
        run([sys.executable, str(root / 'scripts' / script), *args], cwd=root, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='Refresh record pages and map without rebuilding downloads; run the full build before publishing.')
    args = parser.parse_args()
    build(preview=args.preview)
    if args.preview:
        print('Preview ready. Downloads and catalog are unchanged; run the full build before publishing.')
