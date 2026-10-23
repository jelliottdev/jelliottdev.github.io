"""A small mobile-readable summary of four distinct source gates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make() -> str:
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    c10 = max(x["best_llr"] for x in d["c10"])
    c13 = max(x["best_llr"] for x in d["c13"])
    c11 = min(x["p"] for x in d["c11"])
    c12 = min(x["p"] for x in d["c12"])
    assert c10 < -10 and c13 < -10 and c11 > .01/1998 and c12 > .01/1000
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 420" role="img" aria-labelledby="title desc">
<title id="title">Four source-defined keyspace checks</title>
<desc id="desc">C10 and C13 lie beyond their exclusion line under specific unigram models. C11 and C12 have no lag passing corrected detection lines. None recovers a reading.</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#243039}}.k{{font-size:14px;font-weight:700}}.v{{font-size:20px;font-weight:700;fill:#285c78}}.n{{font-size:14px;fill:#4c5961}}.line{{stroke:#c5cdd2}}</style>
<rect x="1" y="1" width="318" height="418" fill="#fff" stroke="#c5cdd2"/>
<text x="16" y="29" class="k">What the source checks found</text>
<text x="16" y="52" class="n">One LP2 rune stream · four distinct models</text>
<line x1="16" y1="67" x2="304" y2="67" class="line"/>
<text x="16" y="92" class="k">C10 · English-like running key</text>
<text x="16" y="120" class="v">{c10:.2f} nats</text>
<text x="16" y="140" class="n">Best model; exclusion line −10</text>
<line x1="16" y1="157" x2="304" y2="157" class="line"/>
<text x="16" y="182" class="k">C13 · small key alphabets</text>
<text x="16" y="210" class="v">{c13:.2f} nats</text>
<text x="16" y="230" class="n">Best model; exclusion line −10</text>
<line x1="16" y1="247" x2="304" y2="247" class="line"/>
<text x="16" y="272" class="k">C11 · ciphertext autokey lag</text>
<text x="16" y="300" class="v">p = {c11:.4g}</text>
<text x="16" y="320" class="n">Smallest; pass line 0.00000501</text>
<line x1="16" y1="337" x2="304" y2="337" class="line"/>
<text x="16" y="362" class="k">C12 · selected alphabet lag</text>
<text x="16" y="390" class="v">p = {c12:.4g}</text>
<text x="16" y="410" class="n">Smallest; pass line 0.00001</text>
</svg>'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path = HERE / "comparison.svg"
    expected = make()
    if args.check:
        assert path.read_text(encoding="utf-8") == expected
    else:
        path.write_text(expected, encoding="utf-8")


if __name__ == "__main__":
    main()
