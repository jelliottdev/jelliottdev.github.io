"""Checks that non-JavaScript references remain usable as instructions."""
import unittest
from build_articles import Text, reference_url

class ArticleExports(unittest.TestCase):
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
        self.assertEqual(reference_url("#/wiki/outguess"),
                         "https://jelliottdev.github.io/reference/articles/outguess.html")
        self.assertEqual(reference_url("#/page/lp2-56?section=reading"),
                         "https://jelliottdev.github.io/reference/lp2-56.html")
        self.assertEqual(reference_url("data/catalog.json"),
                         "https://jelliottdev.github.io/data/catalog.json")

if __name__ == "__main__":
    unittest.main()
