"""Checks that non-JavaScript references remain usable as instructions."""
import unittest
from build_articles import Text, reference_url, linked_articles, article_contents

class ArticleExports(unittest.TestCase):
    def test_native_contents_preserves_heading_text_and_escapes_links(self):
        result = article_contents('<h2 id="part two">Read <em>A &amp; B</em></h2>'
                                  '<h3 id="minor">Minor</h3><h2>No ID</h2>')
        self.assertIn('href="#part%20two">Read A &amp; B</a>', result)
        self.assertIn('<summary>On this page</summary>', result)
        self.assertNotIn('Minor', result)
        self.assertNotIn('No ID', result)
        self.assertEqual(article_contents('<p>No sections</p>'), '')

    def test_backlinks_include_sections_without_prefix_collisions(self):
        body = """<a href="#/wiki/atbash?section=example">Example</a>
        <a href='#/wiki/atbash'>Guide</a>
        <a href="#/wiki/atbash-extra">Different guide</a>
        <a href="#/page/lp1-01">Page</a>
        <p>Text mentioning #/wiki/vigenere is not a link.</p>"""
        self.assertEqual(linked_articles(body), ["atbash", "atbash-extra"])

    def test_preserves_runnable_indentation(self):
        parser = Text()
        parser.feed('<pre><code>def example():\n    return 42\nassert example() == 42</code></pre>')
        code = "".join(parser.parts).strip()
        self.assertIn("\n    return 42\n", code)
        exec(compile(code, "<fixed export fixture>", "exec"), {})

    def test_table_cells_are_separated(self):
        parser = Text()
        parser.feed('<table><tr><td>3258</td><td>3222</td></tr></table>')
        self.assertEqual("".join(parser.parts).strip(), "3258\t3222")

    def test_links_resolve_to_standalone_references(self):
        self.assertEqual(reference_url("#cover", "visual-index"),
                         "https://jelliottdev.github.io/reference/articles/visual-index.html#cover")
        self.assertEqual(reference_url("#part%20two", "example"),
                         "https://jelliottdev.github.io/reference/articles/example.html#part%20two")
        self.assertEqual(reference_url("#/wiki/outguess", "visual-index"),
                         "https://jelliottdev.github.io/reference/articles/outguess.html")
        self.assertEqual(reference_url("#/wiki/outguess"),
                         "https://jelliottdev.github.io/reference/articles/outguess.html")
        self.assertEqual(reference_url("#/wiki/visual-index?section=spiral-branches"),
                         "https://jelliottdev.github.io/reference/articles/visual-index.html#spiral-branches")
        self.assertEqual(reference_url("#/page/lp2-56?section=reading"),
                         "https://jelliottdev.github.io/reference/lp2-56.html")
        self.assertEqual(reference_url("data/catalog.json"),
                         "https://jelliottdev.github.io/data/catalog.json")

if __name__ == "__main__":
    unittest.main()
