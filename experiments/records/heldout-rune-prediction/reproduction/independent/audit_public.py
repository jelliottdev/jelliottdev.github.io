"""Recompute all 26 saved target metrics with the exact external transcription.

The unchanged independent audit_target.py is run in a disposable staged copy.
No target inference, tuning, reference generation or network access is performed.
"""
import argparse, hashlib, importlib.util, json, shutil, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True

def run(record_root, transcription):
    reproduction = record_root/'reproduction'
    manifest = json.loads((reproduction/'source-inputs.json').read_bytes())
    relative = 'liber-primus/data/krisyotam_runes.txt'
    pin = next(row for row in manifest['files'] if row['path']==relative)
    raw = transcription.read_bytes()
    if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('External transcription does not match the pinned source bytes')
    with tempfile.TemporaryDirectory(prefix='d02-independent-') as temporary:
        stage = Path(temporary)/'reproduction'
        shutil.copytree(reproduction,stage,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        destination=stage/'source'/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
        independent=stage/'independent'
        sys.path.insert(0,str(independent))
        try:
            spec=importlib.util.spec_from_file_location('d02_independent_target',independent/'audit_target.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            return module.run(stage)
        finally:
            sys.path.remove(str(independent))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-root',required=True,type=Path)
    parser.add_argument('--transcription',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output and args.output.exists():raise FileExistsError('Refusing to overwrite receipt')
    receipt=run(args.record_root.resolve(),args.transcription.resolve())
    receipt['portable_adapter_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output:args.output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
