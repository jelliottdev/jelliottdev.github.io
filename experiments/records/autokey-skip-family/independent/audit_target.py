"""All autokey target witnesses plus declared unchanged-native terminal sample."""
import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
from check_parity import native_terminals

def valid_pointers(cipher,plain,primer,mode,sign):
    L=len(cipher);lp=len(primer);limit=max(lp+L,4*L+8)
    if len(plain)!=L or (cipher[0]+sign*primer[0])%29!=plain[0]:return set()
    def key(t,known):
        if t<lp:return primer[t]
        u=t-lp
        if mode=='P':return plain[u] if u<known else None
        return cipher[u] if u<L else 0
    pointers={0}
    for i in range(1,L):
        nxt=set()
        for previous in pointers:
            for advance in range(1,5):
                accepted=previous+advance
                if mode=='C' and accepted>=limit:break
                value=key(accepted,i)
                if value is None:break
                if (cipher[i]+sign*value)%29!=plain[i]:continue
                if all(key(t,i) is not None and (plain[i]-sign*key(t,i))%29==cipher[i-1] for t in range(previous+1,accepted)):nxt.add(accepted)
        pointers=nxt
        if not pointers:break
    return pointers

def run(root):
    start=time.perf_counter();read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    protocol=read(root/'target-protocol-frozen.json');result=read(root/'results.json')
    for path,digest in protocol['pins'].items():assert sha(root/path)==digest,path
    assert result['protocol_sha256']==sha(root/'target-protocol-frozen.json') and result['measurements_sha256']==sha(root/'measurements.npz')
    sys.path.insert(0,str(root.resolve()));spec=importlib.util.spec_from_file_location('independent_autokey_target_engine',root/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);native=native_terminals(root,e.env)
    primers=e.primers();assert len(primers)==45 and len({tuple(p) for _,p in primers})==45
    alphabet={row[1]:row[0] for row in e.gp.GEMATRIA};spelling={row[0]:row[2] for row in e.gp.GEMATRIA}
    text=(root/'source/liber-primus/data/krisyotam_runes.txt').read_text(encoding='utf8');pages=[[alphabet[c] for c in s if c in alphabet] for s in text.split('%')];pages=[p for p in pages if p][:-2]
    assert len(pages)==55 and sum(map(len,pages))==12956
    assert [hashlib.sha256(np.asarray(p,dtype='<i8').tobytes()).hexdigest() for p in pages]==result['page_array_sha256'] and list(map(len,pages))==result['source_page_lengths']
    counts={};total=0
    for line in (root/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():q,c=line.split();counts[q]=int(c);total+=int(c)
    logtotal=math.log10(total);model={q:math.log10(c)-logtotal for q,c in counts.items()};floor=math.log10(.01)-logtotal
    def scores(path):
        letters=[];cumulative=0.;sequential=0.
        for rune in path:
            delta=0.
            for char in spelling[int(rune)]:
                letters.append(char)
                if len(letters)>=4:
                    value=model.get(''.join(letters[-4:]),floor);delta+=value;sequential+=value
            cumulative+=delta
        return cumulative,sequential/(len(letters)-3) if len(letters)>3 else -999.
    with np.load(root/'measurements.npz',allow_pickle=False) as z:data={name:z[name] for name in z.files}
    required={'scores','cumulative','pointers','terminal_count','terminal_max','terminal_rank','lengths','source_winner','normalized_winner'};assert set(data)==required
    shape=(55,45,2,2);assert result['cases']==9900
    for name in required-{'lengths','source_winner','normalized_winner'}:assert data[name].shape==shape and np.isfinite(data[name]).all()
    assert data['lengths'].tolist()==list(map(len,pages))
    for name in ('source_winner','normalized_winner'):assert data[name].shape==(*shape,max(map(len,pages)))
    assert np.all((data['terminal_count']>=1)&(data['terminal_count']<=450)) and np.all((data['terminal_rank']>=1)&(data['terminal_rank']<=data['terminal_count']))
    assert np.all(data['terminal_max']>=data['scores'])
    rigid=0;checked=0
    for ix in np.ndindex(shape):
        page,j,m,s=ix;cipher=pages[page];primer=primers[j][1];mode=('P','C')[m];sign=(-1,1)[s];L=len(cipher)
        output=data['source_winner'][ix][:L].tolist();other=data['normalized_winner'][ix][:L].tolist()
        assert all(0<=v<29 for v in output+other) and np.all(data['source_winner'][ix][L:]==-1) and np.all(data['normalized_winner'][ix][L:]==-1)
        cumulative,value=scores(output);assert cumulative==data['cumulative'][ix] and value==data['scores'][ix],('score',ix)
        assert scores(other)[1]==data['terminal_max'][ix]
        pointers=valid_pointers(cipher,output,primer,mode,sign);assert int(data['pointers'][ix]) in pointers,('source admissibility',ix)
        assert valid_pointers(cipher,other,primer,mode,sign),('normalized admissibility',ix)
        if mode=='P':
            assert 0<=int(data['pointers'][ix])-(L-1)<=len(primer)-1
            if len(primer)==1:
                plain=[]
                for i,c in enumerate(cipher):plain.append((c+sign*(primer[0] if i==0 else plain[i-1]))%29)
                assert output==plain and other==plain and data['terminal_count'][ix]==1 and data['pointers'][ix]==L-1;rigid+=1
        if int(data['terminal_rank'][ix])==1:assert output==other
        checked+=1
    assert rigid==result['singleton_P_labels']==3190 and result['non_singleton_P_and_all_C_labels']==6710
    flat_scores=data['scores'].ravel();flat_max=data['terminal_max'].ravel();order=np.argsort(-flat_scores,kind='stable');source_hits=np.flatnonzero(flat_scores> -5.5);normalized_hits=np.flatnonzero(flat_max> -5.5)
    assert len(source_hits)==result['source_hits'] and len(normalized_hits)==result['normalized_terminal_hits'] and int(data['terminal_count'].sum())==result['retained_terminal_hypotheses'] and int((data['terminal_max']>data['scores']).sum())==result['normalized_improvements']
    def witness(flat,kind='source'):
        ix=np.unravel_index(int(flat),shape);p,j,m,s=map(int,ix);plain=data['source_winner' if kind=='source' else 'normalized_winner'][ix][:len(pages[p])].tolist()
        return dict(page=p,physical_page=f'lp2-{p if p<50 else p+1:02d}',primer_index=j,primer_label=primers[j][0],primer=primers[j][1],mode=('P','C')[m],sign=(-1,1)[s],kind=kind,score=float(data['scores' if kind=='source' else 'terminal_max'][ix]),source_score=float(data['scores'][ix]),terminal_count=int(data['terminal_count'][ix]),terminal_rank=1 if kind=='source' else int(data['terminal_rank'][ix]),plain=plain,translit=''.join(spelling[v] for v in plain))
    assert result['global_best']==witness(order[0]) and result['top40']==[witness(i) for i in order[:40]]
    assert result['source_hit_witnesses']==[witness(i) for i in source_hits] and result['normalized_hit_witnesses']==[witness(i,'normalized') for i in normalized_hits]
    selected=set(range(0,9900,97))|{9899}|set(map(int,order[:40]))|set(map(int,source_hits))|set(map(int,normalized_hits))|{int(np.argmax(flat_max))}
    for page in range(55):selected.add(page*180+int(np.argmax(data['scores'][page])))
    for mode in range(2):
        sub=data['scores'][:,:,mode,:];p,j,s=np.unravel_index(int(np.argmax(sub)),sub.shape);selected.add(int(np.ravel_multi_index((p,j,mode,s),shape)))
    native_hypotheses=0
    for flat in sorted(selected):
        ix=np.unravel_index(flat,shape);page,j,m,s=map(int,ix);terminals=native[('P','C')[m]](pages[page],primers[j][1],sign=(-1,1)[s],beam_w=450,max_skip=3);native_hypotheses+=len(terminals);L=len(pages[page]);norms=[scores(t[3])[1] for t in terminals];best=max(range(len(norms)),key=lambda i:norms[i])
        assert len(terminals)==data['terminal_count'][ix] and list(terminals[0][3])==data['source_winner'][ix][:L].tolist()
        assert terminals[0][0]==data['cumulative'][ix] and terminals[0][1]==data['pointers'][ix] and norms[0]==data['scores'][ix]
        assert best+1==data['terminal_rank'][ix] and norms[best]==data['terminal_max'][ix] and list(terminals[best][3])==data['normalized_winner'][ix][:L].tolist()
    return dict(status='PASS',protocol_sha256=sha(root/'target-protocol-frozen.json'),result_sha256=sha(root/'results.json'),script_sha256=sha(Path(__file__)),all_source_witnesses_rescored_and_pointer_validated=checked,all_normalized_witnesses_rescored_and_validated=checked,singleton_P_rigid_equal_cases=rigid,native_complete_beams_checked=len(selected),native_retained_terminal_hypotheses_checked=native_hypotheses,all_gate_crossing_beams_in_native_selection=True,source_hits=len(source_hits),normalized_terminal_hits=len(normalized_hits),normalized_improvements=result['normalized_improvements'],global_best=result['global_best'],coverage='Complete rescoring/admissibility of both9900winner sets; complete accounting and allcrossing/top40/pageleaders/fixedsample native beams. Not a second full9900native-beam run.',limits='Amended historical algorithm diagnostic; source-generated control mismatches and singleton rigid overlap retained. No general autokey, OTP, plaintext or cipher-family verdict.',seconds=time.perf_counter()-start)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--producer-root',type=Path,required=True);parser.add_argument('--output',type=Path);parser.add_argument('--check-only',action='store_true');a=parser.parse_args();assert a.output or a.check_only
    if a.output:assert not a.output.exists(),'Refusing overwrite'
    result=run(a.producer_root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2))
