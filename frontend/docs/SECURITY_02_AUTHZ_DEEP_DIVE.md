# SECURITY_02: Authorization Deep Dive

> RBAC, permissions, policies, and access control

---

## Table of Contents

1. [Overview](#overview)
2. [Role-Based Access Control](#role-based-access-control)
3. [Permission System](#permission-system)
4. [Resource Authorization](#resource-authorization)
5. [Agency Isolation](#agency-isolation)
6. [Policy Engine](#policy-engine)
7. [API Authorization](#api-authorization)
8. [Admin vs Agent Access](#admin-vs-agent-access)

---

## Overview

### Authorization Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHORIZATION MODEL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User ──► Role ──► Permissions ──► Resources                    │
│   │           │            │                │                   │
│   │           │            │                │                   │
│   ▼           ▼            ▼                ▼                   │
│ John     ─►  Agent   ─► trips:*    ─►  /trips/*                │
│                │           │                                   │
│                │           └─ trips:read                        │
│                │               trips:write                      │
│                │               trips:delete                     │
│                │                                                   │
│                └─ customers:*                                   │
│                    customers:read                               │
│                    customers:write                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Access Control Layers

| Layer | Responsibility | Example |
|-------|----------------|---------|
| **Authentication** | Verify identity | JWT validation |
| **Role Assignment** | Assign role to user | User has role "agent" |
| **Role Permissions** | Define what role can do | Agent can manage trips |
| **Resource Check** | Verify ownership | Agent can only edit their trips |
| **Field Level** | Hide/show specific fields | Hide payment details from agents |

---

## Role-Based Access Control

### Role Definitions

```typescript
type UserRole =
  | 'super_admin'    // Platform administrator
  | 'agency_admin'   // Agency owner/admin
  | 'agency_manager' // Agency manager
  | 'senior_agent'   // Senior agent with extra permissions
  | 'agent'          // Regular agent
  | 'junior_agent'   // Junior agent with limited permissions
  | 'support'        // Customer support
  | 'customer';      // Customer portal user

interface Role {
  id: string;
  name: UserRole;
  description: string;
  permissions: Permission[];
  isSystemRole: boolean;  // Can't be deleted
  level: number;          // Hierarchy level for comparisons
}

export const ROLE_DEFINITIONS: Record<UserRole, Omit<Role, 'id'>> = {
  super_admin: {
    name: 'super_admin',
    description: 'Full platform access',
    permissions: ['*'], // All permissions
    isSystemRole: true,
    level: 100,
  },

  agency_admin: {
    name: 'agency_admin',
    description: 'Full agency access including billing and team management',
    permissions: [
      'agency:*',
      'trips:*',
      'customers:*',
      'quotes:*',
      'bookings:*',
      'payments:*',
      'team:*',
      'reports:*',
      'settings:*',
    ],
    isSystemRole: true,
    level: 90,
  },

  agency_manager: {
    name: 'agency_manager',
    description: 'Manage agency operations and oversee agents',
    permissions: [
      'trips:*',
      'customers:*',
      'quotes:*',
      'bookings:*',
      'reports:view',
      'team:view',
      'team:assign',
    ],
    isSystemRole: true,
    level: 70,
  },

  senior_agent: {
    name: 'senior_agent',
    description: 'Agent with additional permissions for quotes and approvals',
    permissions: [
      'trips:*',
      'customers:view',
      'customers:write',
      'quotes:*',
      'bookings:*',
      'reports:view',
    ],
    isSystemRole: true,
    level: 60,
  },

  agent: {
    name: 'agent',
    description: 'Standard agent permissions',
    permissions: [
      'trips:view',
      'trips:write',
      'trips:create',
      'customers:view',
      'customers:write',
      'customers:create',
      'quotes:view',
      'quotes:create',
      'bookings:view',
      'bookings:create',
    ],
    isSystemRole: true,
    level: 50,
  },

  junior_agent: {
    name: 'junior_agent',
    description: 'Junior agent with limited permissions',
    permissions: [
      'trips:view',
      'customers:view',
      'quotes:view',
    ],
    isSystemRole: true,
    level: 40,
  },

  support: {
    name: 'support',
    description: 'Customer support with read-only access',
    permissions: [
      'trips:view',
      'customers:view',
      'bookings:view',
    ],
    isSystemRole: true,
    level: 30,
  },

  customer: {
    name: 'customer',
    description: 'Customer portal access to own data',
    permissions: [
      'own:trips:view',
      'own:documents:view',
      'own:payments:view',
      'own:messages:write',
    ],
    isSystemRole: true,
    level: 10,
  },
};
```

### Role Assignment

```typescript
interface UserRoleAssignment {
  id: string;
  userId: string;
  agencyId: string;
  role: UserRole;
  assignedBy: string;      // User who assigned the role
  assignedAt: Date;
  expiresAt?: Date;        // Temporary role assignment
  permissions?: Permission[]; // Additional permissions beyond role
  restrictions?: Permission[]; // Permissions to restrict from role
}

export class RoleService {
  async assignRole(
    userId: string,
    role: UserRole,
    assignedBy: string,
    options?: {
      expiresAt?: Date;
      additionalPermissions?: Permission[];
      restrictions?: Permission[];
    }
  ): Promise<UserRoleAssignment> {
    // Verify assigner has permission
    const assigner = await UserRepository.findById(assignedBy);
    if (!await this.canAssignRole(assigner!, role)) {
      throw new AuthError('CANNOT_ASSIGN_ROLE', 'You cannot assign this role');
    }

    // Get user
    const user = await UserRepository.findById(userId);
    if (!user) {
      throw new ValidationError('USER_NOT_FOUND', 'User not found');
    }

    // Check if user already has this role in the agency
    const existing = await RoleAssignmentRepository.findUserAgencyRole(userId, user!.agencyId);
    if (existing) {
      await RoleAssignmentRepository.update(existing.id, {
        role,
        assignedBy,
        assignedAt: new Date(),
        expiresAt: options?.expiresAt,
        permissions: options?.additionalPermissions,
        restrictions: options?.restrictions,
      });
      return RoleAssignmentRepository.findById(existing.id)!;
    }

    // Create new assignment
    return RoleAssignmentRepository.create({
      userId,
      agencyId: user!.agencyId,
      role,
      assignedBy,
      assignedAt: new Date(),
      expiresAt: options?.expiresAt,
      permissions: options?.additionalPermissions,
      restrictions: options?.restrictions,
    });
  }

  async getUserRoles(userId: string): Promise<UserRoleAssignment[]> {
    const assignments = await RoleAssignmentRepository.findByUser(userId);

    // Filter out expired roles
    const now = new Date();
    return assignments.filter(
      (a) => !a.expiresAt || a.expiresAt > now
    );
  }

  async getUserEffectivePermissions(userId: string): Promise<Permission[]> {
    const assignments = await this.getUserRoles(userId);
    const permissions: Set<Permission> = new Set();

    for (const assignment of assignments) {
      // Get base role permissions
      const roleDef = ROLE_DEFINITIONS[assignment.role];

      for (const perm of roleDef.permissions) {
        permissions.add(perm);
      }

      // Add additional permissions
      if (assignment.permissions) {
        for (const perm of assignment.permissions) {
          permissions.add(perm);
        }
      }

      // Apply restrictions
      if (assignment.restrictions) {
        for (const perm of assignment.restrictions) {
          permissions.delete(perm);
        }
      }
    }

    return Array.from(permissions);
  }

  private async canAssignRole(assigner: User, role: UserRole): Promise<boolean> {
    // Super admin can assign any role
    if (assigner.role === 'super_admin') return true;

    // Agency admin can assign roles <= their level
    if (assigner.role === 'agency_admin') {
      const targetLevel = ROLE_DEFINITIONS[role].level;
      const assignerLevel = ROLE_DEFINITIONS[assigner.role].level;
      return targetLevel < assignerLevel;
    }

    return false;
  }
}
```

---

## Permission System

### Permission Structure

```typescript
type Permission = string;

// Permission format: resource:action
// Examples: trips:view, customers:write, quotes:delete

// Wildcard permissions
type WildcardPermission =
  | '*'               // Everything
  | 'trips:*'         // All trip actions
  | 'customers:*';    // All customer actions

export enum Resource {
  // Core resources
  TRIPS = 'trips',
  CUSTOMERS = 'customers',
  QUOTES = 'quotes',
  BOOKINGS = 'bookings',
  PAYMENTS = 'payments',
  DOCUMENTS = 'documents',

  // Communication
  MESSAGES = 'messages',
  TEMPLATES = 'templates',

  // Team & Agency
  TEAM = 'team',
  AGENCY = 'agency',
  SETTINGS = 'settings',

  // Reports & Analytics
  REPORTS = 'reports',
  ANALYTICS = 'analytics',

  // System
  USERS = 'users',
  ROLES = 'roles',
  AUDIT_LOGS = 'audit_logs',

  // Self (customer portal)
  OWN = 'own',
}

export enum Action {
  VIEW = 'view',
  CREATE = 'create',
  WRITE = 'write',
  DELETE = 'delete',
  EXPORT = 'export',
  APPROVE = 'approve',
  ASSIGN = 'assign',
  MANAGE = 'manage',
}

export class PermissionService {
  // Check if user has specific permission
  async hasPermission(userId: string, permission: Permission): Promise<boolean> {
    const userPermissions = await roleService.getUserEffectivePermissions(userId);

    // Check wildcard permission
    if (userPermissions.includes('*')) return true;

    // Check exact permission
    if (userPermissions.includes(permission)) return true;

    // Check resource wildcard
    const [resource] = permission.split(':') as [Resource, Action];
    if (userPermissions.includes(`${resource}:*`)) return true;

    return false;
  }

  // Check multiple permissions (AND logic)
  async hasAllPermissions(userId: string, permissions: Permission[]): Promise<boolean> {
    const results = await Promise.all(
      permissions.map((p) => this.hasPermission(userId, p))
    );
    return results.every((r) => r);
  }

  // Check multiple permissions (OR logic)
  async hasAnyPermission(userId: string, permissions: Permission[]): Promise<boolean> {
    const results = await Promise.all(
      permissions.map((p) => this.hasPermission(userId, p))
    );
    return results.some((r) => r);
  }

  // Get all permissions for a user
  async getUserPermissions(userId: string): Promise<Permission[]> {
    return roleService.getUserEffectivePermissions(userId);
  }

  // Filter accessible resources
  async filterAccessibleResources<T extends { id: string }>(
    userId: string,
    resources: T[],
    resourceType: Resource,
    action: Action = Action.VIEW
  ): Promise<T[]> {
    const hasWildcard = await this.hasPermission(userId, `${resourceType}:*`);
    const hasSpecific = await this.hasPermission(userId, `${resourceType}:${action}`);

    if (hasWildcard || hasSpecific) {
      return resources;
    }

    // No access - return empty
    return [];
  }
}
```

### Permission Middleware

```typescript
// Express middleware for permission checking
export const requirePermission = (permission: Permission) => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
    }

    const hasPermission = await permissionService.hasPermission(
      req.user.id,
      permission
    );

    if (!hasPermission) {
      return res.status(403).json({
        error: 'PERMISSION_DENIED',
        message: `Permission '${permission}' required`,
      });
    }

    next();
  };
};

// Require any of the listed permissions
export const requireAnyPermission = (...permissions: Permission[]) => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
    }

    const hasAny = await permissionService.hasAnyPermission(
      req.user.id,
      permissions
    );

    if (!hasAny) {
      return res.status(403).json({
        error: 'PERMISSION_DENIED',
        message: `One of permissions [${permissions.join(', ')}] required`,
      });
    }

    next();
  };
};

// Require all of the listed permissions
export const requireAllPermissions = (...permissions: Permission[]) => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
    }

    const hasAll = await permissionService.hasAllPermissions(
      req.user.id,
      permissions
    );

    if (!hasAll) {
      return res.status(403).json({
        error: 'PERMISSION_DENIED',
        message: `All permissions [${permissions.join(', ')}] required`,
      });
    }

    next();
  };
};
```

---

## Resource Authorization

### Resource-Level Access Control

```typescript
interface ResourceAccessRule {
  resource: Resource;
  action: Action;
  ownershipCheck?: 'assigned' | 'created' | 'agency';
  fieldLevelAccess?: Record<string, Permission>;
}

export class ResourceAuthorizationService {
  // Check if user can access specific resource
  async canAccessResource(
    userId: string,
    resourceType: Resource,
    resourceId: string,
    action: Action
  ): Promise<boolean> {
    // Check base permission
    const hasPermission = await permissionService.hasPermission(
      userId,
      `${resourceType}:${action}`
    );

    if (!hasPermission) return false;

    // Get resource ownership rules
    const rule = this.getAccessRule(resourceType, action);

    // No ownership check - permission is enough
    if (!rule.ownershipCheck) return true;

    // Check ownership
    return this.checkOwnership(userId, resourceType, resourceId, rule.ownershipCheck);
  }

  // Check ownership based on rule
  private async checkOwnership(
    userId: string,
    resourceType: Resource,
    resourceId: string,
    ownershipCheck: 'assigned' | 'created' | 'agency'
  ): Promise<boolean> {
    const user = await UserRepository.findById(userId);

    switch (ownershipCheck) {
      case 'assigned':
        // Resource must be assigned to user
        return ResourceRepository.isAssignedTo(resourceType, resourceId, userId);

      case 'created':
        // Resource must be created by user
        return ResourceRepository.isCreatedBy(resourceType, resourceId, userId);

      case 'agency':
        // Resource must belong to user's agency
        return ResourceRepository.isInAgency(resourceType, resourceId, user!.agencyId);

      default:
        return false;
    }
  }

  private getAccessRule(resource: Resource, action: Action): ResourceAccessRule {
    // Define access rules for each resource-action combination
    const rules: Partial<Record<Resource, Partial<Record<Action, ResourceAccessRule>>> = {
      trips: {
        view: { resource: 'trips', action: 'view', ownershipCheck: 'agency' },
        write: { resource: 'trips', action: 'write', ownershipCheck: 'assigned' },
        delete: { resource: 'trips', action: 'delete', ownershipCheck: 'assigned' },
        create: { resource: 'trips', action: 'create' },
      },
      customers: {
        view: { resource: 'customers', action: 'view', ownershipCheck: 'agency' },
        write: { resource: 'customers', action: 'write', ownershipCheck: 'agency' },
        delete: { resource: 'customers', action: 'delete', ownershipCheck: 'agency' },
      },
      payments: {
        view: {
          resource: 'payments',
          action: 'view',
          ownershipCheck: 'agency',
          fieldLevelAccess: {
            // Hide sensitive fields from non-admins
            cardNumber: 'payments:view_full',
            bankAccount: 'payments:view_full',
          },
        },
      },
      settings: {
        write: { resource: 'settings', action: 'write' }, // Only agency admin+
      },
    };

    return rules[resource]?.[action] || { resource, action };
  }

  // Filter fields based on permissions
  filterFields<T extends Record<string, any>>(
    userId: string,
    resource: Resource,
    action: Action,
    data: T
  ): Partial<T> {
    const rule = this.getAccessRule(resource, action);
    if (!rule.fieldLevelAccess) return data;

    const filtered = { ...data };
    for (const [field, requiredPermission] of Object.entries(rule.fieldLevelAccess)) {
      // For now, do synchronous check (in real app, this would be async)
      // User should have their permissions loaded on the request
      delete filtered[field as keyof T];
    }

    return filtered;
  }
}
```

### Authorization Decorator (for classes)

```typescript
// TypeScript decorator for route handlers
export function Authorize(permission: Permission) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const [req, res] = args;

      if (!req.user) {
        return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
      }

      const hasPermission = await permissionService.hasPermission(
        req.user.id,
        permission
      );

      if (!hasPermission) {
        return res.status(403).json({
          error: 'PERMISSION_DENIED',
          message: `Permission '${permission}' required`,
        });
      }

      return originalMethod.apply(this, args);
    };

    return descriptor;
  };
}

// Usage
export class TripController {
  @Authorize('trips:view')
  async getTrips(req: AuthenticatedRequest, res: Response) {
    const trips = await TripRepository.findByAgency(req.user.agencyId);
    res.json(trips);
  }

  @Authorize('trips:delete')
  async deleteTrip(req: AuthenticatedRequest, res: Response) {
    const { id } = req.params;

    // Check ownership
    const canDelete = await resourceAuth.canAccessResource(
      req.user.id,
      'trips',
      id,
      'delete'
    );

    if (!canDelete) {
      return res.status(403).json({
        error: 'PERMISSION_DENIED',
        message: 'You can only delete trips assigned to you',
      });
    }

    await TripRepository.delete(id);
    res.json({ success: true });
  }
}
```

---

## Agency Isolation

### Multi-Tenancy Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENCY ISOLATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Agency A (user@agencya.com)                                    │
│  ├── Trip 1 (visible only to Agency A users)                   │
│  ├── Trip 2                                                     │
│  └── Customer X                                                 │
│                                                                  │
│  Agency B (user@agencyb.com)                                    │
│  ├── Trip 3 (visible only to Agency B users)                   │
│  ├── Trip 4                                                     │
│  └── Customer Y                                                 │
│                                                                  │
│  Super Admin                                                    │
│  └── Can see all agencies (for support)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agency Isolation Middleware

```typescript
// Enforce agency isolation on all queries
export const enforceAgencyIsolation = () => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) return next();

    // Super admin bypasses isolation
    if (req.user.role === 'super_admin') return next();

    // Inject agency filter into query context
    req.context = {
      ...req.context,
      agencyId: req.user.agencyId,
      agencyIsolation: true,
    };

    next();
  };
};

// Repository-level agency filtering
export class TripRepository {
  static async findByAgency(agencyId: string): Promise<Trip[]> {
    return db.trips.where({ agencyId });
  }

  static async findById(id: string, requestingUserId: string): Promise<Trip | null> {
    const user = await UserRepository.findById(requestingUserId);

    // Super admin can access any trip
    if (user!.role === 'super_admin') {
      return db.trips.findById(id);
    }

    // Otherwise, enforce agency isolation
    return db.trips.where({ id, agencyId: user!.agencyId }).first();
  }

  static async findAccessible(userId: string, filters: TripFilters): Promise<Trip[]> {
    const user = await UserRepository.findById(userId);

    let query = db.trips;

    // Super admin sees all
    if (user!.role !== 'super_admin') {
      query = query.where({ agencyId: user!.agencyId });

      // Agents only see assigned trips unless they have view_all permission
      const canViewAll = await permissionService.hasPermission(userId, 'trips:view_all');
      if (!canViewAll && ['agent', 'junior_agent'].includes(user!.role)) {
        query = query.where((trip) =>
          trip.assignedTo === userId || trip.createdBy === userId
        );
      }
    }

    return query.where(filters);
  }
}
```

### Cross-Agency Access Control

```typescript
// Control when agencies can interact
export class CrossAgencyService {
  // Check if users from different agencies can interact
  async canInteract(
    userAId: string,
    userBId: string,
    interaction: 'view' | 'message' | 'transfer'
  ): Promise<boolean> {
    const userA = await UserRepository.findById(userAId);
    const userB = await UserRepository.findById(userBId);

    // Same agency - always allowed
    if (userA!.agencyId === userB!.agencyId) return true;

    // Cross-agency interactions require special permission
    const hasPermission = await permissionService.hasPermission(
      userAId,
      `cross_agency:${interaction}`
    );

    return hasPermission;
  }

  // Transfer trip between agencies (rare, requires approval)
  async transferTrip(
    tripId: string,
    fromAgencyId: string,
    toAgencyId: string,
    requestedBy: string
  ): Promise<void> {
    // Verify requester is admin of source agency
    const requester = await UserRepository.findById(requestedBy);
    if (requester!.agencyId !== fromAgencyId || requester!.role !== 'agency_admin') {
      throw new AuthError('UNAUTHORIZED', 'Only agency admin can initiate transfer');
    }

    // Verify target agency exists and accepts transfers
    const targetAgency = await AgencyRepository.findById(toAgencyId);
    if (!targetAgency || !targetAgency.acceptsTransfers) {
      throw new ValidationError('INVALID_AGENCY', 'Target agency not found or does not accept transfers');
    }

    // Create transfer request
    await TransferRequestRepository.create({
      tripId,
      fromAgencyId,
      toAgencyId,
      requestedBy,
      status: 'pending_approval',
      createdAt: new Date(),
    });

    // Notify both agencies
    await notificationService.sendToAgency(fromAgencyId, {
      type: 'transfer_initiated',
      title: 'Trip transfer initiated',
      message: `Trip transfer to ${targetAgency.name} awaiting approval`,
    });

    await notificationService.sendToAgency(toAgencyId, {
      type: 'transfer_pending',
      title: 'Incoming trip transfer',
      message: `Agency requesting to transfer trip to your agency`,
    });
  }
}
```

---

## Policy Engine

### Policy Definition Language

```typescript
interface Policy {
  id: string;
  name: string;
  description: string;
  effect: 'allow' | 'deny';
  resources: string[];      // Resource patterns
  actions: string[];        // Action patterns
  conditions?: PolicyCondition[];
}

interface PolicyCondition {
  type: 'ip' | 'time' | 'location' | 'attribute' | 'role';
  operator: 'equals' | 'not_equals' | 'in' | 'not_in' | 'matches';
  value: any;
}

export class PolicyEngine {
  private policies: Policy[] = [];

  constructor() {
    this.loadPolicies();
  }

  // Load policies from database/config
  private async loadPolicies(): Promise<void> {
    // Built-in policies
    this.policies = [
      {
        id: 'deny-agents-delete-after-hours',
        name: 'Deny trip deletion outside business hours',
        description: 'Agents cannot delete trips between 10pm and 6am',
        effect: 'deny',
        resources: ['trips'],
        actions: ['delete'],
        conditions: [
          {
            type: 'time',
            operator: 'in',
            value: { start: '22:00', end: '06:00' },
          },
          {
            type: 'role',
            operator: 'in',
            value: ['agent', 'junior_agent'],
          },
        ],
      },
      {
        id: 'require-approval-for-large-bookings',
        name: 'Require approval for bookings over threshold',
        description: 'Bookings over ₹5,00,000 require manager approval',
        effect: 'deny',
        resources: ['bookings'],
        actions: ['create', 'confirm'],
        conditions: [
          {
            type: 'attribute',
            operator: 'matches',
            value: { field: 'amount', operator: 'gt', value: 500000 },
          },
        ],
      },
      {
        id: 'restrict-api-access-by-ip',
        name: 'Restrict API access to known IPs',
        description: 'API access only from whitelisted IPs',
        effect: 'deny',
        resources: ['*'],
        actions: ['*'],
        conditions: [
          {
            type: 'ip',
            operator: 'not_in',
            value: [], // Whitelisted IPs
          },
        ],
      },
    ];
  }

  // Evaluate policies for a request
  async evaluate(request: PolicyRequest): Promise<PolicyDecision> {
    const applicablePolicies = this.getApplicablePolicies(request);

    // Default deny
    let decision: PolicyDecision = {
      allowed: false,
      reason: 'No applicable policy',
    };

    for (const policy of applicablePolicies) {
      const conditionsMet = await this.evaluateConditions(
        policy.conditions || [],
        request
      );

      if (conditionsMet) {
        if (policy.effect === 'deny') {
          return {
            allowed: false,
            reason: policy.name,
            policyId: policy.id,
          };
        } else {
          decision = {
            allowed: true,
            reason: policy.name,
            policyId: policy.id,
          };
        }
      }
    }

    return decision;
  }

  private getApplicablePolicies(request: PolicyRequest): Policy[] {
    return this.policies.filter((policy) =>
      this.matchesResource(policy.resources, request.resource) &&
      this.matchesAction(policy.actions, request.action)
    );
  }

  private matchesResource(patterns: string[], resource: string): boolean {
    return patterns.some((p) =>
      p === '*' || p === resource || this.wildcardMatch(p, resource)
    );
  }

  private matchesAction(patterns: string[], action: string): boolean {
    return patterns.some((p) =>
      p === '*' || p === action || this.wildcardMatch(p, action)
    );
  }

  private wildcardMatch(pattern: string, value: string): boolean {
    const regex = new RegExp(
      '^' + pattern.replace(/\*/g, '.*').replace(/\?/g, '.') + '$'
    );
    return regex.test(value);
  }

  private async evaluateConditions(
    conditions: PolicyCondition[],
    request: PolicyRequest
  ): Promise<boolean> {
    for (const condition of conditions) {
      const result = await this.evaluateCondition(condition, request);
      if (!result) return false;
    }
    return true;
  }

  private async evaluateCondition(
    condition: PolicyCondition,
    request: PolicyRequest
  ): Promise<boolean> {
    switch (condition.type) {
      case 'role':
        return this.evaluateRoleCondition(condition, request);

      case 'time':
        return this.evaluateTimeCondition(condition);

      case 'ip':
        return this.evaluateIpCondition(condition, request);

      case 'attribute':
        return this.evaluateAttributeCondition(condition, request);

      case 'location':
        return this.evaluateLocationCondition(condition, request);

      default:
        return true;
    }
  }

  private evaluateRoleCondition(condition: PolicyCondition, request: PolicyRequest): boolean {
    const roles = condition.value as string[];
    return this.operatorMatch(roles, request.userRole, condition.operator);
  }

  private evaluateTimeCondition(condition: PolicyCondition): boolean {
    const { start, end } = condition.value;
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    const [startHour, startMin] = start.split(':').map(Number);
    const [endHour, endMin] = end.split(':').map(Number);
    const startTime = startHour * 60 + startMin;
    const endTime = endHour * 60 + endMin;

    // Handle overnight range (e.g., 22:00 to 06:00)
    if (startTime > endTime) {
      return currentTime >= startTime || currentTime <= endTime;
    }

    return currentTime >= startTime && currentTime <= endTime;
  }

  private evaluateIpCondition(condition: PolicyCondition, request: PolicyRequest): boolean {
    const allowedIps = condition.value as string[];
    return this.operatorMatch(allowedIps, request.ip, condition.operator);
  }

  private evaluateAttributeCondition(condition: PolicyCondition, request: PolicyRequest): boolean {
    const { field, operator: attrOp, value: attrValue } = condition.value;
    const actualValue = request.attributes?.[field];

    switch (attrOp) {
      case 'eq':
        return actualValue === attrValue;
      case 'gt':
        return actualValue > attrValue;
      case 'lt':
        return actualValue < attrValue;
      case 'gte':
        return actualValue >= attrValue;
      case 'lte':
        return actualValue <= attrValue;
      default:
        return false;
    }
  }

  private evaluateLocationCondition(condition: PolicyCondition, request: PolicyRequest): boolean {
    const locations = condition.value as string[];
    return this.operatorMatch(locations, request.location?.country, condition.operator);
  }

  private operatorMatch(
    expected: any[],
    actual: any,
    operator: string
  ): boolean {
    switch (operator) {
      case 'equals':
        return expected.includes(actual);
      case 'not_equals':
        return !expected.includes(actual);
      case 'in':
        return expected.includes(actual);
      case 'not_in':
        return !expected.includes(actual);
      default:
        return false;
    }
  }
}

interface PolicyRequest {
  userId: string;
  userRole: UserRole;
  agencyId: string;
  resource: string;
  action: string;
  ip?: string;
  location?: { country: string; city: string };
  attributes?: Record<string, any>;
}

interface PolicyDecision {
  allowed: boolean;
  reason: string;
  policyId?: string;
}
```

---

## API Authorization

### Route-Level Authorization

```typescript
// API route definitions with authorization
export const tripRoutes = Router();

// All trip routes require authentication
tripRoutes.use(authenticate);

// Get trips - requires trips:view permission
tripRoutes.get('/',
  requirePermission('trips:view'),
  async (req: AuthenticatedRequest, res: Response) => {
    const trips = await TripRepository.findAccessible(req.user.id, req.query);
    res.json(trips);
  }
);

// Create trip - requires trips:create permission
tripRoutes.post('/',
  requirePermission('trips:create'),
  async (req: AuthenticatedRequest, res: Response) => {
    const trip = await TripRepository.create({
      ...req.body,
      agencyId: req.user.agencyId,
      createdBy: req.user.id,
      assignedTo: req.user.id,
    });
    res.status(201).json(trip);
  }
);

// Update trip - resource-level authorization
tripRoutes.patch('/:id',
  requirePermission('trips:write'),
  async (req: AuthenticatedRequest, res: Response) => {
    const { id } = req.params;

    // Check if user can modify this specific trip
    const canModify = await resourceAuth.canAccessResource(
      req.user.id,
      'trips',
      id,
      'write'
    );

    if (!canModify) {
      return res.status(403).json({
        error: 'PERMISSION_DENIED',
        message: 'You can only modify trips assigned to you',
      });
    }

    const trip = await TripRepository.update(id, req.body);
    res.json(trip);
  }
);

// Delete trip - higher permission required
tripRoutes.delete('/:id',
  requirePermission('trips:delete'),
  async (req: AuthenticatedRequest, res: Response) => {
    const { id } = req.params;

    // Policy engine check
    const decision = await policyEngine.evaluate({
      userId: req.user.id,
      userRole: req.user.role,
      agencyId: req.user.agencyId,
      resource: 'trips',
      action: 'delete',
      ip: req.ip,
    });

    if (!decision.allowed) {
      return res.status(403).json({
        error: 'POLICY_DENIED',
        message: decision.reason,
      });
    }

    await TripRepository.delete(id);
    res.json({ success: true });
  }
);
```

### GraphQL Authorization

```typescript
// GraphQL authorization directive
export const authorizationDirective = (schema: GraphQLSchema) => {
  return makeExecutableSchema({
    schemaDirectives: {
      auth: AuthDirective,
      hasPermission: HasPermissionDirective,
    },
    typeDefs: schema,
    resolvers: {},
  });
};

// @auth directive - requires authentication
class AuthDirective extends SchemaDirectiveVisitor {
  visitFieldDefinition(field: any) {
    const { resolve = defaultFieldResolver } = field;

    field.resolve = async function (...args: any[]) {
      const [source, , ctx] = args;

      if (!ctx.user) {
        throw new AuthenticationError('You must be logged in');
      }

      return resolve.apply(this, args);
    };
  }
}

// @hasPermission directive - requires specific permission
class HasPermissionDirective extends SchemaDirectiveVisitor {
  visitFieldDefinition(field: any) {
    const { resolve = defaultFieldResolver } = field;
    const requiredPermission = this.args.permission;

    field.resolve = async function (...args: any[]) {
      const [source, , ctx] = args;

      if (!ctx.user) {
        throw new AuthenticationError('You must be logged in');
      }

      const hasPermission = await permissionService.hasPermission(
        ctx.user.id,
        requiredPermission
      );

      if (!hasPermission) {
        throw new ForbiddenError(`Permission '${requiredPermission}' required`);
      }

      return resolve.apply(this, args);
    };
  }
}

// Schema example
const typeDefs = `
  directive @auth on FIELD_DEFINITION
  directive @hasPermission(permission: String!) on FIELD_DEFINITION

  type Trip {
    id: ID!
    name: String!
    destination: String!
    # Hidden fields based on permission
    cost: Float @hasPermission(permission: "trips:view_cost")
    margin: Float @hasPermission(permission: "trips:view_margin")
  }

  type Query {
    trips: [Trip!]! @auth
    trip(id: ID!): Trip @hasPermission(permission: "trips:view")
  }

  type Mutation {
    createTrip(input: TripInput!): Trip! @hasPermission(permission: "trips:create")
    deleteTrip(id: ID!): Boolean! @hasPermission(permission: "trips:delete")
  }
`;
```

---

## Admin vs Agent Access

### Permission Comparison

| Resource | Action | Admin | Manager | Senior Agent | Agent | Junior |
|----------|--------|-------|---------|--------------|-------|--------|
| **Trips** | View | ✅ | ✅ | ✅ | ✅ | ✅ |
| | Create | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Edit own | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Edit all | ✅ | ✅ | ✅ | ❌ | ❌ |
| | Delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Quotes** | View | ✅ | ✅ | ✅ | ✅ | ✅ |
| | Create | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Send | ✅ | ✅ | ✅ | ❌ | ❌ |
| | Approve | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Customers** | View | ✅ | ✅ | ✅ | ✅ | ✅ |
| | Create | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Edit | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Payments** | View | ✅ | ✅ | ✅ | ✅ | ❌ |
| | Process | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Refund | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Team** | View | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Assign | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Invite | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Reports** | View | ✅ | ✅ | ✅ | ❌ | ❌ |
| | Export | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Settings** | View | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Edit | ✅ | ✅ | ❌ | ❌ | ❌ |

### Role Hierarchy

```typescript
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  super_admin: 100,
  agency_admin: 90,
  agency_manager: 70,
  senior_agent: 60,
  agent: 50,
  junior_agent: 40,
  support: 30,
  customer: 10,
};

export class RoleHierarchyService {
  // Check if user has higher or equal role
  hasRoleOrHigher(userRole: UserRole, requiredRole: UserRole): boolean {
    return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
  }

  // Get all users with role >= given role
  async getUsersWithRoleOrHigher(role: UserRole, agencyId: string): Promise<User[]> {
    const rolesAtOrAbove = Object.entries(ROLE_HIERARCHY)
      .filter(([_, level]) => level >= ROLE_HIERARCHY[role])
      .map(([r]) => r as UserRole);

    return UserRepository.findByAgencyAndRoles(agencyId, rolesAtOrAbove);
  }

  // Check if user can assign another user to a role
  canAssignToRole(assignerRole: UserRole, targetRole: UserRole): boolean {
    // Can only assign to lower roles
    return ROLE_HIERARCHY[assignerRole] > ROLE_HIERARCHY[targetRole];
  }
}
```

---

**Last Updated:** 2026-04-25

**Next:** SECURITY_03 — Data Security Deep Dive (Encryption, secrets, PII protection)
