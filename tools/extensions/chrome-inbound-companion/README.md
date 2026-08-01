# Waypoint OS - Chrome Ingestion Companion

Native multi-channel ingestion Chrome Extension for Waypoint OS.

## Overview
This Chrome Extension solves the Month 6 friction audit finding by allowing travel agents to capture unformatted client inquiries from:
- **WhatsApp Web**
- **Gmail / Email**
- **Web Portals / PDFs**

with a single click or text selection, transmitting them directly into `POST /api/v1/inbound/parse` and triggering real-time optimistic state reconciliation.

## Features
1. **Selection Capture**: Highlight text on any website or WhatsApp message → click floating `✈ Sync to Waypoint` button or right-click context menu.
2. **Auto-Channel Detection**: Detects WhatsApp Web vs Gmail automatically based on active tab domain.
3. **Instant Parsing & Re-evaluation**: Runs `run_spine_once` server-side, returning `decision_state`, `missing_fields`, and an agent-ready draft follow-up prompt.
4. **Zero-friction UI**: Fits seamlessly into high-velocity travel agency agent workflows.

## Installation Instructions (Developer Mode)
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** toggle in the top-right corner.
3. Click **Load unpacked**.
4. Select the directory: `tools/extensions/chrome-inbound-companion/`.
5. Ensure Waypoint OS backend is running (`uv run uvicorn spine_api.server:app --port 8000`).
