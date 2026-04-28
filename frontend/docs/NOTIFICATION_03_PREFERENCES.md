# Notification & Messaging — User Preferences & Consent

> Research document for managing user notification preferences, consent, and opt-out workflows.

---

## Key Questions

1. **What granularity of preference control should users have?**
2. **How do we manage consent across channels (explicit opt-in vs. implied)?**
3. **What's the preference UX — settings page, per-notification controls, or both?**
4. **How do we handle preferences for different user types (agent, customer, corporate admin)?**
5. **What are the regulatory requirements for consent management?**

---

## Research Areas

### Preference Model

```typescript
interface NotificationPreferences {
  userId: string;
  userType: 'agent' | 'customer' | 'corporate_admin';
  globalEnabled: boolean;
  channelPreferences: ChannelPreference[];
  categoryPreferences: CategoryPreference[];
  quietHours: QuietHours;
  frequencyLimits: FrequencyLimit[];
}

interface ChannelPreference {
  channel: NotificationChannel;
  enabled: boolean;
  consentStatus: 'explicit' | 'implicit' | 'not_given';
  consentedAt?: Date;
  consentMethod?: string;
}

interface CategoryPreference {
  category: TemplateCategory;
  channels: NotificationChannel[];   // Which channels for this category
  enabled: boolean;
  frequency: 'immediate' | 'daily_digest' | 'weekly_digest' | 'off';
}

interface QuietHours {
  enabled: boolean;
  startTime: string;              // HH:mm in user timezone
  endTime: string;
  timezone: string;
  overrideForCritical: boolean;   // Still send critical alerts
}

interface FrequencyLimit {
  channel: NotificationChannel;
  maxPerHour: number;
  maxPerDay: number;
}
```

### Consent Management

```typescript
interface ConsentRecord {
  userId: string;
  channel: NotificationChannel;
  consentType: 'explicit' | 'implicit';
  grantedAt: Date;
  method: 'checkbox' | 'sms_reply' | 'whatsapp_opt_in' | 'settings_page';
  ipAddress?: string;
  withdrawnAt?: Date;
  withdrawalMethod?: string;
  legalBasis: string;
}
```

**Regulatory consent requirements:**

| Channel | India | EU (GDPR) | US |
|---------|-------|-----------|-----|
| Email | Implied (transactional), opt-in (promo) | Explicit opt-in | CAN-SPAM (opt-out) |
| SMS | DND compliance, opt-in required | Explicit opt-in | TCPA (written consent) |
| WhatsApp | Opt-in via WhatsApp flow | Explicit opt-in | Opt-in required |
| Push | Explicit opt-in | Explicit opt-in | Opt-in implied |

### Preference UX Patterns

**Where to surface controls:**
1. Global settings page (full control)
2. Per-notification "Manage preferences" link (quick context)
3. First-time prompt when enabling a channel
4. Unsubscribe flow (one-click for email, STOP for SMS)
5. Agent admin can set defaults for new customers

---

## Open Problems

1. **Cross-channel preference sync** — Customer opts out of SMS. Should we also disable WhatsApp? Or keep them independent?

2. **Corporate override** — Corporate travel manager may set notification policies that override individual traveler preferences. How to handle conflicts?

3. **Preference discovery** — New users don't know what notification types exist. How to present options without overwhelming?

4. **Quiet hours across timezones** — A traveler in Singapore has different quiet hours than the agent in Mumbai. How to resolve?

5. **Graceful degradation** — If a customer opts out of all channels except in-app, and they never visit the app, critical alerts can't be delivered. Need a minimum-contact policy.

---

## Next Steps

- [ ] Design preference settings page UX
- [ ] Research consent management platforms (OneTrust, Cookiebot)
- [ ] Map regulatory requirements per channel per market
- [ ] Design unsubscribe/opt-out flow per channel
- [ ] Study preference UX patterns from travel apps (Booking.com, Airbnb)
