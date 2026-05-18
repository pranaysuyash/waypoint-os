# Hermes Gateway UI Guide (Validated on 2026-05-17)

## What you asked
Use Hermes Gateway from a UI (including Kanban and other advanced features), document the practical setup, and add a global shortcut command.

## Ground truth checked
- `hermes --help`
- `hermes gateway --help`
- `hermes dashboard --help`
- `hermes kanban --help`
- Hermes docs in local install:
  - `~/.hermes/hermes-agent/website/docs/user-guide/features/web-dashboard.md`
  - `~/.hermes/hermes-agent/website/docs/user-guide/messaging/open-webui.md`
  - `~/.hermes/hermes-agent/website/docs/user-guide/features/api-server.md`
  - `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban.md`
  - `~/.hermes/hermes-agent/website/docs/reference/slash-commands.md`

## The UI surfaces (and what each is for)

### 1) Hermes Dashboard (native UI)
Command:
- `hermes dashboard --tui`

This gives you:
- Browser UI for config/env/sessions/logs/analytics/cron/skills
- Embedded Hermes chat (the real `hermes --tui` in browser)
- Kanban tab (board switcher, create/list/update/archive)

Best when you want full Hermes control in one local web UI.

### 2) Open WebUI (external frontend) + Hermes Gateway API server
Architecture:
- Open WebUI -> Hermes API server (`http://127.0.0.1:8642/v1`) -> Hermes agent runtime + tools

Best when you want a polished multi-user chat UI.

Important:
- Tools execute on the machine running Hermes gateway/API server.
- API-server toolset is almost full, but drops `clarify`, `send_message`, and `text_to_speech`.

### 3) Messaging UI (Telegram/Discord/Slack/etc.)
- Run gateway platforms and use slash commands directly in those apps.
- `/kanban ...` is supported in gateway chats.

## Recommended setup path (practical)

## A) Start using native Hermes UI immediately
1. Start dashboard:
   - `hermes dashboard --tui`
2. Open browser:
   - `http://127.0.0.1:9119`
3. Use:
   - Chat tab for agent interaction
   - Kanban tab for board/task operations

## B) Enable Open WebUI bridge (if you want third-party UI)
1. Enable API server:
   - `hermes config set API_SERVER_ENABLED true`
   - `hermes config set API_SERVER_KEY <strong-secret>`
2. Restart gateway:
   - `hermes gateway restart`
3. Verify:
   - `curl -s http://127.0.0.1:8642/health`
   - `curl -s -H "Authorization: Bearer <API_SERVER_KEY>" http://127.0.0.1:8642/v1/models`
4. Bootstrap Open WebUI quickly:
   - `bash ~/.hermes/hermes-agent/scripts/setup_open_webui.sh`

## Kanban from UI: what works

### In dashboard
- Kanban tab supports board switching and task operations.

### In chat UI (dashboard chat or messaging apps)
Use slash commands:
- `/kanban list`
- `/kanban create "Task title" --assignee researcher`
- `/kanban show <task_id>`
- `/kanban comment <task_id> "update"`
- `/kanban unblock <task_id>`
- `/kanban boards list`
- `/kanban boards create <slug>`
- `/kanban boards switch <slug>`

Equivalent CLI works too:
- `hermes kanban ...`

## Global shortcut command created

Installed:
- `/Users/pranay/.local/bin/hermes-ui`

It is executable and on your PATH (because `~/.local/bin` is in PATH).

### Usage
- `hermes-ui` or `hermes-ui start`
  - starts `hermes dashboard --tui`
- `hermes-ui stop`
  - stops dashboard processes
- `hermes-ui status`
  - shows dashboard + gateway status
- `hermes-ui gateway-start`
- `hermes-ui gateway-stop`
- `hermes-ui gateway-restart`
- `hermes-ui gateway-setup`
- `hermes-ui webui-setup`
  - runs `setup_open_webui.sh`
- `hermes-ui health`
  - checks API server health endpoint
- `hermes-ui help`

## Why this is the correct shortcut pattern
You asked for something like `hermes ui ...` globally.
- Hermes CLI does not currently expose `hermes ui` as a native subcommand.
- Safest non-invasive path is a global wrapper command (`hermes-ui`) instead of patching core Hermes CLI internals.
- This keeps updates safe and avoids breaking upstream behavior.

If you want true `hermes ui ...` syntax, that requires upstream CLI command extension in Hermes source.

## Quick daily workflow
1. `hermes-ui status`
2. `hermes-ui start --no-open` (or just `hermes-ui`)
3. Use dashboard Chat + Kanban tabs
4. If using Open WebUI: `hermes-ui webui-setup` once, then open Open WebUI

## Notes
- Dashboard defaults to localhost and has no independent auth layer. Do not expose with `--insecure` unless you know exactly what you are doing.
- Kanban dispatcher is embedded in gateway by default; keep gateway running for automatic task dispatch.
