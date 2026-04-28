# Agent Training — Mentorship & Peer Learning

> Research document for mentorship programs, peer learning, and knowledge transfer.

---

## Key Questions

1. **How do we match mentors with mentees effectively?**
2. **What's the mentor workload, and how do we compensate it?**
3. **What structured activities work for mentor-mentee sessions?**
4. **How do we measure mentorship effectiveness?**
5. **What peer learning mechanisms work in a travel agency environment?**

---

## Research Areas

### Mentorship Model

```typescript
interface MentorshipProgram {
  programId: string;
  menteeId: string;
  mentorId: string;
  startDate: Date;
  targetEndDate: Date;
  objectives: MentorshipObjective[];
  schedule: MentorshipSchedule;
  status: 'active' | 'completed' | 'paused' | 'terminated';
}

interface MentorshipObjective {
  objective: string;
  targetDate: Date;
  status: 'pending' | 'in_progress' | 'achieved';
  evidence: string[];
}

interface MentorshipSchedule {
  frequency: 'weekly' | 'biweekly';
  durationMinutes: number;
  format: 'in_person' | 'video' | 'hybrid';
  recurringDay: string;
}

// Mentor selection criteria:
// - Minimum 1 year experience
// - Above-average customer satisfaction scores
// - Completion of mentor training
// - Capacity (max 2 mentees simultaneously)
// - Domain expertise relevant to mentee's role
```

### Structured Mentorship Activities

```typescript
type MentorshipActivity =
  | 'shadow_session'          // Mentee observes mentor handling real bookings
  | 'reverse_shadow'          // Mentor observes mentee, provides real-time feedback
  | 'case_study_review'       // Review past booking scenarios (successes and failures)
  | 'role_play'               // Simulate customer interactions
  | 'knowledge_transfer'      // Mentor teaches specific skill
  | 'co_booking'              // Both work on the same booking collaboratively
  | 'post_booking_review'     // Review mentee's completed bookings together
  | 'career_development';     // Discuss growth path and goals

interface MentorshipSession {
  sessionId: string;
  programId: string;
  activity: MentorshipActivity;
  date: Date;
  durationMinutes: number;
  notes: string;
  actionItems: ActionItem[];
  menteeFeedback: SessionFeedback;
  mentorFeedback: SessionFeedback;
}

interface SessionFeedback {
  rating: number;               // 1-5
  whatWorked: string;
  whatToImprove: string;
  learned: string;
}
```

### Peer Learning Mechanisms

```typescript
type PeerLearningMechanism =
  | 'booking_club'             // Weekly group discussion of interesting bookings
  | 'destination_deep_dive'    // Agent presents a destination to peers
  | 'problem_solving_circle'   // Group brainstorm for challenging bookings
  | 'skill_share_workshop'     // Agent teaches a specialized skill to peers
  | 'book_club'                // Discuss industry articles/trends
  | 'buddy_system';            // Paired agents for mutual support

interface PeerLearningEvent {
  eventId: string;
  type: PeerLearningMechanism;
  title: string;
  organizer: string;
  participants: string[];
  scheduledAt: Date;
  duration: string;
  materials: string[];
  recording?: string;
  feedback: SessionFeedback[];
}
```

### Mentor Effectiveness Tracking

```typescript
interface MentorMetrics {
  mentorId: string;
  menteesGraduated: number;
  averageTimeToGraduation: string;
  menteeSatisfactionScore: number;
  menteeBookingPerformanceDelta: number;  // Improvement vs. non-mentored
  retentionRate: number;                  // % of mentees still employed after 1 year
  sessionsCompleted: number;
  sessionsCancelled: number;
  qualitativeFeedback: string[];
}
```

---

## Open Problems

1. **Mentor bandwidth** — Top performers are the best mentors but also the busiest agents. How to balance mentoring with their own booking targets?

2. **Remote mentorship** — Shadow sessions are harder remotely. Screen sharing helps but doesn't replicate sitting next to someone.

3. **Mentor quality variance** — Great agents aren't automatically great mentors. Need mentor training and quality standards.

4. **Knowledge capture from mentoring** — Valuable insights shared in 1:1 sessions don't benefit the wider team. How to capture and share selectively?

5. **Graduation criteria** — When is a mentee "ready"? Objective criteria (booking count, error rate) don't capture judgment and customer handling.

---

## Next Steps

- [ ] Design mentorship matching algorithm based on skills and availability
- [ ] Create structured mentorship activity library
- [ ] Study mentorship programs in professional services (consulting, law)
- [ ] Design mentor compensation and workload management
- [ ] Build mentor effectiveness tracking dashboard
- [ ] Design peer learning event calendar and registration system
