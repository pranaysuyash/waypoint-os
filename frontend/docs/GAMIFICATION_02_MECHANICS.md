# Gamification — Points, Badges & Leaderboards

> Research document for specific gamification mechanics, design, and implementation.

---

## Key Questions

1. **What actions earn points, and how are point values calibrated?**
2. **What badge categories exist, and what makes a badge meaningful?**
3. **How do leaderboards encourage without demoralizing?**
4. **What's the progression system (levels, tiers)?**
5. **How do we prevent gaming the metrics?**

---

## Research Areas

### Points System

```typescript
interface PointsConfig {
  actions: PointAction[];
  multipliers: PointMultiplier[];
  caps: PointCap[];
}

interface PointAction {
  action: string;
  basePoints: number;
  category: 'quality' | 'speed' | 'volume' | 'learning' | 'collaboration';
  frequency: 'unlimited' | 'daily_cap' | 'weekly_cap' | 'one_time';
  verification: 'automatic' | 'peer_review' | 'manager_approval';
}

// Point calibration:
// Quality-weighted (high points for quality outcomes):
// - Customer gives 5-star review: 50 points
// - Booking completed with zero issues: 30 points
// - Customer rebooks within 90 days: 40 points
//
// Speed (moderate points):
// - First response in <5 min: 15 points
// - Quote delivered in <2 hours: 20 points
// - Spine run reviewed in <30 min: 10 points
//
// Volume (low points per unit, discourages rushing):
// - Booking completed: 10 points
// - Quote generated: 5 points
//
// Learning (encourages development):
// - Complete certification: 100 points
// - Complete training module: 20 points
// - Help a peer (peer confirms): 25 points
//
// Collaboration (team-oriented):
// - Mentor session completed: 30 points
// - Knowledge article contributed: 15 points
// - Escalation handled smoothly: 20 points
```

### Badge System

```typescript
interface Badge {
  badgeId: string;
  name: string;
  description: string;
  icon: string;
  category: BadgeCategory;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  criteria: BadgeCriteria;
  rarity: number;                 // % of agents who have this
  displayOnProfile: boolean;
}

type BadgeCategory =
  | 'expertise'           // Destination expert, cruise specialist
  | 'quality'             // Customer satisfaction, error-free bookings
  | 'speed'               // Fast response times
  | 'learning'            // Certifications, training completion
  | 'milestone'           // 100th booking, 1st year anniversary
  | 'collaboration'       // Mentoring, knowledge sharing
  | 'customer_favorite'   // Most requested agent, repeat customers
  | 'innovation';         // Process improvement, new idea

// Example badges:
// "Singapore Specialist" → Completed 20+ Singapore bookings with 4.5+ CSAT
// "Speed Demon" → Average first response time <3 min for 30 consecutive days
// "Customer Whisperer" → 95%+ positive feedback over 50+ bookings
// "Knowledge Sage" → Written 10+ knowledge articles with 100+ helpful votes
// "Century Club" → 100th successful booking
// "Mentor" → Successfully mentored 3 new agents to certification
// "Zero Defect" → 30 consecutive bookings with zero post-booking issues
```

### Leaderboard Design

```typescript
interface LeaderboardConfig {
  timeframes: ('weekly' | 'monthly' | 'quarterly' | 'all_time')[];
  categories: LeaderboardCategory[];
  visibility: 'public' | 'team_only' | 'self_only';
  anonymizeBelow: number;         // Hide names below rank N
}

interface LeaderboardCategory {
  name: string;
  metric: string;
  direction: 'highest' | 'lowest';  // Lowest for error rate, etc.
}

// Leaderboard principles:
// 1. Show top 10 publicly, rest self-only → avoids public shaming
// 2. Multiple categories → not just "most bookings"
// 3. Rolling timeframes → new agents can compete weekly
// 4. Team leaderboards alongside individual → encourages collaboration
// 5. "Most improved" alongside "best" → recognizes growth

// Categories:
// - Customer satisfaction (CSAT average)
// - Conversion rate (quotes → bookings)
// - Response speed (avg first response)
// - Quality score (error-free rate)
// - Learning progress (certifications earned)
// - Revenue generated (total booking value)
// - Most improved (delta from previous period)
```

### Anti-Gaming Measures

```typescript
interface AntiGamingRule {
  behavior: string;
  detection: string;
  consequence: string;
}

// Examples:
// - Rapid booking/cancellation → points for cancelled bookings are clawed back
// - Quick low-quality responses → CSAT-adjusted points (bad reviews remove points)
// - Cherry-picking easy trips → difficulty multiplier for complex trips
// - Collaboration gaming → peer verification required for mentor points
// - Badge hunting → badges require sustained performance, not one-time actions
```

---

## Open Problems

1. **Points inflation** — Over time, veteran agents accumulate uncatchable point totals. New agents feel they can never compete. Need rolling windows or handicap systems.

2. **Badge fatigue** — Too many badges dilute their value. Need a curated set where each badge feels earned and meaningful.

3. **Intrinsic vs. extrinsic motivation** — Over-reliance on points and badges may crowd out intrinsic motivation (pride in good work). Balance is critical.

4. **Cross-team fairness** — Comparing agents across different specializations (domestic vs. international) is inherently unfair. Need category-specific leaderboards.

---

## Next Steps

- [ ] Design point system with quality-weighted calibration
- [ ] Create initial badge catalog (10-15 meaningful badges)
- [ ] Design leaderboard with privacy and fairness controls
- [ ] Prototype points dashboard in the workbench
- [ ] Pilot with a small team for 4-week trial
