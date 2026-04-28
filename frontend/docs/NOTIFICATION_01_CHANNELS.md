# Notification & Messaging — Channel Architecture

> Research document for notification channel capabilities, routing, and delivery infrastructure.

---

## Key Questions

1. **What channels must we support (in-app, email, SMS, WhatsApp, push, Slack)?**
2. **What's the cost per message per channel, and how do we optimize spend?**
3. **What delivery reliability can we expect per channel in India and international markets?**
4. **How do we handle channel fallback when primary delivery fails?**
5. **What regulatory requirements apply per channel (DND registry, GDPR consent)?**

---

## Research Areas

### Channel Landscape

```typescript
type NotificationChannel =
  | 'in_app'            // Dashboard notification
  | 'email'             // Email via SMTP or API
  | 'sms'               // SMS via gateway
  | 'whatsapp'          // WhatsApp Business API
  | 'push_web'          // Browser push notification
  | 'push_mobile'       // Mobile app push
  | 'slack'             // Slack webhook/Bot
  | 'voice'             // Automated voice call (IVR);

interface ChannelCapability {
  channel: NotificationChannel;
  supportsRichContent: boolean;
  supportsAttachment: boolean;
  supportsTemplate: boolean;
  supportsTwoWay: boolean;       // Can receive replies
  deliveryConfirmation: boolean;
  readConfirmation: boolean;
  costPerMessage: number;
  reliabilityPercent: number;
  latencyMs: number;
  maxContentLength: number;
  regulatoryRequirements: string[];
}
```

### Channel Cost & Reliability (India)

| Channel | Cost/Message | Reliability | Latency | Best For |
|---------|-------------|-------------|---------|----------|
| In-app | Free | 100% (if online) | Instant | All non-urgent |
| Email | ~₹0.05 | 95-98% | 1-5 min | Transactional, detailed content |
| SMS | ₹0.10-0.50 | 90-95% | 5-30 sec | OTPs, urgent alerts |
| WhatsApp | ₹0.30-0.70 | 95-98% | 1-10 sec | Customer communication, rich media |
| Push (web) | Free | 80-90% | Instant | Engagement, reminders |
| Push (mobile) | Free | 85-95% | Instant | Engagement, alerts |
| Voice | ₹1-3/min | 95-99% | 1-5 min | Critical alerts, elderly users |
| Slack | Free | 99% | Instant | Internal team alerts |

### Regulatory Requirements (India)

**SMS:**
- DND (Do Not Disturb) registry compliance
- TRAI DLT (Distributed Ledger Technology) registration required
- Template pre-approval for promotional SMS
- Transactional SMS exempt from DND but must be genuinely transactional

**WhatsApp:**
- WhatsApp Business API requires Meta Business verification
- Pre-approved message templates for outbound (24h window)
- Free-form messages only within 24h of customer-initiated message
- India-specific pricing tiers

**Email:**
- No specific regulatory requirements
- SPF, DKIM, DMARC setup required for deliverability
- Unsubscribe link mandatory for promotional emails

**Push notifications:**
- Require explicit opt-in
- No specific India regulation but follow general consent principles

---

## Open Problems

1. **WhatsApp 24-hour window** — Can only send free-form messages within 24 hours of customer's last message. Outside that, must use pre-approved templates. Limits proactive communication.

2. **DND compliance** — If a customer is on the DND list, promotional SMS are blocked. Need real-time DND checking before sending.

3. **Channel preference discovery** — Some customers prefer WhatsApp, others prefer email. How to learn and respect preferences?

4. **International channel costs** — Sending SMS to international numbers is 5-10x more expensive. Need cost-aware routing.

5. **Delivery confirmation gaps** — SMS delivery reports are unreliable in India. Email read tracking is blocked by many clients. How to confirm delivery?

---

## Next Steps

- [ ] Evaluate messaging providers (Twilio, MSG91, Gupshup, Interakt for WhatsApp)
- [ ] Research TRAI DLT registration and template approval process
- [ ] Compare email delivery services (SendGrid, Amazon SES, Postmark)
- [ ] Design channel fallback chain (in-app → push → email → SMS)
- [ ] Study WhatsApp Business API template approval workflow
