# motto_v2.md Guard Decision (2026-05-18)

## Problem

During this session, parallel agents deleted Section 20 of `motto_v2.md`
("Commit Attribution Rule — No Agent Co-Author Trailers") from the working tree
at least three times. Each time the deletion was unstaged and never committed —
agents were editing the motto file, removing the no-trailer rule, and then
committing unrelated files. The rule was silently absent from the working tree
during those commits.

A local `.git/hooks/commit-msg` hook was installed earlier in the session to
block AI co-author trailers in commit messages. That hook works correctly, but
it does not protect against the working-tree corruption of `motto_v2.md` itself.
The hook is also local-only and not tracked — it would not survive a fresh clone
or new worktree.

## What was insufficient

`commit-msg` alone is insufficient because:

1. It runs after the commit message is written, not before files are staged.
2. It blocks trailers in the message but cannot detect that the rule source file
   (`motto_v2.md`) has been corrupted in the working tree.
3. It is `.git/hooks/commit-msg` — untracked, lost on fresh clone or worktree.

## Decision

Add two tracked hooks in `scripts/hooks/` and an install script:

### `scripts/hooks/commit-msg`

Identical behavior to the previous local-only hook. Rejects any commit message
containing an AI agent `Co-Authored-By:` trailer matching:
`claude|anthropic|chatgpt|codex|openai|copilot|qwen|gemini` (case-insensitive).
Human co-author trailers not matching those names are allowed.

### `scripts/hooks/pre-commit`

New. Checks the **working tree** `motto_v2.md` before every commit, regardless
of what files are staged. Rejects the commit if either of these strings is
absent from the file:

- `## 20. Commit Attribution Rule — No Agent Co-Author Trailers`
- `Do not add AI-agent co-author trailers to commits.`

Why the working tree and not only the staged version: the failure mode is agents
editing `motto_v2.md` (deleting Section 20) and then committing other files
without staging the motto edit. Checking the staged version would miss this
entirely. Checking the working tree catches it: any commit attempt while Section
20 is absent is rejected, no matter what files are staged.

The hook prints the exact restore command:
```
git restore -- motto_v2.md
```

### `scripts/install-git-hooks.sh`

Sets `core.hooksPath scripts/hooks` in the local `.git/config` and chmod +x
both hooks. Must be run once per clone or worktree. It is NOT run automatically
during this commit — it requires an explicit local action.

## Install

```bash
bash scripts/install-git-hooks.sh
```

Verify:
```bash
git config --get core.hooksPath
# → scripts/hooks
```

## Verification commands

```bash
# Trailer guard should fail (exit 1):
printf "test\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>\n" \
  | scripts/hooks/commit-msg /dev/stdin

# Human co-author should pass (exit 0):
printf "test\n\nCo-Authored-By: Jane Doe <jane@example.com>\n" \
  | scripts/hooks/commit-msg /dev/stdin

# Normal commit should pass (exit 0):
printf "fix: normal commit\n" | scripts/hooks/commit-msg /dev/stdin

# Motto guard should pass with intact motto_v2.md (exit 0):
scripts/hooks/pre-commit

# After install, both guards run automatically on every git commit.
```

## Migration note

Once `bash scripts/install-git-hooks.sh` is run, `git config core.hooksPath`
is set to `scripts/hooks`. Git then ignores `.git/hooks/` entirely. The previous
local `.git/hooks/commit-msg` becomes inert — it is superseded by the tracked
`scripts/hooks/commit-msg` with identical behavior.

## What this does not cover

- Commits pushed from other repos or forks that do not run `install-git-hooks.sh`
- Agents that bypass `--no-verify` (which would skip all hooks)
- History rewrite of existing trailer violations on remote (requires explicit approval)
