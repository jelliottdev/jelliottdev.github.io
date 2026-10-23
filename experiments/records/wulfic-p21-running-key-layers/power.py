"""Post-target one-page natural-language gate diagnostic."""
import hashlib
import argparse
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run

def calculate(source, variant):
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    corpora={name:run.source_running_text(run.source_bytes(source,'data/corpora/'+filename+'.txt',plan)) for name,filename in [('deor','deor_poem'),('self_reliance','self_reliance')]}
    raw=run.source_bytes(source,'pages/page_21/runes.txt',plan).decode('utf8').strip()
    lengths=run.source_words(raw)
    if variant=='known-reading':
        evidence=run.ROOT/'data/evidence/known-readings.json'
        v3plan=json.loads((HERE/'power-addendum-v3-plan.json').read_text(encoding='utf8'))
        assert hashlib.sha256(evidence.read_bytes()).hexdigest()==v3plan['known_readings_sha256']
        controls=json.loads(evidence.read_text(encoding='utf8'))['controls']
        welcome=next(c for c in controls if c['id']=='welcome')['decoded_pages']
        known=welcome[0]['rune_indices']+welcome[1]['rune_indices'][:10]
    else:
        known=corpora['deor'][:sum(lengths)]
    assert len(known)==sum(lengths)
    lex={w.strip().upper() for w in run.source_bytes(source,'data/corpora/wordlist.txt',plan).decode().splitlines() if 3<=len(w.strip())<=15}
    key_name='deor' if variant=='original' else 'self_reliance'
    key=run.key_for(corpora[key_name],0,len(known))
    cipher=run.encrypt(known,key,'sub')
    decoded=run.decode(cipher,key,'sub')
    result=run.search([('lp2-04',cipher,lengths,run.CONFIG[21][1])],corpora,lex,True)
    top=result['top']; true_rank=next((i+1 for i,row in enumerate(top) if row['branch']=='running' and row['corpus']==key_name and row['offset']==0 and row['mode']=='sub'),None)
    file={'original':'power-addendum-plan.json','independent-key':'power-addendum-v2-plan.json','known-reading':'power-addendum-v3-plan.json'}[variant]
    version={'original':'v1','independent-key':'v2','known-reading':'v3'}[variant]
    output={'schema':'wulfic-p21-running-key-posttarget-power-'+version,
            'plan_sha256':hashlib.sha256((HERE/file).read_bytes()).hexdigest(),
            'key_source':key_name,
            'known_sha256':run.digest(bytes(known)),'cipher_sha256':run.digest(bytes(cipher)),
            'full_recovery':decoded==known,'known_ioc':run.ioc(known),'known_word_score':run.score(known,lengths,lex)[0],
            'true_rank':true_rank,'grid_counts':result['counts'],'best':result['global_best']}
    if variant=='original':
        output.pop('key_source')  # preserve the first addendum's bytes and schema
    return output

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=run.DEFAULT_SOURCE);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    for variant,name in (('original','power-addendum.json'),('independent-key','power-addendum-v2.json'),('known-reading','power-addendum-v3.json')):
        output=calculate(args.source_root,variant)
        path=HERE/name
        if args.check:assert json.loads(path.read_text(encoding='utf8'))==output,name
        else:path.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
        print(variant,output['full_recovery'],output['known_ioc'],output['known_word_score'],output['true_rank'])

if __name__=='__main__':main()
