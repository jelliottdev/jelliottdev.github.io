"""Run the exact pinned archived script with its pinned files in a temp folder.

Requires an external checkout containing commit bf89d3d. No source code or
archive files are copied into the website; only the short stdout witness is.
"""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
PINS = {
    'tools/legacy/p20_interlocking.py': '4c8f02bc4a8e055e29e9dcd0902fa12c727862b17fe0465f4bab7895dde4cfcd',
    'data/corpora/deor_poem.txt': 'be03dbfbc8d02dd6348611c973dd38ba3960c7d06833461783876546171fd143',
}


def show(repo, path):
    raw = subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=repo)
    expected = PINS.get(path)
    if expected:
        assert hashlib.sha256(raw).hexdigest()==expected, path
    return raw


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True,help='local checkout of pinned Wulfic repository')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory)
        (temp/'pages/page_20').mkdir(parents=True)
        (temp/'data').mkdir()
        (temp/'method.py').write_bytes(show(args.repo,'tools/legacy/p20_interlocking.py'))
        (temp/'data/deor_poem.txt').write_bytes(show(args.repo,'data/corpora/deor_poem.txt'))
        (temp/'pages/page_20/runes.txt').write_bytes(show(args.repo,'pages/page_20/runes.txt'))
        run=subprocess.run(['python','method.py'],cwd=temp,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,encoding='utf-8',timeout=30,check=True)
    saved=HERE/'source-run.txt'
    if args.check:
        assert run.stdout==saved.read_text(encoding='utf-8')
    else:
        saved.write_text(run.stdout,encoding='utf-8',newline='\n')
    print('PASS: exact archived script stdout under pinned input')


if __name__=='__main__':main()
