# Agency Settings 04: Team Management Deep Dive

> Complete guide to team management, roles, permissions, and access control

---

## Document Overview

**Series:** Agency Settings Deep Dive (Document 4 of 4)
**Focus:** Team Management — Roles, Permissions, Onboarding, Access Control
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Team Management Architecture](#team-management-architecture)
3. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
4. [Permission System](#permission-system)
5. [Member Invitation Flow](#member-invitation-flow)
6. [Onboarding Experience](#onboarding-experience)
7. [Audit Logging](#audit-logging)
8. [Access Control Best Practices](#access-control-best-practices)
9. [Implementation Reference](#implementation-reference)

---

## Executive Summary

Team management enables agencies to control who can access what features and data within their workspace. The system uses Role-Based Access Control (RBAC) with granular permissions, secure invitation flows, comprehensive audit logging, and seamless onboarding.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Custom Roles** | Create roles with specific permission sets |
| **Granular Permissions** | Control access to specific resources and actions |
| **Secure Invitations** | JWT-based invitation system with expiration |
| **Audit Trail** | Complete log of all access-related activities |
| **Team Visibility** | Control which team members see what data |

---

## Team Management Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEAM MANAGEMENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐     ┌─────────────────────────────────────────────────┐ │
│  │   TeamPanel   │────▶│               TeamService                       │ │
│  │   (UI Layer)  │     │  - inviteMember()                               │ │
│  └───────────────┘     │  - removeMember()                               │ │
│         │              │  - updateMemberRole()                            │ │
│         │              │  - createRole()                                  │ │
│         │              │  - updateRole()                                  │ │
│         │              └─────────────────────────────────────────────────┘ │
│         │                                   │                              │
│         │                                   ▼                              │
│         │              ┌─────────────────────────────────────────────────┐ │
│         │              │              PermissionService                   │ │
│         │              │  - checkPermission()                            │ │
│         │              │  - getUserPermissions()                         │ │
│         │              │  - getRolePermissions()                         │ │
│         │              └─────────────────────────────────────────────────┘ │
│         │                                   │                              │
│         ▼                                   ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Database Layer                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │  │
│  │  │ team_members    │  │ roles           │  │ permissions     │      │  │
│  │  │ - user_id       │  │ - id            │  │ - id            │      │  │
│  │  │ - agency_id     │  │ - agency_id     │  │ - resource      │      │  │
│  │  │ - role_id       │  │ - name          │  │ - action        │      │  │
│  │  │ - status        │  │ - permissions[] │  │ - description   │      │  │
│  │  │ - joined_at     │  │ - is_system     │  │                 │      │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Audit Layer                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐│  │
│  │  │ audit_logs                                                        ││  │
│  │  │ - id, agency_id, actor_id, action, resource, details, timestamp  ││  │
│  │  └─────────────────────────────────────────────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
TeamManagementFeature
│
├── TeamPanel
│   ├── TeamMembersList
│   │   ├── TeamMemberCard
│   │   │   ├── MemberAvatar
│   │   │   ├── MemberInfo
│   │   │   ├── MemberRoleBadge
│   │   │   └── MemberActions
│   │   │       ├── RoleSelector
│   │   │       ├── RemoveMemberButton
│   │   │       └── ViewActivityButton
│   │   └── InviteMemberButton
│   │
├── RolesList
│   ├── RoleCard
│   │   ├── RoleHeader
│   │   │   ├── RoleName
│   │   │   ├── RoleDescription
│   │   │   └── RoleMemberCount
│   │   ├── PermissionList
│   │   │   └── PermissionCheckbox
│   │   └── RoleActions
│   │       ├── EditRoleButton
│   │       ├── DuplicateRoleButton
│   │       └── DeleteRoleButton
│   │
├── PermissionMatrix
│   ├── PermissionCategory
│   │   ├── PermissionRow
│   │   │   ├── PermissionLabel
│   │   │   └── RolePermissionCells
│   │   └── CategoryHeader
│   │
├── InvitationsList
│   ├── InvitationCard
│   │   ├── InvitationEmail
│   │   ├── InvitationStatus
│   │   ├── InvitationExpiry
│   │   └── InvitationActions
│   │       ├── ResendButton
│   │       └── CancelButton
│   │
└── AuditLogPanel
    ├── AuditLogFilters
    │   ├── ActionFilter
    │   ├── ActorFilter
    │   └── DateRangeFilter
    └── AuditLogList
        └── AuditLogEntry
```

---

## Role-Based Access Control (RBAC)

### RBAC Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RBAC HIERARCHY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    Agency                                                  │
│                       │                                                     │
│       ┌───────────────┼───────────────┐                                    │
│       │               │               │                                    │
│       ▼               ▼               ▼                                    │
│    Owner           Admin          Agent                                    │
│    (Role)          (Role)         (Role)                                    │
│       │               │               │                                    │
│       │               │               │                                    │
│       ▼               ▼               ▼                                    │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │ *       │     │ trips.* │     │ trips.* │                              │
│  │         │     │ bookings.*│  │         │                              │
│  │         │     │ team.*   │     │         │                              │
│  │         │     │         │     │         │                              │
│  │         │     │         │     │         │                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
│  All Permissions  Most Permissions  Limited Permissions                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### System Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Owner** | Full agency control | All permissions |
| **Admin** | Manage operations | All except billing, delete agency |
| **Senior Agent** | Advanced operations | trips.*, bookings.*, customers.*, reports.view |
| **Agent** | Standard operations | trips.own, bookings.own, customers.own |
| **Junior Agent** | Limited operations | trips.own:read, bookings.own:read |
| **ReadOnly** | View-only access | *.view only |

### Role Inheritance

```
                    Owner (All Permissions)
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
       Admin           Senior Agent       Agent
    (Owner -           (Admin -         (Senior Agent -
     billing,           billing,          + some)
     delete)            delete,           team)
                       team)
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                      Junior Agent
                    (Agent - write)
                           │
                       ReadOnly
                   (Junior Agent -
                    all write)
```

---

## Permission System

### Permission Structure

```
Permission Format: resource:action:scope

Examples:
- trips:*:*              (All trip operations)
- trips:read:*           (Read any trip)
- trips:read:own         (Read own trips only)
- bookings:create:*       (Create any booking)
- bookings:delete:own     (Delete own bookings)
- team:invite:*          (Invite team members)
- settings:write:*       (Write agency settings)
```

### Permission Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PERMISSION CATEGORIES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TRIP MANAGEMENT                                                     │   │
│  │  - trips:create         (Create new trips)                          │   │
│  │  - trips:read           (View trips)                                │   │
│  │  - trips:update         (Edit trip details)                         │   │
│  │  - trips:delete         (Delete trips)                              │   │
│  │  - trips:assign         (Assign trips to agents)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BOOKING MANAGEMENT                                                  │   │
│  │  - bookings:create       (Create bookings)                          │   │
│  │  - bookings:read         (View bookings)                            │   │
│  │  - bookings:update       (Modify bookings)                          │   │
│  │  - bookings:cancel       (Cancel bookings)                          │   │
│  │  - bookings:refund       (Process refunds)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CUSTOMER MANAGEMENT                                                 │   │
│  │  - customers:create     (Add customers)                             │   │
│  │  - customers:read       (View customer profiles)                    │   │
│  │  - customers:update     (Edit customer details)                     │   │
│  │  - customers:delete     (Delete customer records)                   │   │
│  │  - customers:export     (Export customer data)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TEAM MANAGEMENT                                                     │   │
│  │  - team:invite          (Invite new members)                        │   │
│  │  - team:remove          (Remove members)                            │   │
│  │  - team:roles:read      (View roles)                                │   │
│  │  - team:roles:write     (Create/edit roles)                         │   │
│  │  - team:audit:read      (View audit logs)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SETTINGS & CONFIGURATION                                            │   │
│  │  - settings:read        (View agency settings)                      │   │
│  │  - settings:write       (Modify agency settings)                    │   │
│  │  - branding:write       (Modify branding)                           │   │
│  │  - integrations:write   (Manage integrations)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COMMUNICATIONS                                                       │   │
│  │  - communications:send  (Send messages)                              │   │
│  │  - communications:read (View message history)                        │   │
│  │  - templates:write     (Edit message templates)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REPORTING & ANALYTICS                                               │   │
│  │  - reports:read        (View reports)                               │   │
│  │  - reports:create       (Create custom reports)                     │   │
│  │  - analytics:read       (View analytics)                            │   │
│  │  - exports:create       (Export data)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BILLING & PAYMENTS                                                  │   │
│  │  - billing:read        (View invoices, billing info)                │   │
│  │  - billing:write       (Modify billing details)                     │   │
│  │  - payments:process    (Process payments)                           │   │
│  │  - refunds:process     (Process refunds)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Permission Scopes

| Scope | Description | Example |
|-------|-------------|---------|
| `*` | All resources/actions | `trips:*` |
| `all` | All items in category | `trips:read:all` |
| `own` | Only user's items | `trips:read:own` |
| `team` | Items assigned to user's team | `trips:read:team` |
| `none` | No access | `billing:read:none` |

---

## Member Invitation Flow

### Invitation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INVITATION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Agency Owner                                       Invitee                │
│       │                                                                │    │
│       │  1. Enter email + role                                        │    │
│       │         │                                                       │    │
│       ▼         ▼                                                       │    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  2. TeamService.inviteMember()                                      │  │
│  │     - Validate email                                                │  │
│  │     - Check if already member                                       │  │
│  │     - Generate JWT token (exp: 7 days)                              │  │
│  │     - Store in invitations table                                    │  │
│  │     - Send invitation email                                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│       │                                                                 │    │
│       │                        3. Email with link                       │    │
│       │                        ─────────────────                       │    │
│       ▼                        /invite/accept?token=jwt                 │    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  4. Invitation Landing Page                                         │  │
│  │     - Verify JWT signature                                          │  │
│  │     - Check expiration                                               │  │
│  │     - Show agency info + role                                       │  │
│  │     - [Accept] [Decline] buttons                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│       │                                                                 │    │
│       │                        5. [Accept]                              │    │
│       ▼                        ─────────                                │    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  6. Onboarding Flow                                                 │  │
│  │     - Create account / Sign in                                      │  │
│  │     - Link user to agency                                           │  │
│  │     - Assign role                                                   │  │
│  │     - Set up profile                                                │  │
│  │     - Welcome tutorial                                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│       │                                                                 │    │
│       │                        7. Redirect to workspace                 │    │
│       ▼                        ────────────────────────                 │    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  8. Member added to team_members table (status: active)             │  │
│  │     Notification sent to owner                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JWT Token Structure

```typescript
interface InvitationToken {
  iss: string;           // Issuer: agency_id
  sub: string;           // Subject: email
  role: string;          // Assigned role
  agency_id: string;     // Agency ID
  invited_by: string;    // User ID of inviter
  exp: number;           // Expiration timestamp
  iat: number;           // Issued at timestamp
  jti: string;           // Unique token ID
}
```

### Invitation States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INVITATION STATE MACHINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐           │
│     │  PENDING │────▶│ ACCEPTED│────▶│ ACTIVE  │     │ EXPIRED │           │
│     └─────────┘     └─────────┘     └─────────┘     └─────────┘           │
│         │                                  ▲                                 │
│         │                                  │                                 │
│         │           ┌─────────┐            │                                 │
│         └──────────▶│ DECLINED│────────────┘                                 │
│                     └─────────┘                                             │
│                     │                                                       │
│                     ▼                                                       │
│                ┌─────────┐                                                  │
│                │ CANCELLED│                                                 │
│                └─────────┘                                                  │
│                                                                             │
│  Transitions:                                                              │
│  - PENDING → ACCEPTED: User clicks Accept                                 │
│  - PENDING → DECLINED: User clicks Decline                                │
│  - PENDING → CANCELLED: Owner cancels invitation                          │
│  - PENDING → EXPIRED: Token expires (7 days)                              │
│  - ACCEPTED → ACTIVE: User completes onboarding                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Onboarding Experience

### Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEW MEMBER ONBOARDING                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Step 1: Welcome / Authentication                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  Welcome to [Agency Name]!                                      │ │   │
│  │  │                                                                  │ │   │
│  │  │  [Sign In]  [Create Account]                                    │ │   │
│  │  │                                                                  │ │   │
│  │  │  You've been invited as: [Role Badge]                           │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Step 2: Profile Setup                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  Complete your profile                                           │ │   │
│  │  │                                                                  │ │   │
│  │  │  [Avatar Upload]                                                 │ │   │
│  │  │                                                                  │ │   │
│  │  │  Full Name: [________________]                                   │ │   │
│  │  │  Phone:    [________________]                                    │ │   │
│  │  │                                                                  │ │   │
│  │  │  Timezone: [UTC+5:30 ▼]                                         │ │   │
│  │  │                                                                  │ │   │
│  │  │  [Skip for now]    [Continue]                                   │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Step 3: Agency Introduction                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  Meet your team                                                  │ │   │
│  │  │                                                                  │ │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐                               │ │   │
│  │  │  │ Owner  │ │ Admin  │ │ Agent  │                               │ │   │
│  │  │  │ Name   │ │ Name   │ │ Name   │                               │ │   │
│  │  │  └────────┘ └────────┘ └────────┘                               │ │   │
│  │  │                                                                  │ │   │
│  │  │  [View all team members]                                        │ │   │
│  │  │                                                                  │ │   │
│  │  │  Your role: Agent                                               │ │   │
│  │  │  You can: View trips, Manage bookings, Communicate with customers│ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Step 4: Product Tour (Optional)                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │ │   │
│  │  │  │  Welcome to your workspace!                              │   │ │   │
│  │  │  │                                                          │   │ │   │
│  │  │  │  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐              │   │ │   │
│  │  │  │  │  1  │───▶│  2  │───▶│  3  │───▶│  4  │              │   │ │   │
│  │  │  │  │Inbox│    │Trips│    │Chat │    │More │              │   │ │   │
│  │  │  │  └─────┘    └─────┘    └─────┘    └─────┘              │   │ │   │
│  │  │  │                                                          │   │ │   │
│  │  │  │  [Start Tour]    [Skip Tour]                             │   │ │   │
│  │  │  └──────────────────────────────────────────────────────────┘   │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Step 5: Ready to Start                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  You're all set! 🎉                                             │ │   │
│  │  │                                                                  │ │   │
│  │  │  You can now:                                                   │ │   │
│  │  │  • View your assigned trips in the Inbox                        │ │   │
│  │  │  • Respond to customer messages                                 │ │   │
│  │  │  • Update your profile anytime in Settings                      │ │   │
│  │  │                                                                  │ │   │
│  │  │  [Go to Inbox]    [Explore on your own]                         │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Onboarding Checkpoints

| Step | Required | Can Skip | Data Captured |
|------|----------|----------|---------------|
| Authentication | ✅ Yes | ❌ No | User account linked to agency |
| Profile Setup | ⚠️ Conditional | ✅ Yes | Name, phone, timezone |
| Agency Intro | ✅ Yes | ❌ No | None (informational) |
| Product Tour | ❌ No | ✅ Yes | Tutorial completion flag |
| Ready | ✅ Yes | ❌ No | onboarding_completed = true |

---

## Audit Logging

### Audit Event Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUDIT EVENT CATEGORIES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MEMBER MANAGEMENT                                                   │   │
│  │  - member.invited              (New invitation sent)                 │   │
│  │  - member.joined               (Member accepted invitation)          │   │
│  │  - member.role_changed         (Member role updated)                 │   │
│  │  - member.removed              (Member removed from agency)          │   │
│  │  - member.reactivated          (Inactive member reactivated)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ROLE MANAGEMENT                                                     │   │
│  │  - role.created                (New role created)                    │   │
│  │  - role.updated                (Role permissions modified)           │   │
│  │  - role.deleted                (Role deleted)                        │   │
│  │  - role.duplicated             (Role duplicated)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PERMISSION CHANGES                                                  │   │
│  │  - permission.granted          (Permission added to role)            │   │
│  │  - permission.revoked          (Permission removed from role)        │   │
│  │  - permission.bulk_updated     (Multiple permissions changed)        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SETTINGS CHANGES                                                    │   │
│  │  - settings.updated            (Agency settings modified)            │   │
│  │  - branding.updated            (Branding changed)                    │   │
│  │  - integrations.changed        (Integration settings modified)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SECURITY EVENTS                                                     │   │
│  │  - auth.login                  (User logged in)                      │   │
│  │  - auth.logout                 (User logged out)                     │   │
│  │  - auth.failed                 (Failed login attempt)                │   │
│  │  - auth.password_changed       (Password changed)                    │   │
│  │  - auth.mfa_enabled            (MFA enabled)                         │   │
│  │  - auth.suspicious_activity    (Unusual activity detected)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Audit Log Schema

```typescript
interface AuditLog {
  id: string;
  agency_id: string;

  // Actor
  actor_id: string;
  actor_type: 'user' | 'system' | 'api';
  actor_name: string;
  actor_role?: string;

  // Action
  action: string;              // e.g., "member.invited"
  action_category: string;     // e.g., "MEMBER_MANAGEMENT"

  // Target
  resource_type: string;       // e.g., "team_member"
  resource_id: string;
  resource_name?: string;

  // Details
  details: Record<string, any>;
  changes?: {
    before?: Record<string, any>;
    after?: Record<string, any>;
  };

  // Context
  ip_address?: string;
  user_agent?: string;

  // Timestamp
  timestamp: Date;
  created_at: Date;
}
```

### Audit Log Retention

| Event Type | Retention Period | Rationale |
|------------|------------------|-----------|
| Security Events | 2 years | Compliance, forensic analysis |
| Member Management | 1 year | Operational history |
| Permission Changes | 1 year | Accountability |
| Settings Changes | 6 months | Recent configuration history |
| Login/Logout | 90 days | Session security |

---

## Access Control Best Practices

### Permission Design Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERMISSION DESIGN PRINCIPLES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LEAST PRIVILEGE                                                        │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Users should have ONLY the permissions needed for their role.  │   │
│     │  Start with minimal access, grant more as needed.               │   │
│     │                                                                  │   │
│     │  ✅ Good: Agent can only view own trips                         │   │
│     │  ❌ Bad: Agent can view all agency trips                        │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. SEPARATION OF DUTIES                                                   │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Critical operations require multiple people.                   │   │
│     │  No single person should have complete control.                 │   │
│     │                                                                  │   │
│     │  Example: One person creates booking, another approves payment  │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. ROLE HIERARCHY                                                          │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Roles should inherit from base roles.                          │   │
│     │  Add permissions incrementally.                                 │   │
│     │                                                                  │   │
│     │  ReadOnly → Junior Agent → Agent → Senior Agent → Admin → Owner │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. EXPLICIT OVER IMPLICIT                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  All access must be explicitly granted.                         │   │
│     │  Default to deny, allow only if permitted.                      │   │
│     │                                                                  │   │
│     │  if (!hasPermission(user, 'trips:read')) { return 403; }        │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. AUDIT EVERYTHING                                                        │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Log all permission checks, especially denials.                 │   │
│     │  Monitor for suspicious patterns.                               │   │
│     │                                                                  │   │
│     │  Alert on: Multiple denied access, unusual time, new location   │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Access Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMMON ACCESS PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. OWNER CHECKS (Can this user modify this resource?)                     │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  function canModify(user: User, trip: Trip): boolean {          │   │
│     │    if (hasPermission(user, 'trips:update:all')) return true;    │   │
│     │    if (hasPermission(user, 'trips:update:team')) {              │   │
│     │      return isSameTeam(user, trip.assigned_to);                 │   │
│     │    }                                                             │   │
│     │    if (hasPermission(user, 'trips:update:own')) {               │   │
│     │      return trip.assigned_to === user.id;                       │   │
│     │    }                                                             │   │
│     │    return false;                                                 │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. DATA FILTERING (What can this user see?)                               │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  function getAccessibleTrips(user: User): QueryBuilder {        │   │
│     │    let query = db.select().from(trips);                         │   │
│     │                                                                   │  │
│     │    if (hasPermission(user, 'trips:read:all')) {                 │   │
│     │      return query.where('agency_id', user.agency_id);           │   │
│     │    }                                                             │   │
│     │    if (hasPermission(user, 'trips:read:team')) {                │   │
│     │      return query.where('team_id', user.team_id);               │   │
│     │    }                                                             │   │
│     │    // Default: own trips only                                    │   │
│     │    return query.where('assigned_to', user.id);                  │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. FIELD-LEVEL SECURITY (Hide sensitive fields)                            │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  function sanitizeBooking(booking: Booking, user: User) {       │   │
│     │    const canViewCost = hasPermission(user, 'bookings:cost');   │   │
│     │    return {                                                     │   │
│     │      ...booking,                                                │   │
│     │      cost: canViewCost ? booking.cost : undefined,             │   │
│     │      margin: canViewCost ? booking.margin : undefined,         │   │
│     │    };                                                           │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. BULK OPERATION CHECKS                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  function canBulkUpdate(user: User, trips: Trip[]): boolean {   │   │
│     │    const hasAll = hasPermission(user, 'trips:update:all');      │   │
│     │    const hasTeam = hasPermission(user, 'trips:update:team');   │   │
│     │                                                                   │  │
│     │    return trips.every(trip =>                                    │   │
│     │      hasAll ||                                                   │   │
│     │      (hasTeam && isSameTeam(user, trip.assigned_to)) ||          │   │
│     │      trip.assigned_to === user.id                                │   │
│     │    );                                                             │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Reference

### TeamService

```typescript
// services/team.service.ts
import { db } from '@/db';
import { teamMembers, roles, invitations, auditLogs } from '@/db/schema';
import { PermissionService } from './permission.service';
import { EmailService } from './email.service';
import jwt from 'jsonwebtoken';

export class TeamService {
  private permissionService: PermissionService;
  private emailService: EmailService;

  async inviteMember(input: {
    agencyId: string;
    email: string;
    roleId: string;
    invitedBy: string;
  }): Promise<{ invitationId: string; token: string }> {
    // Validate permissions
    const canInvite = await this.permissionService.checkPermission(
      input.invitedBy,
      'team:invite'
    );
    if (!canInvite) {
      throw new Error('Insufficient permissions');
    }

    // Check if already a member
    const existing = await db.query.teamMembers.findFirst({
      where: eq(teamMembers.email, input.email)
    });
    if (existing) {
      throw new Error('User is already a team member');
    }

    // Check for pending invitation
    const pendingInvite = await db.query.invitations.findFirst({
      where: and(
        eq(invitations.email, input.email),
        eq(invitations.agencyId, input.agencyId),
        eq(invitations.status, 'pending')
      )
    });
    if (pendingInvite) {
      // Resend existing invitation
      await this.sendInvitationEmail(pendingInvite);
      return { invitationId: pendingInvite.id, token: pendingInvite.token };
    }

    // Generate JWT token
    const token = jwt.sign(
      {
        email: input.email,
        agency_id: input.agencyId,
        role: input.roleId,
        invited_by: input.invitedBy,
      },
      process.env.JWT_SECRET!,
      { expiresIn: '7d', jwtid: randomUUID() }
    );

    // Create invitation
    const [invitation] = await db.insert(invitations).values({
      id: randomUUID(),
      agencyId: input.agencyId,
      email: input.email,
      roleId: input.roleId,
      invitedBy: input.invitedBy,
      token,
      status: 'pending',
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    }).returning();

    // Send email
    await this.sendInvitationEmail(invitation);

    // Log
    await this.logAction({
      agencyId: input.agencyId,
      actorId: input.invitedBy,
      action: 'member.invited',
      resourceType: 'invitation',
      resourceId: invitation.id,
      details: { email: input.email, roleId: input.roleId },
    });

    return { invitationId: invitation.id, token };
  }

  async acceptInvitation(input: {
    token: string;
    userId: string;
  }): Promise<void> {
    // Verify token
    let payload: any;
    try {
      payload = jwt.verify(input.token, process.env.JWT_SECRET!);
    } catch {
      throw new Error('Invalid or expired invitation');
    }

    // Get invitation
    const invitation = await db.query.invitations.findFirst({
      where: eq(invitations.token, input.token),
    });
    if (!invitation || invitation.status !== 'pending') {
      throw new Error('Invitation not found or already processed');
    }

    if (new Date(invitation.expiresAt) < new Date()) {
      await db.update(invitations)
        .set({ status: 'expired' })
        .where(eq(invitations.id, invitation.id));
      throw new Error('Invitation has expired');
    }

    // Create team member
    await db.insert(teamMembers).values({
      id: randomUUID(),
      agencyId: invitation.agencyId,
      userId: input.userId,
      roleId: invitation.roleId,
      email: invitation.email,
      status: 'active',
      joinedAt: new Date(),
    });

    // Update invitation status
    await db.update(invitations)
      .set({ status: 'accepted', acceptedAt: new Date() })
      .where(eq(invitations.id, invitation.id));

    // Log
    await this.logAction({
      agencyId: invitation.agencyId,
      actorId: input.userId,
      action: 'member.joined',
      resourceType: 'team_member',
      resourceId: input.userId,
      details: { invitationId: invitation.id },
    });
  }

  async removeMember(input: {
    agencyId: string;
    memberId: string;
    removedBy: string;
  }): Promise<void> {
    // Check permissions
    const canRemove = await this.permissionService.checkPermission(
      input.removedBy,
      'team:remove'
    );
    if (!canRemove) {
      throw new Error('Insufficient permissions');
    }

    // Get member
    const member = await db.query.teamMembers.findFirst({
      where: eq(teamMembers.id, input.memberId),
    });
    if (!member) {
      throw new Error('Member not found');
    }

    // Cannot remove owner
    const role = await db.query.roles.findFirst({
      where: eq(roles.id, member.roleId),
    });
    if (role?.name === 'Owner') {
      throw new Error('Cannot remove agency owner');
    }

    // Remove member
    await db.update(teamMembers)
      .set({ status: 'removed', removedAt: new Date() })
      .where(eq(teamMembers.id, input.memberId));

    // Log
    await this.logAction({
      agencyId: input.agencyId,
      actorId: input.removedBy,
      action: 'member.removed',
      resourceType: 'team_member',
      resourceId: input.memberId,
      details: { memberEmail: member.email },
    });
  }

  async updateMemberRole(input: {
    agencyId: string;
    memberId: string;
    newRoleId: string;
    updatedBy: string;
  }): Promise<void> {
    // Check permissions
    const canUpdate = await this.permissionService.checkPermission(
      input.updatedBy,
      'team:roles:write'
    );
    if (!canUpdate) {
      throw new Error('Insufficient permissions');
    }

    // Get current role
    const member = await db.query.teamMembers.findFirst({
      where: eq(teamMembers.id, input.memberId),
      with: { role: true },
    });
    if (!member) {
      throw new Error('Member not found');
    }

    // Cannot change owner role
    if (member.role.name === 'Owner') {
      throw new Error('Cannot modify owner role');
    }

    // Update role
    await db.update(teamMembers)
      .set({ roleId: input.newRoleId })
      .where(eq(teamMembers.id, input.memberId));

    // Log
    await this.logAction({
      agencyId: input.agencyId,
      actorId: input.updatedBy,
      action: 'member.role_changed',
      resourceType: 'team_member',
      resourceId: input.memberId,
      details: {
        previousRole: member.role.name,
        newRole: input.newRoleId,
      },
    });
  }

  private async sendInvitationEmail(invitation: any): Promise<void> {
    const acceptUrl = `${process.env.APP_URL}/invite/accept?token=${invitation.token}`;

    await this.emailService.send({
      to: invitation.email,
      template: 'team-invitation',
      data: {
        acceptUrl,
        agencyName: invitation.agency.name,
        roleName: invitation.role.name,
        expiresIn: '7 days',
      },
    });
  }

  private async logAction(input: {
    agencyId: string;
    actorId: string;
    action: string;
    resourceType: string;
    resourceId: string;
    details?: Record<string, any>;
  }): Promise<void> {
    await db.insert(auditLogs).values({
      id: randomUUID(),
      agencyId: input.agencyId,
      actorId: input.actorId,
      action: input.action,
      resourceType: input.resourceType,
      resourceId: input.resourceId,
      details: input.details || {},
      timestamp: new Date(),
    });
  }
}
```

### PermissionService

```typescript
// services/permission.service.ts
import { db } from '@/db';
import { roles, teamMembers, permissions } from '@/db/schema';
import { eq, and } from 'drizzle-orm';

export class PermissionService {
  private cache = new Map<string, Set<string>>();

  async getUserPermissions(userId: string): Promise<Set<string>> {
    // Check cache first
    const cacheKey = `user:${userId}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    // Get user's role
    const member = await db.query.teamMembers.findFirst({
      where: eq(teamMembers.userId, userId),
      with: { role: { with: { permissions: true } } },
    });

    if (!member) {
      return new Set();
    }

    // Build permission set
    const userPermissions = new Set<string>();
    for (const perm of member.role.permissions) {
      userPermissions.add(`${perm.resource}:${perm.action}:${perm.scope || '*'}`);
    }

    // Cache for 5 minutes
    this.cache.set(cacheKey, userPermissions);
    setTimeout(() => this.cache.delete(cacheKey), 5 * 60 * 1000);

    return userPermissions;
  }

  async checkPermission(
    userId: string,
    requiredPermission: string
  ): Promise<boolean> {
    const permissions = await this.getUserPermissions(userId);

    // Parse required permission
    const [resource, action, scope] = requiredPermission.split(':');

    // Check for exact match
    if (permissions.has(requiredPermission)) {
      return true;
    }

    // Check for wildcard match
    if (permissions.has(`${resource}:*:*`)) {
      return true;
    }

    // Check for action wildcard
    if (permissions.has(`${resource}:${action}:*`)) {
      return true;
    }

    return false;
  }

  async checkAllPermissions(
    userId: string,
    requiredPermissions: string[]
  ): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    for (const permission of requiredPermissions) {
      results[permission] = await this.checkPermission(userId, permission);
    }

    return results;
  }

  async getRolePermissions(roleId: string): Promise<string[]> {
    const role = await db.query.roles.findFirst({
      where: eq(roles.id, roleId),
      with: { permissions: true },
    });

    if (!role) {
      return [];
    }

    return role.permissions.map(
      p => `${p.resource}:${p.action}:${p.scope || '*'}`
    );
  }

  invalidateCache(userId?: string): void {
    if (userId) {
      this.cache.delete(`user:${userId}`);
    } else {
      this.cache.clear();
    }
  }

  // Helper: Filter accessible resources
  async filterAccessibleResources<T extends { assignedTo?: string }>(
    userId: string,
    resources: T[],
    permission: string
  ): Promise<T[]> {
    const hasAllAccess = await this.checkPermission(userId, `${permission}:all`);
    if (hasAllAccess) {
      return resources;
    }

    const hasTeamAccess = await this.checkPermission(userId, `${permission}:team`);
    if (hasTeamAccess) {
      // Get user's team and filter
      const member = await db.query.teamMembers.findFirst({
        where: eq(teamMembers.userId, userId),
      });
      return resources.filter(r => r.assignedTo === member?.userId);
    }

    // Default: own resources only
    return resources.filter(r => r.assignedTo === userId);
  }
}
```

### Permission Middleware

```typescript
// middleware/permission.middleware.ts
import { PermissionService } from '@/services/permission.service';
import { Request, Response, NextFunction } from 'express';

export function requirePermission(permission: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const permissionService = new PermissionService();
    const hasPermission = await permissionService.checkPermission(
      userId,
      permission
    );

    if (!hasPermission) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Insufficient permissions: ${permission} required`,
      });
    }

    next();
  };
}

export function requireAnyPermission(...permissions: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const permissionService = new PermissionService();
    const checks = await Promise.all(
      permissions.map(p => permissionService.checkPermission(userId, p))
    );

    if (!checks.some(Boolean)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Insufficient permissions: one of ${permissions.join(', ')} required`,
      });
    }

    next();
  };
}

// Usage example:
// router.get('/trips/:id', requirePermission('trips:read:own'), getTrip);
// router.delete('/trips/:id', requirePermission('trips:delete:all'), deleteTrip);
// router.post '/admin', requireAnyPermission('admin:*', 'settings:write'), adminAction);
```

### React Components

```typescript
// components/team/TeamMembersList.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function TeamMembersList() {
  const queryClient = useQueryClient();

  const { data: members } = useQuery({
    queryKey: ['team-members'],
    queryFn: () => fetch('/api/team/members').then(r => r.json()),
  });

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: () => fetch('/api/team/roles').then(r => r.json()),
  });

  const removeMutation = useMutation({
    mutationFn: (memberId: string) =>
      fetch(`/api/team/members/${memberId}`, { method: 'DELETE' })
        .then(r => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-members'] }),
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ memberId, roleId }: { memberId: string; roleId: string }) =>
      fetch(`/api/team/members/${memberId}`, {
        method: 'PATCH',
        body: JSON.stringify({ roleId }),
        headers: { 'Content-Type': 'application/json' },
      }).then(r => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-members'] }),
  });

  return (
    <div className="space-y-4">
      {members?.map((member: TeamMember) => (
        <TeamMemberCard
          key={member.id}
          member={member}
          roles={roles}
          onRemove={() => removeMutation.mutate(member.id)}
          onRoleChange={(roleId) => updateRoleMutation.mutate({ memberId: member.id, roleId })}
        />
      ))}
    </div>
  );
}

// components/team/TeamMemberCard.tsx
interface TeamMemberCardProps {
  member: TeamMember;
  roles: Role[];
  onRemove: () => void;
  onRoleChange: (roleId: string) => void;
}

function TeamMemberCard({ member, roles, onRemove, onRoleChange }: TeamMemberCardProps) {
  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
      <div className="flex items-center gap-4">
        <Avatar src={member.avatar} name={member.name} />
        <div>
          <h3 className="font-medium">{member.name}</h3>
          <p className="text-sm text-gray-500">{member.email}</p>
        </div>
        <RoleBadge role={member.role} />
      </div>

      <div className="flex items-center gap-2">
        <select
          value={member.roleId}
          onChange={(e) => onRoleChange(e.target.value)}
          className="px-3 py-1 border rounded"
        >
          {roles.map((role) => (
            <option key={role.id} value={role.id}>
              {role.name}
            </option>
          ))}
        </select>

        <button
          onClick={onRemove}
          className="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
        >
          Remove
        </button>
      </div>
    </div>
  );
}

// components/team/PermissionMatrix.tsx
export function PermissionMatrix() {
  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: () => fetch('/api/team/roles').then(r => r.json()),
  });

  const { data: permissions } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => fetch('/api/team/permissions').then(r => r.json()),
  });

  const updatePermission = useMutation({
    mutationFn: ({ roleId, permissionId, granted }: any) =>
      fetch(`/api/team/roles/${roleId}/permissions`, {
        method: 'PUT',
        body: JSON.stringify({ permissionId, granted }),
      }).then(r => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  });

  const groupedPermissions = groupBy(permissions, 'category');

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left p-2">Permission</th>
            {roles?.map((role: Role) => (
              <th key={role.id} className="p-2 text-center">
                {role.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(groupedPermissions).map(([category, perms]) => (
            <Fragment key={category}>
              <tr className="bg-gray-100">
                <td colSpan={roles.length + 1} className="p-2 font-medium">
                  {category}
                </td>
              </tr>
              {perms.map((perm: Permission) => (
                <tr key={perm.id}>
                  <td className="p-2">{perm.description}</td>
                  {roles?.map((role: Role) => {
                    const hasPermission = role.permissions.some(
                      (p: Permission) => p.id === perm.id
                    );
                    return (
                      <td key={role.id} className="text-center p-2">
                        <input
                          type="checkbox"
                          checked={hasPermission}
                          onChange={(e) =>
                            updatePermission.mutate({
                              roleId: role.id,
                              permissionId: perm.id,
                              granted: e.target.checked,
                            })
                          }
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Summary

The Team Management system provides comprehensive access control for agencies through:

- **RBAC Architecture**: Hierarchical roles with granular permissions
- **Secure Invitations**: JWT-based flow with expiration and audit trail
- **Permission Middleware**: Easy-to-use decorators for API protection
- **Audit Logging**: Complete history of all access-related events
- **Onboarding**: Guided experience for new team members
- **Best Practices**: Least privilege, separation of duties, explicit denies

This completes the Agency Settings deep dive series.

---

**Related Documents:**
- [Technical Deep Dive](./AGENCY_SETTINGS_01_TECHNICAL_DEEP_DIVE.md)
- [UX/UI Deep Dive](./AGENCY_SETTINGS_02_UX_UI_DEEP_DIVE.md)
- [Branding Deep Dive](./AGENCY_SETTINGS_03_BRANDING_DEEP_DIVE.md)

**Master Index:** [Agency Settings Deep Dive Master Index](./AGENCY_SETTINGS_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
