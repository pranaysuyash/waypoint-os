# Travel Agency Landing Page Review

**Date:** 2026-04-29  
**Scope:** Landing-page / GTM wedge review for `frontend/src/app/page.tsx`, `frontend/src/components/marketing/marketing.tsx`, and `frontend/src/app/itinerary-checker/page.tsx`  
**Skills applied:** `page-cro`, `plan-design-review`

## Source Notes

- Reviewed the B2B homepage design and the itinerary checker acquisition page as landing surfaces, not app UI.
- Used the repo’s public landing docs and the live design renders in `frontend/public/landing/`.
- Landing-page rules from `plan-design-review` were used for hierarchy, CTA priority, and message-match checks.

## Overall Read

The public landing surfaces are directionally strong. The homepage has a clear brand position, a strong first-screen composition, and a coherent dark product aesthetic. The itinerary checker is also visually polished and functions as a credible GTM wedge.

The main issues are not visual polish. They are conversion integrity issues:

1. one CTA is mislabeled relative to where it sends the user
2. the waitlist email box reads like a conversion form but currently does not capture anything real
3. the itinerary checker uses trust proof that appears ungrounded unless those numbers and testimonials are already validated elsewhere

## Findings

### 1) [High] `See pricing` does not lead to pricing

**Evidence**
- `frontend/src/app/page.tsx:438-446`
- The bottom CTA band is mounted under `#pricing`, but its secondary CTA is labeled `See pricing` while the link target is `/itinerary-checker`.

**Why this matters**
- This breaks message match.
- A visitor clicking `See pricing` expects pricing, not a separate wedge page.
- On a landing page, this kind of mismatch reduces trust faster than a weak visual hierarchy does.

**Recommendation**
- Either:
  - route that secondary CTA to a real pricing destination, or
  - relabel it to match the destination, for example `Try the itinerary checker`
- If pricing is intentionally not public, remove pricing language from the CTA and nav rather than implying a section that does not exist.

### 2) [Medium] The waitlist email box is a dead-end conversion affordance

**Evidence**
- `frontend/src/components/marketing/marketing.tsx:98-160`
- `CtaBand` shows a waitlist email field, but submission only toggles local component state. There is no actual lead capture, no backend handoff, and no persisted result.

**Why this matters**
- A landing page should either convert or clearly defer.
- An email field that looks actionable but only produces local UI feedback is a false affordance.
- Visitors who enter a real email will reasonably expect it to go somewhere.

**Recommendation**
- Wire this to the actual lead capture path, or remove the field until that path exists.
- If the goal is only demo conversion, keep the band focused on one clean CTA and drop the faux waitlist.

### 3) [Medium] The itinerary checker social proof appears unverified

**Evidence**
- `frontend/src/app/itinerary-checker/page.tsx:274-279`
- `frontend/src/app/itinerary-checker/page.tsx:345-353`
- `frontend/src/app/itinerary-checker/page.tsx:412-415`

**Why this matters**
- The page asserts `20,000+ itineraries analyzed`, `98% recommend to friends`, and `4.8/5 traveler rating`.
- It also shows testimonial-style quotes and brand names.
- If those numbers or quotes are not backed by real evidence, the page reads as promotional filler rather than trustworthy utility.

**Recommendation**
- If the proof is real, source it visibly or attach provenance elsewhere in the flow.
- If it is not real, replace it with lower-risk proof: honest product claims, example output, or a clearly labeled sample audit.

## What Is Working

- The homepage first screen has a strong composition and a believable product artifact.
- The itinerary checker hero has a clean, focused conversion path.
- The dark visual system is cohesive and does not fall into a generic SaaS template.
- The wedge page is productized rather than looking like a generic lead form.

## Not in Scope

- Full brand strategy changes
- Copywriting rewrite of the entire site
- Backend implementation of the lead flow
- Mobile QA beyond what is visible from the current source and render set

## Suggested Next Step

Fix the CTA destination mismatch first, then decide whether the waitlist form should become a real lead capture flow or be removed. After that, validate whether the itinerary checker proof set is factual enough to keep as-is.
