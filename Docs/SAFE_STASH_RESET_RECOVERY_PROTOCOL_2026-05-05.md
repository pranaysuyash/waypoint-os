# Safe Stash / Reset Recovery Protocol

- Date: 2026-05-05
- Scope: repo-local prevention note for unsafe `git stash`, `git reset`, `git restore`, `git checkout --`, and worktree cleanup shortcuts
- Applies to: `/Users/pranay/Projects/travel_agency_agent`

## Why This Exists

A prior agent used destructive stash workflow without permission, which created false-loss panic, mixed source recovery with runtime artifact churn, and forced manual forensics through `.git` objects and opencode session history.

This repo already forbids unsafe stash/reset behavior in [AGENTS.md](/Users/pranay/Projects/travel_agency_agent/AGENTS.md). This note makes the operational workflow explicit and gives future agents a concrete repo-local tool to use before attempting recovery.

## Hard Rules

1. Do not use `git stash pop`, `git stash apply`, `git reset`, `git restore`, `git checkout --`, or `git clean` as recovery shortcuts.
2. Do not remove a worktree or delete its branch until you prove there is no unique additive work left inside it.
3. Do not treat `data/overrides/...` churn as source loss without first classifying it as runtime-generated versus canonical source.
4. Do not claim files are lost until you have checked:
   - current working tree
   - stash metadata
   - worktree metadata
   - opencode session history when relevant
5. Never replay a stash wholesale in a dirty multi-agent tree.

## Required Workflow

### 1. Capture evidence first

Run the repo-local guard tool:

```bash
cd /Users/pranay/Projects/travel_agency_agent
.venv/bin/python tools/recovery_guard_report.py
```

This reports:

- current branch / HEAD
- linked worktrees
- stash-log presence
- tracked `.claude/worktrees/...` artifact state
- working-tree summary
- the safe selective-recovery checklist

### 2. Inspect, do not replay

Allowed read-first commands:

```bash
git status --short --branch
git worktree list --porcelain
git stash list
git show <stash-or-commit>
git diff --stat <A>..<B>
git diff-tree --no-commit-id --name-status -r <commit>
git reflog --date=iso
```

Primary questions:

1. Is the suspect branch actually ahead of `master`, or already behind it?
2. Are the “missing files” source files, docs, or runtime artifacts?
3. Does the stash/branch/worktree contain unique additive code, or stale parallel paths?

### 3. Recover selectively

Per-file disposition must be one of:

- `already present`
- `recover selectively`
- `runtime/generated only`
- `stale/superseded`
- `needs human decision`

Never use a single “apply everything” operation to answer a mixed-state recovery.

### 4. Verify after recovery

At minimum:

1. run focused tests for recovered source paths in the repo venv
2. document the recovery decision
3. update context/handoff docs if the recovery changes the state agents need to know

## Worktree-Specific Rule

If `.claude/worktrees/...` or another linked worktree is involved:

1. inspect branch ancestry first
2. inspect uncommitted tracked additions/modifications only
3. ignore `.venv`, `egg-info`, and other environment noise
4. port additive work into canonical files only
5. then remove worktree and delete branch

## Runtime Artifact Rule

Files under these paths often represent runtime churn rather than source regressions:

- `data/overrides/index.json`
- `data/overrides/patterns/*.jsonl`
- `data/overrides/per_trip/*.jsonl`

Treat them as source only if there is an explicit product decision that they are canonical tracked assets. Otherwise classify them separately from source recovery.

## Repo-Local Tool

- Tool: [tools/recovery_guard_report.py](/Users/pranay/Projects/travel_agency_agent/tools/recovery_guard_report.py)
- Purpose: give future agents a safe, repeatable starting point before any stash/reset/worktree recovery action

