"""Build bounded, traceable retrieval documents from the existing wiki, without AI."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
docs = []


def add(id, title, kind, href, text, page=None):
    # Split at paragraph boundaries; label each excerpt. Never invent a summary.
    paragraphs = text.strip().split("\n\n")
    chunks, chunk = [], ""
    for paragraph in paragraphs:
        if len(chunk) + len(paragraph) > 2800 and chunk:
            chunks.append(chunk)
            chunk = ""
        while len(paragraph) > 2800:
            cut = paragraph.rfind("\n", 0, 2800)
            if cut < 500:
                cut = paragraph.rfind(" ", 0, 2800)
            if cut < 1:
                cut = 2800
            chunks.append(paragraph[:cut])
            paragraph = paragraph[cut:].lstrip()
        chunk += ("\n\n" if chunk else "") + paragraph
    if chunk:
        chunks.append(chunk)
    for i, content in enumerate(chunks):
        docs.append(dict(id=f"{id}-{i}", title=title, kind=kind, href=href,
                         page=page, excerpt=f"Excerpt {i+1} of {len(chunks)}",
                         text=content))


for path in sorted((ROOT / "data/pages").glob("*.json")):
    p = json.loads(path.read_text(encoding="utf-8"))
    pid = p["id"]
    text = (f'{pid.upper()}; zero-based release page {p["release_index"]}.\n'
            f'Status: {p["status"]}. Basis: {p["status_basis"]}.\n'
            f'Archived transcription rune count: {p["rune_count"]}; prime sum: {p["prime_sum"]}. '
            'These counts are transcription-derived, not a visual verification.\n\n')
    text += "\n\n".join(n["title"] + ": " + n["text"] for n in p["notes"])
    if not p["notes"]:
        text += "No detailed visual inventory is published for this page."
    if p.get("numbers"):
        text += "\n\nPrinted decimal rows:\n" + "\n".join(" ".join(map(str, r)) for r in p["numbers"])
    add(pid, pid.upper() + (": " + p["title"] if p["title"] else ""), "page",
        f"#/page/{pid}", text, pid)
    if p.get("reading"):
        r = p["reading"]
        add(pid+"-reading", pid.upper()+" — known reading", "reading", f"#/reader/{pid}",
            f'Method: {r["method"]}\n\nLiteral reading for this page:\n{r["literal"]}\n\n'
            f'Contextual whole-section reading. Covers {", ".join(r["section_pages"])}; '
            f'not solely this page:\n{r["reading"]}', pid)

encoded = json.dumps(docs, ensure_ascii=False, separators=(",", ":"))
result = {"schema": "liberpedia-assistant-v1",
          "revision": hashlib.sha256(encoded.encode()).hexdigest()[:16], "documents": docs}
(ROOT / "data/assistant-index.json").write_text(
    json.dumps(result, ensure_ascii=False, separators=(",", ":"))+"\n", encoding="utf-8", newline="\n")
print(f"Built {len(docs)} source excerpts; {len(encoded.encode()):,} bytes")
