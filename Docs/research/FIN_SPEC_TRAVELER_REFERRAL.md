# Fin Spec: Agentic 'Traveler-Referral' Engine (FIN-REAL-025)

**Status**: Research/Draft
**Area**: Agency Growth Loops & Referral Management

---

## 1. The Problem: "The Static Referral Program"
Most travel agency referral programs are "Manual" and "Static." A traveler is told "Refer a friend and get $50 off." This fails to capture the "Contextual-Moment-of-Delight" (e.g., right after a successful trip) or the "Influence-Network" of a specific traveler. Without "Agentic-Orchestration," referrals are a missed growth opportunity.

## 2. The Solution: 'Growth-Viral-Loop-Protocol' (GVLP)

The GVLP acts as the "Viral-Growth-Manager."

### Referral Actions:

1.  **High-Moment-Detection**:
    *   **Action**: Identifying the optimal "Moment-of-Delight" to request a referral (e.g., within 24 hours of a traveler posting a positive social media photo or giving a 5-star trip review).
2.  **Network-Influence-Analysis**:
    *   **Action**: Analyzing the traveler's "Social-Graph" (if authorized) to identify "Potential-Referral-Targets" who match the agency's ideal traveler profile.
3.  **Autonomous-Referral-Invite**:
    *   **Action**: Generating and sending a personalized "Referral-Invite" to the traveler, complete with a "Unique-Referral-Link" and a "Dynamic-Incentive" (e.g., "Refer your friend for their Japan trip, and we'll upgrade your own next booking to Business Class").
4.  **Automated-Reward-Payout**:
    *   **Action**: When a referred traveler completes a booking, the agent autonomously validates the referral and triggers the reward payout (e.g., issuing travel credits or updating the loyalty tier) for both the referrer and the referee.

## 3. Data Schema: `Referral_Loop_Event`

```json
{
  "referral_id": "GVLP-88221",
  "referrer_id": "TRAVELER_ALPHA",
  "referee_email_hash": "SHA256_A99221X",
  "referral_incentive": "BUSINESS_CLASS_UPGRADE_TOKEN",
  "referral_status": "REFEREE_BOOKED",
  "payout_status": "REWARD_ISSUED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Privacy-First' Invitation**: The agent MUST NOT scrape the traveler's contacts without explicit, granular consent. The invitation process MUST be traveler-led.
- **Rule 2: Anti-Spam-Guardrail**: The agent MUST limit the frequency and number of referral requests to ensure they don't become a "Nuisance" to the traveler.
- **Rule 3: Success-Based-Issuance**: Rewards MUST only be issued after the referred traveler has made a "Non-Refundable-Booking" or completed their trip, preventing "Referral-Fraud."

## 5. Success Metrics (Referrals)

- **Referral-Conversion-Rate**: % of referral invites that result in a new traveler booking.
- **Viral-Coefficient**: Average number of new travelers acquired per existing traveler through the GVLP.
- **Referral-ROI**: Net revenue generated from referred travelers vs. the total cost of referral incentives.
