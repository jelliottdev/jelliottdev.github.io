"""Quick independent saved-evidence audit, not the full control/target replay."""
import sys,json,argparse
from pathlib import Path
sys.dont_write_bytecode=True
import run

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.parse_args()
    root=Path(__file__).resolve().parent
    record=run.read(root/'record.json')
    repo=root.parents[2]
    for row in record['reproduction']['inputs']+record['reproduction']['outputs']:
        assert run.sha(repo/row['path'])==row['sha256'],row['path']
    r=run.configured()
    for module,expected in [('audit_control','control-failure-audit.json'),('audit_target','independent-target-audit.json')]:
        captured={};r.write=lambda name,obj:captured.update({name:obj})
        audit=run.load(module,root/(module+'.py'));audit.main()
        run.equivalent(captured[expected],run.read(root/expected))
    print('PASS: declared hashes, independent raw-table scoring/beam control audit, all eight admissible target paths, aliases, ordering and selected null arithmetic.')
if __name__=='__main__':main()
