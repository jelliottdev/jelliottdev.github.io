"""Build complete-section references from the existing verified reading controls.

This preserves each literal page separately. Contextual English is a labeled
whole-section derivative, never reassigned to a single manuscript page.
"""
from pathlib import Path
import json
from html import escape

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "warning": "A Warning",
    "welcome": "Welcome, Pilgrim",
    "some-wisdom": "Some Wisdom",
    "first-koan": "A Koan: first section",
    "loss-of-divinity": "The Loss of Divinity",
    "second-koan": "A Koan: second section",
    "instruction": "An Instruction",
    "lp2-56": "An End: the hash reference",
    "lp2-57": "Parable",
}
METHODS = {
    "direct": ("direct-reading", "Direct reading", "p = c"),
    "atbash": ("atbash", "Atbash", "p = 28 − c"),
    "shifted-atbash": ("atbash", "Shifted Atbash", "p = (28 − c + 3) mod 29"),
    "vigenere": ("vigenere", "Vigenère", "p = (c − key[j mod key length]) mod 29"),
    "prime-minus-one": ("prime-minus-one", "Prime-minus-one", "p = (c − (prime[j] − 1)) mod 29"),
}

def build():
    controls = json.loads((ROOT / "data/evidence/reading-methods.json").read_text(encoding="utf-8"))["controls"]
    output = ROOT / "articles/readings"
    output.mkdir(exist_ok=True)
    metadata = []
    for control in controls:
        section = control["id"]
        pages = [json.loads((ROOT / f'data/pages/{pid}.json').read_text(encoding="utf-8")) for pid in control["pages"]]
        assert all(p["reading"]["section"] == section for p in pages)
        assert all(p["reading"]["section_pages"] == control["pages"] for p in pages)
        assert len({p["reading"]["reading"] for p in pages}) == 1
        guide, method, formula = METHODS[control["method"]]
        page_links = " · ".join(f'<a href="#/page/{p["id"]}">{p["id"].upper()}</a>' for p in pages)
        body = f'<p>This known section covers {page_links}, in that order. The literal readings below preserve individual page boundaries. The contextual English at the end describes the whole section.</p>'
        if section in {'first-koan', 'second-koan'}:
            body += '<p>For the meaning and relationship of the dialogues, read <a href="#/wiki/koans">The two koans: identity and the inner voice</a>.</p>'
        body += f'<h2 id="method">Method and reproduction</h2><p><a href="#/wiki/{guide}">{method}: worked explanation</a>. The recorded transformation is <code>{escape(formula)}</code>, using zero-based positions in the 29-rune alphabet.</p>'
        if control["key"]:
            body += '<p>Key indices: <code>' + ", ".join(map(str, control["key"])) + '</code>.</p>'
        if control["method"] in {"vigenere", "prime-minus-one"}:
            boundary = "Carry the sequence across the listed page boundaries." if control["boundary"] == "carry" else "Reset the sequence at the page boundary."
            body += f'<p>Start at sequence position {control["start"]}. {boundary} Non-rune characters do not consume key positions.</p>'
        if control["skip"]:
            body += '<p>Copy these zero-based rune ordinals without advancing the sequence: <code>' + ", ".join(map(str, control["skip"])) + '</code>. See <a href="#/wiki/interruptions">interruptions and counting conventions</a>; these recorded positions are not a universal rule for other pages.</p>'
        body += f'<pre><code>python scripts/reproduce_reading.py {section}\npython scripts/reproduce_reading.py {section} --trace</code></pre>'
        body += '<p>Run with Python 3 from the extracted <a href="downloads/reference-data.zip">reference-data bundle</a> or a full repository checkout. The script checks its result against the shipped literal controls before printing. It uses no network or AI requests. <a href="scripts/reproduce_reading.py">Read the script</a> · <a href="data/evidence/reading-methods.json">Exact parameters and provenance</a>.</p>'
        for p in pages:
            pid = p["id"]
            body += f'<h2 id="{pid}">{pid.upper()}: literal reading</h2><p><a href="#/reader/{pid}">Compare with the image</a> · <a href="#/page/{pid}?section=transcription">Transcription and corrections</a> · <a href="exports/{pid}.known-literal.txt" download>Download literal text</a></p>'
            if p["corrections"]:
                body += f'<p>This page has documented transcription corrections. Read the <a href="#/page/{pid}?section=corrections">correction record</a> before comparing another input.</p>'
            body += '<pre><code>' + escape(p["reading"]["literal"]) + '</code></pre>'
        body += '<h2 id="conventions">Reading the notation</h2><p>Latin labels can represent multi-letter runes. Slashes, line markers, and separators retain the exported literal notation; they are not additional decoded letters. See <a href="#/conventions">transcription conventions</a> and <a href="#/wiki/transliteration">literal versus contextual text</a>. Do not silently normalize a spelling before calculating a prime sum.</p>'
        body += '<h2 id="contextual">Contextual whole-section reading</h2><p>This is the archived contextual rendering for all pages listed above. It may normalize or interpret rune labels; use the individual literal texts for sequence and spelling comparisons.</p><details><summary>Show contextual English</summary><p>' + escape(pages[0]["reading"]["reading"]) + '</p></details>'
        body += '<h2 id="sources">Sources and status</h2><p>These are known readings in the 5 October 2026 source snapshot, reproduced using the published controls. <a href="data/evidence/known-readings.json">Compiled readings and provenance</a> · <a href="#/readings">All known sections</a>. Page-specific source images and archive references are linked above. Reproducing a known section does not establish a solution to another page.</p>'
        id = "reading-" + section
        source = f"readings/{id}.html"
        (ROOT / "articles" / source).write_text(body + "\n", encoding="utf-8", newline="\n")
        metadata.append(dict(id=id, source=source, title=NAMES[section] + ": complete reading",
                             summary=f'{method}; {", ".join(pid.upper() for pid in control["pages"])}. Literal pages, contextual text, and exact reproduction.',
                             category="Complete known readings", pages=control["pages"]))
    (output / "index.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(f"Built {len(metadata)} complete-section guides covering {sum(len(c['pages']) for c in controls)} literal pages.")

if __name__ == "__main__":
    build()
