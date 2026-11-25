# WhatsApp inbox and supplier evidence

November 25, 2026. Ownership and progress live in the [Exploration Frontier](../EXPLORATION_FRONTIER.md#supplier-messaging-and-availability). This worklog records the implementation and verification. The [commercial replay](/Users/pranay/Projects/commercial-pipeline/docs/findings/lead-qualification/paradise-parties/local-workflow/README.md) supplied reference scenarios.

## Advisor workflow

`POST /api/v1/messaging/webhook/whatsapp` verifies the raw-body signature and configured Meta business phone number ID. The single-host SQLite journal claims the agency, inbox and provider message ID before Waypoint starts the existing enquiry pipeline. A new text enquiry becomes a new trip in the lead inbox. A sender matching one active trip is linked without rewriting the trip. Media, ambiguous contact matches, staff-owned messages and processing failures stay visible for staff review.

In **Command → Communications → WhatsApp → Open conversation**, an advisor can approve a fixed acknowledgement, take over, compose a staff reply, or release the conversation. Takeover suppresses queued assistant replies. Dispatch checks the owner again in the same transaction that claims the send. Release leaves suppressed drafts closed. Staff replies use a request ID for safe retries. The older follow-up route can create an ask link for manual sharing. Managed conversation dispatch is the sole path to the WhatsApp transport.

The journal claims an attempt before calling Meta. A timeout, uncertain provider response, or interrupted attempt surfaces as `DELIVERY_UNKNOWN` and cannot auto-retry. A signed receipt from the same inbox can reconcile the status through the provider ID or original attempt correlation ID. Provider acceptance and delivery appear separately. Takeover stops queued work. An attempt already claimed for transport may complete. Free-form text requires a verified inbound timestamp in the prior 24 hours. [Meta webhooks](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview/) · [Meta Cloud API text send](https://www.postman.com/meta/whatsapp-business-platform/request/8gvd47s/send-text-message)

The journal encrypts text, phone numbers and attachment filenames with the existing Waypoint key. A scoped keyed hash identifies the same verified sender. Interrupted inbound work is visible for review and does not rerun on provider redelivery. Check whether a trip was already created before using manual intake. Keep the journal and its original key together across restarts. The local journal has no automated retention or key rotation. Unsupported media is recorded without downloading it.

## Supplier lookup

`GET /api/v1/supplier/availability/evidence` takes `supplier_id`, `service_id`, `service_date` and `guests`. The authenticated staff route reads `WAYPOINT_SUPPLIER_EVIDENCE_FILE` from disk. The file names its agency, provenance and schema version. Rate observations include effective dates, guest range, amount, currency and price basis. Calendar observations include date, slot or service ID, and available capacity. Both require a stable source record ID, HTTPS link, observation time and expiry.

The lookup returns `evidence_found` when a current applicable rate and enough observed capacity agree. Missing, stale, conflicting, malformed or insufficient evidence yields `staff_review`. Rate and calendar provenance remain independent. The route performs no network I/O and issues no price approval, discount, hold, or booking confirmation. [Fictional charter snapshot](../../tests/fixtures/supplier_evidence_fictional.json)

## Controlled pilot prerequisites

### Meta test number

1. Authorize a test-only HTTPS callback and one controlled exchange. Use a team-owned Meta developer app with WhatsApp enabled, its app ID, WhatsApp Business Account ID and **test** business phone number ID. Ask one consenting recipient to complete Meta's test-recipient setup. Use fictional enquiry text. [Meta WhatsApp Business Platform](https://developers.facebook.com/documentation/business-messaging/whatsapp/overview/) · [Meta webhook setup](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/)
2. Bind a dedicated Waypoint test agency. Set the app secret and a messaging-enabled test access token through the approved secret store. Configure `WHATSAPP_APP_SECRET`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `MESSAGING_WEBHOOK_AGENCY_ID`, an explicit `ENCRYPTION_KEY` and a private persistent `WAYPOINT_MESSAGES_DIR`. Generate `WHATSAPP_VERIFY_TOKEN` separately and enable `WAYPOINT_WHATSAPP_MANAGED_ENABLED=1` in the test environment after approval. Channel status checks configuration presence and binding.
3. Subscribe the app to the test WhatsApp Business Account and route `messages` to `/api/v1/messaging/webhook/whatsapp`. Verify the handshake, a handset-originated message, duplicate delivery, staff takeover, and one approved reply with a delivery receipt. Verify callback response time and review SQL trip audit logs for identifier redaction before retaining or sharing them. The local Graph pin is `v25.0`. The previous `v21.0` pin expires January 21, 2027. [Meta Graph API versions](https://developers.facebook.com/docs/graph-api/changelog/versions)
4. Keep this test on one host with `TRIPSTORE_BACKEND=sql`. Incoming callbacks stay open while this version runs inquiry processing. Production rollout needs a durable worker and fast acknowledgement, shared state across replicas, protected retention and key rotation, and the template and outbound scope decisions under DP-04b.

### Buyer-owned supplier sources

1. Obtain a buyer-approved contract or rate export and a calendar or inventory export. Confirm data ownership, agency access, service and slot identifiers, timezone and source links that staff can open. Use approved storage for credentials.
2. Confirm currency, price basis, tax and fee treatment, guest eligibility, effective dates, capacity, blocked-slot meaning, and the freshness interval for each source. Reconcile one supplier's representative cases with its staff before using the evidence in pricing.
3. Supply a validated snapshot for the test agency. The local path reads a file after the owner exports it. A live connector, recurring refresh, supplier account access, or reservation capability requires separate authorization.

## Evidence

Local replay uses the real FastAPI routes and enquiry pipeline, JWT-authenticated advisor actions, isolated PostgreSQL for trips, and an isolated encrypted message journal. Meta payloads, recipients and supplier evidence are fictional. Tests replace Graph transport and turn off extraction and decision enrichment. Frontend component tests exercise the existing inbox controls with stubbed HTTP. This is Tier 3 backend integration and Tier 2 component evidence. Live Meta delivery, hosted behavior, handset behavior and buyer-source reconciliation remain open. [Backend scenarios](../../tests/test_waypoint_whatsapp_supplier_workflow.py) · [Inbox controls](../../frontend/src/components/inbox/__tests__/ChannelMessagesPanel.test.tsx)

The focused `pytest` run passed 41 cases, including backend route and OpenAPI parity. The focused `vitest` run passed 60 cases across the inbox, proxy mapping and intake panels. TypeScript, ESLint, Ruff and the Git whitespace check passed. The duplicate-event and dispatch ownership tests failed at the expected assertion when each guard was independently removed in memory (S3). Other passing cases are S1. The isolated production-build attempt stopped while copying its workspace because the disk was full. The partial copy was removed. Production compilation and a browser replay are unverified.

## Local browser preview

The authenticated preview runs on loopback ports 3017 and 8017 with an isolated PostgreSQL database, a separate encrypted message journal, fictional enquiries and simulated WhatsApp transport. The preview sign-in uses `waypoint-demo.localhost` to keep its cookies separate from the shared local preview. [Lead Inbox](http://waypoint-demo.localhost:3017/api/demo-session) · [Suppliers](http://waypoint-demo.localhost:3017/api/demo-session?page=suppliers)

The first browser replay showed one traveler on both lead cards. Managed intake had written the facts only to the older `packet` field, while the SQL inbox reads `extracted`. Managed intake now saves the canonical extracted facts in the field consumed by that projection. The regression failed on the old code and passed after the fix. The corrected signed events produced two Phuket cards showing 8 and 17 travelers and their dates. The advisor browser action suppressed the queued draft after takeover and recorded the staff reply with simulated acceptance. The channel feed shows draft states explicitly. [Inbound persistence](../../spine_api/routers/inbound.py) · [Channel feed](../../frontend/src/components/inbox/ChannelMessagesPanel.tsx)

Suppliers now has a read-only **Rate and calendar lookup**. In the browser, the 17 April 2027 fixture for 17 guests showed THB 35,000 per service and capacity for 20, with a source link for each. Moving to 19 April kept the current rate visible and set the calendar to **Evidence expired** and the result to **Staff review needed**. [Suppliers lookup](../../frontend/src/components/workspace/SupplierEvidenceLookup.tsx)

Browser replay is Tier 4 local evidence with simulated transport. The follow-up passed 15 focused Python tests and 33 focused Vitest tests. TypeScript, ESLint, Ruff and whitespace checks passed. The corrected lead projection is S2. Provider delivery, buyer-owned source validation and a production build remain open.

### WhatsApp in Command

WhatsApp has a dedicated `/whatsapp` page directly below Lead Inbox in the Command navigation. The mobile More menu also links there. Lead Inbox retains the two Phuket lead cards and its collapsed feed for other recent channels. The WhatsApp workspace uses the existing channel-filtered feed, trip links and conversation controls. The authenticated browser replay confirmed desktop placement, both lead cards in the Inbox, and the persisted staff-owned conversation in WhatsApp. It used simulated delivery and preserved the existing preview records. Sixteen focused Vitest tests, TypeScript, ESLint and the diff whitespace check passed. [WhatsApp preview](http://waypoint-demo.localhost:3017/api/demo-session?page=whatsapp) · [Page source](../../frontend/src/app/(agency)/whatsapp/page.tsx)

### Communications workspace

The operator and architecture council seats favored one Command destination, with Lead Inbox retaining enquiry triage. Front and Chatwoot document shared inboxes with distinct channels. These are product references. Waypoint owns the workspace and continues to use its existing WhatsApp routes. The old /whatsapp URL redirects to /communications. Direct Email remains a future Waypoint channel. A future email slice should prove durable threading, staff ownership and linked enquiries through a local test transport before live mailbox access. The council also identified two follow-ups: channel filtering before the feed limit and owner-aware release controls. [Front shared inboxes](https://help.front.com/en/articles/2057) · [Chatwoot channels](https://app.chatwoot.com/hc/user-guide/articles/1677492191-adding-inboxes)

The authenticated local browser followed the legacy redirect and reopened the persisted staff-owned WhatsApp conversation in Communications. Eleven focused tests and TypeScript passed.

The isolated Next.js production build exited successfully and listed both routes. Existing dynamic-render diagnostics appeared for other API routes.

## WhatsApp technical walkthrough

### How chats arrive and what history is available

`Traveler → WhatsApp → Meta webhook → Waypoint journal → Communications`

Meta pushes new inbound messages and outgoing delivery updates for the subscribed business account to our HTTPS endpoint. `GET /api/v1/messaging/webhook/whatsapp` handles Meta's verification challenge. Each POST is authenticated with an HMAC over the raw request bytes using the Meta app secret. Waypoint then checks the event's business phone number ID against the configured inbox and agency. The local adapter handles individual message events and processes text through the existing enquiry pipeline. Media metadata can be recorded for review. Downloading media is separate. [Meta webhook overview](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview/) · [Webhook handler](../../spine_api/routers/messaging.py) · [Event adapter](../../spine_api/services/whatsapp_cloud.py)

The journal groups messages by agency, business inbox and sender. It claims a provider message ID in SQLite before extraction, so redelivery skips the expensive work. One unambiguous active trip can be linked by phone. A new text enquiry can create a lead. Ambiguous matches and interrupted processing remain visible for staff review. The browser polls Waypoint's own authenticated `GET /api/v1/messages?channel=whatsapp` feed, not Meta. It renders the messages Waypoint has stored. This implementation starts accumulating history when events begin arriving. Older chats from a Business App account would require a separately verified onboarding and history-sync path. Ordinary callback setup and the sandbox test number do not establish a historical import. [Journal and feed](../../spine_api/services/whatsapp_journal.py) · [Message routes](../../spine_api/routers/messages.py)

### How replies leave Waypoint

An advisor opens a conversation, approves a saved acknowledgement or takes ownership and writes a staff reply. Authenticated write routes require trip write permission. Before attempting a send, Waypoint checks agency, inbox, ownership and the latest qualifying inbound timestamp in the same transaction that claims the reply. A takeover suppresses queued assistant replies. An attempt already claimed can finish. A staff reply's request ID protects retries of that action. The current implementation allows free-form text in the 24-hour window and does not send approved templates outside it. [Staff routes](../../spine_api/routers/messaging.py) · [Ownership and dispatch transaction](../../spine_api/services/whatsapp_journal.py#L194)

`Communications → Waypoint dispatch journal → Meta Graph /{phone-number-id}/messages → traveler`

The browser sends text to Waypoint. The backend holds the token and sends to Meta's Graph API. The recipient comes from the bound conversation. Meta API acceptance gives a message ID and is separate from delivery. Subsequent signed callbacks update sent, delivered, read or failed status. On a timeout or unclear response, Waypoint shows **Delivery unknown**, skips an automatic resend, and can reconcile a matching receipt using the Meta ID or the original attempt correlation ID. [Meta Cloud API](https://developers.facebook.com/documentation/business-messaging/whatsapp/overview/) · [Outbound transport](../../spine_api/services/message_dispatch.py) · [Receipt reconciliation](../../spine_api/services/whatsapp_journal.py#L270)

### What the chat interface can do

Waypoint builds and owns the interface. Meta supplies the WhatsApp transport. **Command → Communications → WhatsApp** lists each conversation represented in the recent feed once. Selecting a traveler opens recent inbound messages and saved outbound replies together, with trip links, intake fallback, ownership, and the existing reply controls. It is a bounded view of the local journal. The screen reads up to 50 recent channel records across conversations and up to 100 saved replies for the selected conversation. A full transcript needs conversation-scoped inbound paging from the same journal. [Communications page](../../frontend/src/app/(agency)/communications/page.tsx) · [Conversation panel](../../frontend/src/components/inbox/WhatsAppConversation.tsx)

### Navigation and interaction decision

Lead Inbox answers which opportunities need qualification. Communications answers which traveler said what, who can reply, and what happened to the last send. A single Communications destination under Command keeps those jobs easy to reach. In a provider-first sidebar, a second channel would add a second top-level queue even when an advisor's task spans both. An embedded lead inbox makes it harder to continue a conversation after qualification. Keep the trip link in the transcript. Add channel filters as real inboxes connect, with connection setup in settings. Direct email needs its own authorization, ingestion and reply contract before appearing as an active channel.

The in-app ChatGPT 6.2 Extra High consultation used a fictional brief. It favored a unified communications destination scoped by connected channels and highlighted simultaneous replies, ambiguous delivery and wrong-recipient commitments. The source-grounded council critique identified duplicate queue rows, missing inbound context, colleague ownership controls and draft loss on refresh. Front's shared inbox and conversation-status documentation corroborated keeping inbox, channel, assignment and workflow state distinct. The Unslop UI, Unslop and Redesign Existing Projects passes reused Waypoint's shell and placed visual emphasis on the selected traveler, transcript and ownership. [Front shared inboxes](https://help.front.com/en/articles/2057) · [Front conversation status](https://help.front.com/en/articles/2134)

Desktop uses a conversation list and adjacent thread. Narrow screens switch between list and thread, with Back returning focus to the selected row. A refresh error retains the last loaded messages and current composer. Staff ownership stays separate from delivery. The signed-in owner can reply or release, and a colleague sees ownership without those controls. Server-side authorization for release or transfer remains a multi-advisor rollout requirement. Durable drafts across navigation, full history, unread and needs-reply queues, saved filters, and keyboard-open mobile verification are follow-up work. Attention states require durable read and reply semantics before the UI can promise them.

### Design verification

In the existing isolated, authenticated Codex browser preview, opened Communications from the sidebar and inspected both seeded fictional threads. The assistant-owned thread displayed the inbound charter question, linked trip, queued draft, and takeover or approval controls. The staff-owned thread displayed the traveler question, suppressed draft, provider-accepted simulated reply and empty staff composer. Browser observations were desktop checks with synthetic provider data. The targeted Vitest suite covers the existing feed and intake behavior, grouped messages, takeover, draft suppression and retaining a typed reply after refresh failure. The first live acceptance remains one consented test-phone exchange with an actual receipt, as described in the pilot prerequisites above.
