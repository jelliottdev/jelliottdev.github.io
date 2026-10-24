"""Complete target accounting and declared sampled unchanged-native beam checks."""
import argparse,ast,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np

def run(root):
    started=time.perf_counter();read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    protocol=read(root/'target-protocol-frozen.json');result=read(root/'results.json')
    for path,digest in protocol['pins'].items():assert sha(root/path)==digest,path
    assert result['protocol_sha256']==sha(root/'target-protocol-frozen.json')
    for path,digest in result['artifacts'].items():assert sha(root/path)==digest,path
    spec=importlib.util.spec_from_file_location('keyword_target_audit_engine',root/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
    words=read(root/'keywords-frozen.json');assert [(w['label'],w['key']) for w in words]==e.words()
    assert len(words)==623 and len({tuple(w['key']) for w in words})==617 and sum(len(w['key']) for w in words)==2814
    alphabet={row[1]:row[0] for row in e.gp.GEMATRIA};spelling={row[0]:row[2] for row in e.gp.GEMATRIA}
    raw=(root/'source/liber-primus/data/krisyotam_runes.txt').read_text(encoding='utf8')
    pages=[[alphabet[c] for c in segment if c in alphabet] for segment in raw.split('%')];pages=[p for p in pages if p][:-2]
    assert len(pages)==55 and sum(map(len,pages))==12956
    page_hashes=[hashlib.sha256(np.asarray(p,dtype='<i8').tobytes()).hexdigest() for p in pages];assert page_hashes==result['page_array_sha256']
    # Stable physical mapping independently checked against published source arrays before this campaign.
    physical=[f'lp2-{i:02d}' for i in range(56) if i!=50]
    counts={};total=0
    for line in (root/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word,count=line.split();counts[word]=int(count);total+=int(count)
    logtotal=math.log10(total);model={q:math.log10(n)-logtotal for q,n in counts.items()};floor=math.log10(.01)-logtotal
    def score(path):
        text=''.join(spelling[int(x)] for x in path)
        if len(text)<4:return -999.
        value=0.
        for i in range(len(text)-3):value+=model.get(text[i:i+4],floor)
        return value/(len(text)-3)
    source=root/'source/liber-primus/analysis/campaign18_skip/sweep.py';node=next(n for n in ast.parse(source.read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='beam');code=ast.unparse(node);assert code.count('return list(best[3])')==1
    env=dict(e.env);exec(compile(code.replace('return list(best[3])','return beams'),'<source-return-only-terminal-observer>','exec'),env);native=env['beam']
    desc=[(j,w['label'],sign,atbash,phase) for j,w in enumerate(words) for sign in (-1,1) for atbash in (0,1) for phase in range(len(w['key']))]
    scores=np.load(root/'screen-scores.npy',allow_pickle=False);selections=np.load(root/'phase-selections.npy',allow_pickle=False);full=read(root/'full-survivors.json')
    assert scores.shape==(55,11256) and selections.shape==(55,623,2,2,2) and np.isfinite(scores).all() and np.isfinite(selections).all()
    assert result['screens']==scores.size==619080 and result['phase_selections']==137060
    promotions=[];best_indices=[];selection_count=0
    for page in range(55):
        cursor=0
        for j,w in enumerate(words):
            for si,sign in enumerate((-1,1)):
                for atbash in (0,1):
                    block=scores[page,cursor:cursor+len(w['key'])];phase=int(np.argmax(block));value=float(block[phase]);assert selections[page,j,si,atbash].tolist()==[phase,value]
                    if value> -6:promotions.append((page,j,w['label'],sign,atbash,phase))
                    cursor+=len(w['key']);selection_count+=1
        assert cursor==11256
        ix=int(np.argmax(scores[page]));j,label,sign,atbash,phase=desc[ix];row=result['page_results'][page]
        assert row['page']==page and row['length']==len(pages[page]) and row['best_screen']==[float(scores[page,ix]),[label,sign,bool(atbash),phase]]
        best_indices.extend((page,int(i)) for i in np.flatnonzero(scores[page]==scores[page,ix]))
    assert selection_count==137060 and len(promotions)==len(full)==result['full_promotions']
    flat=int(np.argmax(scores));globalpage,globalindex=map(int,np.unravel_index(flat,scores.shape));g=result['best_screen'];j,label,sign,atbash,phase=desc[globalindex]
    assert (g['page'],g['keyword_index'],g['keyword'],g['sign'],g['atbash'],g['phase'],g['score'])==(globalpage,j,label,sign,atbash,phase,float(scores[globalpage,globalindex]))
    # Original fixed-index plan plus all page maxima/ties and producer-requested global top40.
    selected=set(best_indices)
    for flat in list(range(0,619080,12347))+[619079]:selected.add(tuple(map(int,np.unravel_index(flat,scores.shape))))
    top40=np.argsort(-scores.ravel(),kind='stable')[:40]
    selected.update(tuple(map(int,np.unravel_index(int(flat),scores.shape))) for flat in top40)
    maxerror=0.;nativecalls=0
    for page,ix in sorted(selected):
        j,label,sign,atbash,phase=desc[ix];cipher=np.asarray(pages[page],np.int64);cipher=28-cipher if atbash else cipher;key=e.env['tile_key'](words[j]['key'],4*len(cipher)+64)
        terminal=native(cipher,key,sign,phase,min(90,len(cipher)),300);nativecalls+=1;value=score(terminal[0][3]);error=abs(value-scores[page,ix]);maxerror=max(maxerror,error);assert error==0.,(page,ix,error)
        if (page,ix)==(globalpage,globalindex):assert list(terminal[0][3])==g['plain']
    full_terminal_hypotheses=0;normalized_better=0;sourcehits=[]
    for expected,row in zip(promotions,full):
        page,j,label,sign,atbash,phase=expected
        assert expected==(row['page'],row['keyword_index'],row['keyword'],row['sign'],row['atbash'],row['phase'])
        cipher=np.asarray(pages[page],np.int64);cipher=28-cipher if atbash else cipher;key=e.env['tile_key'](words[j]['key'],4*len(cipher)+64);terminals=native(cipher,key,sign,phase,len(cipher),500);nativecalls+=1
        norms=[score(t[3]) for t in terminals];best=max(range(len(norms)),key=lambda i:norms[i]);assert len(terminals)==row['terminal_count'] and norms==row['terminal_scores']
        assert list(terminals[0][3])==row['plain'] and norms[0]==row['score'] and row['source_gate']==(norms[0]> -5.5)
        assert best+1==row['best_normalized_terminal_rank'] and norms[best]==row['best_normalized_terminal_score'] and list(terminals[best][3])==row['best_normalized_terminal'] and row['best_normalized_gate']==(norms[best]> -5.5)
        full_terminal_hypotheses+=len(terminals);normalized_better+=best!=0
        if row['source_gate']:sourcehits.append((page,[norms[0],label,sign,bool(atbash),phase,e.text(row['plain'])]))
    assert result['source_hits']==len(sourcehits)==sum(row['source_gate'] for row in full)
    assert result['normalized_terminal_hits']==sum(row['best_normalized_gate'] for row in full)
    for page,row in enumerate(result['page_results']):assert row['source_hits']==[hit for p,hit in sourcehits if p==page]
    return dict(status='PASS',protocol_sha256=sha(root/'target-protocol-frozen.json'),result_sha256=sha(root/'results.json'),audit_script_sha256=sha(Path(__file__)),all619080_score_cells_accounted=True,all137060_phase_selections_reconstructed=True,source_segments=55,total_runes=12956,physical_pages=physical,complete_promoted_native_decodes=len(full),complete_full_terminal_hypotheses=full_terminal_hypotheses,source_hits=len(sourcehits),normalized_terminal_hits=result['normalized_terminal_hits'],full_decodes_with_better_normalized_terminal=normalized_better,native_screen_sample_count=len(selected),native_total_calls=nativecalls,maximum_native_screen_score_error=maxerror,global_best_screen=g,coverage='All saved dimensions, phase selections, gates and promoted full beams; fixed-index sample, globaltop40 and all55page maxima/ties native-screen checked. Not a second complete619080-screen run.',limits='Historical algorithm score enumeration. Nonselected or unpromoted phases lack complete-page confirmation; failed known-text phase/ranking controls prevent a keyword-family exclusion. No complete-search significance claim.',seconds=time.perf_counter()-started)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--producer-root',required=True,type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--check-only',action='store_true');a=parser.parse_args();assert a.output or a.check_only
    if a.output:assert not a.output.exists(),'Refusing overwrite'
    result=run(a.producer_root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2))
