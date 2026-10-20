"""Check local article destinations without network requests.

Checks guide IDs/section anchors, manuscript IDs, local files/images, duplicate
HTML IDs, metadata destinations, published experiment routes, and topic-index links. Other application routes and external URLs
are outside this check; it does not certify their availability.
"""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

# Stable bookmark IDs rendered by experimentArticle in experiments.js.
EXPERIMENT_SECTIONS = {
    "experiment-finding", "experiment-scope", "experiment-reproduce",
    "experiment-remaining", "experiment-sources",
}


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


def validate(root, articles, topics=(), experiments=()):
    errors = []
    parsed = {}
    published = {r["id"]: r for r in experiments if r.get("status") == "published"}
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

    def destinations(aid, targets, local_ids=()):
        for target in targets:
            if target.startswith("#/wiki/"):
                route = urlsplit(target[1:])
                if "#" in target[1:]:
                    errors.append(f"{aid}: unsupported guide fragment {target}; use ?section= instead")
                    continue
                other = unquote(route.path[len("/wiki/"):])
                if other not in parsed:
                    errors.append(f"{aid}: missing guide {target}")
                    continue
                for section in parse_qs(route.query).get("section", []):
                    if section not in parsed[other].ids:
                        errors.append(f"{aid}: missing guide section {target}")
            elif target.startswith(("#/page/", "#/reader/")):
                manuscript(aid, unquote(target.split("/")[2].split("?")[0]))
            elif target.startswith("#/experiments/"):
                route = urlsplit(target[1:])
                if "#" in target[1:]:
                    errors.append(f"{aid}: unsupported experiment fragment {target}; use ?section= instead")
                    continue
                record = published.get(route.path[len("/experiments/"):])
                if record is None:
                    errors.append(f"{aid}: missing published experiment {target}")
                    continue
                sections = EXPERIMENT_SECTIONS | ({"experiment-family"} if record.get("family") else set())
                for section in parse_qs(route.query).get("section", []):
                    if section not in sections:
                        errors.append(f"{aid}: missing experiment section {target}")
            elif target.startswith("#/"):
                continue  # Other application routes need browser/router checks.
            elif target.startswith("#"):
                if unquote(target[1:]) not in local_ids:
                    errors.append(f"{aid}: missing local anchor {target}")
            else:
                url = urlsplit(target)
                if url.scheme or url.netloc:
                    continue  # Never fetch third-party URLs during this check.
                path = (root / unquote(url.path).lstrip("/")).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    errors.append(f"{aid}: missing local file {target}")

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
        destinations(aid, parsed[aid].targets, parsed[aid].ids)

    topic_counts = Counter(t["id"] for t in topics)
    errors.extend(f"Duplicate topic ID: {tid}" for tid, count in topic_counts.items() if count > 1)
    for topic in topics:
        destinations("topic " + topic["id"], [link["href"] for link in topic["links"]])
    return errors, sum(len(p.targets) for p in parsed.values()) + sum(len(t["links"]) for t in topics)


def main():
    articles = json.loads((ROOT / "articles/index.json").read_text(encoding="utf-8"))
    articles += json.loads((ROOT / "articles/readings/index.json").read_text(encoding="utf-8"))
    topics = json.loads((ROOT / "data/topics.json").read_text(encoding="utf-8"))
    experiments = json.loads((ROOT / "data/experiments.json").read_text(encoding="utf-8"))["records"]
    errors, total = validate(ROOT, articles, topics, experiments)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(articles)} articles, {len(topics)} topics, {total} link/image references; "
          "guide sections, published experiment sections, manuscript IDs, local files, and metadata destinations checked.")
    print("External URLs and other application routes were not checked.")


if __name__ == "__main__":
    main()
