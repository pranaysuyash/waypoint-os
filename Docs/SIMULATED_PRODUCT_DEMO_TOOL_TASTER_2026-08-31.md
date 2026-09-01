# Simulated Product Demo — "The Tool-Taster" Persona (Computer-Use Driven)

*Date: 2026-08-31*
*Method: Live UI walkthrough driven through macOS computer-use (Chrome, isolated scratch profile `/tmp/waypoint-demo-profile`) against local backend (`:8000`) + frontend (`:3005`).*
*Status: Complete — verdict recorded. Findings pending Pranay's ratification before register integration.*

---

## 1. Persona (new, created for this simulation)

**"Dev Sharma", 29 — The Tool-Taster** (most-basic segment; extends `Docs/PRODUCT_STRATEGY_PERSONAS_MARKET_2026.md` personas A/B/C)

- Frontend developer by day; hobbyist who signs up for new SaaS tools for fun
- **Not** a travel advisor — zero domain context, judges as a product connoisseur
- Evaluation criteria:
  1. Frictionless signup (≤2 min to be "in")
  2. A visible "wow moment" within ~5 minutes
  3. Polish good enough to tell friends about
- Decision options: **Buy / Postpone / Pass**

**Demo scenario:** Dev hears about Waypoint OS ("AI that turns messy trip notes into quote-ready briefs"), signs up on a whim, pastes a deliberately messy real-world-style travel note, and judges whether the "autonomous engine" is real or vaporware.

**Test input (messy on purpose — slang phrasing, vague dates, ambiguous budget):**

> hey! me and 3 friends want to do japan next spring, maybe late march for the cherry blossoms. flying from SF. we are all pretty active, one friend is vegetarian. budget around 3.5k USD each, not sure if that includes flights. thinking tokyo + kyoto + osaka, 10-12 days. one of us is terrified of heights so no cable cars please. we saw this amazing ryokan on tiktok, no idea of the name. dates flexible plus or minus a week. we also wanna do a cooking class somewhere. thx!!

---

## 2. Flow Log (what actually happened, step by step)

| # | Step | Result | Notes |
|---|------|--------|-------|
| 1 | Landing page (`/`) | ✅ Good | Clear hero ("Turn raw trip notes into quote-ready briefs"), obvious CTAs. Dev: "polished, I know what this does." |
| 2 | Click **Create workspace** | ✅ Smooth | One-page signup: name, email, password, confirm. Live strength meter ("Weak"→"Strong"), "Passwords match" indicator. No email verification loop. |
| 3 | Submit signup | ✅ Excellent | Straight into `/overview`, logged in, in under a minute. Onboarding checklist (Invite team → Add first inquiry → Review Lead Inbox) visible immediately. |
| 4 | Land on Overview | ⚠️ Confusing | "Captured Details" panel shows a fully populated stranger: **"Alex Morgan — Repeat Client (3 Bookings) — Delta Diamond Medallion"** incl. SkyMiles number — above text saying "details will appear here after processing." On a brand-new account. Trust-killer for a privacy-minded user. |
| 5 | Click **Process New Inquiry** → Workbench intake | ✅ Good | Clean two-box design (Customer Message vs Agent Notes), helper chip ("Need the purpose fast?"), example placeholder, explainer strip ("After processing: incomplete leads appear in Lead Inbox…"), Process button properly disabled until input. |
| 6 | Paste messy note | ✅ (after friction, see §4) | Autosave ("Saving…") fired; Process Inquiry enabled reactively. |
| 7 | Click **Process Inquiry** | ✅ Works | Draft created (`draft_22c74baae1d8`), title becomes the note snippet, status "Processing…" with spinner. Feels like a real pipeline. |
| 8 | Pipeline result (~10–15 s) | ⚠️ Honest but deflating | Banner: **"Trip Details Need Your Input — Trip details are incomplete."** Draft status: **Blocked**. Run trace shown (`packet, validation, decision, strategy, blocked_result`). No human-readable "what's missing" on this surface — you must click through. |
| 9 | Open **Trip Details** repair surface | 🎯 Key finding | Extracted packet shows: **Destination: `-` (Japan NEVER captured despite saying "japan" + 3 cities)**, **Party: 1 (note says "me and 3 friends" = 4)**, Origin: SF ✓, Budget ✓ ("budget around 3.5k usd", min 3500 @90%), Dates/Purpose missing. Blocked on exactly: **"Missing fields: Travel Dates, Trip Purpose."** Per-field Confidence + Authority (`explicit_user`) shown — excellent transparency. |
| 10 | Try repair flow | ❌ Friction | "Review Missing Fields" button did not visibly scroll/focus the edit form; the editable fields were not reachable in the demo session (time-boxed). Recovery path exists but discoverability is weak. |
| 11 | Check **Lead Inbox** | ❌ Broken promise | First load: **tab crashed ("Aw, Snap! Error code: 5", renderer crash)**. Reload → page renders. But: **"No new leads — 0 leads total"** despite a blocked draft existing. The app's own banner promised "incomplete leads appear in Lead Inbox." The lead never appeared. |
| 12 | Check **Pricing** (`/pricing`) | ✅ Honest | Three tiers: Traveler Checker (Free) / Workspace Access (self-serve, Recommended) / Guided Rollout. **No dollar amounts anywhere** — FAQ candidly admits numbers aren't public ("No fake demo gate. No hidden pricing funnel."). "WHAT'S LIVE RIGHT NOW" panel honestly scopes current capability. |

---

## 3. What Went Well (Dev's "this is actually good" moments)

1. **Signup → workspace in <60 s, zero friction.** No email loop, no wizard. Best-in-class for a B2B tool demo.
2. **Visual design quality is high.** Dark ops-console aesthetic is coherent across landing, auth, overview, and workbench. Dev would screenshot the workbench.
3. **The intake surface design is genuinely thoughtful** — separate Customer Message vs internal Agent Notes, purpose helper chip, expectation-setting explainer strip, disabled-until-valid Process button.
4. **Pipeline feels real**: draft IDs, live status ("Processing…"), run trace (`de9c10ef: packet, validation, decision, strategy, blocked_result`), autosave.
5. **Failure UX is honest and traceable.** The blocked state names exactly which fields are missing, and the packet table shows per-field confidence + authority. Most "AI tools" hide this; Waypoint shows its work. This is a differentiator worth protecting.
6. **Pricing page honesty** — no fake gates, explicit "what's live right now," realistic tier framing.

## 4. What Went Bad (ranked by demo impact)

| Rank | Finding | Evidence | Severity (product view) |
|------|---------|----------|------------------------|
| 1 | **Lead Inbox promise broken**: blocked lead never appears; inbox shows 0 leads while a Blocked draft exists | Banner copy on workbench vs `/inbox` ("No new leads", "0 leads total") after processing | **P0 — core loop dead-ends.** First-run user loses their lead. Either the draft→lead promotion is missing or the copy is wrong; both are broken promises. |
| 2 | **Extraction misses the headline entity**: "japan" + "tokyo + kyoto + osaka" never captured; Destination `-`, "Destination Status: open" | Trip Details packet table | **P1 — the wow moment inverts.** The one thing the note screams is the one thing missing. Slangy verb-object phrasing ("do japan") likely defeats pattern extractors. Also suggests the golden-set F1 (0.9524) doesn't cover real-world phrasings — eval/real-world gap. |
| 3 | **Party size wrong**: "me and 3 friends" → Party 1 | Trip Details "PARTY 1" | **P1 — silently wrong data is worse than missing data** (a quote built on Party 1 is commercially wrong; missing fields at least get caught). |
| 4 | **Stranger's profile (Alex Morgan + loyalty numbers) rendered on a fresh tenant's workspace** | Overview + Workbench "Captured Details" panel pre-processing | **P1 — trust/isolation optics.** If it's a demo/seed artifact, it must not render on brand-new accounts; reads as cross-tenant data leak to any privacy-aware user. |
| 5 | **Renderer crash on first `/inbox` load** ("Aw, Snap!", code 5); recovered on reload | Demo session | **P1 if reproducible** (OOM in dev build?); could be dev-environment noise — needs a clean repro before escalating. |
| 6 | **Repair-surface discoverability**: "Review Missing Fields" didn't visibly navigate/scroll to an editable form; fields unreachable in-session | Step 10 | **P2 — recovery path exists but the user can't complete the loop.** |
| 7 | **Minor:** "WORK EMAIL / you@agency.com" framing mildly excludes non-agency tinkerers; sidebar workspace label drifted ("Waypoint HQ" → "Agency Workspace") between sessions | Signup + sidebar | **P3 polish.** |

**Environment caveats (honesty):** the synthetic-input harness had flakiness (window Space-drift, dropped letter keystrokes while typing — repro'd once even with the window active; AX tree timeouts on heavy pages). The typing anomaly was checked against `IntakeTab.tsx` — **no app-side key handlers/sanitizers exist**, so it is harness-suspect, not a confirmed app bug. Findings 1–4 are based on rendered UI state (screenshots + AX tree), independent of input mechanics. Finding 5 needs manual repro.

## 5. Verdict (the persona's decision)

**Demo outcome: CONDITIONAL FAIL — the shell is shippable, the loop is not.**

- **Buy: NO.** Dev isn't the ICP, and there are no prices to buy against anyway.
- **Evangelize today: PASS.** He wouldn't send his travel-agent friend a tool whose first-run loop ends in "Blocked" + an empty inbox.
- **Postpone: YES — revisit in ~2–3 months.** He leaves impressed by the transparency and design ("this team shows its work") and would return if the funnel completes. This is a *positive* postpone, the best non-buy outcome.

**One-line quote for the persona:** *"Gorgeous cockpit, honest gauges — but my flight never took off."*

## 6. Recommended Fixes (in demo-impact order)

1. **Close the lead loop**: either promote blocked drafts to Lead Inbox (matching the banner copy) or change the copy to "incomplete requests stay in your draft until completed." Then E2E-test: new tenant → process → blocked → lead visible in inbox.
2. **Extraction robustness pass for colloquial phrasings**: add eval cases for verb-object destinations ("do japan", "hit bali"), group-size phrasings ("me and N friends", "the four of us"), and relative date windows ("next spring, late march", "flexible ±1 week"). Feed findings into the D6 audit-gate eval set (F-18 baseline) rather than ad-hoc fixes.
3. **Party-size under-detection** should be a validation warning (party inferred < explicit "N people" phrasing) instead of silent 1.
4. **Gate the Alex Morgan profile** behind a real tenant-memory hit or an explicit "Sample data" badge; never render on accounts with zero bookings.
5. **Repro the `/inbox` renderer crash** outside the demo harness; if real, profile OOM (dev-mode React + heavy AX polling is a plausible amplifier).
6. **Make "Review Missing Fields" scroll-and-focus the first empty field** (anchor + highlight ring).

## 7. Follow-ups

- [ ] Pranay ratifies findings 1–6 → then add as rows to `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` (proposed IDs: F-19…F-24, source: this demo; run `scripts/check_findings_register.py` after integration)
- [ ] Manual repro attempt for finding 5 (crash) and finding 7 typing anomaly with a human keyboard
- [ ] Extract colloquial-phrasing eval fixtures from this note (candidate for `data/fixtures/` + audit eval manifest)
