import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "app-dna"

def load(n):
    p = OUT / f"{n}.json"
    return json.loads(p.read_text()) if p.exists() else None

which = sys.argv[1:] or ["landing"]

for name in which:
    d = load(name)
    if not d:
        print(f"!! no probe for {name}")
        continue
    print(f"\n{'='*78}\n{name}  ->  {d.get('path')}\n{'='*78}")
    print("meta:", d.get("meta"))
    print("\n-- OUTLINE (headings, DOM order) --")
    for h in d.get("outline", []):
        print(f"   {h['tag']}: {h['text']}")
    print("\n-- CTAs (deduplicated, painted) --")
    seen = set()
    for c in d.get("ctas", []):
        k = (c["text"], c["bg"], c["color"], c["radius"])
        if k in seen:
            continue
        seen.add(k)
        print(f"   {c['text'][:40]!r:44} bg={c['bg']:20} fg={c['color']:20} r={c['radius']:9} h={c['h']}")
    print("\n-- infinite CSS animations --")
    for a in d.get("smells", {}).get("infiniteCssAnimations", []):
        print("   ", a)
    print("\n-- painted backgrounds (top 8) --")
    for k, v in list(d.get("painted", {}).get("backgrounds", {}).items())[:8]:
        print(f"   {v:5}  {k}")
    print("\n-- painted text colors (top 8) --")
    for k, v in list(d.get("painted", {}).get("textColors", {}).items())[:8]:
        print(f"   {v:5}  {k}")
    print("\n-- tokens (first 40) --")
    for k, v in list(d.get("tokens", {}).items())[:40]:
        print(f"   {k:28} {v}")
