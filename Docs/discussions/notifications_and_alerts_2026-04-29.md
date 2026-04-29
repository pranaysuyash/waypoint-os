# Notifications & Alerts — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, WhatsApp-primary, NO payment collection  
**Approach:** Independent analysis — alert fatigue kills productivity, keep it lean  

---

## 1. The Core Principle: Alert WHEN It Matters, Not Everything**

### Your Reality (Solo Dev)

| What Needs Alerting | What Can Wait |
|-------------------|-------------------|
| ✅ SLA breach (agent silent 4h+) | ❌ Daily digest (too noisy) |
| ✅ VIP customer message arrived | ❌ Weekly summary |
| ✅ Vendor hasn't replied in 24h | ❌ System health checks |
| ✅ EMI overdue (customer owes) | ❌ New enquiry assigned (you know) |
| ✅ Booking confirmation pending 48h | ❌ Template usage stats |

**My insight:**  
As solo dev, YOU are the only agent. Alerts must go to **YOUR WhatsApp/email**, not a dashboard you'll forget to check.

---

## 2. My Notification Entity Model (Lean)**

### Core Notification Record**

```json
{
  "notification_id": "string (UUID)",
  "notification_type": "SLA_BREACH | VENDOR_SILENT | EMI_OVERDUE | VIP_MESSAGE | BOOKING_STUCK | SYSTEM_WARNING",
  
  // Severity (drives urgency)
  "severity": "INFO | WARNING | URGENT | CRITICAL",
  "title": "string",  // "Agent idle 4h+ on VIP enquiry"
  "message": "string",  // "VIP customer Ravi waiting since 2pm"
    
  // What triggered it?
  "triggered_by": "ENQUIRY | BOOKING | PAYMENT | VENDOR | SYSTEM",
  "triggered_by_id": "string",  // enquiry_id, booking_id, etc.
  "triggered_at": "string (ISO8601)",
    
  // Who should see it?
  "recipient_agent_id": "string",  // Usually YOU
  "recipient_whatsapp": "string",  // Your WhatsApp number
  "recipient_email": "string | null",
    
  // Channel to send
  "channel": "WHATSAPP | EMAIL | IN_APP | SMS",
  "channel_status": "PENDING | SENT | FAILED",
  "sent_at": "string | null",
    
  // State
  "status": "UNREAD | READ | ACTIONED | DISMISSED",
  "read_at": "string | null",
  "action_taken": "string | null",  // "Called vendor", "Sent reminder"
  "actioned_at": "string | null",
    
  // Escalation (if you ignore it)
  "escalation_level": "0 | 1 | 2",  // 0=first, 1=reminder, 2=urgent
  "next_escalation_at": "string | null",  // Auto-escalate if still UNREAD
  "max_escalations": "integer (default: 2)"
}
```

**My insight:**  
`next_escalation_at` — if YOU don't ack in 2h, send WhatsApp AGAIN with "⚠️ URGENT" prefix.  
After 3 ignored alerts → mark as CRITICAL, maybe SMS backup.

---

## 3. Alert Rules (What Triggers What)**

### Rule 1: SLA Breach (Agent Silent)**

```json
{
  "rule_name": "Agent SLA Breach",
  "trigger": {
    "check_every_minutes": 30,
    "condition": "enquiry.status IN (RECEIVED, TRIAGED, RESEARCHING, DRAFTING) AND enquiry.updated_at < NOW() - INTERVAL '4 hours'"
  },
  "action": {
    "severity": "WARNING",
    "channel": "WHATSAPP",
    "message": "⏰ Enquiry #EQ-0042 (VIP Ravi) waiting 4h+ — no reply yet. Reply now?"
  },
  "escalation": {
    "level_1": { "after_minutes": 120, "severity": "URGENT", "prefix": "⚠️" },
    "level_2": { "after_minutes": 240, "severity": "CRITICAL", "add_sms": true }
  }
}
```

**My insight:**  
At 4h → WhatsApp. At 6h → WhatsApp with ⚠️. At 8h → WhatsApp + SMS backup.  
Solo dev = no manager to escalate to, so **escalate to yourself** with higher urgency.

---

### Rule 2: Vendor Silent (No Quote)**

```json
{
  "rule_name": "Vendor Quote Pending",
  "trigger": {
    "check_every_minutes": 60,
    "condition": "communication.thread_type = VENDOR_NEGOTIATION AND last_comm_at < NOW() - INTERVAL '24 hours' AND status = PENDING"
  },
  "action": {
    "severity": "WARNING",
    "channel": "WHATSAPP",
    "message": "📞 Vendor (Bali Paradise Resort) hasn't replied in 24h on quote request. Follow up?"
  }
}
```

**My insight:**  
Vendors are notorious for ignoring emails. WhatsApp follow-up → higher response rate.

---

### Rule 3: EMI Overdue (Customer Owes)**

```json
{
  "rule_name": "EMI Overdue",
  "trigger": {
    "check_every_minutes": 1440,  // Daily check
    "condition": "emi_tracking.next_due_date < NOW() AND emi_tracking.overdue_count >= 1"
  },
  "action": {
    "severity": "URGENT",
    "channel": "WHATSAPP",
    "message": "💰 EMI overdue: Ravi (EQ-0042) missed payment ₹15k due on 25th. Call him?"
  }
}
```

**My insight:**  
EMI overdue = cash flow risk. Alert IMMEDIATELY, don't wait for monthly review.

---

### Rule 4: VIP Customer Message**

```json
{
  "rule_name": "VIP Message Arrived",
  "trigger": {
    "check_every_minutes": 5,  // Frequent check
    "condition": "communication.sender_type = CUSTOMER AND customer.customer_segment = VIP AND communication.received_at > NOW() - INTERVAL '5 minutes'"
  },
  "action": {
    "severity": "URGENT",
    "channel": "WHATSAPP",
    "message": "👑 VIP (Priya) sent message: 'Need to change dates' — reply within 1h!"
  }
}
```

**My insight:**  
VIP = immediate attention. Even if it's 11pm, you want to know.  
Maybe add "quiet hours" (10pm-8am) for non-urgent, but VIP = always alert.

---

### Rule 5: Booking Confirmation Pending**

```json
{
  "rule_name": "Booking Stuck",
  "trigger": {
    "check_every_minutes": 60,
    "condition": "booking.status = CONFIRMED AND booking.vendor_booking_ref IS NULL AND booking.confirmed_at < NOW() - INTERVAL '48 hours'"
  },
  "action": {
    "severity": "WARNING",
    "channel": "WHATSAPP",
    "message": "⚠️ Booking #BK-001 (Bali trip) confirmed 48h ago but vendor hasn't sent voucher. Call them?"
  }
}
```

**My insight:**  
Confirmed ≠ Voucher issued. Voucher = customer can travel.  
48h without voucher = customer anxiety → YOU need to chase vendor.

---

## 4. Notification Channels (Solo Dev Reality)**

### Channel Priority (What to Use)**

| Channel | Cost | Speed | Reliability | When to Use |
|---------|------|-------|-------------|--------------|
| **WhatsApp** | Free (personal) | Instant | High | ⭐ PRIMARY — all alerts |
| **Email** | Free (Gmail) | Minutes | Medium | Backup for non-urgent |
| **SMS** | ₹0.25-0.50/message | Instant | Very High | CRITICAL only (SLA breached 8h+) |
| **In-App** | Free | When logged in | Low | You'll never check it |
| **Telegram/Slack** | Free | Instant | High | If you already use them |

**My recommendation:**  
**WhatsApp only** for solo dev. Email as daily digest backup. SMS for CRITICAL only (costs money).

---

### WhatsApp Alert Format (Keep it Scannable)**

```
⚠️ TRAVEL AGENCY ALERT

📍 Type: SLA Breach
👤 Customer: Ravi (VIP)
🆔 Enquiry: EQ-0042
⏰ Waiting: 4h 23m
📝 Last action: Sent quote on WhatsApp

➡️ Action: Reply now?
🔗 http://localhost:3000/enquiries/eq-0042
```

**My insight:**  
Include **deep link** to the exact enquiry/booking.  
You're on mobile, click link → see full context → reply fast.

---

## 5. Notification Preferences (Simple Settings)**

```json
{
  "agent_id": "string",  // Usually just YOU
  "whatsapp_number": "string",  // "+91 98765 43210"
  "email": "string | null",
  "sms_number": "string | null",
    
  // Quiet hours (don't alert)
  "quiet_hours_start": "22:00",  // 10pm
  "quiet_hours_end": "08:00",  // 8am
  "quiet_hours_timezone": "Asia/Kolkata",
  "quiet_hours_exceptions": ["VIP", "CRITICAL"],  // Always alert these
    
  // Alert frequency
  "digest_frequency": "NEVER | DAILY | WEEKLY",  // Email digest
  "max_alerts_per_hour": "integer (default: 10)",  // Prevent spam
    
  // Channel per severity
  "severity_routing": {
    "INFO": ["EMAIL"],
    "WARNING": ["WHATSAPP"],
    "URGENT": ["WHATSAPP", "EMAIL"],
    "CRITICAL": ["WHATSAPP", "SMS", "EMAIL"]
  }
}
```

**My insight:**  
`max_alerts_per_hour = 10` prevents "alert storm" if system glitches.  
`quiet_hours_exceptions = ["VIP"]` — even at 11pm, VIP message wakes you up.

---

## 6. Current State vs Notification Model**

| Concept | Current Schema | My Lean Model |
|---------|---------------|-------------------|
| Notifications | None | `Notification` entity with severity + channel |
| SLA tracking | None | `escalation_level` + `next_escalation_at` |
| Alert rules | None | 5 core rules (SLA, vendor, EMI, VIP, booking) |
| WhatsApp integration | None | `channel = WHATSAPP` + deep link |
| Quiet hours | None | `quiet_hours_start/end` + VIP exception |
| Digest | None | `digest_frequency = DAILY` (email backup) |

---

## 7. Decisions Needed (Simple Answers)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Primary channel? | WhatsApp / Email / In-App | **WhatsApp** — you live there |
| SMS for critical? | Yes / No | **YES** — ₹0.50/month for peace of mind |
| Quiet hours? | Yes / No | **YES** — 10pm-8am, VIP exempt |
| Daily digest? | Yes / No | **YES** — email backup, in case WhatsApp fails |
| Escalation levels? | 1 / 2 / 3 | **2** — Warning → Urgent → (stop, you're solo) |
| In-app notifications? | Yes / No | **NO** — you won't check dashboard |

---

## 8. Next Discussion: Roles & Permissions (RBAC)**

Now that we know **WHO gets alerted**, we need to discuss: **WHO can do WHAT?**

Key questions for next discussion:
1. **Solo dev reality** — do you even need RBAC? (spoiler: maybe not)
2. **If you hire help** — what can junior vs senior agent do?
3. **Data access** — can agents see all customers, or only assigned?
4. **Approval chains** — who can approve refunds? (only you?)
5. **API keys/secrets** — who can see Stripe keys? (only you)
6. **Audit logs** — who changed what? (for disputes)
7. **Visibility rules** — can agents see each other's commissions?

---

**Next file:** `Docs/discussions/roles_and_permissions_2026-04-29.md`
