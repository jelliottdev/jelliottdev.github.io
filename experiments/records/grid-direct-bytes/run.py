"""Screen 16 direct byte routes through the LP2 grid under ten stem variants."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAGIC = {
    'PNG': bytes.fromhex('89504e470d0a1a0a'),
    'gzip': bytes.fromhex('1f8b08'),
    'ZIP': bytes.fromhex('504b0304'),
}
SCREENS = ('ASCII', 'UTF-8', 'PNG', 'gzip', 'ZIP', 'zlib')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base60(token, alphabet):
    number = 60 * alphabet.index(token[0]) + alphabet.index(token[1])
    assert 0 <= number <= 255
    return number


def routes():
    result = []
    for axis, outer_size, inner_size in (('rows', 32, 8), ('columns', 8, 32)):
        for outer_reverse in (False, True):
            for inner_reverse in (False, True):
                for alternate in (False, True):
                    outer = list(range(outer_size))
                    if outer_reverse:outer.reverse()
                    order=[]
                    for step, outer_index in enumerate(outer):
                        inner=list(range(inner_size))
                        if inner_reverse ^ (alternate and step % 2 == 1):inner.reverse()
                        for inner_index in inner:
                            row,col=(outer_index,inner_index) if axis=='rows' else (inner_index,outer_index)
                            order.append(row*8+col)
                    assert len(order)==256 and set(order)==set(range(256))
                    result.append({'id':f'{axis}-{int(outer_reverse)}{int(inner_reverse)}{int(alternate)}',
                                   'axis':axis,'outer_reverse':outer_reverse,
                                   'inner_reverse':inner_reverse,'alternate':alternate,
                                   'positions':order})
    assert len(result)==16 and len({tuple(r['positions']) for r in result})==16
    return result


def screen(data):
    ascii_ok=all(v in (9,10,13) or 32 <= v <= 126 for v in data)
    try:
        data.decode('utf-8','strict')
        utf8_ok=True;error_at=None
    except UnicodeDecodeError as exc:
        utf8_ok=False;error_at=exc.start
    cmf,flg=data[:2]
    zlib_ok=(cmf & 15)==8 and (cmf >> 4)<=7 and ((cmf<<8)+flg)%31==0
    return {'ASCII':ascii_ok,'UTF-8':utf8_ok,
            **{kind:data.startswith(magic) for kind,magic in MAGIC.items()},
            'zlib':zlib_ok,'utf8_error_at':error_at}


def figure(rows, variant_count):
    width,height=620,625
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Direct byte-format screen across 16 grid routes</title>',
           '<desc id="desc">Each row is one complete rectangular traversal, evaluated under 1,024 I/l stem variants. Cells show counts that pass six declared direct-format screens.</desc>',
           f'<rect width="{width}" height="{height}" fill="#fbfaf6"/>',
           '<g font-family="Arial, sans-serif" fill="#26343c">',
           '<text x="20" y="31" font-size="19" font-weight="bold">Direct byte-format screen</text>',
           f'<text x="20" y="52" font-size="12">16 routes × {variant_count:,} stem settings · 256 bytes in every case</text>']
    xs=[230,288,346,404,462,520]
    for x,label in zip(xs,SCREENS):
        parts.append(f'<text x="{x+21}" y="86" text-anchor="middle" font-size="10">{label}</text>')
    y=98
    for row in rows:
        parts.append(f'<text x="20" y="{y+21}" font-size="12">{row["id"]}</text>')
        for x,label in zip(xs,SCREENS):
            count=row['screen_counts'][label]
            fill='#cfe7dc' if count else '#e9e8e3'
            parts.append(f'<rect x="{x}" y="{y+2}" width="43" height="25" rx="2" fill="{fill}"/>')
            parts.append(f'<text x="{x+21}" y="{y+19}" text-anchor="middle" font-size="12" font-weight="bold">{count}</text>')
        y+=30
    parts += ['<text x="20" y="600" font-size="11">Route suffix: outer direction / initial inner direction / alternate after each row or column.</text>',
              '<text x="20" y="615" font-size="11">0 = forward or constant; 1 = reverse or alternate. Counts are screens, not decoded files.</text>',
              '</g></svg>']
    assert y < 595
    return ('\n'.join(parts)+'\n').encode('utf-8')


def report():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:
        assert sha(ROOT/item['path'])==item['sha256'],item['path']
    with (ROOT/'exports/alphanumeric-grids.csv').open(encoding='utf-8',newline='') as f:
        entries=list(csv.DictReader(f))
    assert len(entries)==256 and [int(e['sequence']) for e in entries]==list(range(1,257))
    stem=json.loads((ROOT/'experiments/records/grid-stem-uncertainty/results.json').read_text(encoding='utf-8'))['stem_cells']
    assert len(stem)==10
    alphabet=plan['digit_alphabet']
    baseline=[base60(e['token'],alphabet) for e in entries]
    for cell in stem:
        i=cell['sequence']-1
        assert entries[i]['page']==cell['page'] and int(entries[i]['row'])==cell['row'] and int(entries[i]['column'])==cell['column']
        assert [base60(t,alphabet) for t in cell['alternatives']]==cell['base60_bytes']
    cases=[];route_rows=[]
    for route in routes():
        counts=Counter()
        error_positions=[]
        for mask in range(1<<len(stem)):
            values=baseline.copy()
            for i,cell in enumerate(stem):
                values[cell['sequence']-1]=cell['base60_bytes'][(mask>>i)&1]
            payload=bytes(values[j] for j in route['positions'])
            outcome=screen(payload)
            counts.update({label:int(outcome[label]) for label in SCREENS})
            if outcome['utf8_error_at'] is not None:error_positions.append(outcome['utf8_error_at'])
            cases.append({'route':route['id'],'mask':mask,'sha256':hashlib.sha256(payload).hexdigest(),
                          'first_8_hex':payload[:8].hex(),'screens':{key:outcome[key] for key in SCREENS},
                          'utf8_error_at':outcome['utf8_error_at']})
        route_rows.append({key:route[key] for key in ('id','axis','outer_reverse','inner_reverse','alternate')}
                          | {'first_positions':route['positions'][:12],
                             'screen_counts':{label:counts[label] for label in SCREENS},
                             'utf8_first_error_range':[min(error_positions),max(error_positions)] if error_positions else None})
    result={'schema':'liberpedia-grid-direct-bytes-v1','plan_sha256':sha(HERE/'plan.json'),
            'grid_shape':[32,8],'byte_count':256,'route_count':len(route_rows),
            'stem_variant_count':1<<len(stem),'case_count':len(cases),
            'total_screen_counts':{label:sum(r['screen_counts'][label] for r in route_rows) for label in SCREENS},
            'routes':route_rows,'cases':cases,
            'limits':['Only the six declared screens are evaluated at byte offset zero.',
                      'An absent header does not exclude encrypted, headerless or transformed data.',
                      'UTF-8 validity alone would not establish language or meaning.',
                      'The ten I/l changes are a bounded input sensitivity set, not a complete glyph audit.']}
    return result,figure(route_rows,1<<len(stem))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    result,chart=report()
    outputs={HERE/'results.json':(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'),
             HERE/'route-screen.svg':chart}
    if args.check:
        for path,content in outputs.items():assert path.read_bytes()==content,path
    else:
        for path,content in outputs.items():path.write_bytes(content)
    print('Checked',result['case_count'],'byte streams; totals',result['total_screen_counts'])


if __name__=='__main__':main()
