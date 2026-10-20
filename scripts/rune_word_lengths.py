"""Audit LP2-00–55 token lengths and a pinned historical summary.

Standard library; no network or corpus significance test.
--write updates the two generated reports. --check recomputes both and compares.
Without either flag, prints the measured summary.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
REPORT='exports/unsolved-word-lengths.json'
LEDGER='exports/unsolved-word-tokens.json'
HISTORICAL='exports/sources/unsolved-word-length-summary.csv'
SOURCE='https://github.com/mae3301/lp_experiments/blob/cb5cdb908bb34b68d8a05353eaace56e83d0bbf2/data/unsolved_summary.csv'


def measure():
    index=ROOT/'data/index.json'
    runes=''.join(a['rune'] for a in json.loads(index.read_text(encoding='utf-8'))['alphabet'])
    source_files=[{'path':'data/index.json','sha256':hashlib.sha256(index.read_bytes()).hexdigest()}]
    chars=[];locations=[];page_local_tokens=0
    for n in range(56):
        path=f'text/lp2-{n:02d}.txt';raw=(ROOT/path).read_bytes()
        source_files.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest()})
        page_text=raw.decode('utf-8').translate(str.maketrans('','','/\r\n'))
        page_local_tokens+=len(re.findall(f"[{runes}]+(?:'[{runes}]+)*",page_text))
        for offset,c in enumerate(raw.decode('utf-8')):
            if '\u16a0'<=c<='\u16ff' and c not in runes:raise ValueError('Unknown rune in '+path)
            if c not in '/\r\n':
                chars.append(c);locations.append({'page':f'lp2-{n:02d}','offset':offset})
    text=''.join(chars)
    tokens=[]
    pattern=re.compile(f"[{runes}]+(?:'[{runes}]+)*")
    for m in pattern.finditer(text):
        tokens.append({'ordinal':len(tokens)+1,'token':m.group(),'rune_length':sum(c in runes for c in m.group()),'start':locations[m.start()],'end':{'page':locations[m.end()-1]['page'],'offset_exclusive':locations[m.end()-1]['offset']+1}})
    digits=[{'token':m.group(),'location':locations[m.start()]} for m in re.finditer(r'(?<!\w)[0-9](?!\w)',text)]
    lengths=[t['rune_length'] for t in tokens]
    augmented=lengths+[1]*len(digits)
    with (ROOT/HISTORICAL).open(encoding='utf-8',newline='') as f:historical=next(csv.DictReader(f))
    source_files.append({'path':HISTORICAL,'sha256':hashlib.sha256((ROOT/HISTORICAL).read_bytes()).hexdigest()})
    hist=Counter(augmented)
    matched={k:abs(hist[int(k[7:])]/len(augmented)-float(v))<1e-14 for k,v in historical.items() if k.startswith('length_')}
    metrics={'mean':statistics.mean(augmented),'std':statistics.stdev(augmented),'var':statistics.variance(augmented),'median':statistics.median(augmented),'min':min(augmented),'max':max(augmented)}
    # pandas quantile defaults to linear interpolation between sorted positions.
    ordered=sorted(augmented)
    for name,q in [('percentile_25',.25),('percentile_75',.75)]:
        position=(len(ordered)-1)*q;i=int(position);fraction=position-i
        metrics[name]=ordered[i]*(1-fraction)+ordered[min(i+1,len(ordered)-1)]*fraction
    matched.update({k:abs(v-float(historical[k]))<1e-12 for k,v in metrics.items()})
    def summary(values):
        return {'tokens':len(values),'total_counted_units':sum(values),'histogram':{str(k):v for k,v in sorted(Counter(values).items())},'two_rune_fraction':values.count(2)/len(values),'three_rune_fraction':values.count(3)/len(values)}
    result={'schema':'liberpedia-word-length-audit-v1','pages':'LP2-00–55','method':'Concatenate archived pages in order; remove slash and CR/LF wraps; preserve other delimiters. Rune runs with internal apostrophes are tokens; apostrophes count zero. Do not reset at page boundaries. Include headings. Decimal and alphanumeric content is excluded from rune tokens.','inputs':source_files,'page_local_token_pieces':page_local_tokens,'rune_only':summary(lengths),'standalone_single_digits':digits,'runes_plus_single_digits':summary(augmented),'augmented_metrics':metrics,'historical_summary_url':SOURCE,'historical_comparisons':matched,'all_historical_fields_match':all(matched.values()),'interpretation':'Including six isolated decimal digits as length-one tokens reconstructs the pinned summary. This is consistent with a counting convention; without its token ledger it does not prove the historical pipeline used that exact rule. No corpus comparison or p-value is reproduced here.'}
    matches = []
    for start in range(len(tokens) - 2):
        window = tokens[start:start + 3]
        if [token['rune_length'] for token in window] == [11, 11, 10]:
            matches.append({'first_ordinal': start + 1, 'tokens': window})
    result['eleven_eleven_ten'] = {
        'pattern': [11, 11, 10],
        'windows_examined': len(tokens) - 2,
        'matches': matches,
        'interpretation': 'Descriptive exact-pattern count under the existing joined-page tokenization. No English baseline or significance test.',
    }
    return result,tokens


def figure(report):
    rows=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="315" viewBox="0 0 360 315" role="img" aria-labelledby="title desc">','<title id="title">Rune-token lengths in LP2-00 to LP2-55</title>','<desc id="desc">2896 rune-only tokens, with headings and joined line/page wraps. Three-rune tokens are most frequent at 720; two-rune tokens number 448. Decimal labels are excluded. No English corpus comparison is shown.</desc>','<rect width="360" height="315" fill="#faf9f5"/>','<g font-family="Arial,sans-serif" fill="#263b45">','<text x="16" y="25" font-size="18">Lengths in the archived runes</text>','<text x="16" y="48" font-size="13">LP2-00 to LP2-55 · 2,896 rune tokens</text>']
    for count in range(0,801,200):
        y=245-count*.2
        rows.append(f'<path d="M40 {y}H332" stroke="#d8dcd9"/><text x="35" y="{y+4}" text-anchor="end" font-size="12">{count}</text>')
    for length,count in report['rune_only']['histogram'].items():
        x=44+(int(length)-1)*20;height=int(count)*.2
        rows.append(f'<rect x="{x}" y="{245-height:.2f}" width="14" height="{height:.2f}" fill="#315f73"/><text x="{x+7}" y="264" text-anchor="middle" font-size="11">{length}</text>')
    rows+=['<text x="184" y="286" text-anchor="middle" font-size="13">Runes per token</text>','<text x="16" y="307" font-size="12">Counts only; decimal digits excluded.</text>','</g></svg>']
    return '\n'.join(rows)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group();group.add_argument('--check',action='store_true');group.add_argument('--write',action='store_true');args=p.parse_args()
    report,tokens=measure()
    for path,value in [(REPORT,report),(LEDGER,tokens)]:
        if args.check:
            if json.loads((ROOT/path).read_text(encoding='utf-8'))!=value:raise SystemExit('FAIL: '+path+' differs')
        elif args.write:(ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    chart=ROOT/'exports/figures/word-lengths.svg'
    if args.check:
        if chart.read_text(encoding='utf-8')!=figure(report):raise SystemExit('FAIL: chart differs')
    elif args.write:chart.write_text(figure(report),encoding='utf-8',newline='\n')
    if not args.check:print(json.dumps({k:report[k] for k in ['rune_only','runes_plus_single_digits','all_historical_fields_match']},indent=2))
    if args.check:print('PASS: token ledger, source hashes and historical-summary comparisons reproduce')

if __name__=='__main__':main()
