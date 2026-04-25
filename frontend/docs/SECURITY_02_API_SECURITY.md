# SECURITY_02: API Security

> API authentication, authorization, rate limiting, and secure API practices

---

## Document Overview

**Series:** Security Hardening
**Document:** 2 of 4
**Focus:** API Security
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [API Authentication](#api-authentication)
3. [Authorization & Permissions](#authorization--permissions)
4. [Rate Limiting](#rate-limiting)
5. [API Key Management](#api-key-management)
6. [Webhook Security](#webhook-security)
7. [GraphQL Security](#graphql-security)
8. [API Gateway Security](#api-gateway-security)
9. [DDoS Protection](#ddos-protection)
10. [API Security Testing](#api-security-testing)

---

## 1. Introduction

### API Security Principles

API security protects the interfaces that connect all components of the Travel Agency Agent:

- **Public APIs** - Customer portal, mobile app integrations
- **Internal APIs** - Microservice communication
- **Partner APIs** - Supplier integrations, webhooks
- **Admin APIs** - Management interfaces

### Threat Model

| Threat | Impact | Mitigation |
|--------|--------|------------|
| **Unauthorized Access** | Data breach | Strong authentication, MFA |
| **API Abuse** | Service degradation | Rate limiting, quotas |
| **Data Scraping** | Intellectual property loss | Bot detection |
| **Man-in-the-Middle** | Data interception | TLS, certificate pinning |
| **Injection Attacks** | System compromise | Input validation |
| **DDoS** | Service unavailability | Rate limiting, CDN |

---

## 2. API Authentication

### JWT Authentication

```typescript
// auth/jwt.ts

import jwt from 'jsonwebtoken';
import { JWK, JWKS } from 'jose';

/**
 * JWT token service
 */
export class JWTService {
  private privateKey: string;
  private publicKey: string;
  private keyId: string;

  constructor() {
    this.privateKey = process.env.JWT_PRIVATE_KEY || this.generateKeyPair();
    this.publicKey = process.env.JWT_PUBLIC_KEY || this.getPublicKey();
    this.keyId = process.env.JWT_KEY_ID || 'key-1';
  }

  /**
   * Generate access token
   */
  async generateAccessToken(payload: AccessTokenPayload): Promise<string> {
    const token = jwt.sign(payload, this.privateKey, {
      algorithm: 'RS256',
      keyid: this.keyId,
      expiresIn: '15m',
      issuer: 'travel-agency-agent',
      audience: 'api'
    });

    return token;
  }

  /**
   * Generate refresh token
   */
  async generateRefreshToken(userId: string): Promise<string> {
    const tokenId = crypto.randomUUID();

    const token = jwt.sign(
      {
        userId,
        tokenId,
        type: 'refresh'
      },
      this.privateKey,
      {
        algorithm: 'RS256',
        expiresIn: '30d',
        issuer: 'travel-agency-agent',
        audience: 'auth'
      }
    );

    // Store token ID for revocation
    await this.refreshTokenStore.set(tokenId, {
      userId,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    });

    return token;
  }

  /**
   * Verify and decode token
   */
  async verifyToken(token: string): Promise<{
    valid: boolean;
    payload?: AccessTokenPayload;
    error?: string
  }> {
    try {
      const decoded = jwt.verify(token, this.publicKey, {
        issuer: 'travel-agency-agent',
        algorithms: ['RS256']
      }) as AccessTokenPayload;

      // Check if token is revoked
      if (decoded.type === 'refresh') {
        const stored = await this.refreshTokenStore.get(decoded.tokenId);
        if (!stored) {
          return { valid: false, error: 'Token revoked' };
        }
      }

      return { valid: true, payload: decoded };
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        return { valid: false, error: 'Token expired' };
      }
      if (error instanceof jwt.JsonWebTokenError) {
        return { valid: false, error: 'Invalid token' };
      }
      return { valid: false, error: 'Verification failed' };
    }
  }

  /**
   * Revoke refresh token
   */
  async revokeRefreshToken(token: string): Promise<void> {
    const decoded = jwt.decode(token) as RefreshTokenPayload;

    if (decoded?.tokenId) {
      await this.refreshTokenStore.delete(decoded.tokenId);
    }
  }
}

/**
 * Express middleware for JWT authentication
 */
export function authenticateJWT(options: {
  required?: boolean;
  refreshToken?: boolean;
} = {}) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      if (options.required) {
        return res.status(401).json({ error: 'Missing authorization header' });
      }
      return next();
    }

    const token = authHeader.replace('Bearer ', '');
    const jwtService = new JWTService();

    const result = await jwtService.verifyToken(token);

    if (!result.valid) {
      return res.status(401).json({ error: result.error || 'Invalid token' });
    }

    req.user = {
      id: result.payload!.userId,
      roles: result.payload!.roles,
      agencyId: result.payload!.agencyId
    };

    req.token = token;

    next();
  };
}

/**
 * API key authentication for external integrations
 */
export class APIKeyAuth {
  /**
   * Verify API key
   */
  async verifyAPIKey(key: string): Promise<{
    valid: boolean;
    credentials?: APIKeyCredentials;
    error?: string;
  }> {
    // Check key format
    if (!key.startsWith('ta_')) {
      return { valid: false, error: 'Invalid API key format' };
    }

    // Lookup in database
    const credentials = await this.apiKeyStore.findByKey(key);

    if (!credentials) {
      return { valid: false, error: 'API key not found' };
    }

    // Check if active
    if (!credentials.active) {
      return { valid: false, error: 'API key inactive' };
    }

    // Check expiration
    if (credentials.expiresAt && credentials.expiresAt < new Date()) {
      return { valid: false, error: 'API key expired' };
    }

    // Check rate limits
    const usage = await this.rateLimitTracker.check(credentials.id);
    if (!usage.allowed) {
      return { valid: false, error: 'Rate limit exceeded' };
    }

    // Update last used
    await this.apiKeyStore.updateLastUsed(credentials.id);

    return {
      valid: true,
      credentials: {
        id: credentials.id,
        agencyId: credentials.agencyId,
        scopes: credentials.scopes,
        rateLimit: credentials.rateLimit
      }
    };
  }

  /**
   * Express middleware for API key auth
   */
  middleware() {
    return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      const apiKey = req.headers['x-api-key'] as string;

      if (!apiKey) {
        return res.status(401).json({ error: 'Missing API key' });
      }

      const result = await this.verifyAPIKey(apiKey);

      if (!result.valid) {
        return res.status(401).json({ error: result.error });
      }

      req.apiKey = result.credentials;
      req.user = {
        id: result.credentials.id,
        agencyId: result.credentials.agencyId,
        scopes: result.credentials.scopes
      };

      next();
    };
  }
}
```

### OAuth 2.0 / OpenID Connect

```typescript
// auth/oauth.ts

/**
 * OAuth 2.0 authorization server
 */
export class OAuthServer {
  /**
   * Generate authorization code
   */
  async generateAuthorizationCode(request: {
    clientId: string;
    redirectUri: string;
    scope: string[];
    userId: string;
  }): Promise<string> {
    // Validate client
    const client = await this.clientStore.findByClientId(request.clientId);
    if (!client) {
      throw new Error('Invalid client_id');
    }

    // Validate redirect URI
    if (!client.redirectUris.includes(request.redirectUri)) {
      throw new Error('Invalid redirect_uri');
    }

    // Validate scope
    const validScopes = this.validateScopes(request.scope, client.allowedScopes);
    if (validScopes.length === 0) {
      throw new Error('Invalid scope');
    }

    // Generate authorization code
    const code = crypto.randomBytes(32).toString('base64url');

    await this.authorizationCodeStore.set(code, {
      clientId: request.clientId,
      redirectUri: request.redirectUri,
      scopes: validScopes,
      userId: request.userId,
      expiresAt: new Date(Date.now() + 10 * 60 * 1000)  // 10 minutes
    });

    return code;
  }

  /**
   * Exchange authorization code for tokens
   */
  async exchangeCodeForTokens(request: {
    code: string;
    clientId: string;
    clientSecret: string;
    redirectUri: string;
  }): Promise<TokenResponse> {
    // Verify client credentials
    const client = await this.clientStore.findByClientId(request.clientId);

    if (!client || client.secret !== request.clientSecret) {
      throw new Error('Invalid client credentials');
    }

    // Get authorization code
    const authCode = await this.authorizationCodeStore.get(request.code);

    if (!authCode) {
      throw new Error('Invalid authorization code');
    }

    if (authCode.expiresAt < new Date()) {
      throw new Error('Authorization code expired');
    }

    if (authCode.clientId !== request.clientId) {
      throw new Error('Client ID mismatch');
    }

    if (authCode.redirectUri !== request.redirectUri) {
      throw new Error('Redirect URI mismatch');
    }

    // Delete authorization code (single use)
    await this.authorizationCodeStore.delete(request.code);

    // Generate tokens
    const jwtService = new JWTService();

    const accessToken = await jwtService.generateAccessToken({
      userId: authCode.userId,
      clientId: authCode.clientId,
      scopes: authCode.scopes
    });

    const refreshToken = await jwtService.generateRefreshToken(authCode.userId);

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'Bearer',
      expires_in: 15 * 60,  // 15 minutes
      scope: authCode.scopes.join(' ')
    };
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
    const jwtService = new JWTService();
    const result = await jwtService.verifyToken(refreshToken);

    if (!result.valid || result.payload?.type !== 'refresh') {
      throw new Error('Invalid refresh token');
    }

    // Get user's scopes
    const user = await this.userStore.findById(result.payload.userId);

    const accessToken = await jwtService.generateAccessToken({
      userId: user.id,
      scopes: user.defaultScopes
    });

    return {
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: 15 * 60
    };
  }

  /**
   * Validate OAuth scopes
   */
  private validateScopes(requested: string[], allowed: string[]): string[] {
    return requested.filter(scope => allowed.includes(scope));
  }
}
```

---

## 3. Authorization & Permissions

### Role-Based Access Control

```typescript
// auth/rbac.ts

export enum Permission {
  // Trip management
  TRIP_CREATE = 'trip:create',
  TRIP_READ = 'trip:read',
  TRIP_UPDATE = 'trip:update',
  TRIP_DELETE = 'trip:delete',
  TRIP_READ_ALL = 'trip:read_all',

  // Customer management
  CUSTOMER_CREATE = 'customer:create',
  CUSTOMER_READ = 'customer:read',
  CUSTOMER_UPDATE = 'customer:update',
  CUSTOMER_DELETE = 'customer:delete',

  // Agency management
  AGENCY_READ = 'agency:read',
  AGENCY_UPDATE = 'agency:update',
  AGENCY_MANAGE_USERS = 'agency:manage_users',
  AGENCY_MANAGE_SETTINGS = 'agency:manage_settings',

  // Admin
  ADMIN = 'admin',
  ADMIN_ANALYTICS = 'admin:analytics',
  ADMIN_REPORTS = 'admin:reports'
}

export enum Role {
  SUPER_ADMIN = 'super_admin',
  AGENCY_OWNER = 'agency_owner',
  AGENCY_ADMIN = 'agency_admin',
  AGENT = 'agent',
  CUSTOMER = 'customer'
}

/**
 * Role-Permission mapping
 */
export const rolePermissions: Record<Role, Permission[]> = {
  [Role.SUPER_ADMIN]: Object.values(Permission),

  [Role.AGENCY_OWNER]: [
    Permission.TRIP_CREATE,
    Permission.TRIP_READ,
    Permission.TRIP_UPDATE,
    Permission.TRIP_DELETE,
    Permission.TRIP_READ_ALL,
    Permission.CUSTOMER_CREATE,
    Permission.CUSTOMER_READ,
    Permission.CUSTOMER_UPDATE,
    Permission.AGENCY_READ,
    Permission.AGENCY_UPDATE,
    Permission.AGENCY_MANAGE_USERS,
    Permission.AGENCY_MANAGE_SETTINGS
  ],

  [Role.AGENCY_ADMIN]: [
    Permission.TRIP_CREATE,
    Permission.TRIP_READ,
    Permission.TRIP_UPDATE,
    Permission.TRIP_READ_ALL,
    Permission.CUSTOMER_CREATE,
    Permission.CUSTOMER_READ,
    Permission.CUSTOMER_UPDATE,
    Permission.AGENCY_READ,
    Permission.AGENCY_MANAGE_USERS
  ],

  [Role.AGENT]: [
    Permission.TRIP_CREATE,
    Permission.TRIP_READ,
    Permission.TRIP_UPDATE,
    Permission.CUSTOMER_CREATE,
    Permission.CUSTOMER_READ,
    Permission.CUSTOMER_UPDATE,
    Permission.AGENCY_READ
  ],

  [Role.CUSTOMER]: [
    Permission.TRIP_READ,  // Only own trips
    Permission.CUSTOMER_READ,  // Only own profile
    Permission.AGENCY_READ
  ]
};

/**
 * Authorization service
 */
export class AuthorizationService {
  /**
   * Check if user has permission
   */
  async hasPermission(userId: string, permission: Permission): Promise<boolean> {
    const user = await this.userStore.findById(userId);

    if (!user) {
      return false;
    }

    // Get all user's roles
    const roles = await this.getUserRoles(userId);

    // Check each role for permission
    for (const role of roles) {
      const permissions = rolePermissions[role] || [];

      if (permissions.includes(permission)) {
        return true;
      }

      // Admin wildcard
      if (permissions.includes(Permission.ADMIN)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Check if user can access specific resource
   */
  async canAccessResource(userId: string, resource: {
    type: string;
    id: string;
    action: string;
  }): Promise<boolean> {
    // First check general permission
    const permission = this.getActionPermission(resource.type, resource.action);

    if (!await this.hasPermission(userId, permission)) {
      return false;
    }

    // Then check resource-level access
    return await this.checkResourceAccess(userId, resource);
  }

  /**
   * Get action permission for resource type
   */
  private getActionPermission(resourceType: string, action: string): Permission {
    return `${resourceType}:${action}` as Permission;
  }

  /**
   * Check resource-level access (ownership, agency membership, etc.)
   */
  private async checkResourceAccess(userId: string, resource: {
    type: string;
    id: string;
  }): Promise<boolean> {
    switch (resource.type) {
      case 'trip':
        return await this.checkTripAccess(userId, resource.id);

      case 'customer':
        return await this.checkCustomerAccess(userId, resource.id);

      case 'agency':
        return await this.checkAgencyAccess(userId, resource.id);

      default:
        return true;
    }
  }

  /**
   * Express middleware for authorization
   */
  requirePermission(permission: Permission) {
    return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({ error: 'Not authenticated' });
      }

      const authz = new AuthorizationService();
      const hasPermission = await authz.hasPermission(req.user.id, permission);

      if (!hasPermission) {
        return res.status(403).json({
          error: 'Insufficient permissions',
          required: permission
        });
      }

      next();
    };
  }

  /**
   * Express middleware for resource-level authorization
   */
  requireAccess(action: string, resourceType: string) {
    return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({ error: 'Not authenticated' });
      }

      const authz = new AuthorizationService();
      const hasAccess = await authz.canAccessResource(req.user.id, {
        type: resourceType,
        id: req.params.id,
        action
      });

      if (!hasAccess) {
        return res.status(403).json({
          error: 'Access denied to this resource'
        });
      }

      next();
    };
  }
}
```

### Scope-Based Authorization

```typescript
// auth/scopes.ts

/**
 * OAuth scope definitions
 */
export const scopes = {
  // Trip scopes
  'trips.read': 'Read your trips',
  'trips.write': 'Create and modify your trips',
  'trips.all': 'Access all trips (agent only)',

  // Customer scopes
  'profile.read': 'Read your profile',
  'profile.write': 'Update your profile',

  // Agency scopes
  'agency.read': 'Read agency information',
  'agency.manage': 'Manage agency settings',

  // Booking scopes
  'bookings.read': 'Read booking information',
  'bookings.write': 'Create and modify bookings',
  'payments.write': 'Process payments',

  // Admin scopes
  'admin.analytics': 'Access analytics dashboard',
  'admin.users': 'Manage users',
  'admin.reports': 'Access reports'
};

/**
 * Scope checker
 */
export class ScopeChecker {
  /**
   * Check if granted scopes cover required scope
   */
  async hasScope(grantedScopes: string[], requiredScope: string): Promise<boolean> {
    // Direct match
    if (grantedScopes.includes(requiredScope)) {
      return true;
    }

    // Wildcard scope
    if (grantedScopes.includes('*')) {
      return true;
    }

    // Hierarchical scope (e.g., trips.write implies trips.read)
    const [resource] = requiredScope.split('.');
    if (grantedScopes.includes(`${resource}.write`)) {
      return true;
    }

    return false;
  }

  /**
   * Check if request has all required scopes
   */
  async requireScopes(requiredScopes: string[]) {
    return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      const userScopes = req.user?.scopes || [];

      const missing = requiredScopes.filter(scope =>
        !this.hasScope(userScopes, scope)
      );

      if (missing.length > 0) {
        return res.status(403).json({
          error: 'Insufficient scopes',
          required: requiredScopes,
          missing
        });
      }

      next();
    };
  }
}
```

---

## 4. Rate Limiting

### Token Bucket Rate Limiter

```typescript
// rate-limit/token-bucket.ts

export interface RateLimitConfig {
  requests: number;
  window: number;  // milliseconds
  burst?: number;
}

/**
 * Token bucket rate limiter
 */
export class TokenBucketRateLimiter {
  private buckets = new Map<string, TokenBucket>();
  private cleanupInterval: NodeJS.Timeout;

  constructor() {
    // Clean up expired buckets every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60 * 1000);
  }

  /**
   * Check if request is allowed
   */
  async checkLimit(identifier: string, config: RateLimitConfig): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: Date;
  }> {
    let bucket = this.buckets.get(identifier);

    const now = Date.now();

    if (!bucket || bucket.resetAt < now) {
      // Create new bucket
      bucket = {
        tokens: config.requests,
        capacity: config.requests,
        lastRefill: now,
        resetAt: now + config.window
      };
      this.buckets.set(identifier, bucket);
    } else {
      // Refill tokens based on time passed
      const timePassed = now - bucket.lastRefill;
      const tokensToAdd = (timePassed / config.window) * config.requests;

      bucket.tokens = Math.min(
        config.requests,
        bucket.tokens + tokensToAdd
      );
      bucket.lastRefill = now;
    }

    // Check if tokens available
    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return {
        allowed: true,
        remaining: Math.floor(bucket.tokens),
        resetAt: new Date(bucket.resetAt)
      };
    }

    return {
      allowed: false,
      remaining: 0,
      resetAt: new Date(bucket.resetAt)
    };
  }

  /**
   * Reset rate limit for identifier
   */
  async reset(identifier: string): Promise<void> {
    this.buckets.delete(identifier);
  }

  /**
   * Clean up expired buckets
   */
  private cleanup(): void {
    const now = Date.now();

    for (const [identifier, bucket] of this.buckets) {
      if (bucket.resetAt < now) {
        this.buckets.delete(identifier);
      }
    }
  }
}

interface TokenBucket {
  tokens: number;
  capacity: number;
  lastRefill: number;
  resetAt: number;
}

/**
 * Express middleware for rate limiting
 */
export function rateLimit(config: RateLimitConfig & {
  keyPrefix?: string;
  keyGenerator?: (req: Request) => string;
}) {
  const limiter = new TokenBucketRateLimiter();
  const prefix = config.keyPrefix || 'ratelimit';

  return async (req: Request, res: Response, next: NextFunction) => {
    const key = config.keyGenerator
      ? config.keyGenerator(req)
      : `${prefix}:${req.ip}`;

    const result = await limiter.checkLimit(key, config);

    // Set rate limit headers
    res.setHeader('X-RateLimit-Limit', config.requests);
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    res.setHeader('X-RateLimit-Reset', Math.floor(result.resetAt.getTime() / 1000));

    if (!result.allowed) {
      return res.status(429).json({
        error: 'Too many requests',
        retryAfter: Math.ceil((result.resetAt.getTime() - Date.now()) / 1000)
      });
    }

    next();
  };
}

/**
 * Rate limit configurations
 */
export const rateLimitConfigs = {
  // API endpoints
  publicAPI: {
    requests: 100,
    window: 60 * 1000,  // 1 minute
    burst: 20
  },

  authenticatedAPI: {
    requests: 1000,
    window: 60 * 1000,
    burst: 100
  },

  // Auth endpoints
  login: {
    requests: 5,
    window: 15 * 60 * 1000,  // 15 minutes
    burst: 2
  },

  passwordReset: {
    requests: 3,
    window: 60 * 60 * 1000,  // 1 hour
    burst: 1
  },

  // Expensive operations
  search: {
    requests: 30,
    window: 60 * 1000
  },

  export: {
    requests: 10,
    window: 60 * 60 * 1000  // 1 hour
  },

  // Webhooks
  webhookDelivery: {
    requests: 100,
    window: 60 * 1000
  }
};
```

### Adaptive Rate Limiting

```typescript
// rate-limit/adaptive.ts

/**
 * Adaptive rate limiting based on system load and user behavior
 */
export class AdaptiveRateLimiter {
  private systemLoad: number = 0;  // 0-1
  private userBehaviorScores = new Map<string, number>();  // 0-1

  /**
   * Get dynamic rate limit for user
   */
  async getLimit(userId: string, baseLimit: number): Promise<number> {
    // Get user behavior score
    const behaviorScore = this.userBehaviorScores.get(userId) ?? 0.5;

    // Adjust based on behavior
    let limit = baseLimit;

    if (behaviorScore < 0.3) {
      // Suspicious behavior - reduce limit
      limit = Math.floor(baseLimit * 0.2);
    } else if (behaviorScore > 0.8) {
      // Trusted behavior - increase limit
      limit = Math.floor(baseLimit * 2);
    }

    // Adjust based on system load
    if (this.systemLoad > 0.8) {
      limit = Math.floor(limit * 0.5);
    }

    return Math.max(1, limit);
  }

  /**
   * Update user behavior score
   */
  async updateBehaviorScore(userId: string, action: {
    type: 'success' | 'failure' | 'abuse';
    weight?: number;
  }): Promise<void> {
    const currentScore = this.userBehaviorScores.get(userId) ?? 0.5;
    const weight = action.weight ?? 1;

    let newScore = currentScore;

    switch (action.type) {
      case 'success':
        newScore = Math.min(1, currentScore + (0.01 * weight));
        break;

      case 'failure':
        newScore = Math.max(0, currentScore - (0.05 * weight));
        break;

      case 'abuse':
        newScore = Math.max(0, currentScore - (0.2 * weight));
        break;
    }

    this.userBehaviorScores.set(userId, newScore);
  }

  /**
   * Update system load
   */
  setSystemLoad(load: number): void {
    this.systemLoad = Math.max(0, Math.min(1, load));
  }
}
```

---

## 5. API Key Management

### API Key Lifecycle

```typescript
// auth/api-keys.ts

/**
 * API key management service
 */
export class APIKeyService {
  /**
   * Create new API key
   */
  async createKey(request: {
    agencyId: string;
    name: string;
    scopes: string[];
    rateLimit?: RateLimitConfig;
    expiresAt?: Date;
    createdBy: string;
  }): Promise<APIKey> {
    const keyId = crypto.randomUUID();
    const keySecret = crypto.randomBytes(32).toString('base64url');
    const prefixedKey = `ta_${keySecret}`;

    const apiKey: APIKey = {
      id: keyId,
      key: prefixedKey,
      agencyId: request.agencyId,
      name: request.name,
      scopes: request.scopes,
      rateLimit: request.rateLimit || rateLimitConfigs.publicAPI,
      expiresAt: request.expiresAt,
      active: true,
      createdAt: new Date(),
      lastUsedAt: null,
      createdBy: request.createdBy
    };

    // Hash the key for storage
    const hashedKey = this.hashKey(prefixedKey);
    await this.apiKeyStore.save({
      ...apiKey,
      key: hashedKey
    });

    // Return with actual key (only shown once)
    return apiKey;
  }

  /**
   * List API keys for agency
   */
  async listKeys(agencyId: string): Promise<APIKeyInfo[]> {
    const keys = await this.apiKeyStore.findByAgency(agencyId);

    return keys.map(key => ({
      id: key.id,
      name: key.name,
      scopes: key.scopes,
      active: key.active,
      expiresAt: key.expiresAt,
      createdAt: key.createdAt,
      lastUsedAt: key.lastUsedAt
    }));
  }

  /**
   * Rotate API key
   */
  async rotateKey(keyId: string, rotatedBy: string): Promise<APIKey> {
    const existing = await this.apiKeyStore.findById(keyId);

    if (!existing) {
      throw new Error('API key not found');
    }

    // Create new key with same properties
    const newKey = await this.createKey({
      agencyId: existing.agencyId,
      name: existing.name,
      scopes: existing.scopes,
      rateLimit: existing.rateLimit,
      expiresAt: existing.expiresAt,
      createdBy: rotatedBy
    });

    // Revoke old key
    await this.revokeKey(keyId, rotatedBy, 'Rotated');

    return newKey;
  }

  /**
   * Revoke API key
   */
  async revokeKey(keyId: string, revokedBy: string, reason?: string): Promise<void> {
    await this.apiKeyStore.update(keyId, {
      active: false,
      revokedAt: new Date(),
      revokedBy,
      revokeReason: reason
    });

    // Log to audit
    await this.auditLogger.log({
      action: 'api_key_revoked',
      keyId,
      revokedBy,
      reason
    });
  }

  /**
   * Get API key usage statistics
   */
  async getUsageStats(keyId: string, period: {
    start: Date;
    end: Date;
  }): Promise<APIKeyUsageStats> {
    const logs = await this.auditLogger.query({
      action: 'api_request',
      keyId,
      startTime: period.start,
      endTime: period.end
    });

    // Group by endpoint
    const byEndpoint = new Map<string, number>();
    const byStatus = new Map<number, number>();

    for (const log of logs) {
      const endpoint = log.endpoint || 'unknown';
      byEndpoint.set(endpoint, (byEndpoint.get(endpoint) || 0) + 1);

      const status = log.statusCode || 0;
      byStatus.set(status, (byStatus.get(status) || 0) + 1);
    }

    return {
      totalRequests: logs.length,
      byEndpoint: Object.fromEntries(byEndpoint),
      byStatus: Object.fromEntries(byStatus),
      successRate: (byStatus.get(200) || 0) / logs.length,
      avgLatency: logs.reduce((sum, log) => sum + (log.latency || 0), 0) / logs.length
    };
  }

  /**
   * Hash API key for storage
   */
  private hashKey(key: string): string {
    return crypto
      .createHash('sha256')
      .update(key)
      .digest('hex');
  }
}
```

---

## 6. Webhook Security

### Webhook Signature Verification

```typescript
// webhooks/security.ts

/**
 * Webhook security service
 */
export class WebhookSecurity {
  /**
   * Generate webhook signature
   */
  generateSignature(payload: string, secret: string): string {
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(payload);
    return hmac.digest('hex');
  }

  /**
   * Verify webhook signature
   */
  async verifySignature(
    payload: string,
    signature: string,
    secret: string
  ): Promise<boolean> {
    const expectedSignature = this.generateSignature(payload, secret);

    // Timing-safe comparison
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }

  /**
   * Express middleware for webhook verification
   */
  middleware(getSecret: (webhookId: string) => Promise<string>) {
    return async (req: Request, res: Response, next: NextFunction) => {
      const signature = req.headers['x-webhook-signature'] as string;
      const webhookId = req.headers['x-webhook-id'] as string;

      if (!signature || !webhookId) {
        return res.status(401).json({ error: 'Missing webhook headers' });
      }

      const secret = await getSecret(webhookId);

      if (!secret) {
        return res.status(401).json({ error: 'Unknown webhook' });
      }

      // Get raw body for signature verification
      const payload = req.body;

      const isValid = await this.verifySignature(
        JSON.stringify(payload),
        signature,
        secret
      );

      if (!isValid) {
        return res.status(401).json({ error: 'Invalid signature' });
      }

      next();
    };
  }
}

/**
 * Webhook replay protection
 */
export class WebhookReplayProtection {
  private processedIds = new Map<string, number>();  // eventId -> timestamp
  private readonly TTL = 15 * 60 * 1000;  // 15 minutes

  /**
   * Check if webhook was already processed
   */
  async isDuplicate(webhookId: string, eventId: string): Promise<boolean> {
    const key = `${webhookId}:${eventId}`;
    const processed = this.processedIds.get(key);

    if (processed && (Date.now() - processed) < this.TTL) {
      return true;
    }

    this.processedIds.set(key, Date.now());
    return false;
  }

  /**
   * Clean up old entries
   */
  cleanup(): void {
    const cutoff = Date.now() - this.TTL;

    for (const [key, timestamp] of this.processedIds) {
      if (timestamp < cutoff) {
        this.processedIds.delete(key);
      }
    }
  }
}
```

---

## 7. GraphQL Security

### GraphQL Security Best Practices

```typescript
// graphql/security.ts

import { GraphQLResolveInfo } from 'graphql';

/**
 * GraphQL security middleware
 */
export class GraphQLSecurity {
  private maxDepth: number = 10;
  private maxComplexity: number = 1000;
  private rateLimiter: TokenBucketRateLimiter;

  /**
   * Validate query depth
   */
  validateDepth(info: GraphQLResolveInfo): boolean {
    const depth = this.calculateDepth(info);
    return depth <= this.maxDepth;
  }

  /**
   * Calculate query depth
   */
  private calculateDepth(info: GraphQLResolveInfo, currentDepth = 0): number {
    const fieldNodes = info.fieldNodes;

    if (fieldNodes.length === 0) {
      return currentDepth;
    }

    let maxChildDepth = 0;

    for (const field of fieldNodes) {
      if (field.selectionSet) {
        for (const selection of field.selectionSet.selections) {
          if (selection.kind === 'Field') {
            const childDepth = this.calculateDepthForField(selection, info, currentDepth + 1);
            maxChildDepth = Math.max(maxChildDepth, childDepth);
          }
        }
      }
    }

    return Math.max(currentDepth, maxChildDepth);
  }

  /**
   * Validate query complexity
   */
  validateComplexity(info: GraphQLResolveInfo): boolean {
    const complexity = this.calculateComplexity(info);
    return complexity <= this.maxComplexity;
  }

  /**
   * Calculate query complexity
   */
  private calculateComplexity(info: GraphQLResolveInfo): number {
    let complexity = 0;

    const complexityMap = {
      Query: 1,
      Mutation: 2,
      Subscription: 1,
      Trip: 5,
      Customer: 3,
      Booking: 5,
      Payment: 10
    };

    for (const field of info.fieldNodes) {
      const fieldType = info.parentType.getFields()[field.name.value]?.type;
      complexity += complexityMap[fieldType.toString()] || 1;

      if (field.selectionSet) {
        for (const selection of field.selectionSet.selections) {
          if (selection.kind === 'Field') {
            complexity += this.calculateComplexityForField(selection, info);
          }
        }
      }
    }

    return complexity;
  }

  /**
   * Enforce rate limiting on GraphQL operations
   */
  async checkRateLimit(
    operation: 'query' | 'mutation' | 'subscription',
    userId?: string
  ): Promise<boolean> {
    const key = userId ? `graphql:${userId}` : `graphql:${operation}`;

    const result = await this.rateLimiter.checkLimit(key, {
      requests: operation === 'query' ? 100 : 10,
      window: 60 * 1000
    });

    return result.allowed;
  }

  /**
   * Strip sensitive fields from responses
   */
  sanitizeResponse(data: any, sensitiveFields: string[]): any {
    if (typeof data !== 'object' || data === null) {
      return data;
    }

    const sanitized = Array.isArray(data) ? [] : {};

    for (const key in data) {
      if (sensitiveFields.includes(key)) {
        continue;
      }

      if (typeof data[key] === 'object' && data[key] !== null) {
        sanitized[key] = this.sanitizeResponse(data[key], sensitiveFields);
      } else {
        sanitized[key] = data[key];
      }
    }

    return sanitized;
  }
}

/**
 * Field-level authorization for GraphQL
 */
export class GraphQLAuthz {
  /**
   * Check if user can access field
   */
  canAccessField(
    userId: string,
    fieldName: string,
    parentType: string
  ): boolean {
    const fieldPermissions = {
      'User.email': 'user:read_email',
      'User.phone': 'user:read_phone',
      'Trip.paymentInfo': 'trip:read_payment',
      'Booking.ssn': 'admin:read_ssn'
    };

    const permission = fieldPermissions[`${parentType}.${fieldName}`];

    if (!permission) {
      return true;  // No specific permission required
    }

    const authz = new AuthorizationService();
    return authz.hasPermission(userId, permission);
  }
}
```

---

## 8. API Gateway Security

### Gateway Security Features

```typescript
// gateway/security.ts

/**
 * API gateway security middleware
 */
export class APIGatewaySecurity {
  private authz: AuthorizationService;
  private rateLimiter: TokenBucketRateLimiter;
  private waf: WebApplicationFirewall;

  /**
   * Gateway request handler
   */
  async handleRequest(request: GatewayRequest): Promise<GatewayResponse> {
    // 1. Check IP whitelist/blacklist
    if (!this.checkIPAllowed(request.ip)) {
      return {
        status: 403,
        body: { error: 'IP not allowed' }
      };
    }

    // 2. WAF check
    const wafResult = await this.waf.checkRequest(request);
    if (!wafResult.allowed) {
      await this.alertSecurityTeam('WAF_BLOCKED', {
        ip: request.ip,
        reason: wafResult.reason
      });

      return {
        status: 403,
        body: { error: 'Request blocked by WAF' }
      };
    }

    // 3. Authentication
    const authResult = await this.authenticate(request);
    if (!authResult.authenticated) {
      return {
        status: 401,
        body: { error: 'Authentication required' }
      };
    }

    // 4. Rate limiting
    const rateLimitResult = await this.rateLimiter.checkLimit(
      request.userId || request.ip,
      this.getRateLimitForRoute(request.route)
    );

    if (!rateLimitResult.allowed) {
      return {
        status: 429,
        headers: {
          'Retry-After': String(
            Math.ceil((rateLimitResult.resetAt.getTime() - Date.now()) / 1000)
          )
        },
        body: { error: 'Rate limit exceeded' }
      };
    }

    // 5. Authorization
    if (authResult.userId) {
      const authorized = await this.authz.hasPermission(
        authResult.userId,
        this.getRequiredPermission(request.route, request.method)
      );

      if (!authorized) {
        return {
          status: 403,
          body: { error: 'Insufficient permissions' }
        };
      }
    }

    // 6. Request validation
    const validationResult = await this.validateRequest(request);
    if (!validationResult.valid) {
      return {
        status: 400,
        body: { error: validationResult.error }
      };
    }

    // Request passed all security checks - proceed
    return null;
  }

  /**
   * Check if IP is allowed
   */
  private checkIPAllowed(ip: string): boolean {
    // Check blacklist first
    if (this.ipBlacklist.has(ip)) {
      return false;
    }

    // If whitelist exists, IP must be on it
    if (this.ipWhitelist.size > 0) {
      return this.ipWhitelist.has(ip);
    }

    return true;
  }

  /**
   * Get required permission for route
   */
  private getRequiredPermission(route: string, method: string): Permission {
    const routePermissions: Record<string, Record<string, Permission>> = {
      '/api/trips': {
        GET: Permission.TRIP_READ,
        POST: Permission.TRIP_CREATE
      },
      '/api/trips/:id': {
        GET: Permission.TRIP_READ,
        PUT: Permission.TRIP_UPDATE,
        DELETE: Permission.TRIP_DELETE
      },
      '/api/admin/*': {
        '*': Permission.ADMIN
      }
    };

    // Find matching route
    for (const [routePattern, methods] of Object.entries(routePermissions)) {
      if (this.matchRoute(route, routePattern)) {
        return methods[method] || methods['*'];
      }
    }

    return null;
  }

  private matchRoute(route: string, pattern: string): boolean {
    // Simple glob matching
    const regexPattern = pattern
      .replace('*', '.*')
      .replace(/:\w+/g, '[^/]+');

    return new RegExp(`^${regexPattern}$`).test(route);
  }
}
```

---

## 9. DDoS Protection

### Multi-Layer DDoS Protection

```typescript
// security/ddos.ts

/**
 * DDoS protection service
 */
export class DDoSProtection {
  private ipScores = new Map<string, IPScore>();
  private globalTrafficThreshold: number = 10000;  // requests per second

  /**
   * Check if request should be allowed
   */
  async checkRequest(request: IncomingRequest): Promise<{
    allowed: boolean;
    action?: 'challenge' | 'block' | 'rate_limit';
    reason?: string;
  }> {
    const ip = request.ip;

    // Get IP score
    const score = this.getIPScore(ip);

    // Check global traffic
    const currentLoad = await this.getGlobalTrafficRate();

    if (currentLoad > this.globalTrafficThreshold * 0.9) {
      // Near capacity - be more aggressive
      if (score.score < 50) {
        return {
          allowed: false,
          action: 'block',
          reason: 'DDoS protection active - low score IP'
        };
      }
    }

    // Check IP-specific rate limits
    const ipRateLimit = await this.checkIPRateLimit(ip, request);
    if (!ipRateLimit.allowed) {
      this.updateIPScore(ip, -20);

      if (score.score < 30) {
        return {
          allowed: false,
          action: 'block',
          reason: 'Rate limit exceeded - IP blocked'
        };
      }

      return {
        allowed: false,
        action: 'rate_limit',
        reason: 'Rate limit exceeded'
      };
    }

    // Check for attack patterns
    const attackPattern = this.detectAttackPattern(request);
    if (attackPattern) {
      this.updateIPScore(ip, -50);

      return {
        allowed: false,
        action: 'block',
        reason: `Attack pattern detected: ${attackPattern}`
      };
    }

    // If score is very low, challenge the request
    if (score.score < 40) {
      return {
        allowed: false,
        action: 'challenge',
        reason: 'Low IP reputation - captcha required'
      };
    }

    return { allowed: true };
  }

  /**
   * Get IP reputation score
   */
  private getIPScore(ip: string): IPScore {
    let score = this.ipScores.get(ip);

    if (!score) {
      score = {
        score: 50,  // Start at 50
        requests: 0,
        lastUpdate: Date.now()
      };
      this.ipScores.set(ip, score);
    }

    return score;
  }

  /**
   * Update IP score
   */
  private updateIPScore(ip: string, delta: number): void {
    const score = this.getIPScore(ip);
    score.score = Math.max(0, Math.min(100, score.score + delta));
    score.lastUpdate = Date.now();
  }

  /**
   * Detect attack patterns
   */
  private detectAttackPattern(request: IncomingRequest): string | null {
    const patterns = {
      sqlInjection: /(\bunion\b.*\bselect\b|';.*--)/i,
      xss: /<script|javascript:|onerror=/i,
      pathTraversal: /\.\.[\/\\]/,
      attackTools: /sqlmap|nikto|nmap|burp/i
    };

    const userAgent = request.headers['user-agent'] || '';
    const url = request.url;

    for (const [name, pattern] of Object.entries(patterns)) {
      if (pattern.test(url) || pattern.test(userAgent)) {
        return name;
      }
    }

    return null;
  }

  /**
   * Generate CAPTCHA challenge
   */
  async generateChallenge(): Promise<CaptchaChallenge> {
    return {
      siteKey: process.env.RECAPTCHA_SITE_KEY,
      version: 'v3',
      action: 'ddos_protection'
    };
  }

  /**
   * Verify CAPTCHA response
   */
  async verifyChallenge(token: string): Promise<boolean> {
    const response = await fetch(
      `https://www.google.com/recaptcha/api/siteverify`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          secret: process.env.RECAPTCHA_SECRET_KEY,
          response: token
        })
      }
    );

    const data = await response.json();
    return data.success && data.score > 0.5;
  }
}

interface IPScore {
  score: number;  // 0-100, higher is better
  requests: number;
  lastUpdate: number;
}
```

---

## 10. API Security Testing

### Security Test Suite

```typescript
// __tests__/security/api-security.test.ts

describe('API Security', () => {
  describe('Authentication', () => {
    it('should reject requests without valid token', async () => {
      const response = await app.request('/api/trips', {
        headers: {
          'Authorization': 'Bearer invalid-token'
        }
      });

      expect(response.status).toBe(401);
    });

    it('should reject expired tokens', async () => {
      const expiredToken = generateExpiredToken();

      const response = await app.request('/api/trips', {
        headers: {
          'Authorization': `Bearer ${expiredToken}`
        }
      });

      expect(response.status).toBe(401);
    });

    it('should accept valid tokens', async () => {
      const token = await generateValidToken(user);

      const response = await app.request('/api/trips', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      expect(response.status).not.toBe(401);
    });
  });

  describe('Authorization', () => {
    it('should enforce role-based access', async () => {
      const agentToken = await generateTokenForRole('agent');

      // Agent should not be able to access admin endpoints
      const response = await app.request('/api/admin/analytics', {
        headers: {
          'Authorization': `Bearer ${agentToken}`
        }
      });

      expect(response.status).toBe(403);
    });

    it('should enforce resource ownership', async () => {
      const customerToken = await generateTokenForUser('customer-a');
      const tripId = 'trip-b';  // Different customer's trip

      const response = await app.request(`/api/trips/${tripId}`, {
        headers: {
          'Authorization': `Bearer ${customerToken}`
        }
      });

      expect(response.status).toBe(403);
    });
  });

  describe('Rate Limiting', () => {
    it('should enforce rate limits', async () => {
      const requests = [];

      // Send 150 requests (limit is 100)
      for (let i = 0; i < 150; i++) {
        requests.push(
          app.request('/api/search', {
            method: 'POST',
            body: JSON.stringify({ query: 'test' })
          })
        );
      }

      const responses = await Promise.all(requests);

      const rateLimited = responses.filter(r => r.status === 429);
      expect(rateLimited.length).toBeGreaterThan(0);
    });

    it('should set rate limit headers', async () => {
      const response = await app.request('/api/search', {
        method: 'POST',
        body: JSON.stringify({ query: 'test' })
      });

      expect(response.headers['x-ratelimit-limit']).toBeDefined();
      expect(response.headers['x-ratelimit-remaining']).toBeDefined();
      expect(response.headers['x-ratelimit-reset']).toBeDefined();
    });
  });

  describe('Input Validation', () => {
    it('should validate request body', async () => {
      const response = await app.request('/api/trips', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          destinationId: 123,  // Should be string
          startDate: 'not-a-date',
          travelers: 'not-an-object'
        })
      });

      expect(response.status).toBe(400);
      const data = await response.json();
      expect(data.error).toContain('validation');
    });
  });

  describe('API Key Security', () => {
    it('should reject requests with invalid API keys', async () => {
      const response = await app.request('/api/partner/hotels', {
        headers: {
          'X-API-Key': 'invalid-key'
        }
      });

      expect(response.status).toBe(401);
    });

    it('should enforce API key scopes', async () => {
      const limitedKey = await createAPIKey({ scopes: ['hotels.read'] });

      const response = await app.request('/api/partner/hotels', {
        method: 'POST',
        headers: {
          'X-API-Key': limitedKey
        },
        body: JSON.stringify({ name: 'New Hotel' })
      });

      expect(response.status).toBe(403);
    });
  });

  describe('Webhook Security', () => {
    it('should verify webhook signatures', async () => {
      const payload = { event: 'booking.created', data: {} };
      const signature = generateWebhookSignature(payload, webhookSecret);

      const response = await app.request('/api/webhooks/handler', {
        method: 'POST',
        headers: {
          'X-Webhook-Signature': signature,
          'X-Webhook-ID': 'webhook-123'
        },
        body: JSON.stringify(payload)
      });

      expect(response.status).not.toBe(401);
    });

    it('should reject invalid webhook signatures', async () => {
      const payload = { event: 'booking.created', data: {} };

      const response = await app.request('/api/webhooks/handler', {
        method: 'POST',
        headers: {
          'X-Webhook-Signature': 'invalid-signature',
          'X-Webhook-ID': 'webhook-123'
        },
        body: JSON.stringify(payload)
      });

      expect(response.status).toBe(401);
    });

    it('should detect replay attacks', async () => {
      const payload = { event: 'booking.created', data: {} };
      const signature = generateWebhookSignature(payload, webhookSecret);

      // First request
      await app.request('/api/webhooks/handler', {
        method: 'POST',
        headers: {
          'X-Webhook-Signature': signature,
          'X-Webhook-ID': 'webhook-123'
        },
        body: JSON.stringify(payload)
      });

      // Replay same request
      const response = await app.request('/api/webhooks/handler', {
        method: 'POST',
        headers: {
          'X-Webhook-Signature': signature,
          'X-Webhook-ID': 'webhook-123'
        },
        body: JSON.stringify(payload)
      });

      expect(response.status).toBe(409);  // Conflict - duplicate
    });
  });
});
```

---

## Summary

This document defines API security practices for the Travel Agency Agent platform:

**Key Components:**
- **JWT Authentication** - Secure token-based authentication
- **OAuth 2.0** - Third-party authorization flow
- **RBAC** - Role-based access control
- **Scope-Based Authorization** - Fine-grained permissions
- **Rate Limiting** - Token bucket and adaptive rate limiting
- **API Key Management** - Key lifecycle and rotation
- **Webhook Security** - Signature verification and replay protection
- **GraphQL Security** - Depth/complexity limits
- **DDoS Protection** - Multi-layer protection

**Next:** [SECURITY_03: Data Security](./SECURITY_03_DATA_SECURITY.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
