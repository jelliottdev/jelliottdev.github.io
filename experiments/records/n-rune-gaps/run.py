"""Bounded N-rune gap extraction: two distance and two boundary conventions."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def report():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    index_bytes = (ROOT/'data/index.json').read_bytes()
    alphabet = json.loads(index_bytes)['alphabet']
    runes = {r['rune'] for r in alphabet}
    target = next(r['rune'] for r in alphabet if r['latin'] == 'N')
    labels = {r['prime']:r['latin'] for r in alphabet}
    sources = [{'path':'data/index.json','sha256':hashlib.sha256(index_bytes).hexdigest()}]
    streams = []
    for page in plan['pages']:
        path = f'text/{page}.txt';data = (ROOT/path).read_bytes();raw = data.decode('utf-8')
        assert not ({c for c in raw if '\u16a0' <= c <= '\u16ff'} - runes)
        stream = []
        for offset, char in enumerate(raw):
            if char in runes:
                stream.append({'page':page,'rune_ordinal':len(stream)+1,
                               'source_character_offset':offset,'rune':char})
        streams.append(stream)
        sources.append({'path':path,'sha256':hashlib.sha256(data).hexdigest()})
    outputs = []
    for boundary in plan['boundary_modes']:
        groups = streams if boundary == 'reset-at-page' else [sum(streams, [])]
        for convention in plan['distance_modes']:
            for stream in groups:
                positions = [i for i,r in enumerate(stream) if r['rune']==target]
                pairs = []
                for left,right in zip(positions,positions[1:]):
                    distance = right-left-(convention=='intervening-runes')
                    pairs.append({'left':stream[left],'right':stream[right],
                                  'distance':distance,'label':labels.get(distance),
                                  'crosses_page':stream[left]['page']!=stream[right]['page']})
                outputs.append({'boundary':boundary,'distance_mode':convention,
                                'pages':list(dict.fromkeys(r['page'] for r in stream)),
                                'rune_count':len(stream),'n_count':len(positions),
                                'tokens':[p['label'] or '.' for p in pairs],'pairs':pairs})
    return {'scope':plan,'sources':sources,'outputs':outputs}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=report()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: all four configurations and eight output streams reproduced')
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
