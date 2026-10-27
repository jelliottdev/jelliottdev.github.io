"""Build all experiment-dependent views once, in dependency order. No Git push.

Edit record.json, run/review its experiment separately, then use this command.
A failed stage stops the build. Declared count projections are independently
rechecked; exploratory searches and published outcomes are never changed.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    ('build_local_run_inputs.py',),
    ('build_finite_sequence_banks.py',),
    ('build_repeating_key_banks.py', '--check'),
    ('build_published_count_evidence.py',),
    ('build_published_evidence_history.py',),
    ('build_experiments.py',),
    ('build_published_program_catalog.py', '--write'),
    ('build_pinned_parent_artifacts.mjs', '--write'),
    ('build_compiled_program_index.mjs',),
    ('build_evidence_registry_fingerprint.mjs',),
    ('build_published_program_discovery.mjs', '--write'),
    ('archive_authored_sources.py', '--write'),
    ('build_articles.py',),
    ('build_assistant.py',),
    ('build_access_exports.py',),
    ('build_research_map.py',),
    ('build_home_clusters.py', '.'),
    ('check_download_catalog.py',),
    ('build_research_map.py', '--check'),
)


PREVIEW_STAGES = (('build_experiments.py',), ('build_research_map.py',), ('build_home_clusters.py', '.'))


def build(root=ROOT, run=subprocess.run, preview=False, node_executable='node'):
    for script, *args in (PREVIEW_STAGES if preview else STAGES):
        print('Research build: ' + script, flush=True)
        interpreter = node_executable if script.endswith('.mjs') else sys.executable
        run([interpreter, str(root / 'scripts' / script), *args], cwd=root, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='Refresh record pages and map without rebuilding downloads; run the full build before publishing.')
    args = parser.parse_args()
    build(preview=args.preview)
    if args.preview:
        print('Preview ready. Downloads and catalog are unchanged; run the full build before publishing.')
