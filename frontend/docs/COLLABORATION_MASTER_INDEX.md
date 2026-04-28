# Real-Time Collaboration — Master Index

> Exploration of multi-agent collaborative editing, presence, comments, and workflow patterns.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Architecture & Presence](COLLABORATION_01_ARCHITECTURE.md) | Presence model, resource locking, transport layer |
| 02 | [Concurrent Editing](COLLABORATION_02_EDITING.md) | Edit operations, conflict resolution, undo/redo, version vectors |
| 03 | [Comments & Communication](COLLABORATION_03_COMMENTS.md) | In-context comments, threaded discussions, mentions, decision logging |
| 04 | [Workflow & Handoffs](COLLABORATION_04_WORKFLOW.md) | Trip ownership, shift transitions, collaborative patterns, metrics |

---

## Key Themes

- **Presence is ambient** — Agents see who else is working on a trip without actively communicating. Colored cursors, avatar stacks, and status indicators provide awareness.
- **Field-level locking** — Granular enough for parallel work (two agents edit different sections) but coordinated enough to prevent conflicts.
- **Comments lead to decisions** — Every discussion thread should resolve to an action or decision, logged in the trip timeline.
- **Handoffs preserve context** — Shift changes don't lose customer context. Auto-generated summaries from activity logs supplement agent notes.
- **Specialists are consultants** — Visa, pricing, and MICE experts are consulted without transferring full trip ownership.

## Integration Points

- **Trip Builder** — Collaboration happens on trip data; edits flow through the trip data model
- **Notification System** — Comments and mentions trigger notifications via the notification pipeline
- **Audit Trail** — All collaborative edits are logged with attribution for compliance
- **Workflow Automation** — Handoffs and specialist assignments are workflow triggers
- **Conversation UX** — Comments integrate with the message history panel
- **Agent Training** — Collaboration patterns and decision logs feed into training content
