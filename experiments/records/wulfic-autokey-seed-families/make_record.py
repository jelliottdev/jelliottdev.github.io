"""Declare one grouped replay of two pinned archived autokey source scripts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=f'experiments/records/{HERE.name}/'
SOURCE='https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/'


def hashed(path):
    return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def main():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    assert [result['observed'][key]['configurations'] for key in (
        'named_keywords','two_rune_seeds','three_rune_seeds','distinct_p21_deor')] == [4488,171564,4536354,60]
    assert len(result['null'])==49
    pages=sorted({row['page'] for row in inputs['pages'].values()})
    files=[BASE+name for name in (
        'plan.json','inputs.json','snapshot_inputs.py','gate_check.py','engine.py',
        'run.py','source_parity.py','check.py','plot.py','make_record.py','article.md')]
    files+=['data/index.json']
    files+=[row['site_path'] for row in inputs['pages'].values()]
    files=list(dict.fromkeys(files))
    record={
        'id':HERE.name,'status':'draft',
        'title':'Archived autokey seed searches',
        'question':'Do the pinned source keyword, two-rune, or three-rune autokey seeds pass their one-rune and IoC screens on the selected LP2 pages?',
        'reader_question':'Could a short word or rune seed drive an autokey cipher?',
        'summary':'Four related archived search branches were replayed on verified LP2 page streams. None passed the source-defined hit screen; the gate and ciphertext-feedback design sharply limit what that result can exclude.',
        'finding':'Across the four source branches, zero manuscript outputs passed their strict IoC > 1.3 hit threshold. The 4,488 named-keyword settings had 135 one-rune-compatible cases; 171,564 two-rune settings had 5,058; 4,536,354 three-rune settings had none on 31 source-eligible pages. The distinct four-rune DEOR vector gave zero hits among 60 IoC-only settings. A planted reading-like control passed in all six feedback modes.',
        'limitations':'The source requires visible one-rune words to decode to I or A, which assumes this word segmentation and language. Ciphertext-feedback seeds alter only their own short output prefix, so the whole-page screen cannot reliably identify those seeds. Forty-nine full-search shuffles are coarse controls, not a cipher model. Other seed lengths, pages, boundaries and autokey rules remain untested.',
        'next_steps':'Predeclare a seed-specific prediction of a longer passage or independently measurable feature, then check it on held-out pages without selecting another favorable key afterward.',
        'outcome':'not-supported',
        'tags':['LP2','source replay','autokey','feedback','keywords','seed search','index of coincidence'],
        'scope':{
            'pages':pages,
            'artifacts':[BASE+'inputs.json',BASE+'plan.json'],
            'representation':'Pinned archived source GP29 page values verified against current LP2-04–37 text; source pages old21–54 map to LP2-(old−17). Source isolated-word positions retained.',
            'procedure':'Replay six GP29 plaintext/ciphertext feedback recurrences for 22 source keyword seeds, every two-rune seed, every three-rune seed on source-eligible pages, and the one distinct four-rune P21–30 DEOR array. Preserve source gates, strict IoC threshold and page resets; compare 49 full-search shuffles.',
            'parameters':'4,488 named-keyword, 171,564 two-rune, 4,536,354 three-rune, and 60 distinct P21–30 DEOR settings; 49 within-page shuffled complete searches, seed 20261023.',
            'exclusions':'Other seeds or lengths, alternate alphabets, word resets and segmentations, different singleton assumptions, English scoring, the P21–30 running-key/double-layer branches, and manuscript-derived numerical autokey rules without an exact recurrence.'
        },
        'review':{'kind':'pinned archived-source replay with sampled original-function parity and full-search shuffle controls',
                  'retested_on':'2026-10-23',
                  'reviewer':'Original-function parity on sampled decodes and full small grids; independent scalar reconstruction of every saved winner, input hash, and control comparison.',
                  'human_review':'pending'},
        'reproduction':{
            'command':f'python {BASE}check.py && python {BASE}plot.py --check && python {BASE}run.py --check',
            'environment':'Python 3 with NumPy and Numba. Optional source_parity.py and gate_check.py require a local checkout of the pinned upstream commit; the replay uses bundled verified inputs.',
            'script':BASE+'check.py',
            'script_sha256':hashed(BASE+'check.py')['sha256'],
            'inputs':[hashed(path) for path in files],
            'outputs':[hashed(BASE+name) for name in ('results.json','screen.svg')]
        },
        'visuals':[{'path':BASE+'screen.svg','caption':'One row per source-defined branch: searched settings, one-rune-compatible settings and hits. The P21–30 variant has no one-rune gate.'}],
        'sources':[{'label':'Pinned archived '+name,'url':SOURCE+name} for name in ('autokey_comprehensive.py','p21_30_autokey_solver.py')],
        'related':['public-multihistory-feedback','feedback-opening-census','cumulative-autokey-literal']
    }
    (HERE/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
