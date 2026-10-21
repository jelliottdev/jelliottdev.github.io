"""Offline full-corpus reproduction, including independent checks and all ranks.

Requires an existing Git source repository with the pinned objects available.
No source-repository code runs. A failed stage stops the pipeline immediately.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]


def reproduce(source,output):
    source=source.resolve();output=output.resolve()
    if not source.is_dir():raise ValueError('Source must be an existing Git repository directory')
    if output.exists():raise ValueError('Use a new output directory; retain prior runs and checkpoints')
    report=output/'report.json';source_receipt=output/'audit-receipt.json'
    comparison=output/'comparison.json';comparison_receipt=output/'comparison-receipt.json'
    stages=[
        ('Measure every pinned source path','run_corpus_prefixes.py',[source,'--output',output]),
        ('Independently audit source bytes and statistics','check_corpus_prefixes.py',[source,report,'--receipt',source_receipt]),
        ('Calculate all declared comparisons','compare_corpus_prefixes.py',[report,source_receipt,'--output',comparison]),
        ('Independently reconstruct ranks and ties','check_corpus_comparison.py',[report,source_receipt,comparison,'--receipt',comparison_receipt]),
        ('Render all audited measures and weights','render_corpus_comparison.py',[report,source_receipt,comparison,comparison_receipt,'--output',output/'presentation']),
    ]
    for title,script,arguments in stages:
        print(title,flush=True)
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*[str(p) for p in arguments]],cwd=ROOT,check=True)
    print('Full source and comparison checks passed. Review the complete presentation and provenance limits before interpretation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    reproduce(args.source,args.output)
