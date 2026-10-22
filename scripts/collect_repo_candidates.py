"""Snapshot bounded GitHub repository searches for future source screening.

This finds candidates, not experiments. GitHub search is not an exhaustive
index of all public Cicada work, and descriptions are author-supplied.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
QUERIES = [
    'liber primus in:name,description',
    'cicada3301 in:name,description',
    '"cicada 3301" in:name,description',
]


def search(query, page):
    params = urlencode({'q': query, 'per_page': 100, 'page': page,
                        'sort': 'stars', 'order': 'desc'})
    request = Request('https://api.github.com/search/repositories?' + params,
                      headers={'User-Agent': 'Liberpedia-source-inventory',
                               'Accept': 'application/vnd.github+json'})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    checked_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    queries, repos = [], {}
    for query in QUERIES:
        first = search(query, 1)
        total = first['total_count']
        pages = min((total + 99) // 100, 10)  # GitHub Search's 1,000-result limit.
        items = list(first['items'])
        for page in range(2, pages + 1):
            items.extend(search(query, page)['items'])
        queries.append({'query': query, 'reported_count': total,
                        'retrieved_count': len(items),
                        'incomplete_results': first['incomplete_results']})
        for item in items:
            name = item['full_name']
            if name not in repos:
                repos[name] = {
                    'full_name': name, 'url': item['html_url'],
                    'description': item['description'],
                    'default_branch': item['default_branch'],
                    'pushed_at': item['pushed_at'], 'fork': item['fork'],
                    'archived': item['archived'], 'stars': item['stargazers_count'],
                    'matched_queries': []
                }
            repos[name]['matched_queries'].append(query)
    result = {
        'schema': 'liberpedia-public-repo-candidates-v1',
        'checked_at_utc': checked_at,
        'scope': 'Bounded GitHub repository-name/description search only. Candidate discovery does not imply code review, source authenticity, or experiment reproduction. Other hosts and repos without matching metadata are absent.',
        'queries': queries,
        'candidates': [repos[name] for name in sorted(repos, key=str.casefold)]
    }
    path = ROOT / 'research/public-repository-candidates.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')
    print(f"Saved {len(repos)} distinct candidates from {sum(q['retrieved_count'] for q in queries)} search hits")
    for query in queries:
        print(f"{query['query']}: {query['retrieved_count']} / {query['reported_count']}")


if __name__ == '__main__':
    main()
