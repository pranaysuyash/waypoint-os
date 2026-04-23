# Feature: Omnichannel Message Stitching

## POV: System Core / Agency Operator

### 1. Objective
To create a single, unified "Context Thread" for every customer, ensuring that communication across WhatsApp, Email, Voice, and SMS is stitched into one cohesive timeline.

### 2. Functional Requirements

#### A. Multi-Channel Ingestion
- **WhatsApp/Signal/Telegram Hook**: Real-time intake of messages with media support (photos of passports, voice notes).
- **Email-to-Thread**: Automatically mapping incoming emails (even from personal addresses) to the traveler's "Genome" using NLP and sender patterns.
- **Voice Transcription**: Converting call recordings into searchable text segments in the timeline.

#### B. The "Unified Inbox" (Agent Side)
- **Thread Continuity**: An agent replies via a web dashboard, but the customer receives it on WhatsApp. The system handles the "Handshake" between protocols.
- **Channel Suggestion**: The system recommends the best channel for a specific message (e.g., "Use SMS for this gate change; user is offline on WhatsApp").

#### C. Context Preservation
- **"Brackets" Integration**: When an agent sends a set of options (The "Bracket"), the status of that bracket (Sent, Seen, Accepted) is tracked across all channels.
- **Agent Handoff Summaries**: If Agent A finishes their shift, Agent B gets an AI-generated "Context Summary" of the last 48 hours of chat.

### 3. Core Engine Logic
- **Traveler ID Mapping**: Using a combination of Phone Number, Email, and PNR to ensure the right message goes to the right "Genome."
- **NLP Intent Extraction**: Identifying when a traveler says "Check this" (attaching a photo) vs. "Cancel this" (requesting a change).

### 4. Privacy & Compliance
- **Data Scrubbing**: Automatically hiding credit card numbers or PII from the common chat view.
- **Audit Trail**: Every outgoing message is timestamped and logged for "Service Guarantee" verification.
