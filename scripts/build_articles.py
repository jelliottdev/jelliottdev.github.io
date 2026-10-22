"""Build searchable wiki articles and standalone HTML/text from authored sources."""
from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re
from urllib.parse import urljoin, parse_qs, quote

ROOT = Path(__file__).resolve().parents[1]

# Keep the family directory synchronized with published experiment scopes.
import runpy
runpy.run_path(str(ROOT / 'scripts/build_method_map.py'))
runpy.run_path(str(ROOT / 'scripts/build_research_coverage.py'))
runpy.run_path(str(ROOT / 'scripts/build_transcription_decisions.py'))

def linked_reference_text(text):
    """Keep reference text intact while making its explicit HTTP(S) URLs usable."""
    parts = []
    position = 0
    for match in re.finditer(r"""https?://[^\s<>"']+""", text):
        parts.append(html.escape(text[position:match.start()]))
        url = html.escape(match.group(), quote=True)
        parts.append(f'<a href="{url}">{url}</a>')
        position = match.end()
    parts.append(html.escape(text[position:]))
    return "".join(parts)

def manuscript_reference_html(text):
    """Render only the heading structure emitted by our manuscript exporter."""
    title, separator, remainder = text.partition("\n\n")
    if not title.startswith("# ") or not separator:
        raise ValueError("Expected a generated manuscript reference heading")
    parts = re.split(r"(?m)^## ([^\n]+)\n\n", remainder)
    sections = []
    for index in range(1, len(parts), 2):
        identifier = "record-section-" + str((index + 1) // 2)
        sections.append(f'<section><h2 id="{identifier}">{html.escape(parts[index])}</h2>'
                        f'<div class="reference-text">{linked_reference_text(parts[index + 1])}</div>'
                        '</section>')
    body = "".join(sections)
    return (f'<h1>{html.escape(title[2:])}</h1>' + article_contents(body)
            + f'<div class="reference-text">{linked_reference_text(parts[0])}</div>'
            + body)

class Text(HTMLParser):
    blocks = {"p", "h1", "h2", "h3", "h4", "li", "pre", "tr",
              "dt", "dd", "figure", "figcaption", "blockquote"}
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
        self.link_labels = {}
        self.anchor = None
    def add_label(self, target, label):
        label = " ".join(label.split())
        if label and label not in self.link_labels.setdefault(target, []):
            self.link_labels[target].append(label)
    def handle_data(self, data):
        self.parts.append(data)
        if self.anchor is not None:
            self.anchor[1].append(data)
    def boundary(self):
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")
    def handle_starttag(self, tag, attrs):
        if tag in {"sup", "sub"}:
            self.handle_data("^(" if tag == "sup" else "_(")
        if tag in self.blocks or tag == "br":
            self.boundary()
        if tag in {"td", "th"}:
            self.parts.append("\t")
        values = dict(attrs)
        if tag == "img" and values.get("alt", "").strip():
            self.boundary()
            self.parts.append("[Image: " + values["alt"].strip() + "]\n")
        target = values.get("href") if tag == "a" else values.get("src") if tag == "img" else None
        if target and target not in self.links:
            self.links.append(target)
        if tag == "a" and target:
            self.anchor = [target, []]
        if tag == "img" and target:
            label = values.get("alt", "")
            self.add_label(target, label)
            if self.anchor is not None:
                self.anchor[1].append(label)
    def handle_endtag(self, tag):
        if tag in {"sup", "sub"}:
            self.handle_data(")")
        if tag == "a" and self.anchor is not None:
            self.add_label(self.anchor[0], "".join(self.anchor[1]))
            self.anchor = None
        if tag in self.blocks:
            self.boundary()

class Headings(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.items = []
        self.current = None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3"):
            identifier = dict(attrs).get("id")
            self.current = [identifier, [], tag] if identifier else None

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if self.current is not None and tag == self.current[2]:
            identifier, parts, level = self.current
            self.items.append((identifier, "".join(parts).strip(), level))
            self.current = None


def article_contents(body):
    headings = Headings(body).items
    if not headings:
        return ""
    groups = []
    for identifier, label, level in headings:
        entry = (identifier, label, [])
        if level == "h3" and groups:
            groups[-1][2].append(entry)
        else:
            groups.append(entry)

    def render(entries):
        return '<ul class="guide-contents-list">' + "".join(
            f'<li><a href="#{quote(identifier, safe="-_")}">{html.escape(label)}</a>'
            + (render(children) if children else "") + '</li>'
            for identifier, label, children in entries) + '</ul>'

    links = render(groups)
    return ('<details class="standalone-contents"><summary>On this page</summary>'
            '<nav aria-label="Article sections">' + links + '</nav></details>')

def reference_url(target, article_id=None):
    """Prefer standalone guide/page references over JavaScript routes."""
    if target.startswith("#") and not target.startswith("#/") and article_id:
        return urljoin("https://jelliottdev.github.io/reference/articles/"
                       + article_id + ".html", target)
    if target.startswith("#/wiki/"):
        article, _, query = target.split("/")[2].partition("?")
        section = parse_qs(query).get("section", [""])[0]
        return ("https://jelliottdev.github.io/reference/articles/" + article + ".html"
                + ("#" + quote(section, safe="-_") if section else ""))
    if target.startswith("#/page/"):
        return "https://jelliottdev.github.io/reference/" + target.split("/")[2].split("?")[0] + ".html"
    return urljoin("https://jelliottdev.github.io/", target)

def standalone_url(target):
    """Resolve authored site-root-relative resources from reference/articles/."""
    if target.startswith("#/wiki/"):
        article, _, query = target[len("#/wiki/"):].partition("?")
        section = parse_qs(query).get("section", [""])[0]
        return article + ".html" + ("#" + quote(section, safe="-_") if section else "")
    if target.startswith("#/page/"):
        return "../" + target[len("#/page/"):].split("?")[0] + ".html"
    if target.startswith("#/"):
        return "../../index.html" + target
    if not target or target.startswith(("#", "/")) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        return target
    return "../../" + target


def standalone_body(body):
    # Rewrite real link/image attributes, not examples inside code blocks.
    def tag(match):
        return re.sub(r"\b(href|src)=(['\"])(.*?)\2",
                      lambda attr: attr[1] + '=' + attr[2]
                      + html.escape(standalone_url(html.unescape(attr[3])), quote=True)
                      + attr[2], match[0])
    return re.sub(r"<(?:a|img)\b[^>]*>", tag, body)


def linked_articles(body):
    """Collect exact guide destinations, including links to guide sections."""
    parser = Text()
    parser.feed(body)
    return sorted({link[len("#/wiki/"):].split("?")[0].split("#")[0]
                   for link in parser.links if link.startswith("#/wiki/")
                   and link[len("#/wiki/"):].split("?")[0].split("#")[0]})

def guide_discovery_index(articles):
    """Small discovery metadata; article bodies and experiment evidence stay separate."""
    return {
        "schema": "liberpedia-guide-index-v1",
        "scope": "Guide discovery only. Inclusion is not evidence that an experiment was performed.",
        "page_fields": {
            "pages": "All manuscript pages associated with the guide, including contextual references.",
            "feature_pages": "Curated pages where the guide subject is illustrated; not every page in a named group.",
            "alias_pages": "Page IDs for a particular search phrase. Prefer these over the broad pages list when that phrase matches. Keys match case- and accent-insensitively.",
        },
        "guides": [{
            "id": a["id"], "title": a["title"], "summary": a["summary"],
            "category": a.get("category", "Reference"),
            "url": reference_url("#/wiki/" + a["id"]),
            "text_url": reference_url("#/wiki/" + a["id"]).removesuffix(".html") + ".txt",
            "aliases": a.get("aliases", []),
            "alias_urls": {
                alias: reference_url("#/wiki/" + a["id"] + "?section=" + quote(section, safe=""))
                for alias, section in a.get("alias_sections", {}).items()
            },
            "pages": a.get("pages", []),
            "feature_pages": a.get("feature_pages", []),
            "alias_pages": a.get("alias_pages", {}),
        } for a in articles],
    }

def build():
    categories = {g["title"]: g["id"] for g in json.loads((ROOT / "data/guide-categories.json").read_text(encoding="utf-8"))}
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
        a["references"] = [reference_url(link, a["id"]) for link in parser.links]
        reference_details = [{"url": reference_url(link, a["id"]),
                                   "labels": parser.link_labels.get(link, [])}
                                  for link in parser.links]
        a["linked_articles"] = outgoing[a["id"]]
        title = html.escape(a["title"])
        category = a.get("category", "Reference")
        category_link = (f'<a href="../index.html#guides-{html.escape(categories[category], quote=True)}">{html.escape(category)}</a> · '
                         if category in categories else "")
        standalone = standalone_body(body)
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
            '<body><main class="standalone-article"><nav aria-label="Article navigation"><a href="../../reference/index.html">Reference index</a> · '
            + category_link +
            f'<a href="../../index.html#/wiki/{a["id"]}">Open in wiki</a> · <a href="{a["id"]}.txt">Plain text</a></nav>'
            f'<h1>{title}</h1><p>{html.escape(a["summary"])}</p>{article_contents(body)}{standalone}</main></body></html>', encoding="utf-8", newline="\n")
        links = "\n".join(("- " + "; ".join(ref["labels"]) + "\n  " + ref["url"])
                          if ref["labels"] else "- " + ref["url"]
                          for ref in reference_details)
        (out / f'{a["id"]}.txt').write_text(a["title"] + "\n\n" + a["summary"] + "\n\n" + a["text"] + "\n\nSources, related references, and files\n" + links + "\n\nArticle: https://jelliottdev.github.io/reference/articles/" + a["id"] + ".html\n", encoding="utf-8", newline="\n")
    (ROOT / "data/articles.json").write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    search_articles = [{key: value for key, value in a.items() if key != "html"} for a in articles]
    (ROOT / "data/article-search.json").write_text(
        json.dumps(search_articles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(f"Built {len(articles)} searchable articles and standalone HTML/text copies.")

if __name__ == "__main__":
    build()
