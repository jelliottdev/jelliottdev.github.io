"""Execute only the frozen predictor/compression/provenance grid, after an audit gate."""
import argparse,ast,hashlib,json,math,time
from pathlib import Path
import numpy as np
import controls,calibration
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(path):
    manifest=read(H/'source-inputs.json');shape=read(H/'input-shape.json');raw=path.read_bytes()
    expected=next(r for r in manifest['files'] if r['path']=='liber-primus/data/krisyotam_runes.txt')
    assert len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256']
    gp=H/'source/liber-primus/src/lp/gematria.py';gp_pin=next(r for r in manifest['files'] if r['path']=='liber-primus/src/lp/gematria.py');assert sha(gp)==gp_pin['sha256']
    tree=ast.parse(gp.read_text(encoding='utf8'));table=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GEMATRIA' for t in n.targets)));runes={r[1]:i for i,r in enumerate(table)}
    segments=raw.decode('utf8').split('%');assert len(segments)==57
    pages=[np.asarray([runes[c] for c in s if c in runes],dtype=np.uint8) for s in segments[:55]]
    for a,r in zip(pages,shape['pages']):assert len(a)==r['length'] and hashlib.sha256(a.tobytes()).hexdigest()==r['indices_sha256']
    stream=np.concatenate(pages);assert len(stream)==shape['total_runes'] and hashlib.sha256(stream.tobytes()).hexdigest()==shape['stream_sha256']
    return stream,[r['length'] for r in shape['pages']]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--transcription',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    assert not a.output.exists(),'Refusing overwrite'
    authorization=read(H/'execution-authorization-frozen.json')
    for f,h in authorization['pins'].items():assert sha(H/f)==h,f
    assert authorization['authorized_target']=='fixed D02 target only after independent final control review'
    bank=read(H/'null-bank/receipt.json');assert sha(H/'null-bank/measurements.npz')==bank['measurements_sha256']
    start=time.perf_counter();stream,lengths=load(a.transcription);r=controls.evaluate(stream,lengths)
    with np.load(H/'null-bank/measurements.npz',allow_pickle=False) as z:reference=z['metrics']
    joint=calibration.compare(reference,r['values'],bank['tails']);uniform=math.log2(29)
    tolerance=read(H/'reporting-tolerance-addendum-frozen.json')['absolute_bits_per_rune_tolerance'];gains=[uniform-v for v in r['values'][:16]]
    out=dict(protocol_sha256=sha(H/'protocol-frozen.json'),authorization_sha256=sha(H/'execution-authorization-frozen.json'),source_stream_sha256=r['stream_sha256'],bank_receipt_sha256=sha(H/'null-bank/receipt.json'),names=bank['names'],tails=bank['tails'],observed=r,comparison=joint,uniform_bits_per_rune=uniform,predictive_bits_gain_over_uniform=gains,uniform_gain_interpretation=['better' if x>tolerance else 'worse' if x< -tolerance else 'equivalent' for x in gains],uniform_gain_equivalence_tolerance=tolerance,scored_positions=r['context']['scored_positions'],seconds=time.perf_counter()-start,limits='Finite selected models and fixed conditional filtered reference only. Lower than filtered controls need not beat uniform prediction. LZMA is whole-stream, not held-out; packed LZMA lacked planted power. No OTP/randomness/plaintext/cipher-family conclusion.')
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({k:v for k,v in out.items() if k not in ('observed','comparison')},indent=2));print('Joint rank',joint['family_rank'],'/',joint['family_reference_rows'],'gate',joint['gate'],flush=True)
if __name__=='__main__':main()
