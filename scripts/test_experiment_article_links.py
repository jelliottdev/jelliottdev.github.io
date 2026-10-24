"""Navigation aliases never become scientific inputs or permission to embed images."""
import copy
import tempfile
import unittest
from pathlib import Path

from build_experiments import article_link_aliases, authored_link_targets


class ArticleLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='article-links-')
        self.root = Path(self.temp.name)
        self.record = {
            'id': 'current', 'article_path': 'experiments/records/current/article.md',
            'article': '', 'reproduction': {'script': 'experiments/records/current/run.py',
                                         'inputs': [], 'outputs': []}}
        for path in ['experiments/records/current/results.json',
                     'experiments/records/other/article.md',
                     'experiments/records/other/control.json',
                     'research/note.md', 'images/lp2-15.jpg',
                     'downloads/original-images.zip']:
            file = self.root / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('fixture', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def aliases(self, text):
        self.record['article'] = text
        return article_link_aliases(self.root, self.record, {'current', 'other'})

    def test_public_links_and_relative_results(self):
        (self.root / 'results.json').write_text('unrelated root file', encoding='utf-8')
        text = ('[result](results.json) [other](experiments/records/other/article.md) '
                '[data](experiments/records/other/control.json) [note](research/note.md) '
                '[image](images/lp2-15.jpg) [originals](downloads/original-images.zip) '
                '[future bundle](downloads/experiments/current.zip)')
        self.record['article'] = text
        before = copy.deepcopy(self.record)
        aliases = article_link_aliases(self.root, self.record, {'current', 'other'})
        self.assertEqual(aliases['results.json'], 'experiments/records/current/results.json')
        self.assertEqual(aliases['experiments/records/other/article.md'], '#/experiments/other')
        for href in ['experiments/records/other/control.json', 'research/note.md',
                     'images/lp2-15.jpg', 'downloads/original-images.zip',
                     'downloads/experiments/current.zip']:
            self.assertEqual(aliases[href], href)
        self.assertEqual(self.record, before, 'Authored evidence and dependencies stay unchanged')
        self.assertFalse((self.root / 'downloads/experiments/current.zip').exists())

    def test_existing_permissions_and_code_are_not_aliases(self):
        self.record['reproduction']['outputs'] = [{'path': 'experiments/records/current/results.json'}]
        self.assertEqual(self.aliases('[data](experiments/records/current/results.json) '
                                     '[site](https://example.com) [route](#/wiki/atbash)'), {})
        code = ('`[inline](missing.json)`\n```text\n[fenced](missing.json)\n```\n'
                '![not a hyperlink](missing.svg)\n[real](results.json)')
        self.assertEqual(list(authored_link_targets(code)), ['results.json'])
        self.assertEqual(self.aliases(code), {'results.json': 'experiments/records/current/results.json'})

    def test_plural_catalog_cannot_masquerade_as_page_detail(self):
        for href in ['#/pages/lp2-49', '#/pages/lp2-12?section=text', '#/pages/LP1-01']:
            with self.subTest(href=href), self.assertRaisesRegex(ValueError, 'page detail must use'):
                self.aliases(f'[Page]({href})')
        for href in ['#/pages', '#/pages?release=LP2', '#/page/lp2-49', '#/reader/lp2-12']:
            with self.subTest(href=href):
                self.assertEqual(self.aliases(f'[Valid route]({href})'), {})
        self.assertEqual(self.aliases('`[Example](#/pages/lp2-49)`\n```text\n'
                                     '[Example](#/pages/lp2-12)\n```'), {},
                         'Literal code examples are not publication links')

    def test_unsafe_syntax_cannot_authorize_navigation(self):
        unsafe = ['../note.md', './results.json', '/research/note.md', '//evil.example/x',
                  'research//note.md', 'research/./note.md', 'research/../note.md',
                  'research%2fnote.md', r'research\note.md', 'results.json?q=1',
                  'results.json#x', 'javascript:alert', 'data:text/plain,x']
        for path in unsafe:
            with self.subTest(path=path):
                self.assertEqual(self.aliases(f'[unsafe]({path})'), {})

    def test_missing_files_and_draft_owners_fail_publication(self):
        for href in ['missing.json', 'downloads/experiments/draft.zip',
                     'experiments/records/draft/article.md']:
            if 'draft/article' in href:
                file = self.root / href
                file.parent.mkdir(parents=True)
                file.write_text('draft', encoding='utf-8')
            with self.subTest(href=href), self.assertRaises(ValueError):
                self.aliases(f'[bad]({href})')


if __name__ == '__main__':
    unittest.main()
