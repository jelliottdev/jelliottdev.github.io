"""Declare the grouped page-24 source replay for later registry integration."""
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
    assert result['page']=='lp2-07' and result['stage_two']['source_settings']==377
    assert len(result['null'])==256
    files=[BASE+name for name in ('plan.json','inputs.json','positive.json',
           'snapshot_inputs.py','positive.py','engine.py','run.py','check.py','plot.py',
           'make_record.py','article.md')]
    files+=['text/lp2-07.txt']
    record={
        'id':HERE.name,'status':'draft',
        'title':'Page-24 prime positions and column readings',
        'question':'Does the archived zero-based prime extraction followed by column reading and GP29 shifts yield an unusual trigram score on LP2-07?',
        'reader_question':'What if we take prime-indexed runes, rearrange them, then shift the alphabet?',
        'summary':'The complete 377-setting archived page-specific grid found no distinctive score: 222 of 256 full-search shuffles equaled or exceeded its best result.',
        'finding':'The best source trigram score was 225 at width 10, shift 16 on 46 zero-based-prime runes from LP2-07. In 222 of 256 page-shuffled full searches, the maximum was at least 225 (add-one 223/257). All 377 settings share exactly the same GP29 IoC, 0.981, because columnar reordering and alphabet shifting preserve rune frequencies.',
        'limitations':'Only source page 24/current LP2-07, its 46-rune zero-based-prime selection, widths 2–14, shifts 0–28 and the source short Runeglish trigram table were tested. Shuffles are a selection control rather than a cipher model. The source relative page path is broken in the pinned tree, so this is a replay of stated operations from verified page bytes, not verification of a saved upstream run. Other index origins, layers and language scorers remain open.',
        'next_steps':'Fix a specific alternate positional or decoding rule and a longer predicted passage before scoring it; compare its entire selected search with controls.',
        'outcome':'not-supported',
        'tags':['LP2-07','source replay','prime positions','columnar transposition','Caesar shift','selection effects'],
        'scope':{
            'pages':['lp2-07'],
            'artifacts':[BASE+'inputs.json',BASE+'plan.json',BASE+'positive.json'],
            'representation':'All 208 pinned source page_24 runes, GP29-indexed, byte-for-byte equal to current LP2-07; punctuation and separators excluded from positions.',
            'procedure':'Record seven first-stage source views. From zero-based prime positions, replay widths 2–14 and all 29 GP shifts under the source weighted Runeglish trigram scorer, then rerun that full grid after each of 256 within-page shuffles.',
            'parameters':'Seven source views; one subsequent 13×29=377-setting grid; 256 complete-search shuffles with Random(20261023+trial). Planted selector/columnar/shift/scorer control fixed before manuscript scoring.',
            'exclusions':'Other pages, index origins, prime complements in the second stage, widths or shifts outside source bounds, other scoring models, second ciphers or selected fragments.'
        },
        'review':{'kind':'pinned archived-source operation replay with source-function parity, planted control and complete-search shuffles',
                  'retested_on':'2026-10-23',
                  'reviewer':'Independent scalar checker reconstructs every source arm, 377 sorted candidate outputs and 256 full-search controls.',
                  'human_review':'pending'},
        'reproduction':{
            'command':f'python {BASE}check.py && python {BASE}plot.py --check && python {BASE}run.py --check',
            'environment':'Python 3 standard library for bundled-input checks. snapshot_inputs.py and positive.py additionally use a local checkout of the pinned upstream commit.',
            'script':BASE+'check.py','script_sha256':hashed(BASE+'check.py')['sha256'],
            'inputs':[hashed(path) for path in files],
            'outputs':[hashed(BASE+name) for name in ('results.json','comparison.svg')]
        },
        'visuals':[{'path':BASE+'comparison.svg','caption':'The best weighted trigram score on the page compared with maxima from 256 shuffles that each repeated all 377 settings.'}],
        'sources':[{'label':'Pinned archived '+name,'url':SOURCE+name} for name in ('p24_char_tests.py','p24_prime0_post.py')],
        'related':['prime-fibonacci-position-extraction','english-scorer-controls']
    }
    (HERE/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
