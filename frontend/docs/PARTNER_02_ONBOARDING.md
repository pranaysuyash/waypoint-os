# Partner & Affiliate Management 02: Onboarding

> Partner registration, verification, and setup

---

## Document Overview

**Focus:** Partner onboarding process
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Registration Process
- How do partners apply?
- What information is required?
- How do we verify applicants?
- What is the approval workflow?

### Account Setup
- How are partner accounts created?
- What permissions are granted?
- How do they access tools?
- What about branding?

### Training & Enablement
- How do partners learn the system?
- What training materials are needed?
- How do we ensure success?
- What about ongoing support?

### Integration Setup
- How do partners integrate?
- What technical options exist?
- How do we handle testing?
- What about API access?

---

## Research Areas

### A. Registration Workflow

**Application Steps:**

```
1. Discovery
   → Partner finds program
   → Reviews benefits
   → Decides to apply

2. Application
   → Submit form
   → Provide details
   → Upload documents

3. Review
   → Verify information
   → Check suitability
   → Assess potential

4. Approval
   → Accept/reject
   → Set terms
   → Notify partner

5. Setup
   → Create account
   → Configure access
   → Generate tracking

6. Enablement
   → Training materials
   → Integration support
   → Go live
```

**Required Information:**

| Field | Purpose | Research Needed |
|-------|---------|-----------------|
| **Business name** | Identification | ? |
| **Contact info** | Communication | ? |
| **Tax ID** | Compliance | ? |
| **Website URL** | Verification | ? |
| **Traffic metrics** | Assessment | ? |
| **Marketing methods** | Suitability | ? |

**Verification Methods:**

| Method | For | Research Needed |
|--------|-----|-----------------|
| **Email verification** | Contact | ? |
| **Domain verification** | Website ownership | ? |
| **Document review** | Business legitimacy | ? |
| **Traffic check** | Audience quality | ? |
| **Social review** | Online presence | ? |

### B. Approval Process

**Approval Criteria:**

| Criterion | Threshold | Research Needed |
|-----------|-----------|-----------------|
| **Website quality** | Professional, relevant | ? |
| **Traffic volume** | Minimum visits/month | ? |
| **Audience match** | Relevant to travel | ? |
| **Compliance** | No red flags | ? |
| **Geography** | Served markets | ? |

**Approval Tiers:**

| Tier | Criteria | Research Needed |
|------|----------|-----------------|
| **Auto-approve** | Clear domain, good metrics | ? |
| **Manual review** | Standard | ? |
| **Reject** | Poor quality, irrelevant | ? |

**Approval Timeline:**

| Stage | SLA | Research Needed |
|-------|-----|-----------------|
| **Application** | Immediate | ? |
| **Auto-approve** | Immediate | ? |
| **Manual review** | 1-3 days | ? |
| **Setup** | 1-2 days | ? |

### C. Account Configuration

**Account Setup:**

| Configuration | Options | Research Needed |
|---------------|---------|-----------------|
| **Commission tier** | Based on potential | ? |
| **Payment method** | Bank, wallet, etc. | ? |
| **Branding** | White label options | ? |
| **Permissions** | Features available | ? |

**Tracking Setup:**

| Element | Description | Research Needed |
|---------|-------------|-----------------|
| **Partner ID** | Unique identifier | ? |
| **Tracking link** | Default referral URL | ? |
| **Tracking pixel** | For conversion tracking | ? |
| **API key** | If API access | ? |

**Dashboard Access:**

| Feature | Access Level | Research Needed |
|---------|--------------|-----------------|
| **Earnings view** | All | ? |
| **Reporting** | All | ? |
| **Marketing materials** | All | ? |
| **API access** | Approved | ? |
| **White label** | Premium | ? |

### D. Integration Options

**Integration Methods:**

| Method | Complexity | Best For | Research Needed |
|--------|------------|----------|-----------------|
| **Tracking link** | Low | Small partners | ? |
| **Widget/embed** | Medium | Medium partners | ? |
| **API** | High | Large partners | ? |
| **White label** | High | Strategic partners | ? |

**API Onboarding:**

| Step | Description | Research Needed |
|------|-------------|-----------------|
| **API keys** | Generate credentials | ? |
| **Documentation** | Provide API docs | ? |
| **Sandbox** | Test environment | ? |
| **Review** | Code review if needed | ? |
| **Production** | Go live | ? |

**Testing Requirements:**

| Method | Testing | Research Needed |
|--------|---------|-----------------|
| **Tracking link** | Test click-through | ? |
| **Widget** | Test display, clicks | ? |
| **API** | Integration tests | ? |
| **White label** | Full booking flow | ? |

### E. Enablement Materials

**Training Content:**

| Content | Format | Research Needed |
|---------|---------|-----------------|
| **Getting started** | Guide, video | ? |
| **Platform tour** | Video, screenshots | ? |
| **Best practices** | Guide | ? |
| **FAQ** | Document | ? |
| **API docs** | Technical | ? |

**Marketing Materials:**

| Material | Provided | Research Needed |
|----------|----------|-----------------|
| **Banners** | Various sizes | ? |
| **Text links** | Pre-written | ? |
| **Email templates** | Customizable | ? |
| **Social media** | Posts, images | ? |
| **Product feeds** | CSV/XML/API | ? |

**Support Channels:**

| Channel | Response Time | Research Needed |
|---------|--------------|-----------------|
| **Email** | 24-48 hours | ? |
| **Chat** | Business hours | ? |
| **Phone** | Premium partners | ? |
| **Dedicated manager** | Strategic partners | ? |

---

## Data Model Sketch

```typescript
interface PartnerApplication {
  applicationId: string;
  submittedAt: Date;

  // Applicant info
  businessName: string;
  contactName: string;
  email: string;
  phone: string;

  // Business details
  website: string;
  taxId?: string;
  businessType?: string;

  // Marketing
  trafficMetrics?: TrafficMetrics;
  marketingMethods: string[];
  targetAudience?: string;

  // Program
  appliedProgram: string;
  requestedTier?: PartnerTier;

  // Status
  status: ApplicationStatus;
  reviewedAt?: Date;
  reviewedBy?: string;
  rejectionReason?: string;
}

type ApplicationStatus =
  | 'pending'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'more_info_needed';

interface TrafficMetrics {
  monthlyVisitors?: number;
  monthlyPageViews?: number;
  primaryGeographies?: string[];
  primaryAudience?: string[];
}

interface PartnerAccount {
  partnerId: string;
  accountId: string;

  // Profile
  businessName: string;
  primaryContact: ContactInfo;
  billingContact: ContactInfo;

  // Program
  programId: string;
  tier: PartnerTier;
  joinedAt: Date;

  // Configuration
  commissionRate: number;
  paymentMethod: PaymentMethod;
  paymentDetails: PaymentDetails;

  // Access
  apiAccess: boolean;
  apiKey?: string;
  whiteLabel: boolean;

  // Status
  status: PartnerStatus;
  activatedAt: Date;

  // Branding
  branding?: PartnerBranding;
}

type PartnerStatus =
  | 'pending_setup'
  | 'active'
  | 'suspended'
  | 'terminated';

interface PartnerBranding {
  logo?: string;
  colors?: {
    primary?: string;
    secondary?: string;
  };
  domain?: string; // For white label
}

interface OnboardingChecklist {
  partnerId: string;
  steps: OnboardingStep[];

  // Progress
  completedSteps: number;
  totalSteps: number;
  percentage: number;

  // Status
  status: OnboardingStatus;
  completedAt?: Date;
}

interface OnboardingStep {
  stepId: string;
  name: string;
  description: string;
  required: boolean;

  // Status
  completed: boolean;
  completedAt?: Date;
  notes?: string;
}

type OnboardingStatus =
  | 'in_progress'
  | 'completed'
  | 'blocked';
```

---

## Open Problems

### 1. Application Quality
**Challenge:** Many low-quality applications

**Options:** Clear criteria, pre-qualification, better filtering

### 2. Time to Value
**Challenge:** Slow onboarding loses partners

**Options:** Self-service, automation, parallel steps

### 3. Integration Complexity
**Challenge:** Technical setup is hard

**Options:** Better docs, examples, support, simpler options

### 4. Partner Success
**Challenge:** Partners never go live

**Options:** Proactive outreach, enablement, incentives

### 5. Scale
**Challenge:** Manual onboarding doesn't scale

**Options:** Automation, tiered process, self-service

---

## Next Steps

1. Design onboarding flow
2. Create application form
3. Build approval workflow
4. Develop enablement materials

---

**Status:** Research Phase — Onboarding patterns unknown

**Last Updated:** 2026-04-27
