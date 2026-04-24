# Safety & Risk Systems — UX/UI Deep Dive

> Part 2 of 5 in the Safety & Risk Systems Deep Dive Series

**Series Index:**
1. [Technical Deep Dive](SAFETY_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Risk Engine
2. [UX/UI Deep Dive](SAFETY_02_UX_UI_DEEP_DIVE.md) — Risk Display & Warning UI (this document)
3. [Business Value Deep Dive](SAFETY_03_BUSINESS_VALUE_DEEP_DIVE.md) — Protection & ROI
4. [Compliance Deep Dive](SAFETY_04_COMPLIANCE_DEEP_DIVE.md) — GST, TCS & Regulations
5. [Escalation Deep Dive](SAFETY_05_ESCALATION_DEEP_DIVE.md) — Owner Workflows & Alerts

---

## Document Overview

**Purpose:** Comprehensive exploration of how risks are presented to users — visual design, interaction patterns, and user experience for risk awareness and resolution.

**Scope:**
- Risk visualization philosophy
- Risk indicator components
- Warning and alert UI patterns
- Confirmation flows
- Risk resolution interface
- Owner approval workflow UI
- Mobile considerations
- Accessibility requirements

**Target Audience:** Designers, frontend engineers, and product managers working on the safety system interface.

**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Risk Visualization Philosophy](#risk-visualization-philosophy)
3. [Risk Indicator Components](#risk-indicator-components)
4. [Warning & Alert UI](#warning--alert-ui)
5. [Confirmation Flows](#confirmation-flows)
6. [Risk Resolution Interface](#risk-resolution-interface)
7. [Owner Approval Workflow UI](#owner-approval-workflow-ui)
8. [Dashboard Integration](#dashboard-integration)
9. [Mobile Considerations](#mobile-considerations)
10. [Accessibility Requirements](#accessibility-requirements)

---

## 1. Executive Summary

### The UX Challenge

Risk information exists on a spectrum from "nice to know" to "must act now." Poor UX can:
- **Desensitize users** — Too many warnings → alert fatigue → risks ignored
- **Block legitimate work** — Overly aggressive blocking → frustration → workarounds
- **Miss critical issues** — Subtle risks overlooked → consequences

Good risk UX balances:
- **Visibility** — Risks are apparent without being intrusive
- **Clarity** — Nature and severity are immediately understood
- **Actionability** — Clear paths to resolution
- **Context** — Risks presented at the right moment

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Progressive disclosure** | Show risk detail appropriate to severity |
| **Color consistency** | Consistent semantic colors across all risk indicators |
| **Action-oriented** | Every risk has a clear next step |
| **Non-disruptive by default** | Risks visible without blocking work |
| **Blocking when necessary** | Critical risks prevent dangerous actions |
| **Explainable** | Users understand why something is risky |

### Visual Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK VISUAL HIERARCHY                               │
└─────────────────────────────────────────────────────────────────────────────┘

  CRITICAL (Blocks Action)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  🚨 FULL SCREEN MODAL                                              │
  │  Red background, prominent icon, owner approval required            │
  └─────────────────────────────────────────────────────────────────────┘

  HIGH (Requires Confirmation)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚠️ INLINE CONFIRMATION DIALOG                                     │
  │  Yellow/orange, explicit checkboxes, detailed explanation           │
  └─────────────────────────────────────────────────────────────────────┘

  MEDIUM (Show Warning)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚡ ALERT BANNER / TOAST                                          │
  │  Yellow, dismissible, visible but not blocking                    │
  └─────────────────────────────────────────────────────────────────────┘

  LOW (Informational)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  ℹ️ INDICATOR BADGE / ICON                                        │
  │  Blue/green, subtle, shows on hover/click                          │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Risk Visualization Philosophy

### 2.1 Severity-Based Presentation

Risks are presented differently based on severity level:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SEVERITY-BASED PRESENTATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

  CRITICAL ────────────────────────────────────────────────────────────────
  Presentation: BLOCKING MODAL
  ┌─────────────────────────────────────────────────────────────────┐
  │  🚨                                                              │
  │                                                                  │
  │   CRITICAL RISK DETECTED                                         │
  │                                                                  │
  │   This action cannot be completed due to critical compliance     │
  │   issues. Owner approval is required to proceed.                │
  │                                                                  │
  │   Issue: GST compliance — Invalid GSTIN format                   │
  │                                                                  │
  │   ┌──────────────┐  ┌────────────────────────────────────────┐  │
  │   │ View Details │  │ Request Owner Approval                 │  │
  │   └──────────────┘  └────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘

  HIGH ────────────────────────────────────────────────────────────────────
  Presentation: CONFIRMATION DIALOG
  ┌─────────────────────────────────────────────────────────────────┐
  │  ⚠️  Confirm Action with Risks                                  │
  │                                                                  │
  │   This quote has 2 high-severity risks:                          │
  │                                                                  │
  │   • Budget overrun: Quote exceeds budget by 12%                 │
  │   • Timeline risk: Departure in 3 days, booking tight            │
  │                                                                  │
  │   □ I understand these risks and want to proceed                │
  │                                                                  │
  │   ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
  │   │   Cancel   │  │ Go Back    │  │ Confirm Anyway          │  │
  │   └────────────┘  └────────────┘  └─────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘

  MEDIUM ──────────────────────────────────────────────────────────────────
  Presentation: INLINE BANNER
  ┌─────────────────────────────────────────────────────────────────┐
  │  ⚡ Some risks detected. Review before proceeding.              │
  │  [View 2 risks] [Dismiss]                                        │
  └─────────────────────────────────────────────────────────────────┘

  LOW ────────────────────────────────────────────────────────────────────
  Presentation: SUBTLE INDICATOR
  │  ℹ️  (info badge - on hover shows: "Flexible refund terms not guaranteed")
```

### 2.2 Color System

```typescript
/**
 * Risk Color System
 */

const RISK_COLORS = {
  critical: {
    background: "#FEE2E2",      // Light red
    border: "#DC2626",          // Red 600
    text: "#991B1B",            // Red 800
    icon: "#DC2626",
    badge: "#DC2626"
  },
  high: {
    background: "#FEF3C7",      // Light amber
    border: "#D97706",          // Amber 600
    text: "#92400E",            // Amber 800
    icon: "#D97706",
    badge: "#F59E0B"
  },
  medium: {
    background: "#FEF3C7",      // Light amber
    border: "#F59E0B",          // Amber 500
    text: "#B45309",            // Amber 700
    icon: "#F59E0B",
    badge: "#FBBF24"
  },
  low: {
    background: "#DBEAFE",      // Light blue
    border: "#3B82F6",          // Blue 500
    text: "#1E40AF",            // Blue 800
    icon: "#3B82F6",
    badge: "#60A5FA"
  },
  info: {
    background: "#F3F4F6",      // Gray 100
    border: "#6B7280",          // Gray 500
    text: "#374151",            // Gray 700
    icon: "#6B7280",
    badge: "#9CA3AF"
  },
  resolved: {
    background: "#D1FAE5",      // Light emerald
    border: "#059669",          // Emerald 600
    text: "#065F46",            // Emerald 800
    icon: "#059669",
    badge: "#10B981"
  }
};
```

### 2.3 Icon System

```typescript
/**
 * Risk Icon System
 */

const RISK_ICONS = {
  critical: "alert-circle-fill",     // Filled circle with exclamation
  high: "exclamation-triangle-fill", // Filled triangle
  medium: "exclamation-triangle",    // Outline triangle
  low: "info-circle",                // Outline circle
  info: "info-circle",
  resolved: "check-circle-fill",     // Filled checkmark
  warning: "warning-fill",
  budget: "currency-dollar",
  compliance: "shield-fill",
  operational: "gear-fill",
  customer: "person-fill",
  agency: "building-fill"
};
```

---

## 3. Risk Indicator Components

### 3.1 Risk Badge

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RISK BADGE COMPONENT                              │
└─────────────────────────────────────────────────────────────────────────────┘

  STATES:

  ┌─────────────────┐
  │  🚨 3 Critical  │  Red background, white text
  └─────────────────┘

  ┌─────────────────┐
  │  ⚠️  2 High     │  Orange background, dark text
  └─────────────────┘

  ┌─────────────────┐
  │  ⚡ 1 Medium    │  Yellow background, dark text
  └─────────────────┘

  ┌─────────────────┐
  │  ℹ️  4 Risks    │  Blue background, dark text
  └─────────────────┘

  INTERACTION:
  - Click: Opens risk summary panel
  - Hover: Shows tooltip with top 3 risks
```

### 3.2 Risk Status Pill

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RISK STATUS PILL                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  PLACEMENT: Next to packet/quote/booking status

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Packet #2847  │  🟢 Active  │  ⚠️ 2 Risks  │  💰 ₹1.2L  │  📅 Jun 12 │
  └─────────────────────────────────────────────────────────────────────┘

  COLOR STATES:

  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
  │  ✅ No Risks       │  │  ⚠️ Risks Present  │  │  🚨 Action Needed  │
  │  Green badge       │  │  Yellow badge       │  │  Red badge         │
  └────────────────────┘  └────────────────────┘  └────────────────────┘
```

### 3.3 Inline Risk Indicators

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INLINE RISK INDICATORS                               │
└─────────────────────────────────────────────────────────────────────────────┘

  BUDGET FIELD WITH OVERRUN WARNING:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Budget                                                            │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ ₹1,00,000                                    ⚠️ Over by 12%   │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │  Quote: ₹1,12,000                                                │
  │  💡 Consider: Adjust itinerary or discuss budget increase         │
  └─────────────────────────────────────────────────────────────────────┘

  DATE FIELD WITH TIMELINE WARNING:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Departure Date                                                    │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 12 Jun 2026                                  ⚡ Tight timeline │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │  3 days away — booking may require expedited processing           │
  └─────────────────────────────────────────────────────────────────────┘

  CUSTOMER FIELD WITH COMPLIANCE WARNING:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Customer GSTIN                                                   │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 22AAAAA0000A1Z5                              🚨 Invalid format│   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │  GSTIN format appears incorrect. Verify before invoicing.          │
  └─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Component Specifications

```typescript
/**
 * Risk Badge Component
 */

interface RiskBadgeProps {
  risks: DetectedRisk[];
  onClick?: () => void;
  showTooltip?: boolean;
  variant?: "compact" | "detailed";
}

// Usage
<RiskBadge
  risks={detectedRisks}
  onClick={() => setShowRiskPanel(true)}
  showTooltip={true}
  variant="compact"
/>

/**
 * Risk Status Pill Component
 */

interface RiskStatusPillProps {
  assessment: RiskAssessment;
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  onClick?: () => void;
}

// Usage
<RiskStatusPill
  assessment={riskAssessment}
  size="md"
  interactive={true}
  onClick={() => navigateToRisks()}
/>

/**
 * Inline Risk Indicator Component
 */

interface InlineRiskIndicatorProps {
  field: string;
  risk?: DetectedRisk;
  position?: "top" | "right" | "bottom";
  size?: "sm" | "md";
}

// Usage
<InlineRiskIndicator
  field="budget.total"
  risk={budgetRisk}
  position="right"
  size="sm"
/>
```

---

## 4. Warning & Alert UI

### 4.1 Alert Banner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ALERT BANNER                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  HIGH SEVERITY BANNER (Top of page):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚠️  2 high-severity risks require attention before proceeding.     │
  │  [Review Risks] [Dismiss]                                             │
  └─────────────────────────────────────────────────────────────────────┘

  MEDIUM SEVERITY BANNER:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚡ Budget exceeds customer stated amount. Consider discussing.    │
  │  [Adjust Budget] [Mark Reviewed]                                    │
  └─────────────────────────────────────────────────────────────────────┘

  INFO BANNER:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ℹ️  Customer is eligible for TCS credit on this booking.           │
  │  [Learn More] [Dismiss]                                              │
  └─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Toast Notifications

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TOAST NOTIFICATIONS                               │
└─────────────────────────────────────────────────────────────────────────────┘

  RISK DETECTED TOAST:

  ┌────────────────────────────────────────────────────────┐
  │  ⚠️  Risk Detected                                     │
  │  Budget exceeds stated limit by ₹12,000                │
  │                                    [Dismiss] [Fix]    │
  └────────────────────────────────────────────────────────┘

  RISK RESOLVED TOAST:

  ┌────────────────────────────────────────────────────────┐
  │  ✅ Risk Resolved                                      │
  │  GSTIN verified and valid                              │
  │                                    [Dismiss]         │
  └────────────────────────────────────────────────────────┘

  OWNER APPROVAL REQUESTED TOAST:

  ┌────────────────────────────────────────────────────────┐
  │  📧 Owner approval requested                           │
  │  You'll be notified when approval is granted           │
  │                                    [View Status]      │
  └────────────────────────────────────────────────────────┘
```

### 4.3 Alert Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ALERT PANEL                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  SLIDE-OUT PANEL (Right side of screen):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Risks (3)                                           ────────── ✕   │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 🚨 CRITICAL                                                 │   │
  │  │                                                             │   │
  │  │  Invalid GSTIN format                                       │   │
  │  │  The provided GSTIN does not match the required format.     │   │
  │  │  Current: 22AAAAA0000A1Z5                                   │   │
  │  │                                                             │   │
  │  │  Impact: Cannot issue compliant invoice                      │   │
  │  │                                                             │   │
  │  │  Suggested actions:                                         │   │
  │  │  • Verify GSTIN with customer                               │   │
  │  │  • Check against GST portal                                 │   │
  │  │  • Request corrected GSTIN                                   │   │
  │  │                                                             │   │
  │  │  ┌────────────────┐  ┌─────────────────────────────────┐   │   │
  │  │  │ Fix Now        │  │ Request Owner Approval          │   │   │
  │  │  └────────────────┘  └─────────────────────────────────┘   │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ ⚠️  HIGH                                                     │   │
  │  │                                                             │   │
  │  │  Budget overrun: 12% over customer limit                    │   │
  │  │  Quote: ₹1,12,000 | Budget: ₹1,00,000                       │   │
  │  │                                                             │   │
  │  │  [Adjust Quote] [Mark Reviewed]                            │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ ⚡ MEDIUM                                                    │   │
  │  │                                                             │   │
  │  │  Timeline risk: 3 days until departure                      │   │
  │  │  Expedited booking may be required                          │   │
  │  │                                                             │   │
  │  │  [Acknowledge] [Set Reminder]                               │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Confirmation Flows

### 5.1 Risk Acknowledgment Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RISK ACKNOWLEDGMENT DIALOG                            │
└─────────────────────────────────────────────────────────────────────────────┘

  DIALOG (Centered modal):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚠️  Proceed with Risks?                                    ───── ✕  │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  This action has risks that should be reviewed before proceeding.   │
  │                                                                     │
  │  Risks detected:                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ ⚠️  Budget overrun by ₹12,000 (12%)                          │   │
  │  │    Customer may need to approve increase                    │   │
  │  │    [View Details]                                            │   │
  │  ├─────────────────────────────────────────────────────────────┤   │
  │  │ ⚡ Timeline: 3 days to departure                             │   │
  │  │    Booking may require expedited processing                  │   │
  │  │    [View Details]                                            │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  To proceed, you must acknowledge these risks:                      │
  │                                                                     │
  │  □ I have reviewed the risks above                                │
  │  □ I have discussed with the customer (if applicable)              │
  │  □ I understand the implications of proceeding                     │
  │                                                                     │
  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────────────┐  │
  │  │   Cancel   │  │ Go Back    │  │ Acknowledge & Proceed       │  │
  │  └────────────┘  └────────────┘  └─────────────────────────────┘  │
  │                              (disabled until checked)               │
  └─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Critical Risk Block Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CRITICAL RISK BLOCK DIALOG                          │
└─────────────────────────────────────────────────────────────────────────────┘

  FULL SCREEN MODAL:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  🚨                                                                  │
  │                                                                     │
  │   ACTION BLOCKED                                                    │
  │                                                                     │
  │   This action cannot be completed due to critical compliance        │
  │   issues. These must be resolved before proceeding.                 │
  │                                                                     │
  │   Critical Issues:                                                   │
  │   ┌─────────────────────────────────────────────────────────────┐   │
  │  │  🚨 Invalid GSTIN Format                                     │   │
  │  │                                                             │   │
  │  │  The provided GSTIN "22AAAAA0000A1Z5" does not match the    │   │
  │  │  required format. This will prevent compliant invoicing.     │   │
  │  │                                                             │   │
  │  │  Required actions:                                           │   │
  │  │  • Verify correct GSTIN with customer                        │   │
  │  │  • Update customer profile                                   │   │
  │  │  │                                                             │   │
  │  │  ┌────────────────┐  ┌────────────────────────────────────┐  │   │
  │  │  │ Fix GSTIN      │  │ Request Owner Approval              │  │   │
  │  │  └────────────────┘  └────────────────────────────────────┘  │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │   Why is this blocked?                                              │
  │   GST compliance is required for all invoices. Invalid GSTIN       │
  │   can result in penalties and tax notices.                          │
  │                                                                     │
  │                                    [Learn More about GST Compliance]│
  │                                                                     │
  │   ┌─────────────────────────────────────────────────────────────┐  │
  │  │                        Go Back                               │  │
  │  └─────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Owner Approval Request Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OWNER APPROVAL REQUEST DIALOG                          │
└─────────────────────────────────────────────────────────────────────────────┘

  DIALOG:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  📧 Request Owner Approval                                   ───── ✕  │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  This action requires owner approval due to critical risks.          │
  │                                                                     │
  │  Risk summary:                                                       │
  │  • Budget overrun: ₹12,000 (12%)                                    │
  │  • Timeline: 3 days to departure                                    │
  │                                                                     │
  │  Your justification:                                                 │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │                                                             │   │
  │  │ Customer is VIP and has approved budget via WhatsApp...     │   │
  │  │                                                             │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  Owner will be notified and can approve from their dashboard or     │
  │  email. You'll be notified when a decision is made.                  │
  │                                                                     │
  │  Expected response time: Within 24 hours                            │
  │                                                                     │
  │  ┌────────────┐  ┌─────────────────────────────────────────────────┐│
  │  │   Cancel   │  │ Request Approval                                ││
  │  └────────────┘  └─────────────────────────────────────────────────┘│
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Risk Resolution Interface

### 6.1 Risk Resolution Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK RESOLUTION PANEL                               │
└─────────────────────────────────────────────────────────────────────────────┘

  DEDICATED RISKS TAB IN PACKET DETAIL:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Packet Details │ Timeline │ Quote │ Risks (3) │ Communications    │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Risk Summary                                                 │   │
  │  │ ┌──────────┬──────────┬──────────┬──────────┬────────────┐ │   │
  │  │ │ Critical │   High   │  Medium  │    Low   │   Total     │ │   │
  │  │ │    1     │    1     │    1     │    0     │     3       │ │   │
  │  │ └──────────┴──────────┴──────────┴──────────┴────────────┘ │   │
  │  │ Overall: HIGH RISK | Action Required                          │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 1. Invalid GSTIN Format                    CRITICAL  ────     │   │
  │  │                                                             │   │
  │  │  The provided GSTIN does not match required format.        │   │
  │  │  This will prevent compliant invoicing.                     │   │
  │  │                                                             │   │
  │  │  Detected: 2 hours ago | Expires: Never                     │   │
  │  │  Status: ┌──────────────┐  Assigned: You                    │   │
  │  │          │ Open         │                                   │   │
  │  │          └──────────────┘                                   │   │
  │  │                                                             │   │
  │  │  Suggested Actions:            Progress:                     │   │
  │  │  □ Verify GSTIN with customer    ░░░░░░░░░░░░ 0%            │   │
  │  │  □ Check against GST portal                                   │   │
  │  │  □ Update customer profile                                   │   │
  │  │                                                             │   │
  │  │  Your Notes:                                                 │   │
  │  │  ┌─────────────────────────────────────────────────────────┐ │   │
  │  │  │ Waiting for customer to share correct GSTIN...          │ │   │
  │  │  └─────────────────────────────────────────────────────────┘ │   │
  │  │                                                             │   │
  │  │  ┌────────────────┐  ┌────────────┐  ┌───────────────────┐  │   │
  │  │  │ View Details   │  │ Add Note   │  │ Mark Resolved     │  │   │
  │  │  └────────────────┘  └────────────┘  └───────────────────┘  │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 2. Budget Overrun                           HIGH    ────      │   │
  │  │                                                             │   │
  │  │  Quote exceeds customer budget by ₹12,000 (12%)            │   │
  │  │  Detected: 3 hours ago | Expires: Booking confirmation     │   │
  │  │  Status: ┌──────────────┐                                   │   │
  │  │          │ In Progress  │                                   │   │
  │  │          └──────────────┘                                   │   │
  │  │                                                             │   │
  │  │  ┌────────────────┐  ┌────────────┐  ┌───────────────────┐  │   │
  │  │  │ Discuss Budget │  │ Add Note   │  │ Mark Resolved     │  │   │
  │  │  └────────────────┘  └────────────┘  └───────────────────┘  │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ 3. Timeline Risk                           MEDIUM  ────      │   │
  │  │                                                             │   │
  │  │  Only 3 days until departure. Expedited processing needed.  │   │
  │  │  Status: ┌──────────────┐                                   │   │
  │  │          │ Acknowledged │                                   │   │
  │  │          └──────────────┘                                   │   │
  │  │                                                             │   │
  │  │  ┌────────────────┐  ┌────────────┐  ┌───────────────────┐  │   │
  │  │  │ Expedite       │  │ Add Note   │  │ Mark Resolved     │  │   │
  │  │  └────────────────┘  └────────────┘  └───────────────────┘  │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │                     Show Resolved (12)                       │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Quick Resolution Actions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUICK RESOLUTION ACTIONS                             │
└─────────────────────────────────────────────────────────────────────────────┘

  INLINE ACTIONS ON RISK ITEM:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚠️  Budget exceeds stated limit by ₹12,000                          │
  │                                                                     │
  │  Quick Actions:                                                     │
  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
  │  │ Adjust     │  │ Discuss    │  │ Add Note   │  │ Dismiss    │   │
  │  │ Quote      │  │ Customer   │  │            │  │            │   │
  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘

  ACTION MENU (three dots):

  ┌─────────────────────────────────────┐
  │  • View full details                │
  │  • Change severity                  │
  │  • Assign to different agent        │
  │  • Request owner approval           │
  │  • Escalate to owner                │
  │  • Mark as false positive           │
  │  • Link to related risk             │
  └─────────────────────────────────────┘
```

### 6.3 Resolution Confirmation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESOLUTION CONFIRMATION DIALOG                         │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ✅ Mark Risk as Resolved?                                  ───── ✕  │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  You're about to mark this risk as resolved:                        │
  │                                                                     │
  │  Budget overrun: Quote exceeds customer budget by ₹12,000          │
  │                                                                     │
  │  How was this resolved?                                             │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ ○ Customer approved budget increase                        │   │
  │  │ ○ Itinerary adjusted to fit budget                          │   │
  │  │ ○ Customer decided to reduce scope                          │   │
  │  │ ○ Marked as false positive (not actually a risk)            │   │
  │  │ ○ Other (please specify)                                    │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  Additional notes (optional):                                       │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │                                                             │   │
  │  │ Customer approved via phone call. Updated quote sent...    │   │
  │  │                                                             │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  □ Notify owner of resolution                                       │
  │                                                                     │
  │  ┌────────────┐  ┌─────────────────────────────────────────────────┐│
  │  │   Cancel   │  │ Confirm Resolution                              ││
  │  └────────────┘  └─────────────────────────────────────────────────┘│
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Owner Approval Workflow UI

### 7.1 Pending Approvals Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OWNER APPROVALS DASHBOARD                           │
└─────────────────────────────────────────────────────────────────────────────┘

  OWNER DASHBOARD SECTION:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  📧 Pending Approvals (3)                              View All →    │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ PKG-2847 │ Budget Overrun                    │ 2h ago  │ ⏱️  │   │
  │  │────────────────────────────────────────────────────────────│   │
  │  │ Agent: Priya S. │ Quote: ₹1.12L │ Budget: ₹1.0L             │   │
  │  │ "Customer VIP, approved budget increase via WhatsApp"       │   │
  │  │                                                             │   │
  │  │ ┌────────────┐ ┌────────────┐ ┌───────────────────────────┐ │   │
  │  │ │   View     │ │    Deny    │ │      Approve             │ │   │
  │  │ │ Details    │ │            │ │                           │ │   │
  │  │ └────────────┘ └────────────┘ └───────────────────────────┘ │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ PKG-2845 │ GSTIN Invalid                     │ 5h ago  │ ⏱️  │   │
  │  │────────────────────────────────────────────────────────────│   │
  │  │ Agent: Amit K. │ GSTIN: 22AAAAA0000A1Z5                      │   │
  │  │ "Customer confirmed GSTIN, waiting for updated document"    │   │
  │  │                                                             │   │
  │  │ ┌────────────┐ ┌────────────┐ ┌───────────────────────────┐ │   │
  │  │ │   View     │ │    Deny    │ │      Approve             │ │   │
  │  │ │ Details    │ │            │ │                           │ │   │
  │  │ └────────────┘ └────────────┘ └───────────────────────────┘ │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ PKG-2841 │ Timeline Risk                    │ Yesterday│ ⏱️  │   │
  │  │────────────────────────────────────────────────────────────│   │
  │  │ Agent: Neha R. │ Departure: Jun 15 │ Today: Jun 12           │   │
  │  │ "Expedited booking confirmed with supplier"                │   │
  │  │                                                             │   │
  │  │ ┌────────────┐ ┌────────────┐ ┌───────────────────────────┐ │   │
  │  │ │   View     │ │    Deny    │ │      Approve             │ │   │
  │  │ │ Details    │ │            │ │                           │ │   │
  │  │ └────────────┘ └────────────┘ └───────────────────────────┘ │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Approval Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          APPROVAL DETAIL VIEW                              │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Approval Request                                            ← Back │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Packet #2847 - Europe Summer Package                        │   │
  │  │ Customer: Sharma Family │ Agent: Priya S.                    │   │
  │  │ Requested: 2 hours ago │ Expires: Tomorrow 10:30 AM          │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Risk Summary                                                 │   │
  │  ├─────────────────────────────────────────────────────────────┤   │
  │  │ Type: Budget Overrun                                         │   │
  │  │ Severity: HIGH                                               │   │
  │  │                                                             │   │
  │  │ Quote: ₹1,12,000                                              │   │
  │  Budget: ₹1,00,000                                              │   │
  │  Overrun: ₹12,000 (12%)                                         │   │
  │  │                                                             │   │
  │  │ Impact: Customer may not approve final cost                   │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Agent's Justification                                        │   │
  │  ├─────────────────────────────────────────────────────────────┤   │
  │  │                                                             │   │
  │  │ Customer is VIP tier and has approved budget increase via   │   │
  │  │ WhatsApp call. They were aware of final cost and are        │   │
  │  │ comfortable with the amount. Quote has been updated and      │   │
  │  │ sent for confirmation.                                       │   │
  │  │                                                             │   │
  │  │ Customer conversation available in communications tab.       │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Quote Preview                                                 │   │
  │  ├─────────────────────────────────────────────────────────────┤   │
  │  │ • 7 nights Paris, 4 nights Swiss                             │   │
  │  │ • Flights, hotels, transfers included                        │   │
  │  │ • Total: ₹1,12,000                                            │   │
  │  │                                                             │   │
  │  │ [View Full Quote]                                            │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ Your Decision                                                 │   │
  │  ├─────────────────────────────────────────────────────────────┤   │
  │  │                                                             │   │
  │  │ ○ Approve - Allow agent to proceed with this quote          │   │
  │  │ ○ Deny - Risk must be resolved before proceeding            │   │
  │  │                                                             │   │
  │  │ Notes for agent (optional):                                  │   │
  │  │ ┌────────────────────────────────────────────────────────────┐│  │
  │  │                                                            ││  │
  │  │  Please document customer approval in the packet...       ││  │
  │  │                                                            ││  │
  │  │ └────────────────────────────────────────────────────────────┘│  │
  │  │                                                             │   │
  │  │ □ Require additional documentation before booking            │   │
  │  │                                                             │   │
  │  │ ┌────────────┐  ┌─────────────────────────────────────────────────┐│
  │  │ │   Cancel   │  │ Submit Decision                                 ││
  │  │ └────────────┘  └─────────────────────────────────────────────────┘│
  │  └─────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Approval Notification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPROVAL NOTIFICATION                                │
└─────────────────────────────────────────────────────────────────────────────┘

  EMAIL TEMPLATE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Subject: 🔔 Approval Required: Budget Overrun - PKG-2847          │
  │                                                                     │
  │  Hi [Owner Name],                                                   │
  │                                                                     │
  │  Priya S. is requesting your approval for a risk detected in        │
  │  packet PKG-2847.                                                   │
  │                                                                     │
  │  Risk: Budget Overrun                                               │
  │  Quote: ₹1,12,000 | Budget: ₹1,00,000                               │
  │  Severity: HIGH                                                     │
  │                                                                     │
  │  Agent's note:                                                      │
  │  "Customer is VIP tier and has approved budget increase via         │
  │  WhatsApp call. They were aware of final cost and are               │
  │  comfortable with the amount."                                      │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ [Review and Decide]                                         │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  This request will expire in 24 hours.                             │
  │                                                                     │
  │  View all pending approvals: [Owner Dashboard]                      │
  └─────────────────────────────────────────────────────────────────────┘

  IN-APP NOTIFICATION:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  🔔 Approval Request                                               │
  │                                                                     │
  │  Priya S. requests approval for budget overrun in PKG-2847         │
  │                                                                     │
  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────────────┐  │
  │  │   View     │  │    Deny    │  │      Approve               │  │
  │  └────────────┘  └────────────┘  └─────────────────────────────┘  │
  │                                                                     │
  │  2h ago                                             [Dismiss]      │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Dashboard Integration

### 8.1 Operations Dashboard Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPERATIONS DASHBOARD - RISK WIDGET                       │
└─────────────────────────────────────────────────────────────────────────────┘

  RISK STATUS CARD:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Risk Status                                            See Details →│
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │  Active Risks by Severity                                    │   │
  │  │                                                              │   │
  │  │  Critical  ████████  4                                      │   │
  │  │  High      ████████████████  12                             │   │
  │  │  Medium   ████████████████████████████████  34              │   │
  │  │  Low      ████████████████████  18                           │   │
  │  │                                                              │   │
  │  │  Total: 68 active risks                                     │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │  Top Risk Categories                                        │   │
  │  │  ┌───────────────────────────────────────────────────────┐  │   │
  │  │  │ Budget         ████████████████  23                    │  │   │
  │  │  │ Timeline       ████████████  15                        │  │   │
  │  │  │ Compliance    ██████████  12                           │  │   │
  │  │  │ Documentation ████████  8                             │  │   │
  │  │  └───────────────────────────────────────────────────────┘  │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │  Pending Approvals: 3  |  Overdue: 0  |  Expired Today: 1    │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  Trend: ▲ 12% vs last week                                          │
  └─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Packet List Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PACKET LIST - RISK COLUMN                             │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  Packet    │ Customer       │ Destination   │  Status   │  Risk    │ Act │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │  PKG-2847  │ Sharma Family  │ Europe        │  Active   │ 🚨 3    │ ⋯   │
  │  PKG-2846  │ Patel Group    │ Thailand     │ Quoting   │ ⚠️  2    │ ⋯   │
  │  PKG-2845  │ Singh Couple   │ Dubai        │ Booked    │ ⚡  1    │ ⋯   │
  │  PKG-2844  │ Kumar Family   │ Kerala       │ Active    │ ✅      │ ⋯   │
  │  PKG-2843  │ Reddy Family   │ Singapore    │ Negotiating│ ⚠️  1    │ ⋯   │
  └─────────────────────────────────────────────────────────────────────────────┘

  RISK COLUMN LEGEND:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  🚨 3     = 3 Critical/High risks (Action needed)                 │
  │  ⚠️  2     = 2 Medium risks (Review recommended)                  │
  │  ⚡  1     = 1 Low risk (Informational)                           │
  │  ✅       = No active risks                                        │
  └─────────────────────────────────────────────────────────────────────┘

  CLICK ON RISK CELL → Opens risk summary panel
```

---

## 9. Mobile Considerations

### 9.1 Mobile Risk Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MOBILE RISK UI                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  MOBILE RISK BANNER (Compact):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚠️  3 risks detected                                    [View ▼]   │
  └─────────────────────────────────────────────────────────────────────┘

  EXPANDED MOBILE RISK PANEL:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Risks (3)                                                        │
  │  ─────────────────────────────────────────────────────────────────  │
  │                                                                     │
  │  🚨 Invalid GSTIN                                   Critical        │
  │     Verify format before invoicing                                │
  │     [Fix Now] [Request Approval]                                  │
  │  ─────────────────────────────────────────────────────────────────  │
  │                                                                     │
  │  ⚠️  Budget: ₹12K over                            High            │
  │     Discuss with customer                                         │
  │     [Adjust] [Discuss] [Dismiss]                                  │
  │  ─────────────────────────────────────────────────────────────────  │
  │                                                                     │
  │  ⚡ Timeline: 3 days                               Medium          │
  │     Expedite booking                                              │
  │     [Acknowledge] [Set Reminder]                                  │
  │                                                                     │
  │                                              [Close]               │
  └─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Mobile Confirmation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MOBILE CONFIRMATION FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

  BOTTOM SHEET CONFIRMATION:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ────  │  ⚠️  Proceed with Risks?                                   │
  │  │                                                              │   │
  │  │  This quote has 2 high-severity risks:                          │   │
  │  │                                                              │   │
  │  │  • Budget exceeds stated amount by ₹12,000                    │   │
  │  │  • Only 3 days until departure                                │   │
  │  │                                                              │   │
  │  │  □ I understand these risks                                   │   │
  │  │                                                              │   │
  │  │  ┌────────────────────────────────────────────────────────┐  │   │
  │  │  │              Cancel              │   Proceed →         │  │   │
  │  │  └────────────────────────────────────────────────────────┘  │   │
  └─────────────────────────────────────────────────────────────────────┘

  Swipe up for full details
```

---

## 10. Accessibility Requirements

### 10.1 Screen Reader Support

```typescript
/**
 * Accessibility Props for Risk Components
 */

interface AccessibleRiskProps {
  // ARIA attributes
  ariaLabel: string;
  ariaDescription?: string;
  role?: "alert" | "dialog" | "status" | "alertdialog";

  // Keyboard navigation
  keyboardShortcut?: string;

  // Focus management
  autoFocus?: boolean;
  trapFocus?: boolean;

  // Live regions
  liveRegion?: "polite" | "assertive";
  atomic?: boolean;
}

// Example usage
<RiskBadge
  risks={detectedRisks}
  ariaLabel="3 risks detected: 2 high, 1 medium"
  role="alert"
  liveRegion="polite"
/>
```

### 10.2 Color Blindness Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COLOR BLINDNESS FRIENDLY DESIGN                         │
└─────────────────────────────────────────────────────────────────────────────┘

  DON'T RELY ON COLOR ALONE:

  ❌ Bad: Only color indicates severity
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Red badge = Critical                                               │
  │  Yellow badge = Warning                                             │
  └─────────────────────────────────────────────────────────────────────┘

  ✅ Good: Color + icon + text
  ┌─────────────────────────────────────────────────────────────────────┐
  │  🚨 CRITICAL - Action required                                     │
  │  ⚠️  WARNING - Review recommended                                  │
  │  ⚡ INFO - For your awareness                                      │
  └─────────────────────────────────────────────────────────────────────┘

  ADDITIONAL INDICATORS:
  - Icons always accompany color badges
  - Text labels always present
  - Patterns for critical states (striped background)
  - Underlines for high-severity text
```

### 10.3 Keyboard Navigation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KEYBOARD NAVIGATION PATHS                            │
└─────────────────────────────────────────────────────────────────────────────┘

  TAB ORDER:
  1. Risk badge (if present)
  2. Main action buttons
  3. Risk warning banner
  4. Risk details panel (if open)
  5. Dismiss/Acknowledge buttons
  6. Resolution actions

  SHORTCUTS:
  - Ctrl/Cmd + Shift + R: Open risk panel
  - Ctrl/Cmd + Shift + A: Acknowledge all low/medium risks
  - Esc: Close risk panel
  - Enter: Open risk details from badge
```

---

## Summary

The Safety & Risk UX/UI system balances visibility with non-disruption through:

1. **Severity-based presentation** — Critical risks block, high risks warn, low risks inform
2. **Consistent visual language** — Color, icons, and patterns communicate risk level
3. **Progressive disclosure** — Show detail appropriate to severity and user action
4. **Clear action paths** — Every risk has obvious resolution steps
5. **Owner approval workflows** — Clear escalation process with tracking
6. **Mobile-responsive design** — Compact but complete risk information on all devices
7. **Accessibility-first** — Screen reader support, keyboard navigation, color-blind friendly

The design ensures agents are aware of risks without being overwhelmed, while critical issues always get the attention they require.

---

**Next Document:** SAFETY_03_BUSINESS_VALUE_DEEP_DIVE.md — Protection benefits, ROI calculation, and business impact
