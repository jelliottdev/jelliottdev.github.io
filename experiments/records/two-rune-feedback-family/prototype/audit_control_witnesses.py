"""Check every retained failed known-input witness with unchanged source functions."""
import json
import hashlib
from pathlib import Path
import engine as e

HERE=Path(__file__).resolve().parent


def main():
    saved=json.loads((HERE/'control-witnesses.json').read_bytes())
    prototype=json.loads((HERE/'prototype-results.json').read_bytes())
    checked=0;max_error=0.0
    for row in saved['witnesses']:
        truth=saved['true_passages'][row['text']]
        function=e.source.F_BASIS[row['function']]
        cipher=e.source.encipher(truth,function,2,row['true_primer'],source=row['source'],sign=row['sign'])
        chosen=e.source.decode(cipher,function,2,row['selected_primer'],source=row['source'],sign=row['sign'])
        assert chosen==row['selected_full_indices']
        assert hashlib.sha256(bytes(chosen)).hexdigest()==row['selected_sha256']
        assert e.source.idx_to_trans(chosen)==row['selected_transliteration']
        max_error=max(max_error,abs(e.source.score_norm(chosen[2:])-row['selected_score']))
        mismatch=[i for i,(a,b) in enumerate(zip(truth,chosen)) if a!=b]
        assert mismatch==row['mismatch_positions_zero']
        assert [i for i in mismatch if i>=2]==row['scored_tail_mismatch_positions_zero']
        checked+=1
    expected=sum(not c['search_gate_pass'] for b in prototype['branches'] if b['direction']=='forward' for c in b['controls'])
    assert checked==expected==60 and max_error<=1e-12
    print('PASS:',checked,'retained failed forward controls; source score error',max_error,'; no targets loaded.')


if __name__=='__main__':main()
