"""Independently check pinned inputs, control carriers and retained retrieval bytes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outguess',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    report = json.loads((HERE/'results.json').read_text(encoding='utf8'))
    assert report['plan_sha256'] == digest(HERE/'plan.json')
    assert digest(args.outguess) == plan['tool_sha256'] == report['tool_sha256']
    assert len(plan['images']) == 58 and len(plan['keys']) == 6
    for image in plan['images']:
        assert digest(ROOT/image['path']) == image['sha256']
    assert digest(HERE/plan['plant']['cover']['path']) == plan['plant']['cover']['sha256']
    assert digest(HERE/plan['plant']['payload']['path']) == plan['plant']['payload']['sha256']
    expected = (HERE/plan['plant']['payload']['path']).read_bytes()
    cross = []
    with tempfile.TemporaryDirectory(prefix='outguess-check-') as temp:
        for plant in plan['plant']['carriers']:
            source = HERE/plant['path']
            assert digest(source) == plant['sha256']
            for key in plan['keys']:
                output = Path(temp)/(str(len(cross))+'.bin')
                proc = subprocess.run([str(args.outguess),'-r','-k',key,str(source),str(output)],
                                      capture_output=True,timeout=plan['timeout_seconds'])
                blob = output.read_bytes() if output.exists() else None
                cross.append({'planted_key':plant['key'],'retrieval_key':key,
                              'returncode':proc.returncode,'payload_match':blob==expected,
                              'output_bytes':len(blob) if blob is not None else None,
                              'output_sha256':hashlib.sha256(blob).hexdigest() if blob is not None else None})
                assert (blob == expected) == (key == plant['key'])
    assert cross == report['controls']
    assert len(report['rows']) == 348
    expected_pairs = [(k,i['id']) for k in plan['keys'] for i in plan['images']]
    assert [(r['key'],r['image']) for r in report['rows']] == expected_pairs
    statuses = Counter()
    for row in report['rows']:
        output = args.output_dir/row['output'] if row['output'] else None
        if output:
            assert output.exists()
            assert digest(output) == row['sha256']
            assert output.stat().st_size == row['bytes']
        assert row['status'] == ('timeout' if row['returncode'] is None else
                                 'output-unverified' if row['returncode']==0 and row['bytes'] else
                                 'no-retrieval')
        statuses[row['status']] += 1
    assert dict(sorted(statuses.items())) == report['status_counts']
    print(f"Validated {len(report['rows'])} original-image receipts, all retained bytes, and 36 planted-key checks.")


if __name__ == '__main__': main()
