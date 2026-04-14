# Workflow Location and Usage (2026-04-14 IST)

## Direct Answer
Yes, your workflow is now identified and being followed.

## Where It Is
1. Workspace-level agent workflow:
- `/Users/pranay/Projects/AGENTS.md`

2. Session bootstrap context (workspace memory flow):
- `/Users/pranay/Projects/travel_agency_agent/.agent/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/.agent/SESSION_CONTEXT.md`
- `/Users/pranay/Projects/travel_agency_agent/.agent/STEP1_ENV.sh`

3. Repo-specific instructions for this repo:
- Provided in-session as: **"AGENTS.md instructions for /Users/pranay/Projects/travel_agency_agent"**
- Important note: no physical file currently exists at:
  - `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`

## Workflow I’m Applying in This Thread
- Preserve history; do not delete existing documentation.
- Document completed and pending actions in project docs.
- Validate implementation changes before proceeding.
- Run test suite after updates.
- Do not commit/push without explicit user approval.
- Use date from environment before doc updates.

## Recommended Hardening
Create an actual repo-local `AGENTS.md` file so repo-specific workflow rules are loadable from disk by any future agent/tooling without relying on chat-only context.

## Date Validation
- Environment date/time validated: `2026-04-14 18:09:44 IST +0530`.
