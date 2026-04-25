# Agency Settings — Deep Dive Master Index

> Complete navigation guide for all Agency Settings documentation

---

## Series Overview

**Topic:** Agency Settings / Configuration
**Status:** Complete (4 of 4 documents)
**Last Updated:** 2026-04-25

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [Technical Deep Dive](#agency-settings-01) | Architecture, settings hierarchy, branding, team management | ✅ Complete |
| 2 | [UX/UI Deep Dive](#agency-settings-02) | Interface design, navigation patterns, user experience | ✅ Complete |
| 3 | [Branding Deep Dive](#agency-settings-03) | Logo management, color theming, templates, custom domains | ✅ Complete |
| 4 | [Team Management Deep Dive](#agency-settings-04) | Roles, permissions, onboarding, access control | ✅ Complete |

---

## Document Summaries

### AGENCY_SETTINGS_01: Technical Deep Dive

**File:** `AGENCY_SETTINGS_01_TECHNICAL_DEEP_DIVE.md`

**Key Topics:**
- Settings architecture with 3-tier hierarchy
- Database schema for agencies, settings, branding, and roles
- Settings inheritance (default → agency → user)
- Configuration service with caching
- Branding system with logo upload and color palette generation
- Team service with role-based access control

**Technical Highlights:**
- `SettingsResolver` for hierarchical settings
- `SettingsService` with Redis caching
- `BrandingService` with S3 integration for assets
- `TeamService` with permission checking
- JWT-based invitation system

**Diagrams:**
- Settings categories overview
- High-level architecture (6 layers)
- Component hierarchy

---

### AGENCY_SETTINGS_02: UX/UI Deep Dive

**File:** `AGENCY_SETTINGS_02_UX_UI_DEEP_DIVE.md`

**Key Topics:**
- Settings panel layout with sidebar navigation
- SettingsCard and SettingsField components
- Auto-save pattern with debouncing
- LogoUploader with drag-drop
- ColorPicker with palette suggestions
- TeamMemberList with inline actions
- RoleEditor with permission matrix
- Responsive design patterns

**UI Components:**
- SettingsLayout, SettingsCard, SettingsField
- LogoUploader, ColorPicker, FontSelector
- TeamMemberList, RoleEditor, PermissionMatrix
- InviteMemberModal, AuditLogViewer

---

### AGENCY_SETTINGS_03: Branding Deep Dive

**File:** `AGENCY_SETTINGS_03_BRANDING_DEEP_DIVE.md`

**Key Topics:**
- Logo upload and processing with sharp
- Color palette generation with WCAG contrast checking
- Typography with Google Fonts integration
- Email template customization with dynamic branding
- Document branding for PDF headers/footers
- Custom domain setup with DNS verification
- SSL certificate provisioning with Let's Encrypt
- Brand guidelines generation

**Technical Highlights:**
- LogoProcessorService for image optimization
- ColorPaletteService with contrast validation
- TypographyService with web font management
- EmailTemplateService for branded emails
- DocumentBrandingService for PDF styling
- CustomDomainService with DNS verification

---

### AGENCY_SETTINGS_04: Team Management Deep Dive

**File:** `AGENCY_SETTINGS_04_TEAM_MANAGEMENT_DEEP_DIVE.md`

**Key Topics:**
- Role-Based Access Control (RBAC) architecture
- Permission system with resource:action:scope format
- Member invitation flow with JWT tokens
- Onboarding experience with guided steps
- Audit logging for all team activities
- Access control best practices
- Permission middleware for API protection

**Technical Highlights:**
- TeamService for member management
- PermissionService with caching
- System roles (Owner, Admin, Senior Agent, Agent, Junior Agent, ReadOnly)
- Permission categories (Trips, Bookings, Customers, Team, Settings, etc.)
- Invitation state machine (Pending → Accepted → Active)
- Field-level security patterns

---

## Related Documentation

**Product Features:**
- [Communication Hub](../COMM_HUB_DEEP_DIVE_MASTER_INDEX.md) — Uses agency branding for emails
- [Output Panel](../OUTPUT_DEEP_DIVE_MASTER_INDEX.md) — Uses agency templates for documents

**Cross-References:**
- Settings cascade to all trip-related communications
- Branding applies to customer-facing documents
- Team permissions control feature access

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **3-tier hierarchy** | Default → Agency → User allows flexibility while maintaining consistency |
| **JSONB storage** | Flexible schema for different setting types without migrations |
| **Redis caching** | Frequently accessed settings need fast retrieval |
| **S3 for assets** | Scalable storage for logos and branding assets |
| **RBAC model** | Industry-standard permission model with role inheritance |
| **Audit logging** | Compliance requirements for settings changes |

---

## Implementation Checklist

### Phase 1: Core Settings
- [ ] Database migrations for agencies and settings
- [ ] Default settings seed data
- [ ] Settings resolver service
- [ ] Settings API endpoints
- [ ] Settings cache invalidation

### Phase 2: Branding
- [ ] Branding table migration
- [ ] Logo upload handler
- [ ] Color palette generator
- [ ] Email template renderer
- [ ] Custom domain verification

### Phase 3: Team Management
- [ ] Roles and permissions tables
- [ ] Team service implementation
- [ ] Invitation flow
- [ ] Permission checking middleware
- [ ] Audit logging

### Phase 4: UI Components
- [ ] Settings layout component
- [ ] Branding editor components
- [ ] Team management interface
- [ ] Permission matrix UI
- [ ] Settings form validation

---

## Glossary

| Term | Definition |
|------|------------|
| **Agency** | Top-level entity representing a travel agency company |
| **Setting** | Configuration value with category, key, and value |
| **Override** | User or agency value replacing default value |
| **Role** | Collection of permissions assigned to team members |
| **Permission** | Granular access control for specific resources/actions |
| **Branding** | Visual identity customization (logo, colors, fonts) |

---

**Last Updated:** 2026-04-25

**Current Progress:** 4 of 4 documents complete (100%) ✅
