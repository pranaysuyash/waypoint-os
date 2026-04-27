# Loyalty Programs 02: Balance & Earning

> Tracking loyalty balances and earning points

---

## Document Overview

**Focus**: How customers track and earn loyalty points
**Status**: Research Exploration
**Last Updated**: 2026-04-27

---

## Key Questions to Answer

### 1. Account Linking
- How do customers link their loyalty accounts?
- What authentication is required?
- How do we handle multiple accounts per program?
- What about security concerns?

### 2. Balance Tracking
- How do we get current balances?
- How often do we sync?
- How do we show multi-program balances?
- What about transaction history?

### 3. Earning Points
- How do customers earn points through our platform?
- What are the earning rates?
- How do we track pending points?
- What about missing points?

### 4. Tier Status
- How do we track tier status?
- What are the benefits of each tier?
- How do customers maintain status?
- What about status challenges?

---

## Research Areas

### A. Account Linking Flow

**Linking Steps:**

```
1. Customer selects program
2. Customer enters credentials
3. We verify with program
4. Account linked successfully
5. Balance fetched and displayed
```

**Authentication Methods by Program:**

| Program | Auth Method | 2FA? | Notes |
|----------|-------------|------|-------|
| **Most airlines** | Username/password | Sometimes | ? |
| **Some hotels** | Membership number + PIN | Rare | ? |
| **Credit cards** | Card number + details | Sometimes | ? |

**Research:**
- What are the exact auth flows?
- How do we handle 2FA?
- What if customer forgets credentials?

### B. Balance Sync

**Sync Strategies:**

| Strategy | Frequency | Pros | Cons |
|----------|-----------|------|------|
| **Real-time** | On demand | Always current | API limits |
| **Periodic** | Daily/hourly | Efficient | Stale data |
| **Customer-triggered** | Manual | No overhead | Customer effort |
| **Event-based** | On booking | Targeted | May miss activity |

**Data to Sync:**

| Data Point | Availability | Research Needed |
|------------|---------------|-----------------|
| **Current balance** | Most programs | ? |
| **Pending points** | Some programs | ? |
| **Tier status** | Most programs | ? |
| **Transaction history** | Most programs | ? |
| **Expiration dates** | Some programs | ? |

### C. Earning Mechanics

**Earning Through Our Platform:**

| Booking Type | Earning Rate | Pending Period | Notes |
|---------------|--------------|----------------|-------|
| **Flight** | 1-5x spend | Until flown | ? |
| **Hotel** | 5-10x spend | Until stayed | ? |
| **Car rental** | 2-5x spend | Until rented | ? |
| **Activities** | Rare | Until used | ? |

**Earning Calculation:**

```
Base Points = Spend × Earning Rate
Bonus Points = Promotions × Multiplier
Tier Bonus = Status × Bonus Rate
Total Points = Base + Bonus + Tier
```

**Research:**
- What are the actual earning rates?
- How do pending points become available?
- What are the bonus categories?

### D. Tier Status

**Status Levels by Program:**

| Program | Tiers | Benefits | Requirements |
|----------|-------|----------|--------------|
| **Air India** | ? | ? | ? |
| **Vistara** | Silver, Gold, Platinum | ? | ? |
| **Marriott** | Bonvoy, Silver, Gold, Platinum, Titanium | ? | ? |
| **Hilton** | Member, Silver, Gold, Diamond | ? | ? |

**Status Tracking:**

| Metric | What to Track |
|--------|---------------|
| **Current tier** | Status level |
| **Tier points** | Progress to next tier |
| **Tier validity** | When status expires |
| **Qualifying nights/flights** | Activity toward status |

---

## Balance Tracking Data Model

```typescript
interface LoyaltyBalance {
  customerId: string;
  programId: string;
  accountNumber: string;

  // Balances
  balances: {
    available: number;  // Points/miles available
    pending: number;    // Points not yet posted
    expired: number;    // Expired since last sync
    earnedYTD: number;  | Year to date
  };

  // Tier status
  tierStatus: {
    currentTier: string;
    pointsToNextTier: number;
    tierValidUntil: Date;
    qualifyingActivity: QualifyingActivity[];
  };

  // Expiration
  expirations: {
    points: number;
    expiresAt: Date;
  }[];

  // Sync
  lastSync: Date;
  nextSync: Date;
  syncStatus: 'success' | 'failed' | 'pending';
}

interface QualifyingActivity {
  type: 'flight' | 'night' | 'stay';
  count: number;
  required: number;
  periodStart: Date;
  periodEnd: Date;
}
```

---

## Earning Flow

**When Booking:**

```
1. Customer selects "Earn with [Program]"
2. Customer enters account number
3. We pass account to supplier
4. Supplier credits points after service
5. We track expected earning
6. We notify when points post
```

**Tracking Table:**

| Stage | Timing | Action |
|-------|--------|--------|
| **Expected** | At booking | Show estimated earning |
| **Pending** | After booking | Points pending, not yet posted |
| **Posted** | After travel | Points available to spend |

---

## Open Problems

### 1. Credential Security
**Challenge**: Storing loyalty credentials is risky

**Options:**
- Encrypt at rest
- Don't store, ask each time
- Use OAuth where available

**Research**: What are the security best practices?

### 2. Pending Points Uncertainty
**Challenge**: Points may not post as expected

**Questions:**
- How do we track discrepancies?
- What is our liability?
- How do customers claim missing points?

### 3. Multiple Accounts
**Challenge**: Customer has 2 airline accounts

**Options:**
- Link both
- Allow selection
| Merge somehow

### 4. Status Expiration
**Challenge**: Customer loses status

**Options:**
- Warn in advance
- Show progress to re-qualify
| Suggest status runs

---

## Competitor Research Needed

| Competitor | Balance Tracking UX | Notable Patterns |
|------------|---------------------|------------------|
| **AwardWallet** | ? | ? |
| **UsingMiles** | ? | ? |

---

## Experiments to Run

1. **Link success rate test**: What % of links succeed?
2. **Sync accuracy test**: Are balances accurate?
3. **Earning tracking test**: Do points post as expected?
4. **Security audit**: Are credentials safe?

---

## References

- [Flight Integration - Pricing](./FLIGHT_INTEGRATION_03_PRICING.md) — Earning mechanics
| [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Hotel earning

---

## Next Steps

1. Design account linking flow
2. Implement balance sync
3. Build earning tracking
4. Create status dashboard
5. Implement expiration alerts

---

**Status**: Research Phase — Balance tracking unknown

**Last Updated**: 2026-04-27
