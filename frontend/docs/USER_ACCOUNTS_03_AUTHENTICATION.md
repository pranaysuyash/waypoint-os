# User Accounts 03: Authentication

> Login, sessions, password reset, multi-factor authentication, and single sign-on

---

## Overview

This document details the authentication subsystem, covering credential-based login, session management, password recovery, multi-factor authentication (MFA), and single sign-on (SSO) integration. Authentication is built on JWT tokens with refresh token rotation for secure, scalable session management.

**Key Capabilities:**
- Credential-based and social authentication
- Secure session management with refresh tokens
- Self-service password reset
- Time-based one-time password (TOTP) MFA
- SAML/OIDC single sign-on
- Comprehensive security controls

---

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Login Process](#login-process)
3. [Session Management](#session-management)
4. [Password Reset](#password-reset)
5. [Multi-Factor Authentication](#multi-factor-authentication)
6. [Single Sign-On](#single-sign-on)
7. [Security Controls](#security-controls)
8. [Error Handling](#error-handling)

---

## Authentication Flow

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUTHENTICATION OVERVIEW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │   CREDENTIAL │      │     SOCIAL   │      │     SSO      │              │
│  │     LOGIN    │      │     AUTH     │      │   (SAML)     │              │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘              │
│         │                     │                     │                       │
│         └─────────────────────┴─────────────────────┘                       │
│                               │                                             │
│                               ▼                                             │
│                    ┌──────────────────┐                                     │
│                    │   AUTH SERVICE   │                                     │
│                    │  (validation)    │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                ┌────────────┴────────────┐                                  │
│                │                         │                                  │
│                ▼                         ▼                                  │
│         ┌──────────┐            ┌─────────────┐                            │
│         │   MFA    │            │  NO MFA     │                            │
│         │  CHECK   │            │  CONTINUE   │                            │
│         └────┬─────┘            └──────┬──────┘                            │
│              │                         │                                    │
│              ▼                         │                                    │
│     ┌─────────────────┐                │                                    │
│     │  MFA CHALLENGE  │                │                                    │
│     └────────┬────────┘                │                                    │
│              │                         │                                    │
│              └────────────┬────────────┘                                    │
│                           │                                                 │
│                           ▼                                                 │
│                ┌──────────────────────┐                                     │
│                │   TOKEN GENERATION   │                                     │
│                │  (access + refresh)  │                                     │
│                └──────────┬───────────┘                                     │
│                           │                                                 │
│                           ▼                                                 │
│                ┌──────────────────────┐                                     │
│                │   SESSION CREATED    │                                     │
│                │   + REDIRECT         │                                     │
│                └──────────────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Email/Password** | Traditional credential authentication | Standard user registration |
| **Social OAuth** | Google, Apple, Facebook OAuth 2.0 | Reduced signup friction |
| **SSO/SAML** | Enterprise single sign-on | Corporate travel programs |
| **Magic Link** | Passwordless email login | Enhanced security option |

---

## Login Process

### Credential Login

The credential login validates email/password pairs, enforces account status checks, and initiates MFA when enabled.

**Request Schema:**
```typescript
interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
  deviceInfo?: DeviceInfo;
}

interface DeviceInfo {
  userAgent: string;
  ipAddress: string;
  fingerprint?: string;
  platform: 'web' | 'mobile' | 'tablet';
}
```

**Response Schema:**
```typescript
interface LoginResponse {
  success: boolean;
  requiresMFA: boolean;
  mfaType?: 'totp' | 'sms' | 'email';
  tokens?: TokenPair;
  user?: UserSummary;
  newDevice?: boolean;
}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: 'Bearer';
}
```

**Implementation:**
```typescript
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { UserService } from './user.service';
import { SessionService } from './session.service';
import { MFACheckpoint } from './mfa.checkpoint';

export class AuthenticationService {
  private readonly SALT_ROUNDS = 12;
  private readonly ACCESS_TOKEN_TTL = 15 * 60; // 15 minutes
  private readonly REFRESH_TOKEN_TTL = 30 * 24 * 60 * 60; // 30 days

  constructor(
    private userService: UserService,
    private sessionService: SessionService,
    private mfaCheckpoint: MFACheckpoint
  ) {}

  async loginWithCredentials(
    request: LoginRequest,
    context: AuthContext
  ): Promise<LoginResponse> {
    // 1. Validate input format
    this.validateLoginRequest(request);

    // 2. Retrieve user
    const user = await this.userService.findByEmail(request.email);
    if (!user) {
      // Use constant-time comparison to prevent timing attacks
      await bcrypt.hash('dummy', this.SALT_ROUNDS);
      throw new AuthenticationError('Invalid credentials');
    }

    // 3. Verify password
    const isValid = await bcrypt.compare(request.password, user.passwordHash);
    if (!isValid) {
      await this.recordFailedAttempt(user.id, context);
      throw new AuthenticationError('Invalid credentials');
    }

    // 4. Check account status
    this.checkAccountStatus(user);

    // 5. Check for new device
    const isNewDevice = await this.sessionService.isNewDevice(
      user.id,
      context.deviceInfo
    );

    // 6. MFA checkpoint
    if (user.mfaEnabled) {
      const mfaChallenge = await this.mfaCheckpoint.initiateChallenge(
        user,
        context
      );

      return {
        success: true,
        requiresMFA: true,
        mfaType: user.preferredMFAMethod,
      };
    }

    // 7. Create session
    const tokens = await this.createSession(user, request.rememberMe, context);

    // 8. Send new device notification if applicable
    if (isNewDevice) {
      await this.notifyNewDevice(user, context);
    }

    // 9. Clear failed attempts
    await this.clearFailedAttempts(user.id);

    return {
      success: true,
      requiresMFA: false,
      tokens,
      user: this.summarizeUser(user),
      newDevice: isNewDevice,
    };
  }

  private validateLoginRequest(request: LoginRequest): void {
    if (!request.email || !request.password) {
      throw new ValidationError('Email and password are required');
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(request.email)) {
      throw new ValidationError('Invalid email format');
    }
  }

  private checkAccountStatus(user: User): void {
    switch (user.status) {
      case 'suspended':
        throw new AuthenticationError('Account suspended. Contact support.');
      case 'banned':
        throw new AuthenticationError('Account banned');
      case 'pending':
        throw new AuthenticationError('Please verify your email first');
      case 'locked':
        throw new AuthenticationError(
          'Account locked due to suspicious activity. Reset password to unlock.'
        );
      case 'active':
        return;
      default:
        throw new AuthenticationError('Unknown account status');
    }
  }

  private async createSession(
    user: User,
    rememberMe: boolean,
    context: AuthContext
  ): Promise<TokenPair> {
    const sessionId = crypto.randomUUID();

    const accessToken = jwt.sign(
      {
        sub: user.id,
        email: user.email,
        tier: user.tier,
        sessionId,
      },
      process.env.JWT_SECRET!,
      {
        expiresIn: this.ACCESS_TOKEN_TTL,
        issuer: 'travel-agency',
        audience: 'travel-agency-api',
      }
    );

    const refreshTokenExpiry = rememberMe
      ? this.REFRESH_TOKEN_TTL
      : 7 * 24 * 60 * 60; // 7 days

    const refreshToken = jwt.sign(
      {
        sub: user.id,
        sessionId,
        type: 'refresh',
      },
      process.env.JWT_REFRESH_SECRET!,
      {
        expiresIn: refreshTokenExpiry,
      }
    );

    // Store session
    await this.sessionService.create({
      id: sessionId,
      userId: user.id,
      refreshToken: await bcrypt.hash(refreshToken, this.SALT_ROUNDS),
      deviceInfo: context.deviceInfo,
      ipAddress: context.ipAddress,
      expiresAt: new Date(Date.now() + refreshTokenExpiry * 1000),
      rememberMe,
    });

    return {
      accessToken,
      refreshToken,
      expiresIn: this.ACCESS_TOKEN_TTL,
      tokenType: 'Bearer',
    };
  }

  private async recordFailedAttempt(
    userId: string,
    context: AuthContext
  ): Promise<void> {
    await this.failedLoginService.record(userId, context);

    const attempts = await this.failedLoginService.getRecentCount(userId);
    if (attempts >= 5) {
      await this.userService.lockAccount(userId);
      await this.notifyAccountLocked(userId);
    }
  }

  private async notifyNewDevice(user: User, context: AuthContext): Promise<void> {
    await this.notificationService.send({
      userId: user.id,
      type: 'security',
      channel: 'email',
      template: 'new-device-login',
      data: {
        device: context.deviceInfo,
        ip: context.ipAddress,
        timestamp: new Date(),
      },
    });
  }

  private summarizeUser(user: User): UserSummary {
    return {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      tier: user.tier,
      emailVerified: user.emailVerified,
    };
  }
}
```

### Logout Process

Logout invalidates the current session and refresh token, with options to logout from all devices.

**Request Schema:**
```typescript
interface LogoutRequest {
  refreshToken: string;
  allDevices?: boolean;
}
```

**Implementation:**
```typescript
export class LogoutService {
  async logout(request: LogoutRequest, userId: string): Promise<void> {
    if (request.allDevices) {
      // Invalidate all sessions for user
      await this.sessionService.deleteAllForUser(userId);
    } else {
      // Decode token to get session ID
      const payload = jwt.decode(request.refreshToken) as JwtPayload;
      await this.sessionService.delete(payload.sessionId);
    }

    // Add token to blacklist for remaining TTL
    await this.tokenBlacklist.add(request.refreshToken);
  }
}
```

---

## Session Management

### Session Architecture

Sessions are stored in PostgreSQL with Redis caching for fast validation. Each session contains device metadata and supports "remember me" functionality.

**Session Schema:**
```typescript
interface Session {
  id: string;
  userId: string;
  refreshToken: string; // BCrypt hash
  deviceInfo: {
    userAgent: string;
    platform: string;
    fingerprint?: string;
  };
  ipAddress: string;
  lastActivity: Date;
  createdAt: Date;
  expiresAt: Date;
  rememberMe: boolean;
}
```

**Database Schema:**
```sql
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_token_hash VARCHAR(255) NOT NULL,
  device_user_agent TEXT,
  device_platform VARCHAR(50),
  device_fingerprint VARCHAR(255),
  ip_address INET NOT NULL,
  last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  remember_me BOOLEAN DEFAULT false,

  INDEX idx_user_sessions_user_id (user_id),
  INDEX idx_user_sessions_expires_at (expires_at),
  INDEX idx_user_sessions_device_fingerprint (device_fingerprint)
);

CREATE INDEX idx_user_sessions_active
  ON user_sessions(user_id)
  WHERE expires_at > NOW();
```

### Refresh Token Flow

Refresh tokens rotate on each use to detect token theft. Old tokens are immediately invalidated.

```typescript
export class TokenRefreshService {
  async refreshAccessToken(
    refreshToken: string
  ): Promise<TokenPair> {
    // 1. Verify refresh token signature
    let payload: JwtPayload;
    try {
      payload = jwt.verify(
        refreshToken,
        process.env.JWT_REFRESH_SECRET!
      ) as JwtPayload;
    } catch (error) {
      throw new AuthenticationError('Invalid refresh token');
    }

    // 2. Check if token is blacklisted
    const isBlacklisted = await this.tokenBlacklist.has(refreshToken);
    if (isBlacklisted) {
      throw new AuthenticationError('Token revoked');
    }

    // 3. Retrieve session
    const session = await this.sessionService.findById(payload.sessionId);
    if (!session || session.expiresAt < new Date()) {
      throw new AuthenticationError('Session expired');
    }

    // 4. Verify token hash
    const isValid = await bcrypt.compare(refreshToken, session.refreshTokenHash);
    if (!isValid) {
      // Possible token theft - invalidate all sessions
      await this.sessionService.deleteAllForUser(session.userId);
      throw new AuthenticationError('Invalid token');
    }

    // 5. Get user
    const user = await this.userService.findById(session.userId);
    if (!user || user.status !== 'active') {
      throw new AuthenticationError('User not found or inactive');
    }

    // 6. Blacklist old refresh token
    await this.tokenBlacklist.add(refreshToken);

    // 7. Generate new token pair
    const newTokens = await this.createSession(
      user,
      session.rememberMe,
      { deviceInfo: session.deviceInfo, ipAddress: session.ipAddress }
    );

    // 8. Delete old session
    await this.sessionService.delete(session.id);

    return newTokens;
  }
}
```

### Active Sessions Management

Users can view and manage their active sessions across devices.

```typescript
export class SessionManagementService {
  async getActiveSessions(userId: string): Promise<SessionInfo[]> {
    const sessions = await this.sessionService.findActiveByUser(userId);

    return sessions.map(session => ({
      id: session.id,
      device: this.parseDeviceInfo(session.deviceInfo),
      ipAddress: this.maskIpAddress(session.ipAddress),
      lastActivity: session.lastActivity,
      isCurrent: session.id === this.getCurrentSessionId(),
      expiresAt: session.expiresAt,
    }));
  }

  async revokeSession(userId: string, sessionId: string): Promise<void> {
    const session = await this.sessionService.findById(sessionId);

    if (!session || session.userId !== userId) {
      throw new NotFoundError('Session not found');
    }

    await this.sessionService.delete(sessionId);
  }

  async revokeAllOtherSessions(userId: string): Promise<void> {
    const currentSessionId = this.getCurrentSessionId();
    await this.sessionService.deleteAllForUserExcept(userId, currentSessionId);
  }

  private parseDeviceInfo(deviceInfo: Session['deviceInfo']): DeviceDescription {
    const ua = useragent.parse(deviceInfo.userAgent);
    return {
      platform: deviceInfo.platform,
      browser: `${ua.browser} ${ua.major}`,
      os: `${ua.os} ${ua.osVersion}`,
      isMobile: ua.device !== 'Other',
    };
  }

  private maskIpAddress(ip: string): string {
    const parts = ip.split('.');
    if (parts.length === 4) {
      return `${parts[0]}.${parts[1]}.***.***`;
    }
    return '***';
  }
}
```

---

## Password Reset

### Reset Flow

Password reset uses tokenized links sent via email with a short expiry window.

**Flow Diagram:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PASSWORD RESET FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER REQUESTS RESET                                                    │
│     └─> POST /auth/password-reset                                          │
│         { email }                                                           │
│                                                                             │
│  2. SYSTEM VALIDATES & SENDS TOKEN                                         │
│     ├─> Check user exists                                                  │
│     ├─> Generate reset token (1 hour expiry)                               │
│     ├─> Store token hash                                                   │
│     └─> Send email with reset link                                         │
│                                                                             │
│  3. USER CLICKS LINK                                                       │
│     └─> GET /auth/reset-password?token=xxx                                 │
│         (Validate token, show password form)                               │
│                                                                             │
│  4. USER SUBMITS NEW PASSWORD                                              │
│     └─> POST /auth/reset-password                                          │
│         { token, newPassword, confirmPassword }                            │
│                                                                             │
│  5. SYSTEM PROCESSES RESET                                                 │
│     ├─> Validate token                                                     │
│     ├─> Validate password strength                                         │
│     ├─> Hash new password                                                  │
│     ├─> Update user record                                                 │
│     ├─> Invalidate all existing sessions                                   │
│     ├─> Delete reset token                                                 │
│     └─> Send confirmation email                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Implementation:**
```typescript
export class PasswordResetService {
  private readonly TOKEN_TTL = 60 * 60; // 1 hour
  private readonly MIN_PASSWORD_LENGTH = 8;

  async initiateReset(email: string): Promise<void> {
    // Always return success to prevent email enumeration
    const user = await this.userService.findByEmail(email);

    if (!user) {
      return;
    }

    // Check rate limit
    const recentRequests = await this.resetTokenRepository.countRecent(
      user.id,
      15 * 60 // 15 minutes
    );
    if (recentRequests >= 3) {
      // Rate limit exceeded - still return success
      return;
    }

    // Generate token
    const token = crypto.randomBytes(32).toString('hex');
    const tokenHash = await bcrypt.hash(token, this.SALT_ROUNDS);

    // Store token
    await this.resetTokenRepository.create({
      userId: user.id,
      tokenHash,
      expiresAt: new Date(Date.now() + this.TOKEN_TTL * 1000),
    });

    // Send email
    const resetLink = `${process.env.APP_URL}/auth/reset-password?token=${token}`;
    await this.emailService.send({
      to: user.email,
      template: 'password-reset',
      data: {
        resetLink,
        expiresAt: new Date(Date.now() + this.TOKEN_TTL * 1000),
      },
    });
  }

  async resetPassword(request: PasswordResetRequest): Promise<void> {
    const { token, newPassword, confirmPassword } = request;

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      throw new ValidationError('Passwords do not match');
    }

    // Validate password strength
    this.validatePasswordStrength(newPassword);

    // Find token record
    const resetTokens = await this.resetTokenRepository.findValid();
    let validToken: PasswordResetToken | null = null;

    for (const resetToken of resetTokens) {
      const isValid = await bcrypt.compare(token, resetToken.tokenHash);
      if (isValid) {
        validToken = resetToken;
        break;
      }
    }

    if (!validToken) {
      throw new AuthenticationError('Invalid or expired reset token');
    }

    // Get user
    const user = await this.userService.findById(validToken.userId);

    // Check new password isn't same as old
    const isSamePassword = await bcrypt.compare(
      newPassword,
      user.passwordHash
    );
    if (isSamePassword) {
      throw new ValidationError(
        'New password must be different from current password'
      );
    }

    // Hash new password
    const newPasswordHash = await bcrypt.hash(
      newPassword,
      this.SALT_ROUNDS
    );

    // Update user
    await this.userService.updatePassword(user.id, newPasswordHash);

    // Invalidate all sessions
    await this.sessionService.deleteAllForUser(user.id);

    // Delete reset token
    await this.resetTokenRepository.delete(validToken.id);

    // Unlock account if locked
    if (user.status === 'locked') {
      await this.userService.unlockAccount(user.id);
    }

    // Send confirmation
    await this.emailService.send({
      to: user.email,
      template: 'password-reset-confirmation',
      data: {
        timestamp: new Date(),
      },
    });
  }

  private validatePasswordStrength(password: string): void {
    if (password.length < this.MIN_PASSWORD_LENGTH) {
      throw new ValidationError(
        `Password must be at least ${this.MIN_PASSWORD_LENGTH} characters`
      );
    }

    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);

    if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecial) {
      throw new ValidationError(
        'Password must contain uppercase, lowercase, number, and special character'
      );
    }
  }
}
```

### Password Requirements

| Requirement | Specification |
|-------------|---------------|
| **Minimum Length** | 8 characters |
| **Complexity** | Uppercase, lowercase, number, special |
| **Common Passwords** | Blocked via dictionary check |
| **History** | Cannot reuse last 5 passwords |
| **Expiry** | No forced expiry (NIST guidelines) |

---

## Multi-Factor Authentication

### MFA Overview

MFA adds a second factor of authentication using time-based one-time passwords (TOTP). Users can enable MFA optionally, with required MFA for elevated-risk activities.

**Supported MFA Methods:**
- **TOTP**: Time-based codes (Google Authenticator, Authy, etc.)
- **SMS**: Text message codes (backup method)
- **Email**: Email codes (fallback)

### MFA Setup Flow

```typescript
export class MFASetupService {
  async initiateSetup(userId: string): Promise<MFASetupChallenge> {
    const user = await this.userService.findById(userId);

    if (user.mfaEnabled) {
      throw new ConflictError('MFA already enabled');
    }

    // Generate secret
    const secret = authenticator.generateSecret();

    // Generate QR code URI
    const qrCodeUri = authenticator.keyuri(
      user.email,
      'TravelAgency',
      secret
    );

    // Store temporary secret (encrypted)
    await this.mfaSecretRepository.create({
      userId,
      secretEncrypted: await this.encrypt(secret),
      expiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes
    });

    // Generate backup codes
    const backupCodes = this.generateBackupCodes(userId);

    return {
      qrCodeUri,
      backupCodes,
    };
  }

  async verifyAndEnable(
    userId: string,
    code: string
  ): Promise<void> {
    // Retrieve temporary secret
    const tempSecret = await this.mfaSecretRepository.findPending(userId);

    if (!tempSecret || tempSecret.expiresAt < new Date()) {
      throw new AuthenticationError('MFA setup expired. Please start over.');
    }

    const secret = await this.decrypt(tempSecret.secretEncrypted);

    // Verify code
    const isValid = authenticator.verify({
      token: code,
      secret,
    });

    if (!isValid) {
      throw new AuthenticationError('Invalid code');
    }

    // Enable MFA for user
    await this.userService.enableMFA(userId, secret);

    // Delete temporary secret
    await this.mfaSecretRepository.delete(tempSecret.id);

    // Store backup codes
    await this.backupCodeRepository.store(userId, tempSecret.backupCodes);

    // Send confirmation email
    const user = await this.userService.findById(userId);
    await this.emailService.send({
      to: user.email,
      template: 'mfa-enabled',
      data: {
        timestamp: new Date(),
      },
    });
  }

  async disable(userId: string, password: string): Promise<void> {
    const user = await this.userService.findById(userId);

    // Verify password
    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
      throw new AuthenticationError('Invalid password');
    }

    // Disable MFA
    await this.userService.disableMFA(userId);

    // Delete backup codes
    await this.backupCodeRepository.deleteAll(userId);

    // Send confirmation
    await this.emailService.send({
      to: user.email,
      template: 'mfa-disabled',
      data: {
        timestamp: new Date(),
      },
    });
  }

  private generateBackupCodes(userId: string): string[] {
    const codes: string[] = [];
    for (let i = 0; i < 10; i++) {
      codes.push(crypto.randomBytes(4).toString('hex'));
    }
    return codes;
  }

  private async encrypt(data: string): Promise<string> {
    // Implementation uses AES-256-GCM
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(
      'aes-256-gcm',
      Buffer.from(process.env.MFA_ENCRYPTION_KEY!, 'hex'),
      iv
    );
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag();
    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  private async decrypt(encrypted: string): Promise<string> {
    const [ivHex, authTagHex, data] = encrypted.split(':');
    const iv = Buffer.from(ivHex, 'hex');
    const authTag = Buffer.from(authTagHex, 'hex');
    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      Buffer.from(process.env.MFA_ENCRYPTION_KEY!, 'hex'),
      iv
    );
    decipher.setAuthTag(authTag);
    let decrypted = decipher.update(data, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }
}
```

### MFA Verification

```typescript
export class MFACheckpoint {
  async initiateChallenge(
    user: User,
    context: AuthContext
  ): Promise<MFAChallenge> {
    const challengeId = crypto.randomUUID();

    // Store challenge
    await this.mfaChallengeRepository.create({
      id: challengeId,
      userId: user.id,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes
    });

    return {
      challengeId,
      method: user.preferredMFAMethod || 'totp',
    };
  }

  async verifyChallenge(
    challengeId: string,
    code: string,
    context: AuthContext
  ): Promise<TokenPair> {
    // Retrieve challenge
    const challenge = await this.mfaChallengeRepository.findById(challengeId);

    if (!challenge || challenge.expiresAt < new Date()) {
      throw new AuthenticationError('Challenge expired');
    }

    // Get user
    const user = await this.userService.findById(challenge.userId);

    // Verify code based on method
    let isValid = false;

    switch (user.preferredMFAMethod) {
      case 'totp':
        isValid = this.verifyTOTP(code, user.mfaSecret!);
        break;
      case 'backup':
        isValid = await this.verifyBackupCode(challenge.userId, code);
        break;
      default:
        throw new ValidationError('Unsupported MFA method');
    }

    if (!isValid) {
      // Record failed attempt
      await this.recordFailedMFAAttempt(challengeId);

      const attempts = await this.getMFAAttemptCount(challengeId);
      if (attempts >= 3) {
        await this.mfaChallengeRepository.delete(challengeId);
        throw new AuthenticationError('Too many failed attempts. Please login again.');
      }

      throw new AuthenticationError('Invalid code');
    }

    // Delete challenge
    await this.mfaChallengeRepository.delete(challengeId);

    // Create session
    const tokens = await this.authService.createSession(user, false, context);

    return tokens;
  }

  private verifyTOTP(code: string, secret: string): boolean {
    // Allow 1 time step window (30 seconds)
    return authenticator.verify({
      token: code,
      secret,
      window: 1,
    });
  }

  private async verifyBackupCode(
    userId: string,
    code: string
  ): Promise<boolean> {
    const backupCode = await this.backupCodeRepository.find(userId, code);

    if (!backupCode) {
      return false;
    }

    // Mark as used
    await this.backupCodeRepository.markUsed(backupCode.id);

    // Warn if low on backup codes
    const remainingCount = await this.backupCodeRepository.countUnused(userId);
    if (remainingCount <= 3) {
      const user = await this.userService.findById(userId);
      await this.emailService.send({
        to: user.email,
        template: 'backup-codes-low',
        data: { remaining: remainingCount },
      });
    }

    return true;
  }
}
```

---

## Single Sign-On

### SSO Overview

SSO enables enterprise customers to use their existing identity provider (IdP) for authentication. We support SAML 2.0 and OpenID Connect protocols.

**Supported Providers:**
- Okta
- Azure Active Directory
- Google Workspace
- OneLogin
- Generic SAML 2.0 / OIDC

### SAML SSO Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAML SSO FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER INITIATES LOGIN                                                   │
│     └─> GET /auth/sso/:ssoId                                               │
│                                                                             │
│  2. SYSTEM GENERATES SAML REQUEST                                          │
│     ├─> Retrieve SSO configuration                                         │
│     ├─> Generate SAML AuthnRequest                                         │
│     └─> Redirect to IdP login URL                                          │
│                                                                             │
│  3. USER AUTHENTICATES WITH IDP                                            │
│     └─> (IdP handles authentication)                                       │
│                                                                             │
│  4. IDP SENDS SAML RESPONSE                                                │
│     └─> POST /auth/sso/callback                                           │
│         { SAMLResponse }                                                    │
│                                                                             │
│  5. SYSTEM PROCESSES RESPONSE                                              │
│     ├─> Validate SAML response signature                                  │
│     ├─> Extract user attributes                                            │
│     ├─> Match/create user account                                          │
│     ├─> Provision user if needed                                           │
│     └─> Create session                                                     │
│                                                                             │
│  6. REDIRECT TO APPLICATION                                                │
│     └─> User is logged in                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Implementation:**
```typescript
import { SamlStrategy } from '@node-saml/passport-saml';

export class SSOService {
  async initiateSSO(ssoId: string, relayState?: string): Promise<string> {
    const ssoConfig = await this.ssoConfigRepository.findById(ssoId);

    if (!ssoConfig || !ssoConfig.enabled) {
      throw new NotFoundError('SSO configuration not found');
    }

    // Generate SAML request
    const samlRequest = this.generateSAMLRequest(ssoConfig);

    // Build IdP redirect URL
    const idpUrl = new URL(ssoConfig.idpSsoUrl);
    idpUrl.searchParams.set('SAMLRequest', Buffer.from(samlRequest).toString('base64'));

    if (relayState) {
      idpUrl.searchParams.set('RelayState', relayState);
    }

    return idpUrl.toString();
  }

  async handleSAMLResponse(
    samlResponse: string,
    relayState?: string
  ): Promise<LoginResponse> {
    // Decode and validate SAML response
    const profile = await this.validateSAMLResponse(samlResponse);

    // Find or create user
    let user = await this.userService.findBySSOId(
      profile.nameID,
      profile.issuer
    );

    if (!user) {
      // Check if auto-provisioning is enabled
      const ssoConfig = await this.ssoConfigRepository.findByIssuer(profile.issuer);

      if (!ssoConfig?.autoProvision) {
        throw new AuthenticationError(
          'User not found. Contact your administrator.'
        );
      }

      // Provision user
      user = await this.provisionUser(profile, ssoConfig);
    }

    // Check account status
    if (user.status !== 'active') {
      throw new AuthenticationError(`Account is ${user.status}`);
    }

    // Create session
    const tokens = await this.authService.createSession(
      user,
      false,
      { deviceInfo: this.parseDeviceContext(relayState) }
    );

    return {
      success: true,
      requiresMFA: false,
      tokens,
      user: this.summarizeUser(user),
    };
  }

  private async validateSAMLResponse(
    samlResponse: string
  ): Promise<SAMLProfile> {
    // Verify signature
    const decoded = await this.samlLib.validatePostResponseAsync({
      body: { SAMLResponse: samlResponse },
    });

    // Extract attributes
    return {
      nameID: decoded.nameID,
      issuer: decoded.issuer,
      email: decoded.attributes?.email?.[0],
      firstName: decoded.attributes?.firstName?.[0] || '',
      lastName: decoded.attributes?.lastName?.[0] || '',
      groups: decoded.attributes?.groups || [],
    };
  }

  private async provisionUser(
    profile: SAMLProfile,
    ssoConfig: SSOConfig
  ): Promise<User> {
    // Map groups to roles
    const roles = this.mapGroupsToRoles(profile.groups, ssoConfig);

    return await this.userService.create({
      email: profile.email,
      authProvider: 'sso',
      ssoProvider: profile.issuer,
      ssoId: profile.nameID,
      firstName: profile.firstName,
      lastName: profile.lastName,
      status: 'active',
      tier: ssoConfig.defaultTier || 'standard',
      roles,
    });
  }

  private mapGroupsToRoles(groups: string[], ssoConfig: SSOConfig): string[] {
    const roles: string[] = [];

    for (const [group, mappedRole] of Object.entries(ssoConfig.groupMappings)) {
      if (groups.includes(group)) {
        roles.push(mappedRole);
      }
    }

    return roles.length > 0 ? roles : ['customer'];
  }
}
```

### SSO Configuration Schema

```typescript
interface SSOConfig {
  id: string;
  name: string;
  enabled: boolean;
  autoProvision: boolean;
  defaultTier: CustomerTier;

  // IdP configuration
  idpEntityId: string;
  idpSsoUrl: string;
  idpCertificate: string;
  idpLogoutUrl?: string;

  // SP configuration
  spEntityId: string;
  spAcsUrl: string;
  spCertificate: string;
  spPrivateKey: string;

  // Attribute mapping
  attributeMapping: {
    email: string;
    firstName: string;
    lastName: string;
    groups: string;
  };

  // Role mapping
  groupMappings: Record<string, string>;

  // Domain restriction
  allowedDomains?: string[];
}
```

---

## Security Controls

### Rate Limiting

```typescript
export class AuthRateLimiter {
  private readonly limits = {
    login: { max: 5, window: 60 * 1000 }, // 5 per minute
    passwordReset: { max: 3, window: 15 * 60 * 1000 }, // 3 per 15 min
    mfaVerify: { max: 3, window: 5 * 60 * 1000 }, // 3 per 5 min
    registration: { max: 3, window: 60 * 60 * 1000 }, // 3 per hour
  };

  async checkLimit(
    action: keyof typeof this.limits,
    identifier: string
  ): Promise<void> {
    const { max, window } = this.limits[action];

    const count = await this.redis.incr(`ratelimit:${action}:${identifier}`);

    if (count === 1) {
      await this.redis.expire(`ratelimit:${action}:${identifier}`, window / 1000);
    }

    if (count > max) {
      const retryAfter = await this.redis.ttl(`ratelimit:${action}:${identifier}`);
      throw new RateLimitError(`Too many ${action} attempts`, retryAfter);
    }
  }
}
```

### Account Lockout

```typescript
export class AccountLockoutService {
  private readonly MAX_ATTEMPTS = 5;
  private readonly LOCKOUT_DURATION = 30 * 60 * 1000; // 30 minutes

  async recordFailedAttempt(userId: string, context: AuthContext): Promise<void> {
    const key = `failed_attempts:${userId}`;
    const attempts = await this.redis.incr(key);

    if (attempts === 1) {
      await this.redis.expire(key, 60 * 60); // 1 hour
    }

    if (attempts >= this.MAX_ATTEMPTS) {
      await this.lockAccount(userId, this.LOCKOUT_DURATION);
    }
  }

  async lockAccount(userId: string, duration: number): Promise<void> {
    await this.userService.lockAccount(userId);

    const lockKey = `account_locked:${userId}`;
    await this.redis.set(lockKey, '1', 'PX', duration);

    // Notify user
    await this.sendLockoutNotification(userId);
  }

  async isLocked(userId: string): Promise<boolean> {
    const locked = await this.redis.get(`account_locked:${userId}`);
    return locked !== null;
  }
}
```

### Device Fingerprinting

```typescript
export class DeviceFingerprintService {
  generateFingerprint(request: Request): string {
    const components = {
      userAgent: request.headers['user-agent'],
      acceptLanguage: request.headers['accept-language'],
      acceptEncoding: request.headers['accept-encoding'],
      platform: this.detectPlatform(request),
    };

    const hash = crypto
      .createHash('sha256')
      .update(JSON.stringify(components))
      .digest('hex');

    return hash.substring(0, 16);
  }

  private detectPlatform(request: Request): string {
    const ua = request.headers['user-agent'] || '';

    if (/Mobile|Android|iPhone|iPad/i.test(ua)) {
      return 'mobile';
    }

    if (/Tablet/i.test(ua)) {
      return 'tablet';
    }

    return 'desktop';
  }
}
```

---

## Error Handling

### Error Types

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `InvalidCredentialsError` | 401 | Email/password mismatch |
| `AccountLockedError` | 403 | Account temporarily locked |
| `AccountSuspendedError` | 403 | Account administratively suspended |
| `EmailNotVerifiedError` | 403 | Email verification required |
| `MFANotVerifiedError` | 403 | MFA code required or invalid |
| `TokenExpiredError` | 401 | Access/refresh token expired |
| `TokenInvalidError` | 401 | Token signature invalid |
| `RateLimitError` | 429 | Too many attempts |
| `SSOConfigurationError` | 500 | SSO misconfiguration |

### Error Response Format

```typescript
interface AuthErrorResponse {
  error: {
    code: string;
    message: string;
    details?: {
      field?: string;
      retryAfter?: number;
      remainingAttempts?: number;
    };
  };
}
```

---

## API Endpoints

### Authentication Endpoints

```
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
POST   /auth/register
POST   /auth/verify-email
POST   /auth/resend-verification
POST   /auth/password-reset
POST   /auth/reset-password
POST   /auth/mfa/setup
POST   /auth/mfa/verify
POST   /auth/mfa/disable
GET    /auth/sso/:ssoId
POST   /auth/sso/callback
```

### Session Management Endpoints

```
GET    /auth/sessions
DELETE /auth/sessions/:sessionId
DELETE /auth/sessions
```

---

**Next:** [User Profiles](./USER_ACCOUNTS_04_PROFILES.md) — Profile management, preferences, and settings
