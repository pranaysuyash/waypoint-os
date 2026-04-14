# process issue review

## Issue ID
PIR-2026-04-14-001

## Title
Repo-specific workflow instructions not persisted as an on-disk `AGENTS.md`

## Severity
Medium (process reliability risk)

## Observation
- Repo-specific instructions were provided in conversation.
- No file exists at `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`.
- Agents/tools that rely on on-disk discovery may miss these rules in future sessions.

## Impact
- Inconsistent workflow compliance across sessions.
- Higher chance of drift on commit/push behavior, documentation protocol, and review naming rules.

## Recommended Fix
- Create `/Users/pranay/Projects/travel_agency_agent/AGENTS.md` and store the provided rules verbatim.
- Add an index reference in `/Users/pranay/Projects/travel_agency_agent/Docs/INDEX.md`.
- Optionally add pre-task check script under `/Users/pranay/Projects/travel_agency_agent/tools/` that verifies instruction file presence.

## Status
Open

## Date Validation
- Environment date/time validated: `2026-04-14 18:09:44 IST +0530`.
