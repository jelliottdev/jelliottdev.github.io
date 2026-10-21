"""Export every seed-search cell without selecting successful fixtures."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

def summarize(report,receipt,output):
    data=json.loads(report.read_bytes());audit=json.loads(receipt.read_bytes())
    assert hashlib.sha256(report.read_bytes()).hexdigest()==audit['report_sha256']
    assert len(data['cells'])==audit['cells_checked']==120
    fields=['fixture','search_generator','crib_condition','crib_length','generating_pair_in_search',
        'survivor_count','surviving_seeds','whole_exact_count','suffix_exact_count','withheld_length']
    with output.open('x',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for cell in data['cells']:
            row={field:cell[field] for field in fields[:5]}
            survivors=cell['survivors']
            row.update(survivor_count=len(survivors),surviving_seeds=' '.join(str(s['seed']) for s in survivors),
                whole_exact_count=sum(s['whole_exact'] for s in survivors),
                suffix_exact_count=sum(s['suffix_exact'] for s in survivors),withheld_length=95-cell['crib_length'])
            writer.writerow(row)
    print('All 120 result cells exported, including zero-survivor cells.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('receipt',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();summarize(args.report,args.receipt,args.output)
