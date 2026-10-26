---
name: gauntlet-loop
description: Adversarial Builder -> Fresh-Context Blind Critic -> Surgical Fix -> Re-Capture verification loop. Eliminates self-grading bias on UI/UX, image-to-code, computer-vision segmentation, and complex engineering tasks by looping with a read-only Blind Critic subagent until every frame and rubric dimension scores >= 9.5/10 with zero P0/P1 defects.
---

# The Gauntlet Loop Skill (`gauntlet-loop`)

Canonical Workspace Skill: `/Users/pranay/Projects/skills/gauntlet-loop/SKILL.md`  
Canonical Doctrine: `/Users/pranay/Projects/GAUNTLET_LOOP_DOCTRINE.md` (`Docs/GAUNTLET_LOOP_DOCTRINE.md`)

## Protocol Summary
1. **Iteration 0 (Honest Self-Audit)**: Read all ground-truth reference images and live screenshots side-by-side. Score honestly (`1.0–10.0`) across the 6 Gauntlet Rubric Dimensions and list every discrepancy.
2. **Surgical Fix & Deterministic Capture**: Fix all identified issues, run unit tests + `tsc --noEmit`, and run `node tools/departure-board-pipeline/capture_after_states.mjs` to capture fresh live screenshots.
3. **Fresh-Context Blind Critic Subagent**: Invoke `research` subagent (`Role: "Gauntlet Blind Critic Auditor"`) with fresh context to compare the ground-truth references against the live screenshots without builder excuses.
4. **Loop Until Pass**: Fix every `P0`/`P1`/`P2` finding returned by the Blind Critic, re-capture screenshots, and re-audit until all frames and dimensions score `>= 9.5 / 10.0` with zero `P0`/`P1` defects.
