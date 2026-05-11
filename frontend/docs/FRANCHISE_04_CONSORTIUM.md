# Agency Network & Franchise Management 04: Consortium Model

> Research document for consortium models for independent travel agencies, shared inventory pooling, joint marketing, revenue sharing, consortium governance, B2B marketplace, mutual referral systems, and legal structures for the Indian travel market.

---

## Key Questions

1. **How does a consortium differ from a franchise, and when is it the right model?**
2. **How do independent agencies pool inventory without surrendering autonomy?**
3. **What joint marketing strategies work for a consortium of diverse agencies?**
4. **How does revenue sharing work when agencies collaborate on bookings?**
5. **What governance model balances consortium benefits with member independence?**
6. **What does a B2B marketplace between consortium members look like?**
7. **How does a mutual referral system drive incremental revenue?**
8. **What legal structures work for Indian travel consortiums?**

---

## Research Areas

### A. Consortium Model Overview

```typescript
interface TravelConsortium {
  consortiumId: string;
  name: string;                         // "India Travel Alliance"
  establishedDate: Date;
  members: ConsortiumMember[];
  governance: ConsortiumGovernance;
  sharedResources: SharedResources;
  membershipTiers: MembershipTier[];
  legalStructure: ConsortiumLegalStructure;
}

// Consortium vs. Franchise comparison:
//
// ┌───────────────────┬─────────────────────┬──────────────────────────┐
// │ Aspect            │ Franchise            │ Consortium                │
// ├───────────────────┼─────────────────────┼──────────────────────────┤
// │ Brand             │ Franchisor's brand   │ Each keeps own brand      │
// │ Control           │ High (franchisor)    │ Low (member autonomy)     │
// │ Cost              │ High (royalty + fees)│ Low (membership fee)      │
// │ Entry barrier     │ Strict qualification │ Moderate                  │
// │ Exit              │ Contract-bound       │ Flexible (notice period)  │
// │ Supplier deals    │ Negotiated by HQ     │ Pooled negotiation        │
// │ Technology        │ Mandated platform    │ Shared tools + own tools  │
// │ Customer data     │ Franchisor owns      │ Each agency owns          │
// │ Best for          │ New entrants, brand   │ Established independents  │
// │                   │ leverage             │ seeking scale benefits    │
// └───────────────────┴─────────────────────┴──────────────────────────┘
//
// When to choose consortium:
// - Established agency with own brand and loyal customer base
// - Wants supplier bargaining power without losing independence
// - Happy with own operations but needs technology upgrade
// - Seeks peer network for knowledge sharing and referrals
// - Cannot or will not pay franchise royalties
// - Values flexibility to enter/exit alliance
//
// Indian consortium examples:
// - TAFI (Travel Agents Federation of India) — Industry body with consortium features
// - IATO (Indian Association of Tour Operators) — Inbound tour operator alliance
// - ADTOI (Association of Domestic Tour Operators of India) — Domestic focus
// - OTAs with offline agent networks (MakeMyTrip, Cleartrip partner programs)

interface ConsortiumMember {
  memberId: string;
  consortiumId: string;
  agencyId: string;
  agencyName: string;                   // Retains own brand
  membershipTier: string;
  joinedDate: Date;
  territory: MemberTerritory;
  specializations: string[];            // ["Kerala", "Honeymoon", "Adventure"]
  capabilities: MemberCapability[];
  standing: MemberStanding;
}

interface MemberTerritory {
  primaryCity: string;
  primaryState: string;
  serviceArea: string[];                // Pin codes or cities
  exclusivityGranted: boolean;          // Exclusive in territory?
  overlapsWith: string[];               // Other members in same area
}

type MemberStanding =
  | 'active'
  | 'probation'                         // Performance below threshold
  | 'suspended'                         // Violation of consortium rules
  | 'resigned'                          // Voluntary exit
  | 'expelled';                         // Removed by consortium
```

### B. Membership Tiers & Fees

```typescript
interface MembershipTier {
  tierId: string;
  name: string;                         // "Silver", "Gold", "Platinum"
  annualFee: Money;
  benefits: TierBenefit[];
  requirements: TierRequirement[];
  memberCount: number;
}

// Membership tier structure:
//
// ┌──────────────┬────────────┬────────────┬──────────────────────┐
// │ Tier         │ Annual Fee │ Revenue    │ Key Benefits          │
// │              │            │ Commitment │                       │
// ├──────────────┼────────────┼────────────┼──────────────────────┤
// │ Silver       │ ₹25,000    │ None       │ - Shared supplier     │
// │              │            │            │   rates (basic)       │
// │              │            │            │ - Referral network    │
// │              │            │            │   access              │
// │              │            │            │ - Monthly newsletter  │
// │              │            │            │ - Basic training (2   │
// │              │            │            │   modules/year)       │
// ├──────────────┼────────────┼────────────┼──────────────────────┤
// │ Gold         │ ₹75,000    │ ₹15L/year │ - All Silver benefits │
// │              │            │            │ - Preferred supplier  │
// │              │            │            │   rates (negotiated)  │
// │              │            │            │ - Shared inventory    │
// │              │            │            │   pool access         │
// │              │            │            │ - Joint marketing     │
// │              │            │            │   campaigns           │
// │              │            │            │ - Full training       │
// │              │            │            │   access              │
// │              │            │            │ - B2B marketplace     │
// │              │            │            │   listing             │
// ├──────────────┼────────────┼────────────┼──────────────────────┤
// │ Platinum     │ ₹2,00,000  │ ₹50L/year │ - All Gold benefits   │
// │              │            │            │ - Exclusive supplier  │
// │              │            │            │   contracts           │
// │              │            │            │ - Consortium board    │
// │              │            │            │   voting rights       │
// │              │            │            │ - Premium inventory   │
// │              │            │            │   allocation          │
// │              │            │            │ - Co-branded marketing│
// │              │            │            │   materials           │
// │              │            │            │ - Dedicated support   │
// │              │            │            │   manager             │
// │              │            │            │ - Technology priority │
// └──────────────┴────────────┴────────────┴──────────────────────┘
```

### C. Shared Inventory Pooling

```typescript
interface InventoryPool {
  poolId: string;
  consortiumId: string;
  accessTier: 'silver' | 'gold' | 'platinum';
  hotelAllotments: PooledHotelAllotment[];
  groupTourInventory: PooledGroupTour[];
  contractedRates: PooledContractedRate[];
  surplusInventory: SurplusListing[];
}

interface PooledHotelAllotment {
  hotelId: string;
  hotelName: string;
  destination: string;
  roomType: string;
  season: string;
  totalAllotted: number;                // Rooms consortium controls
  contributingMembers: ContributorDetail[];
  bookingRules: PoolBookingRule[];
}

interface ContributorDetail {
  memberId: string;
  roomsContributed: number;             // Rooms this member committed to
  roomsConsumed: number;                // Rooms this member booked
  netPosition: number;                  // Contributed - Consumed
}

interface PoolBookingRule {
  ruleId: string;
  tier: string;                         // Which tier can access
  advanceBookingDays: number;           // Min days before check-in
  maxRoomsPerBooking: number;
  releaseBackDays: number;              // Unused rooms released N days before
  priorityAlgorithm: PriorityAlgorithm;
}

type PriorityAlgorithm =
  | 'first_come_first_served'           // Simple booking order
  | 'tier_priority'                     // Platinum > Gold > Silver
  | 'contribution_weighted'             // More contribution = more priority
  | 'rotational';                       // Fair rotation among members

// Inventory pool example:
//
// India Travel Alliance — Goa December 2026 Pool
//
// ┌──────────────────────┬───────────┬───────────┬───────────┐
// │ Hotel                │ Rooms     │ Rate      │ vs. Rack  │
// ├──────────────────────┼───────────┼───────────┼───────────┤
// │ Taj Fort Aguada      │ 30 rooms  │ ₹12,500   │ 40% off   │
// │ Grand Hyatt          │ 25 rooms  │ ₹9,800    │ 35% off   │
// │ Holiday Inn Resort   │ 40 rooms  │ ₹6,500    │ 30% off   │
// │ Novotel Dona Sylvia  │ 20 rooms  │ ₹5,800    │ 32% off   │
// └──────────────────────┴───────────┴───────────┴───────────┘
//
// Contributor breakdown (Taj Fort Aguada):
// ┌──────────────────────┬───────────┬───────────┬───────────┐
// │ Member               │ Contrib.  │ Consumed  │ Net Pos.  │
// ├──────────────────────┼───────────┼───────────┼───────────┤
// │ Delhi Travel Co.     │ 10 rooms  │ 8 rooms   │ +2        │
// │ Mumbai Holidays      │ 8 rooms   │ 10 rooms  │ -2        │
// │ Kerala Tours (Plat.) │ 5 rooms   │ 4 rooms   │ +1        │
// │ Chennai Travels      │ 4 rooms   │ 3 rooms   │ +1        │
// │ Overflow (open)      │ 3 rooms   │ 1 room    │ +2        │
// ├──────────────────────┼───────────┼───────────┼───────────┤
// │ TOTAL                │ 30 rooms  │ 26 rooms  │ +4        │
// └──────────────────────┴───────────┴───────────┴───────────┘
// Release: Unused rooms released back to hotel on Dec 10 (14 days prior)
// Settlement: Members settle net positions quarterly

interface SurplusListing {
  listingId: string;
  memberId: string;
  type: 'hotel_rooms' | 'group_seats' | 'transfer_slots' | 'activity_slots';
  details: SurplusDetail;
  offeredTo: string;                    // 'all_members' | 'gold_above' | 'platinum_only'
  price: Money;
  validUntil: Date;
  status: 'available' | 'claimed' | 'expired';
}

// Surplus inventory marketplace:
//
// Member Kerala Tours has 3 unused houseboat nights (Dec 20-22)
// They list on consortium surplus board:
//   - Type: Houseboat nights (Premium AC)
//   - Rate: ₹8,000/night (cost: ₹10,000, loss mitigation)
//   - Available to: Gold and Platinum members
//   - Valid until: Dec 15
//   - First to claim gets it
```

### D. Joint Marketing & Revenue Sharing

```typescript
interface JointMarketing {
  consortiumId: string;
  campaigns: MarketingCampaign[];
  coBranding: CoBrandingConfig;
  costSharing: MarketingCostShare;
}

interface MarketingCampaign {
  campaignId: string;
  name: string;                         // "Summer Kerala 2027"
  type: CampaignType;
  budget: Money;
  contributingMembers: CampaignContributor[];
  leads: CampaignLead[];
  performance: CampaignPerformance;
}

type CampaignType =
  | 'digital_ads'                       // Google, Meta, YouTube ads
  | 'trade_show'                        // TTF, SATTE, OTM
  | 'print_media'                       // Newspaper, magazine
  | 'social_media'                      // Instagram, Facebook
  | 'email_campaign'                    // Joint email blast
  | 'influencer'                        // Travel influencer collaboration
  | 'content_marketing';                // Blog posts, destination guides

// Revenue sharing models:
//
// MODEL 1: Referral Fee (Simple)
// ┌──────────┐  refers    ┌──────────┐  books    ┌──────────┐
// │ Member A │──────────>│ Member B │─────────>│ Customer │
// │ (Kerala  │           │ (Goa     │          │          │
// │  expert) │           │  expert) │          │          │
// └──────────┘           └──────────┘          └──────────┘
//
// Customer from Mumbai wants Kerala + Goa trip
// Mumbai agent (A) refers Kerala leg to Kerala expert (B)
// Revenue split:
//   Member B does Kerala: Full margin on Kerala portion
//   Member A gets referral: 5% of Kerala booking value
//   Consortium fee: 1% of referral value
//
// MODEL 2: Joint Package (Collaborative)
// ┌──────────┐            ┌──────────┐
// │ Member A │  co-creates│ Member B │
// │ (Delhi)  │──────────>│ (Kerala)  │
// └──────────┘           └──────────┘
//
// "Golden Triangle + Kerala" package (₹1,20,000)
// Delhi member handles: Golden Triangle (flights, hotels, transfers)
// Kerala member handles: Kerala portion (houseboat, Munnar, Cochin)
//
// Revenue split (pre-agreed):
//   Delhi member share: ₹55,000 (Golden Triangle costs + margin)
//   Kerala member share: ₹50,000 (Kerala costs + margin)
//   Consortium marketing fund: ₹1,200 (1%)
//   Remaining (joint margin): ₹13,800 split 50/50
//
// MODEL 3: Lead Sharing (Marketplace)
// ┌──────────┐  lists lead ┌──────────┐  claims    ┌──────────┐
// │ Member A │──────────>│ B2B      │──────────>│ Member C │
// │          │            │Marketplace│            │          │
// └──────────┘            └──────────┘            └──────────┘
//
// Member A gets a corporate lead (Mumbai company, 50 pax offsite in Goa)
// A doesn't handle corporate groups, lists on consortium marketplace
// Member C (Goa corporate specialist) claims and services the lead
//
// Revenue split:
//   Member C: Full margin on the booking
//   Member A: 3% finder's fee (lead source)
//   Consortium: 0.5% platform fee

interface RevenueShareRule {
  ruleId: string;
  collaborationType: string;
  sourceShare: number;                  // Percentage for referring member
  executorShare: number;                // Percentage for executing member
  consortiumFee: number;                // Percentage for consortium
  settlementFrequency: 'per_booking' | 'monthly' | 'quarterly';
}
```

### E. Consortium Governance

```typescript
interface ConsortiumGovernance {
  consortiumId: string;
  governanceType: 'democratic' | 'weighted_voting' | 'board_led';
  board: ConsortiumBoard;
  voting: VotingSystem;
  policies: ConsortiumPolicy[];
  disputeResolution: ConsortiumDisputeResolution;
}

interface ConsortiumBoard {
  members: BoardMember[];
  electionCycle: string;                // "annual", "biennial"
  nextElection: Date;
  roles: BoardRole[];
}

// Democratic governance structure:
//
// ┌──────────────────────────────────────────────────────────┐
// │ GENERAL BODY (All Members)                                │
// │ - Annual general meeting (AGM)                           │
// │ - Vote on major decisions (fee changes, policy)          │
// │ - Elect board members                                    │
// │ - Approve annual budget                                  │
// ├──────────────────────────────────────────────────────────┤
// │ EXECUTIVE BOARD (5-7 Members)                             │
// │ - Chairperson (elected by general body)                  │
// │ - Vice Chair                                             │
// │ - Treasurer (financial oversight)                        │
// │ - Secretary (operations)                                 │
// │ - 2-3 Board Members (representing regions/categories)    │
// │ - Meets monthly, decides operational matters             │
// ├──────────────────────────────────────────────────────────┤
// │ COMMITTEES                                                │
// │ - Supplier Negotiation Committee                         │
// │ - Marketing Committee                                    │
// │ - Technology Committee                                   │
// │ - Membership & Ethics Committee                          │
// │ - Finance & Audit Committee                              │
// └──────────────────────────────────────────────────────────┘

interface VotingSystem {
  votingType: VotingType;
  quorumPercentage: number;             // Minimum participation for valid vote
  passingThreshold: number;             // Percentage needed to pass
}

type VotingType =
  | 'one_member_one_vote'               // Equal votes regardless of size
  | 'weighted_by_revenue'               // Higher revenue = more votes
  | 'weighted_by_tier'                  // Platinum > Gold > Silver
  | 'hybrid';                           // Base votes + tier bonus

// Voting weight example (hybrid):
// Base: 1 vote per member
// Gold bonus: +1 vote (total 2)
// Platinum bonus: +2 votes (total 3)
// Revenue bonus: +1 vote per ₹50L annual contribution (max +3)
//
// Member A (Silver, ₹12L revenue): 1 vote
// Member B (Gold, ₹35L revenue): 2 votes
// Member C (Platinum, ₹80L revenue): 3 + 1 = 4 votes
// Member D (Platinum, ₹1.2Cr revenue): 3 + 2 = 5 votes
// Total votes: 12. Simple majority: 7 votes needed.
```

### F. B2B Marketplace

```typescript
interface B2BMarketplace {
  marketplaceId: string;
  consortiumId: string;
  listings: B2BListing[];
  categories: MarketplaceCategory[];
  transactions: B2BTransaction[];
  ratings: MemberRating[];
}

type MarketplaceCategory =
  | 'surplus_inventory'                 // Unsold hotel rooms, seats
  | 'leads'                             // Customer leads for sale
  | 'services'                          // Visa processing, forex, insurance
  | 'packages'                          // Pre-built itineraries
  | 'specialists'                       // Expert agents for hire
  | 'supplier_deals';                   // Expiring supplier deals

interface B2BListing {
  listingId: string;
  sellerMemberId: string;
  category: MarketplaceCategory;
  title: string;
  description: string;
  pricing: ListingPricing;
  availability: ListingAvailability;
  visibility: 'all_members' | 'tier_restricted';
  createdAt: Date;
  expiresAt: Date;
  status: ListingStatus;
}

// B2B marketplace UI (ASCII mockup):
//
// ┌───────────────────────────────────────────────────────────┐
// │ INDIA TRAVEL ALLIANCE — B2B Marketplace                   │
// ├───────────────────────────────────────────────────────────┤
// │ [Inventory] [Leads] [Services] [Packages] [Specialists]  │
// ├───────────────────────────────────────────────────────────┤
// │                                                           │
// │ ┌─── SURPLUS INVENTORY ─────────────────────────────────┐│
// │ │ Goa Dec 20-25: 3 rooms @ ₹6,500/night               ││
// │ │ Seller: Kerala Tours (Platinum)                       ││
// │ │ Rating: ★★★★☆ (4.2)  │  Posted: 2 hours ago         ││
// │ │ [Claim]                                               ││
// │ └────────────────────────────────────────────────────────┘│
// │                                                           │
// │ ┌─── LEADS ─────────────────────────────────────────────┐│
// │ │ Corporate offsite: 50 pax, Goa, Jan 2027              ││
// │ │ Budget: ₹15L  │  Source: Mumbai Holidays (Gold)       ││
// │ │ Finder's fee: 3% (₹45,000)                           ││
// │ │ Rating: ★★★★★ (4.8)  │  Posted: 1 day ago           ││
// │ │ [Claim Lead]                                          ││
// │ └────────────────────────────────────────────────────────┘│
// │                                                           │
// │ ┌─── SPECIALIST AVAILABLE ──────────────────────────────┐│
// │ │ Visa expert: Europe Schengen, 10+ years experience    ││
// │ │ Rate: ₹2,000/visa application                        ││
// │ │ Seller: Delhi Travel Co. (Gold)                       ││
// │ │ Rating: ★★★★★ (4.9)  │  Capacity: 20/month          ││
// │ │ [Book Service]                                        ││
// │ └────────────────────────────────────────────────────────┘│
// └───────────────────────────────────────────────────────────┘

interface B2BTransaction {
  transactionId: string;
  buyerMemberId: string;
  sellerMemberId: string;
  listingId: string;
  type: TransactionType;
  amount: Money;
  consortiumFee: Money;                 // Platform fee
  settlementStatus: SettlementStatus;
  ratings: TransactionRating;
}

type TransactionType =
  | 'inventory_purchase'                // Buying surplus rooms/seats
  | 'lead_purchase'                     // Buying a customer lead
  | 'service_engagement'                // Hiring specialist
  | 'package_resale'                    // Reselling packaged itinerary
  | 'referral_fee';                     // Referral commission settlement
```

### G. Mutual Referral System

```typescript
interface ReferralSystem {
  consortiumId: string;
  referralRules: ReferralRule[];
  referralTracking: ReferralTracking[];
  settlement: ReferralSettlement[];
}

interface ReferralRule {
  ruleId: string;
  category: string;                     // "Kerala", "Corporate", "Honeymoon"
  referralFeePercent: number;           // % of booking value
  minimumBookingValue: Money;
  validityDays: number;                 // Referral valid for N days
  attributionWindow: number;            // Days after referral for credit
}

// Referral flow:
//
// STEP 1: Customer inquiry
// Mumbai Holidays receives inquiry for Ladakh adventure trip
// Mumbai agent checks consortium specialist directory
// Finds "Ladakh Adventures" (Member, Delhi, adventure specialist)
//
// STEP 2: Referral creation
// Mumbai agent creates referral in platform:
//   - Customer: Priya Patel (consent given for referral)
//   - Category: Adventure / Ladakh
//   - Budget: ₹1,50,000 (2 pax)
//   - Notes: "Experienced trekkers, want Markha Valley + Pangong"
//   - Referral fee rule: 5% of booking value
//
// STEP 3: Referral acceptance
// Ladakh Adventures receives referral notification
// Reviews customer profile and requirements
// Accepts referral (commits to 5% fee on successful booking)
// Or declines (no fee, referral expires)
//
// STEP 4: Service delivery
// Ladakh Adventures services the customer directly
// Mumbai agent copied on key communications (optional)
// Customer receives itinerary from Ladakh Adventures
//
// STEP 5: Booking & settlement
// Customer confirms booking: ₹1,45,000
// Platform tracks: Referral from Mumbai → Booked by Ladakh Adventures
// Settlement:
//   Ladakh Adventures: ₹1,45,000 revenue
//   Mumbai Holidays: ₹7,250 referral fee (5%)
//   Consortium: ₹725 platform fee (0.5%)
//   Settlement: Monthly batch (netted against other referrals)
//
// Mutual referral network visualization:
//
// ┌──────────┐  Ladakh referral   ┌──────────┐
// │ Mumbai   │──────────────────>│ Delhi    │
// │ Holidays │                    │ Ladakh   │
// │          │<────── Kerala ────│ Adv.     │
// │          │  referral          │          │
// └────┬─────┘                    └────┬─────┘
//      │                               │
//      │ Goa referral                  │ Corporate referral
//      v                               v
// ┌──────────┐                    ┌──────────┐
// │ Goa      │  Gujarat referral  │ Chennai  │
// │ Expert   │──────────────────>│ Travels  │
// │          │                    │          │
// │          │<── Visa referral ──│          │
// └──────────┘                    └──────────┘
//
// Net settlement (monthly):
// Mumbai owes Delhi: ₹7,250 (Ladakh referral)
// Delhi owes Mumbai: ₹5,500 (Kerala referral)
// Mumbai owes Goa: ₹4,000 (Goa referral)
// Chennai owes Delhi: ₹6,000 (Corporate referral)
// Delhi owes Chennai: ₹2,000 (Visa referral)
//
// Net positions after settlement:
// Mumbai pays: ₹7,250 + ₹4,000 - ₹5,500 = ₹5,750
// Delhi receives: ₹7,250 + ₹6,000 - ₹5,500 - ₹2,000 = ₹5,750
// Goa receives: ₹4,000
// Chennai receives: ₹2,000, pays: ₹6,000, net: -₹4,000

interface ReferralSettlement {
  settlementId: string;
  period: string;                       // "2026-11"
  memberId: string;
  referralsGiven: number;
  referralsReceived: number;
  grossOwed: Money;                     // What this member owes others
  grossOwing: Money;                    // What others owe this member
  netPosition: Money;                   // Positive = receiving, Negative = paying
  transactions: SettlementTransaction[];
  status: 'pending' | 'confirmed' | 'settled';
}
```

### H. Legal Structures for Indian Travel Consortium

```typescript
interface ConsortiumLegalStructure {
  consortiumId: string;
  legalEntityType: ConsortiumLegalType;
  registration: LegalRegistration;
  compliance: LegalCompliance[];
  agreements: ConsortiumAgreement[];
}

type ConsortiumLegalType =
  | 'society_registration'              // Under Societies Registration Act 1860
  | 'section_8_company'                 // Non-profit company under Companies Act
  | 'trust'                             // Under Indian Trusts Act
  | 'llp'                               // Limited Liability Partnership
  | 'informal_alliance';                // No legal entity (contractual only)

// Legal structure comparison for Indian travel consortium:
//
// ┌──────────────────┬────────────┬────────────┬────────────┬────────────┐
// │ Aspect           │ Society    │ Sec 8 Co.  │ LLP        │ Informal   │
// ├──────────────────┼────────────┼────────────┼────────────┼────────────┤
// │ Registration     │ State      │ MCA (ROC)  │ MCA (ROC)  │ None       │
// │                  │ Registrar  │            │            │            │
// │ Cost to setup    │ ₹5-15K     │ ₹20-50K    │ ₹15-30K    │ ₹0         │
// │ Min. members     │ 7          │ 2 directors│ 2 partners │ None       │
// │ Profit motive    │ No         │ No         │ Yes        │ N/A        │
// │ Tax exemption    │ Possible   │ Possible   │ No         │ N/A        │
// │ Liability        │ Limited    │ Limited    │ Limited    │ Unlimited  │
// │ Governance       │ Bye-laws   │ MOA/AOA    │ LLP Agree. │ Contract   │
// │ Bank account     │ Yes        │ Yes        │ Yes        │ Individual │
// │ Property holding │ Yes        │ Yes        │ Yes        │ No         │
// │ Contracts        │ Yes        │ Yes        │ Yes        │ Individual │
// │ Recommended?     │ ★★★★       │ ★★★★★      │ ★★★        │ ★★         │
// └──────────────────┴────────────┴────────────┴────────────┴────────────┘
//
// RECOMMENDED: Section 8 Company
// Why:
// 1. Professional governance structure (board, AGM, audited accounts)
// 2. Can hold property, sign contracts, open bank account
// 3. Limited liability for members
// 4. Possible tax exemption on membership fees (if non-profit activity)
// 5. Credible structure for supplier negotiations
// 6. Recognized legal entity for GST registration
// 7. Can operate B2B marketplace legally
//
// India-specific compliance:
//
// 1. GST Registration:
//    - Consortium entity needs own GST if annual turnover > ₹20L
//    - Membership fees: Taxable at 18% GST
//    - Marketplace fees: Taxable at 18% GST
//    - Referral fees: Taxable at 18% GST
//    - Input tax credit available on consortium expenses
//
// 2. Income Tax:
//    - Section 8 company: Tax-exempt if conditions met
//    - Society: Tax-exempt under Section 11/12 if registered u/s 12AA
//    - LLP: Normal tax rate (30% + surcharge)
//    - TDS: Consortium must deduct TDS on payments to members
//
// 3. RBI / FEMA (if international members):
//    - Foreign travel agencies joining consortium
//    - International supplier deals through consortium
//    - Inbound tour operator membership
//    - Outbound referral fees to international partners
//
// 4. Competition Act Compliance:
//    - Price fixing: Consortium cannot mandate selling prices
//    - Market allocation: Territory exclusivity within consortium is risky
//    - Bid rigging: Members cannot coordinate bids for same corporate client
//    - Collective bargaining: Negotiating with suppliers is generally OK
//    - Must file CCI notification if consortium exceeds thresholds
//
// 5. Consumer Protection:
//    - Consortium is not liable for individual member's service
//    - But consumer can approach consortium for redressal
//    - Need clear disclaimers in customer-facing communication
//    - "Member of [Consortium]" is not endorsement of service quality

interface ConsortiumAgreement {
  agreementId: string;
  type: AgreementType;
  parties: string[];                    // Member IDs or "all_members"
  executedDate: Date;
  expiryDate: Date;
  terms: AgreementTerms;
}

type AgreementType =
  | 'membership_agreement'              // Terms of consortium membership
  | 'referral_protocol'                 // How referrals work
  | 'revenue_sharing'                   // Revenue sharing terms
  | 'ip_sharing'                        // Shared marketing content
  | 'non_disclosure'                    // NDA between members
  | 'data_sharing'                      // What data is shared
  | 'dispute_resolution'               // How inter-member disputes handled
  | 'supplier_joint_contract';         // Joint supplier agreement
```

---

## Open Problems

### 1. Trust Without Central Authority
Consortium members are independent businesses. There is no franchisor to enforce rules. Building trust for inventory sharing, referral payments, and collaborative selling requires transparent tracking, automated settlement, and a reputation system. Without it, members will distrust the system and revert to bilateral relationships.

### 2. Inventory Pooling Risk
Members who contribute to pooled inventory bear the financial risk. If the pool cannot sell the committed rooms, the contributing member eats the cost. Need risk-sharing mechanisms (pool insurance, cost absorption rules, flexible commitment windows) to encourage participation.

### 3. Data Sharing Boundaries
Customer data is the crown jewel for independent agencies. Members will resist sharing customer details through referral systems. The platform needs a "blind referral" mode where customer identity is revealed only after the receiving member commits to the referral fee and the customer consents.

### 4. Settlement Complexity
With 50+ members making referrals, sharing inventory, and splitting revenue, the net settlement calculation is a complex graph problem. Monthly netting reduces transaction volume, but edge cases (member exit mid-period, disputed referrals, partial cancellations) make it non-trivial.

### 5. Competition Law Risk
Indian Competition Commission has become active. A consortium that negotiates collectively, shares territory, or coordinates pricing risks enforcement action. The legal structure and operating protocols must be designed with competition law compliance from day one, not retrofitted.

---

## Next Steps

1. **Design consortium member onboarding** — Lightweight onboarding flow (vs. franchise heavy process) with verification, membership tier selection, and capability profiling
2. **Build B2B marketplace prototype** — Surplus inventory listings, lead marketplace, specialist directory with rating system and automated settlement
3. **Design referral tracking engine** — End-to-end referral lifecycle: create, accept/reject, service, settle — with blind referral mode for data privacy
4. **Research Section 8 company formation** — Draft MOA/AOA for a travel consortium Section 8 company, consult with corporate lawyer on Competition Act compliance
5. **Model settlement graph algorithm** — Design the netting algorithm for multi-party settlements, test with simulated consortium of 20+ members
6. **Study existing Indian consortium models** — Interview TAFI, IATO members on real governance challenges, fee structures, and technology gaps
7. **Prototype shared inventory pool UI** — Member-facing view of pooled inventory with contribution tracking, booking rules, and release schedules

---

**Series:** Agency Network & Franchise Management
**Document:** 4 of 4 (Consortium Model)
**Last Updated:** 2026-04-28
**Status:** Research Exploration
