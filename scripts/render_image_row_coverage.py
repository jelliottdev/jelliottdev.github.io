"""Render audited bands over unmodified source images for visual adjudication."""
import argparse,base64,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def render(report_path,receipt_path,output):
    report=json.loads(report_path.read_bytes());receipt=json.loads(receipt_path.read_bytes())
    assert receipt['report_sha256']==sha(report_path)
    assert receipt['checker_sha256']==sha(ROOT/'scripts/check_image_row_coverage.py')
    ref_path=ROOT/'experiments/records/image-row-coverage/visual-reference.json'
    assert receipt['reference_sha256']==report['reference_sha256']==sha(ref_path)
    assert report['script_sha256']==sha(ROOT/'scripts/image_row_coverage.py')
    reference=json.loads(ref_path.read_bytes())
    if output.exists():raise ValueError('Choose a new output directory')
    output.mkdir(parents=True)
    summary=['| Page | Reference rune rows | Proposed bands | Matched rune rows | Unmatched bands |','| --- | ---: | ---: | ---: | ---: |']
    for page,ref in zip(report['pages'],reference['pages']):
        assert page['page']==ref['page']
        source=ROOT/ref['image']['path'];assert sha(source)==page['image_sha256']
        encoded=base64.b64encode(source.read_bytes()).decode()
        finding=f'{page["maximum_matched_rows"]}/{len(page["runic_rows"])} rune rows matched' if page['runic_rows'] else 'No reference rune rows'
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2800 3900" role="img" aria-labelledby="title desc">',
               f'<title id="title">{page["page"].upper()} image-row coverage</title>',
               '<desc id="desc">Original image with image-only detected bands in blue. Left brackets mark reference runic rows in orange and other text rows in gray. Labels identify intervals, not rune readings.</desc>',
               '<rect width="2800" height="3900" fill="white"/>',
               '<style>text{font:52px Arial,sans-serif;fill:#253d49}.head{font-size:64px;font-weight:bold}</style>',
               f'<text x="80" y="80" class="head">{page["page"].upper()} · {finding}</text>',
               '<text x="80" y="150">Orange R: reference rune row · Gray N: other text</text>',
               '<text x="80" y="215">Blue D: image-only proposal · Source JPEG preserved</text>',
               f'<image x="200" y="260" width="2400" height="3600" href="data:image/jpeg;base64,{encoded}"/>']
        for kind,rows,color,prefix in [('runic',page['runic_rows'],'#9b4f13','R'),('other',page['other_text_rows'],'#666666','N')]:
            for i,row in enumerate(rows):
                a,b=row['y'];y=260+a
                parts.append(f'<path d="M180 {y}H140V{260+b}H180" fill="none" stroke="{color}" stroke-width="9"/>')
                parts.append(f'<text x="12" y="{y+(b-a)/2+18}" style="fill:{color}">{prefix}{i+1}</text>')
        x0,x1=page['column']
        for i,(a,b) in enumerate(page['bands']):
            parts.append(f'<rect x="{200+x0}" y="{260+a}" width="{x1-x0}" height="{b-a}" fill="#2176a5" fill-opacity=".12" stroke="#2176a5" stroke-width="7"/>')
            parts.append(f'<text x="2630" y="{260+(a+b)/2+18}" style="fill:#175d85">D{i+1}</text>')
        parts.append('</svg>')
        (output/(page['page']+'.svg')).write_text('\n'.join(parts)+'\n',encoding='utf-8',newline='\n')
        summary.append(f'| {page["page"].upper()} | {len(page["runic_rows"])} | {len(page["bands"])} | {page["maximum_matched_rows"]} | {len(page["bands_in_no_maximum_matching"])} |')
    (output/'summary.md').write_text('\n'.join(summary)+'\n',encoding='utf-8',newline='\n')
    print('Rendered all eight overlays from the audited report; visual adjudication remains separate.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('receipt',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();render(args.report,args.receipt,args.output)
