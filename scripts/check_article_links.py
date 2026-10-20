"""Check local article destinations without network requests.

Checks guide IDs/section anchors, manuscript IDs, local files/images, duplicate
HTML IDs, and metadata destinations. Other application routes and external URLs
are outside this check; it does not certify their availability.
"""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.ids = []
        self.targets = []
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        target = attrs.get("href") if tag == "a" else attrs.get("src") if tag == "img" else None
        if target:
            self.targets.append(target)


def validate(root, articles):
    errors = []
    parsed = {}
    counts = Counter(a["id"] for a in articles)
    errors.extend(f"Duplicate article ID: {aid}" for aid, count in counts.items() if count > 1)
    for article in articles:
        aid = article["id"]
        path = root / "articles" / article.get("source", aid + ".html")
        if not path.is_file():
            errors.append(f"{aid}: missing source {path}")
            continue
        parsed[aid] = Links(path.read_text(encoding="utf-8"))
        duplicate_ids = Counter(parsed[aid].ids)
        errors.extend(f"{aid}: duplicate HTML ID {key}" for key, n in duplicate_ids.items() if n > 1)

    def manuscript(aid, page):
        if not (root / "data/pages" / (page + ".json")).is_file():
            errors.append(f"{aid}: unknown manuscript {page}")

    for article in articles:
        aid = article["id"]
        if aid not in parsed:
            continue
        for section in article.get("alias_sections", {}).values():
            if section not in parsed[aid].ids:
                errors.append(f"{aid}: search alias points to missing section {section}")
        pages = list(article.get("pages", [])) + list(article.get("feature_pages", []))
        for values in article.get("alias_pages", {}).values():
            pages.extend(values)
        for page in set(pages):
            manuscript(aid, page)
        for target in parsed[aid].targets:
            if target.startswith("#/wiki/"):
                route = urlsplit(target[1:])
                other = unquote(route.path[len("/wiki/"):])
                if other not in parsed:
                    errors.append(f"{aid}: missing guide {target}")
                    continue
                for section in parse_qs(route.query).get("section", []):
                    if section not in parsed[other].ids:
                        errors.append(f"{aid}: missing guide section {target}")
            elif target.startswith(("#/page/", "#/reader/")):
                manuscript(aid, unquote(target.split("/")[2].split("?")[0]))
            elif target.startswith("#/"):
                continue  # Other application routes need browser/router checks.
            elif target.startswith("#"):
                if unquote(target[1:]) not in parsed[aid].ids:
                    errors.append(f"{aid}: missing local anchor {target}")
            else:
                url = urlsplit(target)
                if url.scheme or url.netloc:
                    continue  # Never fetch third-party URLs during this check.
                path = (root / unquote(url.path).lstrip("/")).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    errors.append(f"{aid}: missing local file {target}")
    return errors, sum(len(p.targets) for p in parsed.values())


def main():
    articles = json.loads((ROOT / "articles/index.json").read_text(encoding="utf-8"))
    articles += json.loads((ROOT / "articles/readings/index.json").read_text(encoding="utf-8"))
    errors, total = validate(ROOT, articles)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(articles)} articles, {total} link/image references; "
          "guide sections, manuscript IDs, local files, and metadata destinations checked.")
    print("External URLs and other application routes were not checked.")


if __name__ == "__main__":
    main()
