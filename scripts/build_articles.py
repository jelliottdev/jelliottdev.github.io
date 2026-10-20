"""Build searchable wiki articles and standalone HTML/text from authored sources."""
from pathlib import Path
from html.parser import HTMLParser
import html
import json

ROOT = Path(__file__).resolve().parents[1]

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in {"p", "h2", "h3", "li", "pre", "tr"}:
            self.parts.append("\n")

def build():
    articles = json.loads((ROOT / "articles/index.json").read_text(encoding="utf-8"))
    for a in articles:
        body = (ROOT / f'articles/{a["id"]}.html').read_text(encoding="utf-8")
        parser = Text()
        parser.feed(body)
        a["html"] = body
        a["text"] = "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())
        title = html.escape(a["title"])
        standalone = body.replace('href="#/', 'href="../../index.html#/').replace('href="exports/', 'href="../../exports/').replace('href="scripts/', 'href="../../scripts/').replace('href="data/', 'href="../../data/').replace('src="exports/', 'src="../../exports/')
        out = ROOT / "reference/articles"
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{a["id"]}.html').write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title} — Liberpedia</title><link rel="stylesheet" href="../../style.css">'
            '<body><main class="standalone-article"><nav><a href="../../reference/index.html">Reference index</a> · '
            f'<a href="../../index.html#/wiki/{a["id"]}">Open in wiki</a> · <a href="{a["id"]}.txt">Plain text</a></nav>'
            f'<h1>{title}</h1><p>{html.escape(a["summary"])}</p>{standalone}</main></body></html>', encoding="utf-8", newline="\n")
        (out / f'{a["id"]}.txt').write_text(a["title"] + "\n\n" + a["summary"] + "\n\n" + a["text"] + "\n\nSource links and downloads: https://jelliottdev.github.io/reference/articles/" + a["id"] + ".html\n", encoding="utf-8", newline="\n")
    (ROOT / "data/articles.json").write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Built {len(articles)} searchable articles and standalone HTML/text copies.")

if __name__ == "__main__":
    build()
