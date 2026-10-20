"""Ensure the link audit detects broken paths rather than merely running."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_article_links import validate


class ArticleLinks(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "articles").mkdir()
        (self.root / "data/pages").mkdir(parents=True)
        (self.root / "data/pages/lp1-01.json").write_text("{}")
        (self.root / "sample.txt").write_text("example")

    def write(self, name, body):
        (self.root / "articles" / (name + ".html")).write_text(body, encoding="utf-8")

    def test_valid_sections_images_metadata_and_external_urls(self):
        self.write("one", """<h2 id="a">A</h2><a href='#a'>Local</a>
        <a href="#/wiki/two?section=part%20two">Guide</a>
        <a href="#/reader/lp1-01">Reader</a><img src="sample.txt">
        <a href="https://example.invalid/unavailable">Outside scope</a>""")
        self.write("two", '<h2 id="part two">B</h2>')
        articles = [{"id": "one", "pages": ["lp1-01"], "alias_sections": {"term": "a"}},
                    {"id": "two"}]
        errors, count = validate(self.root, articles)
        self.assertEqual(errors, [])
        self.assertEqual(count, 5)

    def test_detects_each_broken_destination(self):
        self.write("one", """<h2 id="x">A</h2><p id="x">Duplicate</p>
        <a href="#/wiki/missing">Bad guide</a>
        <a href="#/wiki/one?section=missing">Bad section</a>
        <a href="#missing">Bad local anchor</a>
        <a href="#/page/lp2-99">Bad manuscript</a>
        <img src="absent.jpg"><a href="../outside.txt">Outside root</a>""")
        errors, _ = validate(self.root, [{"id": "one", "alias_sections": {"term": "gone"}}])
        self.assertEqual(len(errors), 8)
        for phrase in ["duplicate HTML ID", "missing guide #", "missing guide section",
                       "missing local anchor", "unknown manuscript", "missing local file",
                       "search alias points"]:
            self.assertTrue(any(phrase in e for e in errors), phrase)

    def test_second_hash_is_not_a_router_section(self):
        self.write("one", """<h2 id="exists">Existing</h2>
        <a href="#/wiki/one#exists">Broken despite existing section</a>
        <a href="#/wiki/one?section=exists">Working route</a>""")
        errors, _ = validate(self.root, [{"id": "one"}])
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported guide fragment", errors[0])

    def test_topic_destinations_include_generated_readings(self):
        (self.root / "articles/readings").mkdir()
        (self.root / "articles/readings/reading.html").write_text(
            '<h2 id="argument">Argument</h2>', encoding="utf-8")
        topics = [{"id": "koan", "links": [
            {"href": "#/wiki/reading?section=argument"},
            {"href": "#/page/lp1-01"}, {"href": "sample.txt"}]}]
        errors, count = validate(self.root, [{"id": "reading", "source": "readings/reading.html"}], topics)
        self.assertEqual(errors, [])
        self.assertEqual(count, 3)

    def test_broken_topic_destinations_and_duplicate_ids_fail(self):
        self.write("one", '<h2 id="exists">Existing</h2>')
        topics = [{"id": "detail", "links": [{"href": href} for href in [
            "#/wiki/gone", "#/wiki/one?section=gone", "#/reader/lp2-99",
            "missing.json", "../outside.txt"]]}, {"id": "detail", "links": []}]
        errors, _ = validate(self.root, [{"id": "one"}], topics)
        self.assertEqual(len(errors), 6)
        self.assertTrue(any("Duplicate topic ID" in e for e in errors))
        self.assertEqual(sum(e.startswith("topic detail:") for e in errors), 5)

    def test_duplicate_article_ids_and_missing_sources_fail(self):
        errors, _ = validate(self.root, [{"id": "absent"}, {"id": "absent"}])
        self.assertTrue(any("Duplicate article ID" in e for e in errors))
        self.assertTrue(any("missing source" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
