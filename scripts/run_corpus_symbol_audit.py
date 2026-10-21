"""Measure, independently verify, and export the pinned corpus symbol audit.

Requires Python 3, Git, this repository and the pinned source Git objects.
Offline only; no third-party source code executes. Stops on the first failure.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(repository,output):
    repository=repository.resolve();output=output.resolve()
    if not repository.is_dir():raise ValueError('Source repository directory does not exist')
    if output.exists():raise ValueError('Use a new output directory; existing runs are preserved')
    stages=[
        ('Measure every source prefix','corpus_symbol_inventory.py',[repository,'--output',output]),
        ('Verify source symbols and reconcile the earlier census','check_corpus_symbol_inventory.py',
            [repository,output/'report.json','--receipt',output/'audit.json']),
        ('Export verified tables and coverage figure','export_corpus_symbols.py',
            [output/'report.json',output/'audit.json','--output',output/'presentation'])]
    for label,script,args in stages:
        print(label,flush=True)
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*[str(a) for a in args]],cwd=ROOT,check=True)
    print('Complete source audit passed. Tables and coverage figure are in presentation/.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.repository,args.output)
