# Agent Training — Progress Tracking & Certification

> Research document for tracking agent learning progress, skill development, and certification.

---

## Key Questions

1. **What competencies must be tracked per agent role?**
2. **How do we visualize agent progress for the agent, mentor, and manager?**
3. **What certification levels exist, and what are the criteria for each?**
4. **How do we handle skill decay — agents who don't use a skill for months?**
5. **What's the relationship between training progress and booking permissions?**

---

## Research Areas

### Competency Framework

```typescript
interface AgentCompetency {
  competencyId: string;
  domain: KnowledgeDomain;
  name: string;
  description: string;
  levels: CompetencyLevel[];
  assessmentIds: string[];
}

interface CompetencyLevel {
  level: number;
  name: string;                  // "Beginner", "Proficient", "Expert"
  description: string;
  criteria: string[];
  permissionsGranted: string[];  // What this level unlocks
  bookingTypesAllowed: string[];
}

interface AgentProgress {
  agentId: string;
  role: AgentRole;
  competencies: CompetencyProgress[];
  certifications: Certification[];
  learningHistory: LearningEvent[];
  mentorId: string;
  onboardingPhase: string;
  overallReadiness: number;      // 0-100
}

interface CompetencyProgress {
  competencyId: string;
  currentLevel: number;
  targetLevel: number;
  assessmentsCompleted: AssessmentResult[];
  practicalHours: number;
  lastPracticed: Date;
  status: 'not_started' | 'in_progress' | 'achieved' | 'expired';
}
```

### Certification System

```typescript
interface Certification {
  certificationId: string;
  name: string;
  type: CertificationType;
  requirements: CertificationRequirement[];
  validFor: string;
  privileges: string[];
}

type CertificationType =
  | 'domestic_travel'       // Can handle India trips
  | 'international_travel'  // Can handle international trips
  | 'corporate_travel'      // Can handle B2B/corporate
  | 'cruise_specialist'     // Can book cruises
  | 'mice_specialist'       // Can handle MICE events
  | 'luxury_travel'         // Can handle premium/luxury
  | 'gds_certified'         // GDS booking proficiency
  | 'senior_agent'          // Can handle complex/escalated
  | 'team_lead';            // Can manage other agents

interface CertificationRequirement {
  type: 'assessment_score' | 'practical_hours' | 'booking_count' | 'peer_review' | 'mentor_approval';
  target: number;
  current: number;
  evidence: string[];
}
```

### Skill Decay & Refreshers

```typescript
interface SkillDecayTracker {
  skillId: string;
  agentId: string;
  lastUsed: Date;
  decayThreshold: string;        // E.g., "6_months"
  status: 'active' | 'decaying' | 'expired';
  refresherAssigned: boolean;
}

// Decay rules:
// - Skill not used in 3 months → flag for refresher
// - Skill not used in 6 months → require reassessment
// - Regulatory knowledge (visa, compliance) → annual refresher mandatory
// - System knowledge (platform updates) → refresher on each release
```

### Progress Dashboard

```typescript
interface AgentDashboard {
  agentId: string;
  // Overall progress
  onboardingPercentComplete: number;
  currentPhase: string;
  daysInOnboarding: number;
  targetCompletionDate: Date;
  // Competency radar chart
  competencyScores: Record<string, number>;
  // Recent activity
  recentLearning: LearningEvent[];
  upcomingDeadlines: Deadline[];
  // Certifications
  activeCertifications: Certification[];
  expiringCertifications: Certification[];
  pendingCertifications: Certification[];
  // Recommendations
  recommendedNext: string[];
}
```

---

## Open Problems

1. **Measuring practical competence** — Written tests are easy to assess; practical booking skill is harder. Need rubrics for real-world evaluation.

2. **Permission gating** — Tying booking permissions to certifications creates a safety net but can frustrate agents who feel ready before completing all requirements.

3. **Subjective assessment** — "Customer communication quality" is subjective. Need calibrated rubrics that multiple assessors can apply consistently.

4. **Certification inflation** — If every booking type requires a certification, agents spend more time certifying than booking. Need to balance safety with velocity.

5. **Cross-training incentives** — How to incentivize agents to develop skills beyond their primary role without mandating it.

---

## Next Steps

- [ ] Design competency framework for junior and senior agent roles
- [ ] Build certification requirement matrix for booking permissions
- [ ] Design agent progress dashboard UI
- [ ] Create skill decay detection and refresher assignment system
- [ ] Study gamification patterns for learning engagement (badges, leaderboards)
