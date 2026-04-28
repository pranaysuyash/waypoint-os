# Error Handling & Resilience — Frontend Error UX

> Research document for error presentation, recovery flows, and error UX in the workbench.

---

## Key Questions

1. **How do we present errors to agents without breaking their workflow?**
2. **What's the toast vs. inline vs. modal error pattern hierarchy?**
3. **How do we handle real-time errors (spine run failure, booking failure)?**
4. **What's the recovery UX — retry, alternative, or escalation?**
5. **How do we prevent error fatigue from too many notifications?**

---

## Research Areas

### Error Presentation Patterns

```typescript
interface ErrorPresentation {
  severity: ErrorSeverity;
  display: ErrorDisplay;
  duration: string;                // How long to show
  action: ErrorAction;
}

type ErrorSeverity =
  | 'info'                 // Minor issue, workaround available
  | 'warning'              // Something unexpected, may need attention
  | 'error'                // Action failed, user needs to respond
  | 'critical';            // System-wide issue, work impaired

type ErrorDisplay =
  | 'inline'               // Below the relevant form field or section
  | 'toast'                 // Transient notification (bottom-right)
  | 'banner'                // Top-of-page banner (persistent)
  | 'modal'                 // Blocking dialog (must acknowledge)
  | 'status_indicator'      // Icon change (e.g., connection status)
  | 'panel';                // Replace panel content with error state

// Presentation rules:
// Validation errors → inline below the field
// API timeout → toast with retry button
// Booking failed → modal with details and alternatives
// Spine run failure → panel error state with retry
// Network disconnected → banner + status indicator
// Session expired → modal redirect to login
```

### Recovery Actions

```typescript
interface ErrorRecovery {
  primaryAction: RecoveryAction;
  secondaryActions: RecoveryAction[];
  autoRecovery?: AutoRecovery;
}

interface RecoveryAction {
  label: string;
  type: 'retry' | 'alternative' | 'dismiss' | 'contact_support' | 'manual_workaround';
  action: string;
}

interface AutoRecovery {
  type: 'retry_with_backoff' | 'poll_until_resolved' | 'fallback_to_cached';
  maxAttempts: number;
  onResolve: string;              // What to do when error resolves
}

// Recovery examples:
// "Hotel search failed" → Retry | Try different dates | Contact support
// "Payment declined" → Try different card | Pay later | Contact support
// "Spine run timed out" → Retry | Edit input and retry | Process manually
// "Network disconnected" → Auto-reconnect (no action needed) | Work offline
```

### Connection State Management

```typescript
interface ConnectionState {
  status: 'connected' | 'degraded' | 'disconnected' | 'reconnecting';
  lastConnectedAt: Date;
  degradedFeatures: string[];     // Features limited when degraded
  pendingActions: PendingAction[]; // Queued for when reconnected
  reconnectAttempt: number;
}

interface PendingAction {
  actionId: string;
  description: string;
  queuedAt: Date;
  autoExecuteOnReconnect: boolean;
}

// UX for connection states:
// Connected → Normal operation
// Degraded → Yellow banner "Some features may be slower"
// Disconnected → Red banner "You're offline. Changes will be saved locally."
// Reconnecting → Pulsing indicator "Reconnecting..."
```

### Spine Run Error Handling

```typescript
interface SpineErrorUI {
  runId: string;
  stage: string;                   // Which stage failed
  error: AppError;
  display: SpineErrorDisplay;
}

interface SpineErrorDisplay {
  // Show which stage failed in the pipeline visualization
  failedStage: string;
  // Allow retry from failed stage (not from beginning)
  retryFromStage: boolean;
  // Show partial results if available
  partialResults: boolean;
  // Suggest manual fix
  suggestManualFix: string;
}

// Spine error scenarios:
// Extraction failed → Show raw input, allow manual extraction
// Routing failed → Show extracted data, allow manual selection
// Pricing timeout → Show itinerary without prices, allow manual pricing
// Assembly failed → Show individual components, allow manual assembly
```

---

## Open Problems

1. **Error during multi-step flow** — Agent is in the middle of a booking, and an API fails. Don't lose the work they've done. Need auto-save and resume.

2. **Error aggregation** — Multiple errors happen simultaneously (spine fails + network drops). Need to show the most important one, not a wall of errors.

3. **Error persistence** — Toast notifications disappear. If the agent was away, they miss critical errors. Need an error log/history accessible in the workbench.

4. **Optimistic UI rollback** — We optimistically update the UI before server confirmation. If the server rejects, need smooth rollback without jarring UI jumps.

5. **Error anxiety** — Too many error states make agents nervous about the system's reliability. Need to balance transparency with confidence.

---

## Next Steps

- [ ] Design error component library (inline, toast, banner, modal, panel states)
- [ ] Create error message catalog with recovery actions
- [ ] Design connection state indicator for the workbench
- [ ] Build spine run error recovery UI (partial results + retry)
- [ ] Study error UX patterns (Linear, Notion, Stripe Dashboard)
