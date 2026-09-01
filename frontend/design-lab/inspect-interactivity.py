#!/usr/bin/env python3
"""
inspect-interactivity.py — measure HOW interactive and animated a page actually is.

Complements inspect-app-dna.py (which measures the visual design system). This one
instruments the runtime: it patches requestAnimationFrame, addEventListener,
IntersectionObserver and canvas.getContext BEFORE any page script runs, then
samples what the page does while idle, while scrolling, and while hovered.

Why runtime instrumentation instead of static analysis: "is it animated" cannot be
answered by grepping CSS. A page can be quiet in CSS and run a permanent rAF loop
in JS (a WebGL scene), or vice versa.

Outputs:
  design-lab/interactivity/<slug>.json    raw measurements
  design-lab/interactivity/REPORT.md      side-by-side comparison

Usage:
  python3 inspect-interactivity.py [url ...]
  python3 inspect-interactivity.py https://fieldcanvas.app http://127.0.0.1:3001/
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Sandbox proxy intercepts everything incl. localhost — strip it.
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

HERE = Path(__file__).resolve().parent
OUT = HERE / "interactivity"

DEFAULT_URLS = ["https://fieldcanvas.app", "http://127.0.0.1:3001/"]

# ─────────────────────────────────────────────────────────────────────────────
# Injected BEFORE any page script. Counts what the page does, not what it says.
# ─────────────────────────────────────────────────────────────────────────────
INIT = r"""
window.__probe = {
  raf: 0, rafSamples: [],
  listeners: {}, listenerTotal: 0,
  io: 0, ro: 0, mo: 0,
  canvases: [], glContexts: 0,
  timingStart: performance.now(),
};
(function () {
  const P = window.__probe;

  // rAF — the single best proxy for "is something animating right now".
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) {
    P.raf++;
    return raf(function (t) { return cb(t); });
  };

  // Event listeners by type — reveals scroll/pointer-driven work.
  const ael = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function (type, fn, opts) {
    try {
      P.listeners[type] = (P.listeners[type] || 0) + 1;
      P.listenerTotal++;
    } catch (e) {}
    return ael.call(this, type, fn, opts);
  };

  // Observers
  const IO = window.IntersectionObserver;
  if (IO) window.IntersectionObserver = class extends IO {
    constructor(...a) { P.io++; super(...a); }
  };
  const RO = window.ResizeObserver;
  if (RO) window.ResizeObserver = class extends RO {
    constructor(...a) { P.ro++; super(...a); }
  };
  const MO = window.MutationObserver;
  if (MO) window.MutationObserver = class extends MO {
    constructor(...a) { P.mo++; super(...a); }
  };

  // canvas + WebGL — a 3D scene is the heaviest form of "interactive".
  const gctx = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, ...rest) {
    try {
      P.canvases.push({ type: String(type), w: this.width, h: this.height });
      if (/webgl/i.test(String(type))) P.glContexts++;
    } catch (e) {}
    return gctx.call(this, type, ...rest);
  };
})();
"""

# ─────────────────────────────────────────────────────────────────────────────
# Runs after settle. Static + computed-style census.
# ─────────────────────────────────────────────────────────────────────────────
CENSUS = r"""
() => {
  const out = {};
  const all = Array.from(document.querySelectorAll('*'));

  out.domNodes = all.length;
  out.domDepth = (() => {
    let max = 0;
    for (const el of all) {
      let d = 0, p = el;
      while (p) { d++; p = p.parentElement; }
      if (d > max) max = d;
    }
    return max;
  })();

  // @keyframes defined (from stylesheets, incl. cross-origin-safe try)
  let keyframes = 0, sheetRules = 0, infiniteRules = [], transitions = 0;
  for (const sheet of Array.from(document.styleSheets)) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    const walk = (rs) => {
      for (const r of Array.from(rs)) {
        sheetRules++;
        if (r.type === CSSRule.KEYFRAMES_RULE) keyframes++;
        if (r.type === CSSRule.STYLE_RULE) {
          const s = r.style;
          if (s.transitionDuration && s.transitionDuration !== '0s') transitions++;
          if (s.animationName && s.animationName !== 'none') {
            const it = s.animationIterationCount;
            if (it === 'infinite' || (parseFloat(it) || 0) > 1) {
              infiniteRules.push({ name: s.animationName, dur: s.animationDuration, iter: it });
            }
          }
        } else if (r.cssRules) walk(r.cssRules);
      }
    };
    walk(rules);
  }
  out.keyframeBlocks = keyframes;
  out.cssRules = sheetRules;
  out.infiniteCssRules = infiniteRules.slice(0, 25);
  out.transitionRules = transitions;

  // Computed: how many elements are ACTUALLY animating / transformed right now
  let animating = 0, transformed = 0, willChange = 0, sticky = 0,
      backdrop = 0, blend = 0, gradients = 0, hidden = 0;
  const animNames = new Set();
  for (const el of all) {
    let s; try { s = getComputedStyle(el); } catch (e) { continue; }
    if (!s) continue;
    if (s.animationName && s.animationName !== 'none') { animating++; animNames.add(s.animationName); }
    if (s.transform && s.transform !== 'none') transformed++;
    if (s.willChange && s.willChange !== 'auto') willChange++;
    if (s.position === 'sticky' || s.position === 'fixed') sticky++;
    if (s.backdropFilter && s.backdropFilter !== 'none') backdrop++;
    if (s.mixBlendMode && s.mixBlendMode !== 'normal') blend++;
    if (/gradient\(/.test(s.backgroundImage || '')) gradients++;
    if (s.opacity === '0' || s.visibility === 'hidden') hidden++;
  }
  out.elementsAnimating = animating;
  out.animationNames = Array.from(animNames).slice(0, 25);
  out.elementsTransformed = transformed;
  out.elementsWillChange = willChange;
  out.elementsStickyOrFixed = sticky;
  out.elementsBackdropFilter = backdrop;
  out.elementsBlendMode = blend;
  out.elementsGradient = gradients;
  out.elementsHidden = hidden;

  // Media & 3D
  out.videos = document.querySelectorAll('video').length;
  out.canvasEls = document.querySelectorAll('canvas').length;
  out.svgs = document.querySelectorAll('svg').length;
  out.smil = document.querySelectorAll('animate,animateMotion,animateTransform').length;
  out.lottie = document.querySelectorAll('.lottie,[class*=lottie]').length;
  out.webgl = window.__probe.glContexts;
  out.canvasTypes = window.__probe.canvases.slice(0, 10);

  // Interactive affordances — "interactive" in the UX sense
  out.buttons = document.querySelectorAll('button').length;
  out.links = document.querySelectorAll('a[href]').length;
  out.inputs = document.querySelectorAll('input,select,textarea').length;
  out.ariaExpanded = document.querySelectorAll('[aria-expanded]').length;
  out.ariaControls = document.querySelectorAll('[aria-controls]').length;
  out.tabIndexEls = document.querySelectorAll('[tabindex]').length;
  out.dialogs = document.querySelectorAll('dialog,[role=dialog],[role=tabpanel]').length;

  // Runtime counters injected at init
  out.rafCalls = window.__probe.raf;
  out.listeners = Object.fromEntries(
    Object.entries(window.__probe.listeners).sort((a, b) => b[1] - a[1]).slice(0, 14));
  out.listenerTotal = window.__probe.listenerTotal;
  out.intersectionObservers = window.__probe.io;
  out.resizeObservers = window.__probe.ro;
  out.mutationObservers = window.__probe.mo;

  // Does it honour reduced motion? Test by toggling and re-reading.
  out.hasReducedMotionQuery = (() => {
    for (const sheet of Array.from(document.styleSheets)) {
      let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
      for (const r of Array.from(rules)) {
        if (r.type === CSSRule.MEDIA_RULE && /prefers-reduced-motion/.test(r.conditionText || r.media.mediaText || '')) return true;
      }
    }
    return false;
  })();

  out.docHeight = document.documentElement.scrollHeight;
  out.viewportH = window.innerHeight;
  out.screensOfScroll = +(document.documentElement.scrollHeight / Math.max(1, window.innerHeight)).toFixed(1);
  out.title = document.title;
  out.headings = Array.from(document.querySelectorAll('h1,h2')).length;
  return out;
}
"""


def slug(url: str) -> str:
    s = url.replace("https://", "").replace("http://", "").strip("/")
    s = "".join(c if c.isalnum() or c in ".-_" else "_" for c in s)
    return s or "root"


def chrome_executable() -> str | None:
    for c in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ):
        if os.path.exists(c):
            return c
    return None


def measure(page, url: str) -> dict:
    from playwright.sync_api import Error as PWError

    res = {"url": url, "slug": slug(url)}
    t0 = time.time()

    transfer = {"bytes": 0, "requests": 0}
    def on_resp(r):
        try:
            cl = r.headers.get("content-length")
            if cl and cl.isdigit():
                transfer["bytes"] += int(cl)
            transfer["requests"] += 1
        except Exception:
            pass
    page.on("response", on_resp)

    try:
        # "load" never fires on Vite dev servers (persistent HMR socket keeps a
        # connection open), so wait only for DOM ready, then a bounded network
        # idle, then a fixed settle so the dev bundle / WebGL scene can init.
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except PWError as e:
        res["error"] = f"goto: {e}"
        return res

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    # let fonts, lazy scenes and entry animations settle
    page.wait_for_timeout(5000)

    res.update(page.evaluate(CENSUS))

    # ── sample rAF while IDLE: a permanent loop shows up here ──────────────
    def raf_rate(ms=1600):
        a = page.evaluate("() => window.__probe.raf")
        page.wait_for_timeout(ms)
        b = page.evaluate("() => window.__probe.raf")
        return round((b - a) / (ms / 1000.0), 1)

    res["rafPerSec_idle"] = raf_rate()

    # ── sample rAF while SCROLLING: reveals scroll-driven engines (GSAP/Lenis) ──
    h = res.get("docHeight", 0)
    vh = res.get("viewportH", 900)
    a = page.evaluate("() => window.__probe.raf")
    steps = 8
    for i in range(steps):
        y = int((h - vh) * (i + 1) / steps) if h > vh else 0
        page.evaluate(f"() => window.scrollTo(0, {y})")
        page.wait_for_timeout(200)
    b = page.evaluate("() => window.__probe.raf")
    res["rafPerSec_scroll"] = round((b - a) / (steps * 0.2), 1)

    page.evaluate("() => window.scrollTo(0,0)")
    page.wait_for_timeout(1200)

    # ── hover sweep: reveals pointer-driven interaction ─────────────────────
    try:
        els = page.query_selector_all("button, a[href], [role=tab], [aria-expanded]")
        before = page.evaluate("() => window.__probe.raf")
        for el in els[:12]:
            try:
                el.hover(timeout=900)
                page.wait_for_timeout(110)
            except Exception:
                pass
        after = page.evaluate("() => window.__probe.raf")
        res["rafPerSec_hover"] = round((after - before) / max(0.1, (min(12, len(els)) * 0.11) + 0.1), 1)
        res["hoverTargetsProbed"] = min(12, len(els))
    except Exception as e:
        res["rafPerSec_hover"] = None
        res["hoverError"] = str(e)[:120]

    res["transferKB"] = round(transfer["bytes"] / 1024)
    res["requests"] = transfer["requests"]
    res["measureSeconds"] = round(time.time() - t0, 1)

    try:
        shot = OUT / f"{res['slug']}.png"
        page.screenshot(path=str(shot), full_page=False)
        res["screenshot"] = str(shot)
    except Exception as e:
        res["screenshotError"] = str(e)[:120]

    return res


def build_report(results: list[dict]) -> str:
    L = []
    L.append("# Interactivity & animation — measured at runtime")
    L.append("")
    L.append(f"**Captured:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    L.append("**Method:** instrumented `requestAnimationFrame`, `addEventListener`, "
             "`IntersectionObserver` and `canvas.getContext` **before page scripts ran**, "
             "then sampled rAF throughput while idle, while scrolling, and while "
             "hovering. Static CSS greps cannot answer \"is it animated\" — this can.")
    L.append("")

    keys = [
        ("domNodes", "DOM nodes"),
        ("docHeight", "Page height (px)"),
        ("screensOfScroll", "Screens of scroll"),
        ("transferKB", "Transfer (KB)"),
        ("requests", "Requests"),
        ("buttons", "Buttons"),
        ("links", "Links"),
        ("inputs", "Form inputs"),
        ("ariaExpanded", "[aria-expanded] (disclosure)"),
        ("dialogs", "Dialogs / tabpanels"),
        ("canvasEls", "<canvas> elements"),
        ("webgl", "WebGL contexts"),
        ("videos", "<video> elements"),
        ("smil", "SVG SMIL animations"),
        ("keyframeBlocks", "@keyframes blocks"),
        ("infiniteCssRules", "Infinite CSS rules"),
        ("elementsAnimating", "Elements animating (computed)"),
        ("transitionRules", "Transition rules"),
        ("elementsTransformed", "Elements transformed"),
        ("elementsWillChange", "will-change elements"),
        ("elementsStickyOrFixed", "sticky/fixed elements"),
        ("elementsGradient", "Gradient elements"),
        ("elementsBackdropFilter", "backdrop-filter elements"),
        ("listenerTotal", "Event listeners registered"),
        ("intersectionObservers", "IntersectionObservers"),
        ("rafPerSec_idle", "rAF calls/sec while IDLE"),
        ("rafPerSec_scroll", "rAF calls/sec while SCROLLING"),
        ("rafPerSec_hover", "rAF calls/sec while HOVERING"),
    ]

    ok_rows = [r for r in results if "error" not in r]
    names = [r["url"] for r in ok_rows]

    L.append("## Side by side")
    L.append("")
    L.append("| Metric | " + " | ".join(names) + " |")
    L.append("|---|" + "---:|" * len(ok_rows))
    for k, label in keys:
        vals = []
        for r in ok_rows:
            v = r.get(k)
            if isinstance(v, list):
                v = len(v)
            vals.append("—" if v is None else f"{v:,}" if isinstance(v, int) else str(v))
        L.append(f"| {label} | " + " | ".join(vals) + " |")
    L.append("")

    err_rows = [r for r in results if "error" in r]
    if err_rows:
        L.append("## Not measured (errors)")
        L.append("")
        for r in err_rows:
            L.append(f"- **{r['url']}** — {r['error']}")
        L.append("")

    for r in results:
        if r.get("error"):
            L.append(f"## {r['url']}")
            L.append("")
            L.append(f"**Not measured:** {r['error']}")
            L.append("")
            continue
        L.append(f"## {r['url']}")
        L.append("")
        L.append(f"*Title:* {r.get('title','')}  ")
        L.append(f"*h1+h2 count:* {r.get('headings')} · *DOM depth:* {r.get('domDepth')}  ")
        L.append(f"*Screenshot:* `{r.get('screenshot','n/a')}`")
        L.append("")
        if r.get("listeners"):
            L.append("**Top event listeners:** " + ", ".join(
                f"`{k}`×{v}" for k, v in list(r["listeners"].items())[:10]))
            L.append("")
        if r.get("animationNames"):
            L.append("**Animation names:** " + ", ".join(f"`{n}`" for n in r["animationNames"][:12]))
            L.append("")
        if r.get("canvasTypes"):
            L.append("**Canvas contexts:** " + ", ".join(
                f"`{c.get('type')}` {c.get('w')}×{c.get('h')}" for c in r["canvasTypes"]))
            L.append("")
        L.append(f"**Honours `prefers-reduced-motion`:** "
                 f"{'yes' if r.get('hasReducedMotionQuery') else 'NO'}")
        L.append("")

    L.append("## How to read this")
    L.append("")
    L.append("- **rAF/sec while IDLE** is the headline number. ~0 means the page is "
             "static until you touch it. 30–60 means a permanent animation loop "
             "(a WebGL scene, a marquee, a breathing glow) burning a frame budget "
             "every second the tab is open.")
    L.append("- **rAF/sec while SCROLLING** versus idle tells you whether a scroll "
             "engine (GSAP ScrollTrigger, Lenis, Locomotive) is driving the page.")
    L.append("- **WebGL contexts > 0** means real 3D — the heaviest and most "
             "expensive kind of \"interactive\", and the hardest to make accessible.")
    L.append("- High **DOM nodes** + high **transfer** is the cost column; high "
             "**buttons / [aria-expanded] / inputs** is the actual-interactivity column.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    urls = sys.argv[1:] or DEFAULT_URLS
    OUT.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright missing — run with /usr/bin/python3 (3.9)", file=sys.stderr)
        return 2

    exe = chrome_executable()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=exe, args=["--no-proxy-server"])
        for url in urls:
            print(f"[..] {url}", flush=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            ctx.add_init_script(INIT)
            page = ctx.new_page()
            page.set_default_timeout(90000)
            r = measure(page, url)
            results.append(r)
            (OUT / f"{r['slug']}.json").write_text(json.dumps(r, indent=2))
            if "error" in r:
                print(f"    ERROR {r['error']}", file=sys.stderr)
            else:
                print(f"    idle rAF/s={r.get('rafPerSec_idle')} "
                      f"scroll rAF/s={r.get('rafPerSec_scroll')} "
                      f"webgl={r.get('webgl')} dom={r.get('domNodes')} "
                      f"kb={r.get('transferKB')}", flush=True)
            ctx.close()
        browser.close()

    rep = build_report(results)
    (OUT / "REPORT.md").write_text(rep)
    print(f"\nwrote {OUT/'REPORT.md'}")
    print()
    print(rep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
