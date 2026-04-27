# User Accounts — Master Index

> Complete navigation guide for all User Accounts documentation

---

## Series Overview

**Topic:** User registration, authentication, profiles, and preferences
**Status:** Complete (5 of 5 documents)
**Last Updated:** 2026-04-27

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [User Architecture](#user-01) | System design, data model, security | ✅ Complete |
| 2 | [Registration](#user-02) | Signup flows, verification, onboarding | ✅ Complete |
| 3 | [Authentication](#user-03) | Login, sessions, MFA, SSO | ✅ Complete |
| 4 | [User Profiles](#user-04) | Profile management, preferences, settings | ✅ Complete |
| 5 | [Traveler Management](#user-05) | Traveler profiles, documents, companions | ✅ Complete |

---

## Document Summaries

### USER_01: User Architecture

**File:** `USER_ACCOUNTS_01_ARCHITECTURE.md`

**Topics:**
- User data model design
- Authentication architecture
- Privacy and security considerations
- Multi-tenancy support
- Integration points

---

### USER_02: Registration

**File:** `USER_ACCOUNTS_02_REGISTRATION.md`

**Topics:**
- Registration flow
- Email verification
- Social authentication
- Onboarding experience
- Data collection strategy

---

### USER_03: Authentication

**File:** `USER_ACCOUNTS_03_AUTHENTICATION.md`

**Topics:**
- Login/logout flows
- Session management
- Password reset
- Multi-factor authentication
- Single sign-on (SSO)

---

### USER_04: User Profiles

**File:** `USER_ACCOUNTS_04_PROFILES.md`

**Topics:**
- Profile management
- Preferences and settings
- Communication preferences
- Privacy controls
- Account deletion

---

### USER_05: Traveler Management

**File:** `USER_ACCOUNTS_05_TRAVELERS.md`

**Topics:**
- Traveler profiles
- Document storage (passports, visas)
- Companion management
- Travel history
- Loyalty program integration

---

## Related Documentation

**Cross-References:**
- [Security Architecture](./SECURITY_ARCHITECTURE_MASTER_INDEX.md) — Security patterns
- [Agency Settings](./AGENCY_SETTINGS_MASTER_INDEX.md) — User permissions
- [Customer Portal](./CUSTOMER_PORTAL_MASTER_INDEX.md) — User interface
- [Booking Engine](./BOOKING_ENGINE_MASTER_INDEX.md) — Customer-bookings relationship

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **JWT Tokens** | Stateless auth, works across services |
| **Refresh Tokens** | Secure long-term sessions |
| **BCrypt** | Password hashing with work factor |
| **Email Verification** | Confirm ownership, prevent spam |
| **Social Auth** | Reduce friction, increase signup |

---

## User Tiers

| Tier | Benefits | Requirements |
|------|----------|--------------|
| **Standard** | Basic booking, email support | Email verified |
| **Silver** | Priority support, exclusive deals | 1+ trips completed |
| **Gold** | Fee waivers, dedicated agent | 5+ trips, $2,500+ spent |
| **Platinum** | Best rates, concierge, upgrades | 10+ trips, $10,000+ spent |

---

## Implementation Checklist

### Phase 1: Core Auth
- [ ] User registration flow
- [ ] Email verification
- [ ] Login/logout
- [ ] Password reset
- [ ] Session management

### Phase 2: Profiles
- [ ] Profile CRUD
- [ ] Preferences management
- [ ] Traveler profiles
- [ ] Document storage

### Phase 3: Advanced Features
- [ ] Social authentication
- [ ] Multi-factor auth
- [ ] SSO integration
- [ ] Account merging

### Phase 4: Engagement
- [ ] Tier progression
- [ ] Loyalty integration
- [ ] Communication preferences
- [ ] Privacy controls

---

**Last Updated:** 2026-04-27

**Current Progress:** 5 of 5 documents complete (100%)
