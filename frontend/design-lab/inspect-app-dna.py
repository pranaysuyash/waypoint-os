#!/usr/bin/env python3
"""
inspect-app-dna.py — extract the SHIPPED design system from the running app as DATA.

Why this exists: screenshots are not reliably readable by every model in the loop.
Computed styles + DOM text are. This logs in, walks the authenticated routes, and
dumps the actual tokens, typography, colour histogram, and "design smell" counts
for each route, so design direction can be reasoned about with evidence.

Outputs:
  design-lab/app-dna/<route>.json   raw per-route probe
  design-lab/app-dna/REPORT.md      human-readable comparison against DESIGN.md

Usage:
  python3 inspect-app-dna.py [--base http://127.0.0.1:3001] [--api http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Sandbox sets HTTP_PROXY which routes localhost through a dead proxy. Strip it.
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

HERE = Path(__file__).resolve().parent
OUT = HERE / "app-dna"

USER = os.environ.get("WP_USER", "newuser@test.com")
PASSWORD = os.environ.get("WP_PASSWORD", "testpass123")

# ── routes to walk. name -> path. trip routes are appended if a trip id resolves.
ROUTES = [
    ("landing", "/"),
    ("overview", "/overview"),
    ("trips", "/trips"),
    ("inbox", "/inbox"),
    ("quotes", "/quotes"),
    ("settings", "/settings"),
    ("insights", "/insights"),
    ("suppliers", "/suppliers"),
]

# ─────────────────────────────────────────────────────────────────────────────
# The probe. Runs INSIDE the page. Everything it returns is plain JSON data.
# ─────────────────────────────────────────────────────────────────────────────
PROBE = r"""
() => {
  const out = {};
  const cs = (el) => el ? getComputedStyle(el) : null;

  // 1. LIVE CSS CUSTOM PROPERTIES — the real token table the app is running on.
  const rootCS = cs(document.documentElement);
  const tokens = {};
  const sheetVars = new Set();
  for (const sheet of Array.from(document.styleSheets)) {
    let rules;
    try { rules = sheet.cssRules; } catch (e) { continue; }
    const walk = (rs) => {
      for (const r of Array.from(rs)) {
        if (r.type === CSSRule.STYLE_RULE && r.selectorText) {
          if (/^(html|:root)$/.test(r.selectorText.trim())) {
            for (const p of Array.from(r.style)) {
              if (p.startsWith('--')) sheetVars.add(p);
            }
          }
        } else if (r.cssRules) { walk(r.cssRules); }
      }
    };
    walk(rules);
  }
  for (const v of sheetVars) {
    const val = rootCS.getPropertyValue(v);
    if (val && val.trim()) tokens[v] = val.trim();
  }
  out.tokens = tokens;

  // 2. Page-level surface + typography actually painted.
  const b = cs(document.body);
  out.body = {
    background: b.backgroundColor,
    backgroundImage: (b.backgroundImage || '').slice(0, 300),
    color: b.color,
    fontFamily: b.fontFamily,
    fontSize: b.fontSize,
    lineHeight: b.lineHeight,
  };
  const h = cs(document.documentElement);
  out.html = { background: h.backgroundColor, fontFamily: h.fontFamily, colorScheme: h.colorScheme };

  // 3. Heading outline — what the page claims to be about, in DOM order.
  out.outline = Array.from(document.querySelectorAll('h1,h2,h3'))
    .map(e => ({ tag: e.tagName, text: (e.innerText || '').replace(/\s+/g,' ').trim().slice(0, 110) }))
    .filter(e => e.text);

  // 4. Navigation labels — the product's own information architecture.
  const navSel = 'nav, aside, [role="navigation"]';
  out.nav = Array.from(document.querySelectorAll(navSel)).map(n => {
    const items = Array.from(n.querySelectorAll('a,button'))
      .map(a => (a.innerText || a.getAttribute('aria-label') || '').replace(/\s+/g,' ').trim())
      .filter(t => t && t.length < 40);
    return Array.from(new Set(items)).slice(0, 40);
  }).filter(a => a.length);

  // 5. COLOUR HISTOGRAM — what is actually painted, weighted by element count.
  const bgCounts = new Map();
  const fgCounts = new Map();
  const radiusCounts = new Map();
  const fontCounts = new Map();
  for (const el of Array.from(document.querySelectorAll('*'))) {
    const s = cs(el);
    if (!s) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;                 // skip unrendered
    if (r.width * r.height > 4000000) continue;           // skip giant wrappers
    if (s.display === 'none' || s.visibility === 'hidden') continue;

    let bg = s.backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
      const k = bg.replace(/\s+/g, '');
      bgCounts.set(k, (bgCounts.get(k) || 0) + 1);
    }
    // only count text colour on elements that actually own a text node
    const ownsText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (ownsText) {
      const k = (s.color || '').replace(/\s+/g, '');
      if (k) fgCounts.set(k, (fgCounts.get(k) || 0) + 1);
      const f = (s.fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
      if (f) fontCounts.set(f, (fontCounts.get(f) || 0) + 1);
    }
    const br = s.borderTopLeftRadius;
    if (br && br !== '0px') radiusCounts.set(br, (radiusCounts.get(br) || 0) + 1);
  }
  const top = (m, n) => Object.fromEntries([...m.entries()].sort((a,b) => b[1]-a[1]).slice(0, n));
  out.painted = {
    backgrounds: top(bgCounts, 14),
    textColors: top(fgCounts, 14),
    fonts: top(fontCounts, 8),
    radii: top(radiusCounts, 10),
  };

  // 6. DESIGN SMELLS — objective counts of the patterns DESIGN.md §11 says to retire.
  const all = Array.from(document.querySelectorAll('*'));
  let backdrop = 0, gradients = 0, glowShadow = 0, smil = 0;
  const infiniteRules = [];
  for (const el of all) {
    const s = cs(el);
    if (!s) continue;
    if (s.backdropFilter && s.backdropFilter !== 'none') backdrop++;
    if (/gradient\(/.test(s.backgroundImage || '')) gradients++;
    if (s.boxShadow && s.boxShadow !== 'none') {
      const px = (s.boxShadow.match(/(\d+(?:\.\d+)?)px/g) || []).map(parseFloat);
      if (px.some(v => v >= 24)) glowShadow++;
    }
    if (s.animationName && s.animationName !== 'none') {
      const dur = parseFloat(s.animationDuration) || 0;
      const it = s.animationIterationCount;
      if (it === 'infinite' || (parseFloat(it) || 0) > 1) {
        infiniteRules.push({ name: s.animationName, dur: s.animationDuration, iter: it });
      }
    }
  }
  smil = document.querySelectorAll('animate, animateMotion, animateTransform').length;
  out.smells = {
    backdropFilterElements: backdrop,
    gradientElements: gradients,
    glowShadowElements: glowShadow,
    smilAnimationElements: smil,
    infiniteCssAnimations: infiniteRules.slice(0, 12),
  };

  // 7. Interactive inventory — buttons/links with their fill, for CTA analysis.
  out.ctas = Array.from(document.querySelectorAll('button, a'))
    .filter(e => {
      const r = e.getBoundingClientRect();
      return r.width > 40 && r.height > 20 && (e.innerText || '').trim();
    })
    .slice(0, 40)
    .map(e => {
      const s = cs(e);
      return {
        text: (e.innerText || '').replace(/\s+/g,' ').trim().slice(0, 42),
        bg: s.backgroundColor.replace(/\s+/g,''),
        color: s.color.replace(/\s+/g,''),
        radius: s.borderTopLeftRadius,
        h: Math.round(e.getBoundingClientRect().height),
      };
    });

  out.meta = { title: document.title, url: location.pathname, scrollH: document.documentElement.scrollHeight };
  return out;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Canonical DESIGN.md palettes, for diffing against what actually shipped.
# ─────────────────────────────────────────────────────────────────────────────
THEME_A = {   # "Cartographic Dark" — what is built
    "bg-canvas": "#080a0c", "bg-surface": "#0f1115", "bg-elevated": "#161b22",
    "bg-highlight": "#1c2128", "bg-input": "#111318",
    "text-primary": "#e6edf3", "text-secondary": "#a8b3c1", "text-tertiary": "#8b949e",
    "accent-blue": "#58a6ff", "accent-green": "#3fb950", "accent-amber": "#d29922",
    "accent-red": "#f85149", "accent-cyan": "#39d0d8", "accent-purple": "#a371f7",
    "border-default": "#30363d", "border-hover": "#8b949e", "border-active": "#58a6ff",
}
THEME_B = {   # "Minimalist Document" — specified, implemented nowhere
    "bg-canvas": "#f7f5f2", "bg-surface": "#ffffff", "bg-elevated": "#f0eeea",
    "text-primary": "#1a1a1a", "text-secondary": "#4a4a4a", "text-tertiary": "#6b6b6b",
    "accent-blue": "#2563eb", "accent-green": "#059669", "accent-amber": "#d97706",
    "accent-red": "#dc2626", "border-default": "#e5e2dd", "border-hover": "#c4c0b8",
    "border-active": "#2563eb",
}


def hexof(s: str) -> str | None:
    s = (s or "").strip().lower().replace(" ", "")
    m = re.match(r"^#([0-9a-f]{6})$", s)
    if m:
        return "#" + m.group(1)
    m = re.match(r"^#([0-9a-f]{3})$", s)
    if m:
        return "#" + "".join(c * 2 for c in m.group(1))
    m = re.match(r"^rgba?\((\d+),\s*(\d+),\s*(\d+)", s)
    if m:
        return "#%02x%02x%02x" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def nearest_theme(hexes: list[str]) -> dict:
    """Score how close a set of painted colours is to Theme A vs Theme B."""
    def lum(h):  # 0..1
        h = h.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        def _f(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * _f(r) + 0.7152 * _f(g) + 0.0722 * _f(b)

    def score(palette):
        targets = [hexof(v) for v in palette.values() if hexof(v)]
        best = 0.0
        for h in hexes:
            lh = lum(h)
            best += max((1.0 - min(1.0, abs(lh - lum(t)) * 1.6)) for t in targets)
        return round(best / max(1, len(hexes)), 3)

    a, b = score(THEME_A), score(THEME_B)
    return {"themeA_score": a, "themeB_score": b, "verdict": "A dark" if a > b else "B light"}


def login(api: str):
    import urllib.request
    req = urllib.request.Request(
        api + "/api/auth/login",
        data=json.dumps({"email": USER, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as f:
        resp = f.read().decode()
        cookies = f.headers.get_all("Set-Cookie") or []
    data = json.loads(resp)
    parsed = []
    for c in cookies:
        name, _, rest = c.partition("=")
        val, _, _ = rest.partition(";")
        parsed.append({"name": name.strip(), "value": val, "domain": "127.0.0.1", "path": "/"})
    return data, parsed


def find_trip(api: str, cookies: list[dict]) -> str | None:
    """Resolve a real trip id so /trips/[id]/intake renders with data."""
    import urllib.request
    jar = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    for path in ("/trips", "/api/trips", "/api/dashboard/stats"):
        try:
            req = urllib.request.Request(api + path, headers={"Cookie": jar, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as f:
                body = f.read().decode()
            try:
                d = json.loads(body)
            except Exception:
                continue
            found = []

            def dig(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k in ("trip_id", "tripId", "id") and isinstance(v, str) and len(v) >= 8:
                            found.append(v)
                        else:
                            dig(v)
                elif isinstance(o, list):
                    for v in o[:40]:
                        dig(v)

            dig(d)
            if found:
                return found[0], path
        except Exception as e:
            print(f"   probe {path}: {type(e).__name__} {e}", file=sys.stderr)
    return None, None


def chrome_executable() -> str | None:
    for c in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ):
        if os.path.exists(c):
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:3001")
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed. Install with: pip install playwright", file=sys.stderr)
        return 2

    print(f"[1/4] logging in as {USER} @ {args.api}")
    user, cookies = login(args.api)
    print(f"      ok={user.get('ok')} user={user.get('user',{}).get('email')} "
          f"agency={user.get('agency',{}).get('name')} cookies={len(cookies)}")

    trip_id, trip_src = find_trip(args.api, cookies)
    routes = list(ROUTES)
    if trip_id:
        print(f"      trip {trip_id} (via {trip_src})")
        routes += [
            ("trip-detail", f"/trips/{trip_id}"),
            ("trip-intake", f"/trips/{trip_id}/intake"),
            ("trip-packet", f"/trips/{trip_id}/packet"),
        ]
    else:
        print("      no trip id resolved (intake/packet will render empty)")

    exe = chrome_executable()
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=exe, args=["--no-proxy-server"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        if cookies:
            ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.set_default_timeout(45000)

        for i, (name, path) in enumerate(routes, 1):
            print(f"[2/4] ({i}/{len(routes)}) probing {path}")
            try:
                page.goto(args.base + path, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3500)  # let fonts + client components settle
                # dismiss any onboarding overlay that would pollute the probe
                for label in ("Got it", "Got it, thanks", "Dismiss", "Close", "Skip"):
                    try:
                        page.get_by_role("button", name=label).first.click(timeout=1200)
                        page.wait_for_timeout(500)
                    except Exception:
                        pass
                data = page.evaluate(PROBE)
                results[name] = {"path": path, **data}
                (OUT / f"{name}.json").write_text(json.dumps(results[name], indent=2))
                sm = data.get("smells", {})
                print(f"      bg={data['body']['background']} "
                      f"grad={sm.get('gradientElements')} blur={sm.get('backdropFilterElements')} "
                      f"glow={sm.get('glowShadowElements')} smil={sm.get('smilAnimationElements')}")
            except Exception as e:
                print(f"      FAILED {path}: {type(e).__name__}: {e}", file=sys.stderr)
                results[name] = {"path": path, "error": f"{type(e).__name__}: {e}"}

        browser.close()

    print(f"[3/4] wrote {len(results)} probes to {OUT}")
    report = build_report(results, user, trip_id)
    (OUT / "REPORT.md").write_text(report)
    print(f"[4/4] wrote {OUT / 'REPORT.md'}")
    print()
    print(report)
    return 0


def build_report(results: dict, user: dict, trip_id: str | None) -> str:
    L: list[str] = []
    L.append("# App design DNA — measured from the running product")
    L.append("")
    L.append(f"**Captured:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    L.append(f"**Signed in as:** `{user.get('user',{}).get('email')}` "
             f"(agency `{user.get('agency',{}).get('name')}`, role "
             f"`{user.get('membership',{}).get('role')}`)  ")
    L.append(f"**Trip resolved:** `{trip_id or 'none'}`")
    L.append("")
    L.append("Method: logged into the live app and read **computed styles and DOM** "
             "(not screenshots), so every number below is reproducible by re-running "
             "`python3 inspect-app-dna.py`.")
    L.append("")

    # ── per-route surface table
    L.append("## 1. What each screen is actually painted with")
    L.append("")
    L.append("| Route | Body bg | Body text | Font | Gradients | blur() | Glow shadows | SMIL |")
    L.append("|---|---|---|---|---:|---:|---:|---:|")
    for name, d in results.items():
        if "error" in d:
            L.append(f"| `{d['path']}` | ERROR | | | | | | |")
            continue
        b, s = d["body"], d["smells"]
        font = (b["fontFamily"].split(",")[0] or "").strip('"')
        L.append(f"| `{d['path']}` | `{b['background']}` | `{b['color']}` | {font} "
                 f"| {s['gradientElements']} | {s['backdropFilterElements']} "
                 f"| {s['glowShadowElements']} | {s['smilAnimationElements']} |")
    L.append("")

    # ── theme verdict per route
    L.append("## 2. Theme A vs Theme B — measured, not assumed")
    L.append("")
    L.append("Scored by luminance-distance from each canonical palette (DESIGN.md §2).")
    L.append("")
    L.append("| Route | Dominant painted backgrounds | Verdict |")
    L.append("|---|---|---|")
    for name, d in results.items():
        if "error" in d:
            continue
        bgs = list(d["painted"]["backgrounds"].keys())[:5]
        hexes = [h for h in (hexof(x) for x in bgs) if h]
        v = nearest_theme(hexes) if hexes else {}
        L.append(f"| `{d['path']}` | {' '.join('`%s`' % b for b in bgs)} | "
                 f"{v.get('verdict','?')} (A={v.get('themeA_score')} B={v.get('themeB_score')}) |")
    L.append("")

    # ── live token diff
    L.append("## 3. Live CSS custom properties vs DESIGN.md")
    L.append("")
    all_tokens: dict[str, set[str]] = {}
    for name, d in results.items():
        for k, v in (d.get("tokens") or {}).items():
            all_tokens.setdefault(k, set()).add(v)
    drift_a = []
    missing_b = []
    for key, spec_val in THEME_A.items():
        live = all_tokens.get("--" + key)
        if not live:
            continue
        live_hexes = {hexof(x) for x in live if hexof(x)}
        if hexof(spec_val) not in live_hexes:
            drift_a.append((key, spec_val, sorted(live)))
    # NOTE: Theme A and Theme B share token NAMES. Presence proves nothing —
    # only a VALUE match counts as "Theme B is implemented".
    b_ok, b_wrong = [], []
    for key, spec_val in THEME_B.items():
        live = all_tokens.get("--" + key)
        if not live:
            missing_b.append(key)
            continue
        live_hexes = {hexof(x) for x in live if hexof(x)}
        (b_ok if hexof(spec_val) in live_hexes else b_wrong).append((key, spec_val, sorted(live)))
    L.append(f"Tokens observed live: **{len(all_tokens)}**")
    L.append("")
    if drift_a:
        L.append("### 3a. Theme A tokens that differ from DESIGN.md §2")
        L.append("")
        L.append("| Token | DESIGN.md | Live value(s) |")
        L.append("|---|---|---|")
        for k, spec, live in drift_a:
            L.append(f"| `--{k}` | `{spec}` | {' / '.join('`%s`' % x for x in live)} |")
        L.append("")
    else:
        L.append("Theme A tokens match DESIGN.md §2 exactly.")
        L.append("")
    L.append(f"### 3b. Theme B — implemented? "
             f"**{len(b_ok)}/{len(THEME_B)} tokens carry Theme B VALUES**")
    L.append("")
    L.append("(Token *names* are shared with Theme A, so presence is meaningless. "
             "Only a value match counts.)")
    L.append("")
    if b_wrong:
        L.append("| Token | Theme B spec | Live value(s) |")
        L.append("|---|---|---|")
        for k, spec, live in b_wrong:
            L.append(f"| `--{k}` | `{spec}` | {' / '.join('`%s`' % x for x in live)} |")
        L.append("")
    if missing_b:
        L.append(f"Absent entirely: {', '.join('`--%s`' % m for m in missing_b)}")
        L.append("")

    # ── typography actually used
    L.append("## 4. Typography in use")
    L.append("")
    fonts: Counter = Counter()
    for name, d in results.items():
        for f, n in (d.get("painted", {}).get("fonts", {}) or {}).items():
            fonts[f] += n
    L.append("| Font | elements |")
    L.append("|---|---:|")
    for f, n in fonts.most_common(10):
        L.append(f"| {f} | {n} |")
    L.append("")
    L.append("DESIGN.md §3 specifies **IBM Plex Sans** + **JetBrains Mono**. "
             "`layout.tsx` loads **Sora** + **Rubik**. Measured above is what actually rendered.")
    L.append("")

    # ── IA per route
    L.append("## 5. Navigation / information architecture")
    L.append("")
    for name, d in results.items():
        if "error" in d or not d.get("nav"):
            continue
        L.append(f"**`{d['path']}`** — {', '.join(d['nav'][0][:18]) if d['nav'][0] else '(none)'}")
        L.append("")

    # ── smells rollup
    L.append("## 6. Design-smell rollup (DESIGN.md §11 retirement targets)")
    L.append("")
    tot = Counter()
    for name, d in results.items():
        s = d.get("smells", {})
        tot["gradients"] += s.get("gradientElements", 0)
        tot["backdrop-filter"] += s.get("backdropFilterElements", 0)
        tot["glow-shadows"] += s.get("glowShadowElements", 0)
        tot["smil"] += s.get("smilAnimationElements", 0)
        tot["infinite-css"] += len(s.get("infiniteCssAnimations", []))
    L.append("| Pattern | Total across routes | DESIGN.md §11 says |")
    L.append("|---|---:|---|")
    L.append(f"| gradient backgrounds | {tot['gradients']} | retire (Theme B: none) |")
    L.append(f"| backdrop-filter (glassmorphism) | {tot['backdrop-filter']} | retire (Theme B: none) |")
    L.append(f"| glow shadows (blur >= 24px) | {tot['glow-shadows']} | retire (Theme B: single subtle) |")
    L.append(f"| SMIL animations | {tot['smil']} | not specified |")
    L.append(f"| infinite CSS animations | {tot['infinite-css']} | retire (Theme B: none) |")
    L.append("")

    # ── radii
    L.append("## 7. Border radius in use")
    L.append("")
    radii: Counter = Counter()
    for name, d in results.items():
        for r, n in (d.get("painted", {}).get("radii", {}) or {}).items():
            radii[r] += n
    L.append("| radius | elements |")
    L.append("|---|---:|")
    for r, n in radii.most_common(10):
        L.append(f"| {r} | {n} |")
    L.append("")
    L.append("DESIGN.md §11: Theme A marketing 22–24px -> Theme B 8px everywhere.")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
