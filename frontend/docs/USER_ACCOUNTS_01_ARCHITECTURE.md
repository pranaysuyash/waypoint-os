# User Accounts — Architecture

> System design, data model, and security architecture for user accounts

**Series:** User Accounts | **Document:** 1 of 5 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [User Data Model](#user-data-model)
4. [Authentication Architecture](#authentication-architecture)
5. [Security Considerations](#security-considerations)
6. [Multi-Tenancy](#multi-tenancy)
7. [Integration Points](#integration-points)
8. [Privacy & Compliance](#privacy--compliance)

---

## Overview

The User Accounts system manages customer identities, authentication, profiles, and preferences. It serves as the foundation for all customer interactions with the platform.

### Core Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Identity Management** | User registration, verification, and identity proofing |
| **Authentication** | Login, sessions, MFA, SSO |
| **Profile Management** | User profiles, preferences, and settings |
| **Traveler Data** | Traveler profiles, documents, and history |
| **Privacy** | Consent management, data access, and deletion |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER ACCOUNTS SERVICE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │    API      │   │  AuthN/AuthZ │   │   Profile   │              │
│  │   Gateway   │   │    Service   │   │   Service   │              │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │
│         │                 │                  │                      │
│         └─────────────────┴──────────────────┘                      │
│                           │                                         │
│  ┌────────────────────────┴────────────────────────────────────┐   │
│  │                    User Aggregator                          │   │
│  │  (Combines user, profile, travelers, preferences)          │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│         ┌──────────────────────┼──────────────────────┐             │
│         ▼                      ▼                      ▼             │
│  ┌────────────┐        ┌────────────┐        ┌────────────┐       │
│  │   Users    │        │  Profiles  │        │ Travelers  │       │
│  │  Database  │        │  Database  │        │  Database  │       │
│  └────────────┘        └────────────┘        └────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│   PostgreSQL   │    │   PostgreSQL   │    │   PostgreSQL   │
│  (users, auth) │    │ (profiles)     │    │ (travelers)    │
└────────────────┘    └────────────────┘    └────────────────┘
```

### Component Responsibilities

#### API Gateway
- HTTP/REST endpoints for user operations
- Request validation and rate limiting
- Authentication middleware
- Response formatting

#### Authentication Service
- User authentication and authorization
- Session management
- Token generation and validation
- Password management
- MFA orchestration

#### Profile Service
- Profile CRUD operations
- Preferences management
- Privacy controls
- Communication settings

#### Traveler Service
- Traveler profile management
- Document storage (passports, visas)
- Companion management
- Travel history

---

## User Data Model

### Core Entities

```typescript
// ============================================================================
// USER ACCOUNT AGGREGATE
// ============================================================================

interface User {
  // Identity
  id: string;                    // UUID
  email: string;                 // Unique, verified
  phone?: string;                // Optional, verified if present
  username?: string;             // Optional for login

  // Authentication
  passwordHash?: string;         // BCrypt hash (null if social auth only)
  authProvider: 'email' | 'google' | 'apple' | 'facebook';
  authProviderId?: string;       // Provider's user ID

  // Status
  status: UserStatus;
  tier: CustomerTier;
  emailVerified: boolean;
  phoneVerified: boolean;

  // Security
  lastLoginAt?: Date;
  loginAttempts: number;
  lockedUntil?: Date;
  passwordChangedAt: Date;
  mfaEnabled: boolean;
  mfaMethod?: 'totp' | 'sms' | 'email';

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;               // Soft delete

  // Relationships
  profileId: string;
  travelerIds: string[];
}

type UserStatus =
  | 'pending'           // Email verification pending
  | 'active'            // Fully active
  | 'suspended'         // Temporarily suspended
  | 'banned'            // Permanently banned
  | 'deleted';          // Soft deleted

type CustomerTier =
  | 'standard'
  | 'silver'
  | 'gold'
  | 'platinum';

// ============================================================================
// USER PROFILE
// ============================================================================

interface UserProfile {
  id: string;
  userId: string;                // References User.id

  // Personal Info
  firstName: string;
  lastName: string;
  displayName: string;
  avatar?: string;
  dateOfBirth?: Date;
  nationality?: string;
  language: string;
  currency: string;
  timezone: string;

  // Contact
  email: string;                 // Denormalized from User
  phone?: string;
  address?: Address;

  // Preferences
  preferences: UserPreferences;

  // Privacy
  privacy: PrivacySettings;

  // Marketing
  marketing: MarketingPreferences;

  // Metadata
  metadata: {
    source: 'web' | 'mobile' | 'agent' | 'import';
    referrer?: string;
    campaign?: string;
    utm?: Record<string, string>;
  };

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

interface UserPreferences {
  // Travel preferences
  travel: {
    seatPreference?: 'window' | 'aisle' | 'none';
    mealPreference?: string;
    hotelRoomPreference?: string;
    notificationTiming?: 'immediate' | 'daily' | 'weekly';
  };

  // Communication
  communication: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    pushEnabled: boolean;
    marketingEmails: boolean;
    promotionalSms: boolean;
  };

  // Display
  display: {
    currency: string;
    distanceUnit: 'km' | 'miles';
    dateFormat: string;
  };
}

interface PrivacySettings {
  profileVisibility: 'public' | 'registered' | 'private';
  showTravelHistory: boolean;
  showReviews: boolean;
  allowTagging: boolean;
  dataSharing: {
    analytics: boolean;
    personalization: boolean;
    thirdParty: boolean;
  };
}

interface MarketingPreferences {
  newsletter: boolean;
  offers: boolean;
  newDestinations: boolean;
  travelTips: boolean;
  partnerOffers: boolean;
}

// ============================================================================
// TRAVELER PROFILE
// ============================================================================

interface TravelerProfile {
  id: string;
  userId: string;                // Owner of this traveler
  type: 'primary' | 'companion'; // Primary = user themselves

  // Identity
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  gender?: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  nationality: string;

  // Travel Documents
  documents: TravelerDocument[];

  // Travel Preferences
  preferences: {
    seatPreference?: 'window' | 'aisle';
    mealPreference?: string;
    specialAssistance?: string[];
    frequentFlyer?: FrequentFlyerProgram[];
  };

  // Metadata
  nickname?: string;
  relationship?: string;         // For companions: 'spouse', 'child', etc.
  notes?: string;

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

interface TravelerDocument {
  type: 'passport' | 'visa' | 'id_card' | 'drivers_license';
  number: string;
  issuingCountry: string;
  expiryDate: Date;
  imageUrl?: string;             // Securely stored
  verified: boolean;
  verifiedAt?: Date;
}

interface FrequentFlyerProgram {
  airline: string;
  number: string;
  tier?: string;
}

// ============================================================================
// SESSION & TOKENS
// ============================================================================

interface UserSession {
  id: string;
  userId: string;

  // Token data
  accessToken: string;           // JWT
  refreshToken: string;
  accessTokenExpiresAt: Date;
  refreshTokenExpiresAt: Date;

  // Session info
  device: DeviceInfo;
  location: LocationInfo;
  ipAddress: string;
  userAgent: string;

  // Status
  active: boolean;
  lastActivityAt: Date;

  // Timestamps
  createdAt: Date;
  revokedAt?: Date;
}

interface DeviceInfo {
  type: 'desktop' | 'mobile' | 'tablet';
  os: string;
  browser?: string;
  appVersion?: string;
}

interface LocationInfo {
  country?: string;
  city?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

// ============================================================================
// AUTHENTICATION EVENTS
// ============================================================================

interface AuthEvent {
  id: string;
  userId: string;
  type: AuthEventType;
  status: 'success' | 'failed';

  // Event details
  details: {
    method: 'password' | 'social' | 'mfa' | 'sso';
    provider?: string;
    reason?: string;
  };

  // Context
  context: {
    ipAddress: string;
    userAgent: string;
    location?: LocationInfo;
    deviceId?: string;
  };

  // Security
  flagged: boolean;
  riskScore: number;              // 0-100

  // Timestamps
  timestamp: Date;
}

type AuthEventType =
  | 'registration'
  | 'login'
  | 'logout'
  | 'password_reset'
  | 'email_verification'
  | 'mfa_enabled'
  | 'mfa_disabled'
  | 'profile_updated'
  | 'suspicious_activity';
```

### Database Schema

```sql
-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    username VARCHAR(50) UNIQUE,

    -- Authentication
    password_hash VARCHAR(255),
    auth_provider VARCHAR(20) NOT NULL DEFAULT 'email',
    auth_provider_id VARCHAR(255),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    tier VARCHAR(20) NOT NULL DEFAULT 'standard',
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Security
    last_login_at TIMESTAMPTZ,
    login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_method VARCHAR(10),

    -- Soft delete
    deleted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'active', 'suspended', 'banned', 'deleted'
    )),
    CONSTRAINT valid_tier CHECK (tier IN (
        'standard', 'silver', 'gold', 'platinum'
    ))
);

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_phone ON users(phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_tier ON users(tier);
CREATE UNIQUE INDEX idx_users_email_unique ON users(email)
    WHERE deleted_at IS NULL;

-- ============================================================================
-- USER PROFILES TABLE
-- ============================================================================

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Personal info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    avatar TEXT,
    date_of_birth DATE,
    nationality VARCHAR(2),
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',

    -- Contact
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address JSONB,

    -- Preferences
    preferences JSONB NOT NULL DEFAULT '{}',
    privacy JSONB NOT NULL DEFAULT '{}',
    marketing JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_language CHECK (language ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    CONSTRAINT valid_currency CHECK (currency ~ '^[A-Z]{3}$')
);

-- Indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_name ON user_profiles(
    lower(first_name),
    lower(last_name)
);

-- ============================================================================
-- TRAVELER PROFILES TABLE
-- ============================================================================

CREATE TABLE traveler_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL DEFAULT 'primary',

    -- Identity
    title VARCHAR(20),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    nationality VARCHAR(2) NOT NULL,

    -- Documents (stored separately for security)
    documents JSONB NOT NULL DEFAULT '[]',

    -- Preferences
    preferences JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    nickname VARCHAR(100),
    relationship VARCHAR(50),
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_traveler_type CHECK (type IN ('primary', 'companion')),
    CONSTRAINT valid_gender CHECK (gender IN (
        'male', 'female', 'other', 'prefer_not_to_say'
    ))
);

-- Indexes
CREATE INDEX idx_traveler_profiles_user_id ON traveler_profiles(user_id);
CREATE INDEX idx_traveler_profiles_name ON traveler_profiles(
    lower(first_name),
    lower(last_name)
);

-- Link table for user-travelers relationship
CREATE TABLE user_travelers (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    traveler_id UUID NOT NULL REFERENCES traveler_profiles(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, traveler_id)
);

-- ============================================================================
-- USER SESSIONS TABLE
-- ============================================================================

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Tokens
    access_token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    access_token_expires_at TIMESTAMPTZ NOT NULL,
    refresh_token_expires_at TIMESTAMPTZ NOT NULL,

    -- Session info
    device JSONB NOT NULL,
    location JSONB,
    ip_address INET NOT NULL,
    user_agent TEXT NOT NULL,

    -- Status
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT token_expiry_valid CHECK (
        refresh_token_expires_at > access_token_expires_at
    )
);

-- Indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, active)
    WHERE active = TRUE;
CREATE INDEX idx_user_sessions_refresh ON user_sessions(refresh_token_hash);

-- Cleanup job: delete expired revoked sessions
CREATE INDEX idx_user_sessions_expired ON user_sessions(created_at)
    WHERE active = FALSE AND revoked_at < NOW() - INTERVAL '30 days';

-- ============================================================================
-- AUTH EVENTS TABLE
-- ============================================================================

CREATE TABLE auth_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Event
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',

    -- Context
    context JSONB NOT NULL DEFAULT '{}',

    -- Security
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    risk_score INT NOT NULL DEFAULT 0,

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_auth_events_user_id ON auth_events(user_id);
CREATE INDEX idx_auth_events_type ON auth_events(type);
CREATE INDEX idx_auth_events_timestamp ON auth_events(timestamp DESC);
CREATE INDEX idx_auth_events_flagged ON auth_events(flagged, timestamp)
    WHERE flagged = TRUE;

-- ============================================================================
-- EMAIL VERIFICATIONS TABLE
-- ============================================================================

CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,

    -- Token
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,

    -- Status
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX idx_email_verifications_token ON email_verifications(token_hash)
    WHERE verified = FALSE;

-- ============================================================================
-- PASSWORD RESETS TABLE
-- ============================================================================

CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,

    -- Status
    used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_password_resets_user_id ON password_resets(user_id);
CREATE INDEX idx_password_resets_token ON password_resets(token_hash)
    WHERE used = FALSE;
```

---

## Authentication Architecture

### JWT-Based Authentication

```typescript
// ============================================================================
// JWT TOKEN STRUCTURE
// ============================================================================

interface JWTPayload {
  // Standard claims
  iss: string;                   // Issuer (our domain)
  sub: string;                   // User ID
  aud: string;                   // Audience (api, web, mobile)
  exp: number;                   // Expiration
  nbf: number;                   // Not before
  iat: number;                   // Issued at
  jti: string;                   // JWT ID (unique token identifier)

  // Custom claims
  email: string;
  tier: CustomerTier;
  permissions: string[];

  // Session info
  session_id: string;
  device_id: string;
}

interface RefreshTokenPayload {
  user_id: string;
  session_id: string;
  token_id: string;
  rotation_counter: number;
}

// ============================================================================
// TOKEN SERVICE
// ============================================================================

class TokenService {
  private accessTokenSecret: string;
  private refreshTokenSecret: string;

  constructor() {
    this.accessTokenSecret = process.env.JWT_ACCESS_SECRET!;
    this.refreshTokenSecret = process.env.JWT_REFRESH_SECRET!;
  }

  generateAccessToken(user: User, session: UserSession): string {
    const payload: JWTPayload = {
      iss: process.env.JWT_ISSUER!,
      sub: user.id,
      aud: 'api',
      exp: Math.floor(Date.now() / 1000) + 900, // 15 minutes
      nbf: Math.floor(Date.now() / 1000),
      iat: Math.floor(Date.now() / 1000),
      jti: crypto.randomUUID(),

      email: user.email,
      tier: user.tier,
      permissions: this.getPermissions(user),

      session_id: session.id,
      device_id: session.device.id || '',
    };

    return jwt.sign(payload, this.accessTokenSecret, {
      algorithm: 'HS256',
      header: { typ: 'JWT', alg: 'HS256' },
    });
  }

  generateRefreshToken(user: User, session: UserSession): string {
    const payload: RefreshTokenPayload = {
      user_id: user.id,
      session_id: session.id,
      token_id: crypto.randomUUID(),
      rotation_counter: 0,
    };

    return jwt.sign(payload, this.refreshTokenSecret, {
      algorithm: 'HS256',
      expiresIn: '30d', // 30 days
    });
  }

  verifyAccessToken(token: string): JWTPayload | null {
    try {
      const decoded = jwt.verify(token, this.accessTokenSecret) as JWTPayload;

      // Additional validation
      if (decoded.aud !== 'api') {
        return null;
      }

      return decoded;
    } catch (error) {
      return null;
    }
  }

  verifyRefreshToken(token: string): RefreshTokenPayload | null {
    try {
      return jwt.verify(token, this.refreshTokenSecret) as RefreshTokenPayload;
    } catch (error) {
      return null;
    }
  }

  private getPermissions(user: User): string[] {
    const basePermissions = ['booking:read', 'booking:create'];

    if (user.tier === 'gold' || user.tier === 'platinum') {
      basePermissions.push('booking:modify', 'booking:cancel');
    }

    if (user.tier === 'platinum') {
      basePermissions.push('support:priority', 'fees:waived');
    }

    return basePermissions;
  }
}

// ============================================================================
// AUTHENTICATION SERVICE
// ============================================================================

class AuthenticationService {
  private tokenService: TokenService;
  private db: Database;

  async register(input: RegisterInput): Promise<AuthResult> {
    // Check if email exists
    const existing = await this.db.users.findByEmail(input.email);
    if (existing && !existing.deletedAt) {
      throw new EmailAlreadyExistsError(input.email);
    }

    // Hash password
    const passwordHash = await bcrypt.hash(input.password, 12);

    // Create user
    const user = await this.db.users.create({
      email: input.email,
      passwordHash,
      authProvider: 'email',
      status: 'pending',
      emailVerified: false,
      tier: 'standard',
      passwordChangedAt: new Date(),
    });

    // Create profile
    const profile = await this.db.profiles.create({
      userId: user.id,
      firstName: input.firstName,
      lastName: input.lastName,
      displayName: `${input.firstName} ${input.lastName}`,
      email: input.email,
      language: input.language || 'en',
      currency: input.currency || 'USD',
      timezone: input.timezone || 'UTC',
      preferences: this.getDefaultPreferences(),
      privacy: this.getDefaultPrivacy(),
      marketing: {
        newsletter: input.newsletter || false,
        offers: input.offers || false,
        newDestinations: false,
        travelTips: false,
        partnerOffers: false,
      },
      metadata: {
        source: input.source || 'web',
      },
    });

    // Create primary traveler profile
    const traveler = await this.db.travelers.create({
      userId: user.id,
      type: 'primary',
      title: input.title || 'Mr',
      firstName: input.firstName,
      lastName: input.lastName,
      dateOfBirth: input.dateOfBirth || new Date('1990-01-01'),
      nationality: input.nationality || 'US',
      documents: [],
      preferences: {},
    });

    await this.db.userTravelers.create({
      userId: user.id,
      travelerId: traveler.id,
      isPrimary: true,
    });

    // Send verification email
    await this.sendVerificationEmail(user);

    // Record event
    await this.recordAuthEvent(user.id, 'registration', 'success', {
      method: 'email',
    });

    // Generate tokens (but user is pending)
    const session = await this.createSession(user);
    const accessToken = this.tokenService.generateAccessToken(user, session);
    const refreshToken = this.tokenService.generateRefreshToken(user, session);

    return {
      user: this.sanitizeUser(user),
      profile,
      accessToken,
      refreshToken,
      requiresVerification: true,
    };
  }

  async login(email: string, password: string, deviceInfo: DeviceInfo): Promise<AuthResult> {
    // Find user
    const user = await this.db.users.findByEmail(email);

    if (!user || user.deletedAt) {
      // Prevent timing attacks
      await bcrypt.hash('dummy', 12);
      throw new InvalidCredentialsError();
    }

    // Check if locked
    if (user.lockedUntil && user.lockedUntil > new Date()) {
      throw new AccountLockedError();
    }

    // Verify password
    if (user.passwordHash) {
      const valid = await bcrypt.compare(password, user.passwordHash);

      if (!valid) {
        await this.handleFailedLogin(user);
        throw new InvalidCredentialsError();
      }
    }

    // Check if email verified
    if (!user.emailVerified) {
      throw new EmailNotVerifiedError();
    }

    // Check status
    if (user.status !== 'active') {
      throw new AccountSuspendedError(user.status);
    }

    // Successful login
    await this.handleSuccessfulLogin(user);

    // Create session
    const session = await this.createSession(user, deviceInfo);

    // Generate tokens
    const accessToken = this.tokenService.generateAccessToken(user, session);
    const refreshToken = this.tokenService.generateRefreshToken(user, session);

    // Update session with tokens
    await this.db.sessions.update(session.id, {
      accessTokenHash: this.hashToken(accessToken),
      refreshTokenHash: this.hashToken(refreshToken),
      accessTokenExpiresAt: new Date(Date.now() + 900000), // 15 min
      refreshTokenExpiresAt: new Date(Date.now() + 2592000000), // 30 days
    });

    // Get profile
    const profile = await this.db.profiles.findByUserId(user.id);

    // Record event
    await this.recordAuthEvent(user.id, 'login', 'success', {
      method: 'password',
    });

    return {
      user: this.sanitizeUser(user),
      profile,
      accessToken,
      refreshToken,
    };
  }

  async refreshAccessToken(refreshToken: string): Promise<TokenRefreshResult> {
    // Verify refresh token
    const payload = this.tokenService.verifyRefreshToken(refreshToken);

    if (!payload) {
      throw new InvalidTokenError();
    }

    // Get session
    const session = await this.db.sessions.findById(payload.session_id);

    if (!session || !session.active) {
      throw new InvalidSessionError();
    }

    // Get user
    const user = await this.db.users.findById(session.userId);

    if (!user || user.deletedAt || user.status !== 'active') {
      throw new InvalidUserError();
    }

    // Generate new tokens (rotation)
    const newAccessToken = this.tokenService.generateAccessToken(user, session);
    const newRefreshToken = this.tokenService.generateRefreshToken(user, session);

    // Update session
    await this.db.sessions.update(session.id, {
      accessTokenHash: this.hashToken(newAccessToken),
      refreshTokenHash: this.hashToken(newRefreshToken),
      lastActivityAt: new Date(),
    });

    return {
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
    };
  }

  async logout(accessToken: string): Promise<void> {
    const payload = this.tokenService.verifyAccessToken(accessToken);

    if (!payload) {
      return;
    }

    // Revoke session
    await this.db.sessions.update(payload.session_id, {
      active: false,
      revokedAt: new Date(),
    });

    // Record event
    await this.recordAuthEvent(payload.sub, 'logout', 'success');
  }

  private async createSession(
    user: User,
    deviceInfo?: DeviceInfo
  ): Promise<UserSession> {
    return await this.db.sessions.create({
      userId: user.id,
      accessToken: '', // Will be updated after token generation
      refreshToken: '',
      accessTokenExpiresAt: new Date(),
      refreshTokenExpiresAt: new Date(),
      device: deviceInfo || { type: 'desktop', os: 'unknown' },
      location: {},
      ipAddress: '',
      userAgent: '',
      active: true,
      lastActivityAt: new Date(),
    });
  }

  private async handleFailedLogin(user: User): Promise<void> {
    user.loginAttempts += 1;

    if (user.loginAttempts >= 5) {
      user.lockedUntil = addMinutes(new Date(), 15); // Lock for 15 minutes
    }

    await user.save();

    await this.recordAuthEvent(user.id, 'login', 'failed', {
      reason: 'invalid_password',
    });
  }

  private async handleSuccessfulLogin(user: User): Promise<void> {
    user.loginAttempts = 0;
    user.lockedUntil = undefined;
    user.lastLoginAt = new Date();

    await user.save();
  }

  private async sendVerificationEmail(user: User): Promise<void> {
    const token = crypto.randomBytes(32).toString('hex');
    const tokenHash = createHash('sha256').update(token).digest('hex');

    await this.db.emailVerifications.create({
      userId: user.id,
      email: user.email,
      tokenHash,
      expiresAt: addHours(new Date(), 24),
    });

    await EmailService.send({
      to: user.email,
      subject: 'Verify your email',
      template: 'email-verification',
      data: {
        token,
        expiresIn: 24,
      },
    });
  }

  private async recordAuthEvent(
    userId: string,
    type: AuthEventType,
    status: 'success' | 'failed',
    details?: Record<string, unknown>
  ): Promise<void> {
    await this.db.authEvents.create({
      userId,
      type,
      status,
      details: details || {},
      context: {
        ipAddress: '',
        userAgent: '',
      },
      flagged: false,
      riskScore: 0,
      timestamp: new Date(),
    });
  }

  private hashToken(token: string): string {
    return createHash('sha256').update(token).digest('hex');
  }

  private sanitizeUser(user: User): Partial<User> {
    const { passwordHash, ...sanitized } = user;
    return sanitized;
  }

  private getDefaultPreferences(): UserPreferences {
    return {
      travel: {},
      communication: {
        emailEnabled: true,
        smsEnabled: false,
        pushEnabled: true,
        marketingEmails: false,
        promotionalSms: false,
      },
      display: {
        currency: 'USD',
        distanceUnit: 'km',
        dateFormat: 'DD/MM/YYYY',
      },
    };
  }

  private getDefaultPrivacy(): PrivacySettings {
    return {
      profileVisibility: 'private',
      showTravelHistory: false,
      showReviews: false,
      allowTagging: false,
      dataSharing: {
        analytics: true,
        personalization: true,
        thirdParty: false,
      },
    };
  }
}

interface RegisterInput {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  title?: string;
  dateOfBirth?: Date;
  nationality?: string;
  language?: string;
  currency?: string;
  timezone?: string;
  newsletter?: boolean;
  offers?: boolean;
  source?: string;
}

interface AuthResult {
  user: Partial<User>;
  profile?: UserProfile;
  accessToken: string;
  refreshToken: string;
  requiresVerification?: boolean;
}

interface TokenRefreshResult {
  accessToken: string;
  refreshToken: string;
}
```

---

## Security Considerations

### Password Security

```typescript
// ============================================================================
// PASSWORD POLICY
// ============================================================================

interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  maxAge: number;                // days
  history: number;               // number of previous passwords to remember
  notAllowed: string[];          // common passwords not allowed
}

const PASSWORD_POLICY: PasswordPolicy = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: false,
  maxAge: 90,                    // 90 days
  history: 5,
  notAllowed: [
    'password', '12345678', 'qwerty123',
    // ... loaded from common password lists
  ],
};

class PasswordValidator {
  async validate(password: string): Promise<ValidationResult> {
    const errors: string[] = [];

    if (password.length < PASSWORD_POLICY.minLength) {
      errors.push(`Password must be at least ${PASSWORD_POLICY.minLength} characters`);
    }

    if (PASSWORD_POLICY.requireUppercase && !/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }

    if (PASSWORD_POLICY.requireLowercase && !/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }

    if (PASSWORD_POLICY.requireNumbers && !/\d/.test(password)) {
      errors.push('Password must contain at least one number');
    }

    if (PASSWORD_POLICY.requireSpecialChars && !/[!@#$%^&*]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }

    if (PASSWORD_POLICY.notAllowed.includes(password.toLowerCase())) {
      errors.push('This password is too common. Please choose a more secure password.');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  async checkHistory(userId: string, newPassword: string): Promise<boolean> {
    // Check against password history
    const history = await PasswordHistory.find({
      userId,
    })
      .sort({ createdAt: -1 })
      .limit(PASSWORD_POLICY.history);

    for (const entry of history) {
      const match = await bcrypt.compare(newPassword, entry.passwordHash);
      if (match) {
        return false; // Password was used before
      }
    }

    return true;
  }
}

// ============================================================================
// ACCOUNT LOCKOUT POLICY
// ============================================================================

interface LockoutPolicy {
  maxAttempts: number;
  lockoutDuration: number;       // minutes
  progressiveDelay: boolean;      // Increase delay with each attempt
  trackingWindow: number;         // minutes (count attempts within this window)
}

const LOCKOUT_POLICY: LockoutPolicy = {
  maxAttempts: 5,
  lockoutDuration: 15,
  progressiveDelay: true,
  trackingWindow: 15,
};

class SecurityService {
  async checkRiskScore(
    userId: string,
    context: AuthContext
  ): Promise<number> {
    let score = 0;

    // Check for new device
    const existingDevices = await UserSession.findDistinct('deviceId', { userId });
    if (!existingDevices.includes(context.deviceId)) {
      score += 20;
    }

    // Check for new location
    const recentLogins = await AuthEvent.find({
      userId,
      type: 'login',
      status: 'success',
      timestamp: { $gte: subDays(new Date(), 30) },
    });

    const recentLocations = new Set(
      recentLogins.map(e => e.context.location?.country)
    );

    if (!recentLocations.has(context.location?.country)) {
      score += 15;
    }

    // Check time-based patterns
    const currentHour = new Date().getHours();
    if (currentHour < 6 || currentHour > 23) {
      score += 10; // Unusual hours
    }

    // Check IP reputation
    if (await this.isSuspiciousIP(context.ipAddress)) {
      score += 30;
    }

    return Math.min(100, score);
  }

  private async isSuspiciousIP(ip: string): Promise<boolean> {
    // Check against IP reputation services
    // For now, just check if it's a VPN/Tor exit node
    return false;
  }
}
```

---

## Multi-Tenancy

### Tenant Isolation

```typescript
// ============================================================================
// MULTI-TENANCY MODEL
// ============================================================================

interface Tenant {
  id: string;
  name: string;
  slug: string;                  // URL subdomain
  type: 'agency' | 'corporate' | 'white_label';

  // Branding
  branding: {
    logo?: string;
    colors: {
      primary: string;
      secondary: string;
    };
    domain?: string;
  };

  // Configuration
  config: {
    defaultCurrency: string;
    defaultLanguage: string;
    supportedCurrencies: string[];
    supportedLanguages: string[];
  };

  // Status
  status: 'active' | 'suspended' | 'trial';

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

// Tenant-aware user query
class TenantAwareUserService {
  async findByEmail(
    tenantId: string,
    email: string
  ): Promise<User | null> {
    // Users belong to tenants
    return await User.findOne({
      tenantId,
      email,
      deletedAt: null,
    });
  }

  async create(
    tenantId: string,
    input: RegisterInput
  ): Promise<User> {
    // User created under specific tenant
    return await User.create({
      ...input,
      tenantId,
    });
  }
}
```

---

## Integration Points

### External Services

| Service | Purpose | Integration |
|---------|---------|-------------|
| **SendGrid** | Transactional emails | Email verification, password reset |
| **Twilio** | SMS notifications | 2FA, verification codes |
| **Google OAuth** | Social authentication | Google signup/login |
| **Apple Sign In** | Social authentication | Apple signup/login |
| **Stripe** | Payment methods | Save payment methods to profile |
| **Fivetran** | Data sync | User data to warehouse |

---

## Privacy & Compliance

### GDPR Compliance

```typescript
// ============================================================================
// DATA MANAGEMENT
// ============================================================================

interface DataPrivacyRequest {
  type: 'access' | 'portability' | 'deletion' | 'rectification';
  userId: string;
  status: 'pending' | 'processing' | 'completed';
  requestedAt: Date;
  completedAt?: Date;
  resultUrl?: string;
}

class PrivacyService {
  async exportUserData(userId: string): Promise<string> {
    // Collect all user data
    const user = await User.findById(userId);
    const profile = await UserProfile.findByUserId(userId);
    const travelers = await TravelerProfile.findByUserId(userId);
    const bookings = await Booking.findByUserId(userId);
    const reviews = await Review.findByUserId(userId);

    const exportData = {
      personal: { user, profile },
      travelers,
      bookings: bookings.map(b => ({
        reference: b.reference,
        dates: b.dates,
        destinations: b.destinations,
      })),
      reviews: reviews.map(r => ({
        rating: r.rating,
        comment: r.comment,
        product: r.productId,
      })),
      exportedAt: new Date(),
    };

    return JSON.stringify(exportData, null, 2);
  }

  async deleteUserData(userId: string): Promise<void> {
    // Anonymize rather than delete for data integrity
    await User.update(userId, {
      email: `deleted-${userId}@anonymous.local`,
      phone: null,
      passwordHash: null,
      deletedAt: new Date(),
    });

    // Delete sensitive data
    await UserProfile.deleteByUserId(userId);
    await TravelerProfile.deleteByUserId(userId);

    // Anonymize bookings
    await Booking.anonymizeByUserId(userId);

    // Delete auth events
    await AuthEvent.deleteByUserId(userId);
  }

  async processConsent(userId: string, consent: ConsentRecord): Promise<void> {
    await UserConsent.create({
      userId,
      ...consent,
      recordedAt: new Date(),
      ipAddress: consent.ipAddress,
    });
  }
}

interface ConsentRecord {
  analytics: boolean;
  personalization: boolean;
  thirdParty: boolean;
  marketing: boolean;
  ipAddress: string;
}
```

---

**Next:** [Registration](./USER_ACCOUNTS_02_REGISTRATION.md) — Signup flows, verification, and onboarding
