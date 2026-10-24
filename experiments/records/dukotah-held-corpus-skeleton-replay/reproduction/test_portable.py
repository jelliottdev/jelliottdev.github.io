"""Mocked safety checks plus one local-Git setup/loader/synthetic parity check."""
import argparse,json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import portable as p
class Safety(unittest.TestCase):
    def test_git_disables_lazy_fetch_and_prompt(self):
        import os
        with patch.dict(os.environ,{'GIT_NO_LAZY_FETCH':'0','GIT_TERMINAL_PROMPT':'1'}):
            env=p.git_environment()
            self.assertEqual(env['GIT_NO_LAZY_FETCH'],'1');self.assertEqual(env['GIT_TERMINAL_PROMPT'],'0')
            self.assertEqual(os.environ['GIT_NO_LAZY_FETCH'],'0')
    def test_paths(self):
        root=Path(tempfile.gettempdir()).resolve()
        for value in ['../outside','liber-primus/../../outside','/liber-primus/a','other/a']:
            with self.assertRaises(ValueError):p.safe_path(root,value)
    def test_bytes(self):
        item=dict(path='liber-primus/f',bytes=3,sha256=p.digest(b'abc'))
        p.check_bytes(b'abc',item)
        for raw in [b'ab',b'abd',b'abcd']:
            with self.assertRaises(ValueError):p.check_bytes(raw,item)
    def test_download_is_bounded_and_hash_checked(self):
        item=dict(path='liber-primus/data/kjv.txt',bytes=3,sha256=p.digest(b'abc'))
        class Response:
            url=p.KJV_URL
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):self.bound=n;return b'abc'
        response=Response()
        with patch('urllib.request.urlopen',return_value=response) as request:
            self.assertEqual(p.download_kjv(item),b'abc');self.assertEqual(response.bound,4)
            request.assert_called_once_with(p.KJV_URL,timeout=30)
        response.url='https://example.invalid/substitute'
        with patch('urllib.request.urlopen',return_value=response),self.assertRaises(ValueError):p.download_kjv(item)
    def test_no_implicit_network_or_existing_destination(self):
        with tempfile.TemporaryDirectory(prefix='c01-safety-') as tmp,patch.object(p,'download_kjv') as network:
            with self.assertRaises(ValueError):p.setup_inputs(tmp,Path(tmp)/'new')
            with self.assertRaises(ValueError):p.setup_inputs(tmp,tmp,download=True)
            network.assert_not_called()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--git',required=True);ap.add_argument('--kjv',required=True);ap.add_argument('--receipt',required=True);args=ap.parse_args()
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Safety))
    assert result.wasSuccessful()
    output=Path(args.receipt).resolve();assert not output.exists()
    # Exact named temporary directory under the bundle; never published or retained.
    with tempfile.TemporaryDirectory(prefix='c01-local-input-parity-',dir=p.HERE) as temp:
        root=Path(temp).resolve();assert root.is_relative_to(p.HERE.resolve())
        inputs=root/'external-inputs'
        with patch.object(p,'download_kjv',side_effect=AssertionError('Network prohibited in local test')):
            setup=p.setup_inputs(args.git,inputs,args.kjv,False)
        check=p.parity(inputs,args.git)
        extra=inputs/'liber-primus/data/unexpected.txt';extra.write_text('test '*400,encoding='utf-8')
        try:
            try:p.validate_inputs(inputs)
            except ValueError as e:assert 'membership/order' in str(e)
            else:raise AssertionError('Additional eligible input was silently accepted')
        finally:extra.unlink()
        target=inputs/'liber-primus/data/keys/runepoem_oe.txt';raw=target.read_bytes();target.write_bytes(raw+b'x')
        try:
            try:p.validate_inputs(inputs)
            except ValueError as e:assert 'bytes do not match' in str(e)
            else:raise AssertionError('Tampered raw input was silently accepted')
        finally:target.write_bytes(raw)
    check.update(local_git_setup_files=setup['files'],network_calls=0,temporary_corpus_removed=True,safety_test_methods=result.testsRun,extra_eligible_input_rejected=True,tampered_raw_input_rejected=True,manuscript_target_rerun=False)
    output.write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS local setup +94-array equality + synthetic scanner parity; corpus staging removed.')
if __name__=='__main__':main()
