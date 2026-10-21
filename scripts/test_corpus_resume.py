"""Exercise interruption/resume without downloading or measuring the real corpus."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_corpus_prefixes as runner


class Resume(unittest.TestCase):
    def test_missing_source_resume_weighting_and_overwrite_guards(self):
        blobs=[('x '*2902).encode(),('yy '*2902).encode(),b'']
        ids=[hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() for b in blobs]
        by_id=dict(zip(ids,blobs))
        tree=b''.join(f'100644 blob {ids[i%3]}\tfiles/{i:05}.txt\0'.encode() for i in range(25906))
        missing={ids[1]}
        reads=[]
        def git(command, **kwargs):
            if 'ls-tree' in command:return tree
            self.assertEqual(command[-3:-1],['cat-file','blob'])
            oid=command[-1];reads.append(oid)
            if oid in missing:raise subprocess.CalledProcessError(128,command)
            return by_id[oid]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'exports').mkdir();(root/'scripts').mkdir()
            (root/'scripts/corpus_prefix_statistics.py').write_text('# synthetic fixture\n')
            (root/'exports/runeberg-inventory.json').write_text(json.dumps({'tree_listing_sha256':hashlib.sha256(tree).hexdigest()}))
            out=root/'run'
            with patch.object(runner,'ROOT',root),patch.object(runner.subprocess,'check_output',side_effect=git),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit,'1 entries processed'):
                    runner.run(root/'fake-repository',out)
                self.assertFalse((out/'report.json').exists())
                self.assertEqual(len(list((out/'blobs').glob('*.json'))),1)
                # A changed calculator is refused before any cached data is reused.
                original=(root/'scripts/corpus_prefix_statistics.py').read_bytes()
                (root/'scripts/corpus_prefix_statistics.py').write_text('# changed fixture\n')
                with self.assertRaisesRegex(AssertionError,'Changed run specification'):
                    runner.run(root/'fake-repository',out)
                (root/'scripts/corpus_prefix_statistics.py').write_bytes(original)
                missing.clear();reads.clear()
                runner.run(root/'fake-repository',out)
                self.assertEqual(reads,[ids[1],ids[2]])
                report=json.loads((out/'report.json').read_bytes())
                self.assertEqual(report['entries'],25906)
                self.assertEqual(report['eligible_entries'],17271)
                self.assertEqual(len(report['records']),25906)
                self.assertEqual(sum(r['object_id']==ids[0] for r in report['records']),8636)
                self.assertEqual(report['records'][0]['statistics']['mean'],1)
                self.assertEqual(report['records'][1]['statistics']['mean'],2)
                before=(out/'report.json').read_bytes()
                with self.assertRaisesRegex(SystemExit,'Complete report already exists'):
                    runner.run(root/'fake-repository',out)
                self.assertEqual((out/'report.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
