# Con Spec: Agentic 'Content-Syndication' Watchdog (CON-REAL-018)

**Status**: Research/Draft
**Area**: Agency Content Distribution & Attribution Integrity

---

## 1. The Problem: "The Content-Fragmentation"
Agencies invest heavily in creating unique travel guides, videos, and photography. However, when this content is shared on social media or syndicated to partner sites, "Attribution-Integrity" is often lost. The content becomes "Fragmented," and the original agency doesn't receive the traffic or the "Brand-Equity" it deserves. Without "Agentic-Distribution," content marketing is inefficient.

## 2. The Solution: 'Content-Distribution-Protocol' (CDP)

The CDP acts as the "Content-Traffic-Controller."

### Distribution Actions:

1.  **Automated-Content-Parsing**:
    *   **Action**: Analyzing new agency content (e.g., a guide on 'Hidden Gems of Lisbon') and autonomously generating "Platform-Specific-Snippets" (e.g., a Twitter thread, an Instagram caption, a LinkedIn summary).
2.  **Attributed-Syndication-Routing**:
    *   **Action**: Distributing these snippets across social platforms and partner networks. Every snippet contains a "Tracking-Link" and "Mandatory-Attribution" (e.g., "Full guide at [Agency Link]").
3.  **Engagement-Reciprocity-Monitor**:
    *   **Action**: Monitoring the performance of syndicated content. If a specific partner site is generating high engagement but low traffic back to the agency, the agent suggests adjusting the "Syndication-Terms."
4.  **Copyright-Protection-Watchdog**:
    *   **Action**: Monitoring the web for "Unauthorized-Syndication" (scraping) of the agency's proprietary content and autonomously issuing "Attribution-Requests" or cease-and-desist alerts.

## 3. Data Schema: `Content_Syndication_Job`

```json
{
  "job_id": "CDP-88221",
  "content_id": "GUIDE-LISBON-001",
  "distribution_channels": ["TWITTER", "INSTAGRAM", "TRAVEL_PARTNER_X"],
  "attribution_integrity_score": 0.98,
  "traffic_referrals_count": 450,
  "status": "SYNDICATION_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Attribution-First' Filter**: The agent MUST NOT syndicate any content without a clear and functional link back to the agency's primary portal.
- **Rule 2: Platform-Optimization**: Content MUST be reformatted to fit the "Social-Norms" of each platform (e.g., don't post a 2000-word guide to Instagram).
- **Rule 3: Revenue-Linkage**: The agent SHOULD prioritize syndicating content that is linked to "High-Margin" itineraries or current agency promotions.

## 5. Success Metrics (Content)

- **Referral-Traffic-Growth**: % increase in website traffic originating from syndicated content.
- **Content-Reach-Multiplier**: Number of unique impressions generated per piece of original content.
- **Attribution-Integrity-Rate**: % of syndicated snippets that maintain correct and clickable agency attribution.
