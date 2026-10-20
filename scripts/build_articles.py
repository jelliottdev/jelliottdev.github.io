"""Build searchable wiki articles and standalone HTML/text from authored sources."""
from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re
from urllib.parse import urljoin, parse_qs, quote

ROOT = Path(__file__).resolve().parents[1]

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in {"p", "h2", "h3", "li", "pre", "tr"}:
            self.parts.append("\n")
        if tag in {"td", "th"}:
            self.parts.append("\t")
        values = dict(attrs)
        target = values.get("href") if tag == "a" else values.get("src") if tag == "img" else None
        if target and target not in self.links:
            self.links.append(target)

def reference_url(target):
    """Prefer standalone guide/page references over JavaScript routes."""
    if target.startswith("#/wiki/"):
        article, _, query = target.split("/")[2].partition("?")
        section = parse_qs(query).get("section", [""])[0]
        return ("https://jelliottdev.github.io/reference/articles/" + article + ".html"
                + ("#" + quote(section, safe="-_") if section else ""))
    if target.startswith("#/page/"):
        return "https://jelliottdev.github.io/reference/" + target.split("/")[2].split("?")[0] + ".html"
    return urljoin("https://jelliottdev.github.io/", target)

def linked_articles(body):
    """Collect exact guide destinations, including links to guide sections."""
    parser = Text()
    parser.feed(body)
    return sorted({link[len("#/wiki/"):].split("?")[0].split("#")[0]
                   for link in parser.links if link.startswith("#/wiki/")
                   and link[len("#/wiki/"):].split("?")[0].split("#")[0]})

def build():
    articles = json.loads((ROOT / "articles/index.json").read_text(encoding="utf-8"))
    reading_index = ROOT / "articles/readings/index.json"
    if reading_index.exists():
        articles += json.loads(reading_index.read_text(encoding="utf-8"))
    def source(a):
        return ROOT / "articles" / a.get("source", a["id"] + ".html")
    bodies = {a["id"]: source(a).read_text(encoding="utf-8") for a in articles}
    outgoing = {aid: linked_articles(body) for aid, body in bodies.items()}
    for a in articles:
        body = bodies[a["id"]]
        parser = Text()
        parser.feed(body)
        a["html"] = body
        # Preserve Python indentation and tabular boundaries in downloadable text.
        a["text"] = "".join(parser.parts).strip()
        a["references"] = [reference_url(link) for link in parser.links]
        a["linked_articles"] = outgoing[a["id"]]
        title = html.escape(a["title"])
        standalone = body.replace('href="#/', 'href="../../index.html#/').replace('href="exports/', 'href="../../exports/').replace('href="scripts/', 'href="../../scripts/').replace('href="data/', 'href="../../data/').replace('src="exports/', 'src="../../exports/')
        standalone = standalone.replace('src="images/', 'src="../../images/').replace('href="images/', 'href="../../images/').replace('href="downloads/', 'href="../../downloads/')
        standalone = standalone.replace('src="thumbs/', 'src="../../thumbs/')
        standalone = re.sub(r'href="../../index.html#/wiki/([^"?]+)\?section=([^"]+)"', r'href="\1.html#\2"', standalone)
        standalone = re.sub(r'href="../../index.html#/wiki/([^"?]+)"', r'href="\1.html"', standalone)
        standalone = re.sub(r'href="../../index.html#/page/([^"?]+)(?:\?[^"]*)?"', r'href="../\1.html"', standalone)
        related = [b for b in articles if b["id"] != a["id"] and
                   a["id"] in outgoing[b["id"]]]
        if a.get("pages"):
            standalone += '<h2>Manuscript pages discussed</h2><p>' + " · ".join(f'<a href="../{pid}.html">{pid.upper()}</a>' for pid in a["pages"]) + '</p>'
        if related:
            standalone += '<h2>Guides linking here</h2><ul>' + ''.join(f'<li><a href="{b["id"]}.html">{html.escape(b["title"])}</a></li>' for b in related) + '</ul>'
        out = ROOT / "reference/articles"
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{a["id"]}.html').write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title} — Liberpedia</title><link rel="stylesheet" href="../../style.css">'
            '<body><main class="standalone-article"><nav><a href="../../reference/index.html">Reference index</a> · '
            f'<a href="../../index.html#/wiki/{a["id"]}">Open in wiki</a> · <a href="{a["id"]}.txt">Plain text</a></nav>'
            f'<h1>{title}</h1><p>{html.escape(a["summary"])}</p>{standalone}</main></body></html>', encoding="utf-8", newline="\n")
        links = "\n".join(a["references"])
        (out / f'{a["id"]}.txt').write_text(a["title"] + "\n\n" + a["summary"] + "\n\n" + a["text"] + "\n\nSources, related references, and files\n" + links + "\n\nArticle: https://jelliottdev.github.io/reference/articles/" + a["id"] + ".html\n", encoding="utf-8", newline="\n")
    (ROOT / "data/articles.json").write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Built {len(articles)} searchable articles and standalone HTML/text copies.")

if __name__ == "__main__":
    build()
