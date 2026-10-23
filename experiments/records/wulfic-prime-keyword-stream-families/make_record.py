"""Declare one grouped replay of three related archived source methods."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=f'experiments/records/{HERE.name}/'
SOURCE_BASE='https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/'


def hashed(path):
    return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def main():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    inp=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    assert result['observed']['keyword_only']['candidate_count']==540
    assert result['observed']['prime_stream']['candidate_count']==11880
    assert result['observed']['keyword_stepped']['source_configurations']==5285280
    assert len(result['null'])==49
    pages=sorted({row['site_page'] for row in inp['pages'].values()})
    files=[BASE+name for name in (
        'plan.json','inputs.json','snapshot_inputs.py','engine.py','run.py',
        'source_parity.py','check.py','plot.py','make_record.py','article.md')]
    files+=['data/index.json',BASE.replace('prime-keyword-stream-families/','keyword-prime-layer-grid/')+'keys.json']
    files+=[row['site_path'] for row in inp['pages'].values()]
    files=list(dict.fromkeys(files))
    record={
        'id':HERE.name,'status':'draft',
        'title':'Prime and keyword stream families',
        'question':'Do three archived keyword and prime-stream searches yield a distinctive, source-defined reading on their selected LP2 pages?',
        'reader_question':'Can a word or prime sequence act as the missing key?',
        'summary':'Three complete pinned source grids were replayed together. Their screens do not establish a reading; a prime-stream IoC peak is an unresolved lead under a coarse 49-control comparison.',
        'finding':'The repeating-keyword search produced zero all-singleton fits among 540 settings (best IoC 1.119; 18/49 full-search shuffles reached it). The prime-stream search tested 11,880 settings and yielded nine permissive sequential screen hits; its highest IoC was 1.174 on LP2-09 (1/49 shuffles reached it), but that output missed all six one-rune checks and did not read as a passage. The keyword-stepped search tested 5,285,280 settings; 2,270 passed its all-singleton gate, none exceeded the source IoC 1.3 hit threshold, and its best gated IoC 1.281 was reached by 12/49 shuffles.',
        'limitations':'The prime IoC peak is exploratory and 49 complete-search controls provide coarse tail resolution. Within-page shuffles preserve rune counts but are not a cipher model. Source keyword lists, prime generators, old page selections, offsets and screens define the tested scope. Some stepped arithmetic duplicates a published combined-key grid; neither a high IoC nor a quick-word fragment proves decryption.',
        'next_steps':'Precommit a specific prime rule and a predicted longer passage or held-out page, then test it without another selection search.',
        'outcome':'inconclusive',
        'tags':['LP2','source replay','prime streams','keywords','index of coincidence','stepped key'],
        'scope':{
            'pages':pages,
            'artifacts':[BASE+'inputs.json',BASE+'plan.json'],
            'representation':'Pinned archived rune bytes verified against current canonical LP2 GP29 values. Old source page_N equals current LP2-(N-17); branch-specific source word parsers set singleton positions.',
            'procedure':'Replay three archived finite searches as one shared batch: source keywords, source prime generators and F-skip, and keyword-stepped prime streams. Preserve each source screen and compare branch maxima against 49 full-search within-page shuffles.',
            'parameters':'540 repeating-keyword settings on ten pages; 11,880 prime-stream settings on eight pages; 5,285,280 stepped-keyword settings on eleven pages; three arithmetic directions; 49 seeded complete-search controls, seed 20261023.',
            'exclusions':'Other keywords, prime orders, resets, page sets, languages, model scorers, source-defined but uncalled prime generators, and the optional unverified verified_keys.json input.'
        },
        'review':{'kind':'pinned archived-source replay with selected-function parity and full-search shuffle controls',
                  'retested_on':'2026-10-23',
                  'reviewer':'Sampled key streams and decodes matched extracted pinned source functions; independent scalar checks reconstruct saved winners and 49-control statistics.',
                  'human_review':'pending'},
        'reproduction':{
            'command':f'python {BASE}check.py && python {BASE}plot.py --check && python {BASE}run.py --check',
            'environment':'Python 3 with NumPy and Numba. The optional source_parity.py additionally requires a local checkout of the pinned Wulfic commit; the core replay runs from bundled inputs.',
            'script':BASE+'check.py',
            'script_sha256':hashed(BASE+'check.py')['sha256'],
            'inputs':[hashed(path) for path in files],
            'outputs':[hashed(BASE+name) for name in ('results.json','comparison.svg')]
        },
        'visuals':[{'path':BASE+'comparison.svg','caption':'Observed best IoC in each complete source search against the range of 49 within-page shuffled full searches. The prime peak is a lead, not a reading.'}],
        'sources':[{'label':'Pinned archived '+name,'url':SOURCE_BASE+'tools/legacy/'+name} for name in (
            'p21_30_keyword_sweep.py','prime_stream_solver.py','keyword_stepped_stream.py')],
        'related':['wulfic-keyword-prime-layer-grid','historical-prime-and-ps-keys','lp2-panel-prime-openings']
    }
    (HERE/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
