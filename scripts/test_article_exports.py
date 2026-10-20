"""Checks that non-JavaScript references remain usable as instructions."""
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote
from build_articles import (Text, reference_url, linked_articles, article_contents,
                            linked_reference_text, manuscript_reference_html, standalone_url, standalone_body)

class ArticleExports(unittest.TestCase):
    def test_generated_articles_have_existing_local_link_and_image_targets(self):
        root = Path(__file__).resolve().parents[1]
        articles = list((root / "reference/articles").glob("*.html"))
        self.assertTrue(articles, "Generate the article exports before this check")
        for article in articles:
            parser = Text()
            parser.feed(article.read_text(encoding="utf-8"))
            for target in parser.links:
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                path = unquote(parsed.path)
                resolved = (root / path.lstrip("/") if path.startswith("/")
                            else article.parent / path).resolve()
                with self.subTest(article=article.name, target=target):
                    self.assertTrue(resolved.is_relative_to(root), "Link escapes repository")
                    self.assertTrue(resolved.is_file(), "Missing local destination")

    def test_standalone_resources_preserve_paths_queries_and_fragments(self):
        for path in ("text/lp2-31.txt", "data/catalog.json", "images/1033.jpg",
                     "downloads/reference-data.zip", "exports/example.svg",
                     "reference/index.html", "scripts/rune_ngrams.py"):
            self.assertEqual(standalone_url(path), "../../" + path)
        self.assertEqual(standalone_url("text/example.txt?raw=1#part"),
                         "../../text/example.txt?raw=1#part")
        for path in ("#local", "https://example.org/file", "//example.org/file", "/images/a.jpg", ""):
            self.assertEqual(standalone_url(path), path)
        self.assertEqual(standalone_url("#/wiki/outguess?section=run"), "outguess.html#run")
        self.assertEqual(standalone_url("#/page/lp2-31?section=reading"), "../lp2-31.html")
        self.assertEqual(standalone_url("#/downloads"), "../../index.html#/downloads")

    def test_standalone_rewrites_attributes_not_literal_examples(self):
        body = ('<a href="text/a.txt?x=1&amp;y=2">Source</a>'
                "<img src='images/a.jpg' alt='Example'>"
                '<code>href="text/a.txt"</code>')
        result = standalone_body(body)
        self.assertIn('href="../../text/a.txt?x=1&amp;y=2"', result)
        self.assertIn("src='../../images/a.jpg'", result)
        self.assertIn('<code>href="text/a.txt"</code>', result)

    def test_manuscript_sections_are_native_and_keep_literal_text(self):
        original = ('# LP2-57\n\nIntro\n\n## Archived transcription\n\n'
                    'ᚠᚢᚦ-ᚩ/\n  ᚱᚳ.\n\n## Sources & scope\n\n'
                    'https://example.org/original.jpg\n<script>unsafe()</script>\n')
        rendered = manuscript_reference_html(original)
        self.assertIn('<h1>LP2-57</h1>', rendered)
        self.assertIn('<h2 id="record-section-1">Archived transcription</h2>', rendered)
        self.assertIn('href="#record-section-2">Sources &amp; scope</a>', rendered)
        self.assertIn('ᚠᚢᚦ-ᚩ/\n  ᚱᚳ.\n\n</div>', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('## Archived', rendered)
        with self.assertRaises(ValueError):
            manuscript_reference_html('Not a generated reference')

    def test_reference_urls_are_clickable_without_changing_preserved_text(self):
        original = ('Runes: ᚠᚢᚦ\nGuide: https://example.org/guide?a=1&b=2#part\n'
                    '<script>unsafe()</script>\nImage: https://example.org/image.jpg\n'
                    'Not a link: javascript:alert(1)')
        rendered = linked_reference_text(original)
        self.assertIn('href="https://example.org/guide?a=1&amp;b=2#part"', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('href="javascript:', rendered)
        parser = Text()
        parser.feed(rendered)
        self.assertEqual("".join(parser.parts), original)
        self.assertEqual(parser.links, ['https://example.org/guide?a=1&b=2#part',
                                        'https://example.org/image.jpg'])

    def test_compact_blocks_and_line_breaks_do_not_merge_words(self):
        parser = Text()
        parser.feed('<dl><dt>Newton</dt><dd>Upper panel</dd>'
                    '<dt>Ancient of Days</dt><dd>Lower panel</dd></dl>'
                    '<p>LP1-10<br>LP1-13</p><blockquote>Quoted text</blockquote>After')
        result = "".join(parser.parts).strip()
        self.assertEqual(result.splitlines(),
                         ["Newton", "Upper panel", "Ancient of Days",
                          "Lower panel", "LP1-10", "LP1-13", "Quoted text", "After"])

    def test_images_keep_descriptions_and_source_links(self):
        parser = Text()
        parser.feed('<figure><img src="images/1033.jpg" alt="Hand &amp; compasses">'
                    '<figcaption>Cover detail</figcaption></figure>'
                    '<img src="decoration.svg" alt="">')
        result = "".join(parser.parts)
        self.assertIn("[Image: Hand & compasses]\n", result)
        self.assertIn("\nCover detail\n", result)
        self.assertEqual(result.count("[Image:"), 1)
        self.assertEqual(parser.links, ["images/1033.jpg", "decoration.svg"])

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
