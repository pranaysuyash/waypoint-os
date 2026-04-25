# SECURITY_01: Authentication Deep Dive

> JWT tokens, sessions, MFA, SSO, and identity management

---

## Table of Contents

1. [Overview](#overview)
2. [JWT Architecture](#jwt-architecture)
3. [Session Management](#session-management)
4. [Password Security](#password-security)
5. [Multi-Factor Authentication](#multi-factor-authentication)
6. [Single Sign-On](#single-sign-on)
7. [Token Lifecycle](#token-lifecycle)
8. [Account Recovery](#account-recovery)

---

## Overview

### Authentication vs Authorization

```
┌─────────────────────────────────────────────────────────────────┐
│                   AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. AUTHENTICATION (Who are you?)                               │
│     ├── Credentials (email/password)                            │
│     ├── MFA verification                                        │
│     └── Identity confirmed                                      │
│                                                                  │
│  2. AUTHORIZATION (What can you do?)                            │
│     ├── Role lookup                                            │
│     ├── Permission check                                       │
│     └── Access granted/denied                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Methods Supported

| Method | Use Case | Security |
|--------|----------|----------|
| **Email/Password** | Standard login | Medium |
| **Magic Link** | Passwordless | High |
| **SSO (Google/Microsoft)** | Enterprise | High |
| **Mobile OTP** | 2FA backup | High |
| **Authenticator App** | Preferred 2FA | Very High |
| **Hardware Key** | Premium security | Very High |

---

## JWT Architecture

### Token Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        JWT TOKEN                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM...      │
│  └───────────────┬────────────────┘ └────────────────────┘     │
│                  │                                          │    │
│             HEADER                                    PAYLOAD    │
│                                                         │       │
│                                            ┌────────────┘       │
│                                            │                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SIGNATURE (HMACSHA256)                                  │   │
│  │  = base64url(HMACSHA256(header + "." + payload, secret))│   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Access Token Payload

```typescript
interface JwtPayload {
  // Standard claims
  iss: string;           // Issuer (domain)
  sub: string;           // Subject (user ID)
  aud: string;           // Audience (api/app)
  exp: number;           // Expiration (timestamp)
  iat: number;           // Issued at (timestamp)
  jti: string;           // JWT ID (unique token ID)

  // Custom claims
  userId: string;
  agencyId: string;
  role: UserRole;
  permissions: Permission[];
  mfaVerified: boolean;
  tokenType: 'access' | 'refresh';

  // Session tracking
  sessionId: string;
  deviceFingerprint?: string;
}
```

### Token Generation

```typescript
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';

interface TokenConfig {
  accessTokenExpiry: string;      // e.g., "15m"
  refreshTokenExpiry: string;     // e.g., "7d"
  issuer: string;
  audience: string;
  secret: string;
}

export class TokenService {
  constructor(private config: TokenConfig) {}

  async generateAccessToken(user: User, session: Session): Promise<string> {
    const payload: JwtPayload = {
      iss: this.config.issuer,
      sub: user.id,
      aud: this.config.audience,
      exp: Math.floor(Date.now() / 1000) + this.parseExpiry(this.config.accessTokenExpiry),
      iat: Math.floor(Date.now() / 1000),
      jti: uuidv4(),

      // Custom claims
      userId: user.id,
      agencyId: user.agencyId,
      role: user.role,
      permissions: await this.getUserPermissions(user),
      mfaVerified: session.mfaVerified || false,
      tokenType: 'access',

      // Session tracking
      sessionId: session.id,
      deviceFingerprint: session.deviceFingerprint,
    };

    return jwt.sign(payload, this.config.secret, {
      algorithm: 'HS256',
      header: { typ: 'JWT' },
    });
  }

  async generateRefreshToken(user: User, session: Session): Promise<string> {
    const payload: Partial<JwtPayload> = {
      iss: this.config.issuer,
      sub: user.id,
      aud: this.config.audience,
      exp: Math.floor(Date.now() / 1000) + this.parseExpiry(this.config.refreshTokenExpiry),
      iat: Math.floor(Date.now() / 1000),
      jti: uuidv4(),

      userId: user.id,
      agencyId: user.agencyId,
      tokenType: 'refresh',
      sessionId: session.id,
    };

    return jwt.sign(payload, this.config.secret, {
      algorithm: 'HS256',
    });
  }

  verifyToken(token: string): JwtPayload | null {
    try {
      return jwt.verify(token, this.config.secret, {
        issuer: this.config.issuer,
        audience: this.config.audience,
        algorithms: ['HS256'],
      }) as JwtPayload;
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new AuthError('TOKEN_EXPIRED', 'Token has expired');
      }
      if (error instanceof jwt.JsonWebTokenError) {
        throw new AuthError('TOKEN_INVALID', 'Invalid token');
      }
      throw new AuthError('AUTH_ERROR', 'Authentication failed');
    }
  }

  private parseExpiry(expiry: string): number {
    // Parse "15m", "7d", "1h" etc. to seconds
    const match = expiry.match(/^(\d+)([smhd])$/);
    if (!match) return 3600; // Default 1 hour

    const [, value, unit] = match;
    const multipliers: Record<string, number> = {
      s: 1,
      m: 60,
      h: 3600,
      d: 86400,
    };

    return parseInt(value) * multipliers[unit];
  }

  private async getUserPermissions(user: User): Promise<Permission[]> {
    // Fetch user's permissions based on role
    return PermissionRepository.findByRole(user.role);
  }
}
```

### Token Validation Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    agencyId: string;
    role: UserRole;
    permissions: Permission[];
    sessionId: string;
  };
}

export const authenticate = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader?.startsWith('Bearer ')) {
      throw new AuthError('NO_TOKEN', 'Authorization token required');
    }

    const token = authHeader.substring(7);

    // Verify token
    const payload = tokenService.verifyToken(token);

    if (payload.tokenType !== 'access') {
      throw new AuthError('INVALID_TOKEN_TYPE', 'Access token required');
    }

    // Check if session is still valid
    const session = await SessionRepository.findById(payload.sessionId);
    if (!session || session.revokedAt) {
      throw new AuthError('SESSION_INVALID', 'Session has been revoked');
    }

    // Check device fingerprint for sensitive operations
    if (payload.deviceFingerprint) {
      const currentFingerprint = req.fingerprint?.hash;
      if (currentFingerprint && currentFingerprint !== payload.deviceFingerprint) {
        // Suspicious activity - require re-authentication
        await SessionRepository.revoke(payload.sessionId);
        throw new AuthError('DEVICE_MISMATCH', 'New device detected. Please login again.');
      }
    }

    // Attach user to request
    req.user = {
      id: payload.userId,
      agencyId: payload.agencyId,
      role: payload.role,
      permissions: payload.permissions,
      sessionId: payload.sessionId,
    };

    next();
  } catch (error) {
    if (error instanceof AuthError) {
      res.status(401).json({
        error: error.code,
        message: error.message,
      });
    } else {
      res.status(500).json({ error: 'AUTH_ERROR', message: 'Authentication failed' });
    }
  }
};

// Optional authentication - doesn't throw if no token
export const optionalAuthenticate = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return next();
  }

  return authenticate(req, res, next);
};

// Require specific permission
export const requirePermission = (permission: string) => {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.user) {
      return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
    }

    const hasPermission = req.user.permissions.some(
      (p) => p.name === permission || p.name === '*'
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

// Require specific role
export const requireRole = (...roles: UserRole[]) => {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.user) {
      return res.status(401).json({ error: 'AUTHENTICATED_REQUIRED' });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'ROLE_REQUIRED',
        message: `One of roles ${roles.join(', ')} required`,
      });
    }

    next();
  };
};
```

---

## Session Management

### Session Model

```typescript
interface Session {
  id: string;
  userId: string;
  agencyId: string;

  // Device info
  deviceFingerprint: string;
  deviceInfo: {
    type: 'desktop' | 'mobile' | 'tablet';
    os: string;
    browser: string;
    ip: string;
  };

  // MFA status
  mfaVerified: boolean;
  mfaMethod?: 'totp' | 'sms' | 'email' | 'hardware';

  // Timestamps
  createdAt: Date;
  lastActiveAt: Date;
  expiresAt: Date;
  revokedAt?: Date;

  // Refresh token
  refreshTokenHash: string;

  // Metadata
  location?: {
    country: string;
    city: string;
    timezone: string;
  };
}
```

### Session Creation

```typescript
export class SessionService {
  async createSession(
    user: User,
    deviceInfo: DeviceInfo,
    mfaVerified = false
  ): Promise<{ session: Session; tokens: TokenPair }> {
    // Generate device fingerprint
    const deviceFingerprint = this.generateFingerprint(deviceInfo);

    // Create session
    const session = await SessionRepository.create({
      userId: user.id,
      agencyId: user.agencyId,
      deviceFingerprint,
      deviceInfo: {
        type: deviceInfo.type,
        os: deviceInfo.os,
        browser: deviceInfo.browser,
        ip: deviceInfo.ip,
      },
      mfaVerified,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      location: await this.getLocation(deviceInfo.ip),
    });

    // Generate tokens
    const accessToken = await tokenService.generateAccessToken(user, session);
    const refreshToken = await tokenService.generateRefreshToken(user, session);

    // Hash refresh token for storage
    const refreshTokenHash = await this.hashRefreshToken(refreshToken);
    await SessionRepository.update(session.id, { refreshTokenHash });

    return {
      session,
      tokens: {
        accessToken,
        refreshToken,
        expiresIn: 15 * 60, // 15 minutes
      },
    };
  }

  async refreshAccessToken(refreshToken: string): Promise<TokenPair> {
    // Verify refresh token
    const payload = tokenService.verifyToken(refreshToken);
    if (payload.tokenType !== 'refresh') {
      throw new AuthError('INVALID_TOKEN_TYPE', 'Refresh token required');
    }

    // Get session
    const session = await SessionRepository.findById(payload.sessionId);
    if (!session || session.revokedAt) {
      throw new AuthError('SESSION_INVALID', 'Session has been revoked');
    }

    // Verify refresh token hash
    const refreshTokenHash = await this.hashRefreshToken(refreshToken);
    if (refreshTokenHash !== session.refreshTokenHash) {
      // Possible token theft - revoke session
      await SessionRepository.revoke(session.id);
      throw new AuthError('TOKEN_STOLEN', 'Session compromised');
    }

    // Get user
    const user = await UserRepository.findById(payload.userId);
    if (!user) {
      throw new AuthError('USER_NOT_FOUND', 'User not found');
    }

    // ROTATE refresh token (security best practice)
    const newRefreshToken = await tokenService.generateRefreshToken(user, session);
    const newRefreshTokenHash = await this.hashRefreshToken(newRefreshToken);

    // Generate new access token
    const newAccessToken = await tokenService.generateAccessToken(user, session);

    // Update session with new refresh token hash
    await SessionRepository.update(session.id, {
      refreshTokenHash: newRefreshTokenHash,
      lastActiveAt: new Date(),
    });

    return {
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
      expiresIn: 15 * 60,
    };
  }

  async revokeSession(sessionId: string, userId: string): Promise<void> {
    const session = await SessionRepository.findById(sessionId);

    if (!session || session.userId !== userId) {
      throw new AuthError('SESSION_NOT_FOUND', 'Session not found');
    }

    await SessionRepository.revoke(sessionId);
  }

  async revokeAllSessions(userId: string, exceptSessionId?: string): Promise<void> {
    await SessionRepository.revokeAllForUser(userId, exceptSessionId);
  }

  private generateFingerprint(deviceInfo: DeviceInfo): string {
    // Create a hash of device characteristics
    const data = `${deviceInfo.os}-${deviceInfo.browser}-${deviceInfo.type}`;
    return createHash('sha256').update(data).digest('hex');
  }

  private async hashRefreshToken(token: string): Promise<string> {
    return createHash('sha256').update(token).digest('hex');
  }

  private async getLocation(ip: string): Promise<Location | undefined> {
    try {
      const response = await fetch(`https://ipapi.co/${ip}/json/`);
      const data = await response.json();
      return {
        country: data.country_name,
        city: data.city,
        timezone: data.timezone,
      };
    } catch {
      return undefined;
    }
  }
}
```

### Active Sessions Management

```typescript
export class SessionManagementService {
  async getActiveSessions(userId: string): Promise<Session[]> {
    return SessionRepository.findActiveByUser(userId);
  }

  async revokeSuspiciousSessions(userId: string): Promise<void> {
    const sessions = await this.getActiveSessions(userId);

    // Find sessions from different countries
    const locations = new Map<string, Session[]>();
    for (const session of sessions) {
      const country = session.location?.country || 'unknown';
      if (!locations.has(country)) {
        locations.set(country, []);
      }
      locations.get(country)!.push(session);
    }

    // If sessions from multiple countries, revoke all but most recent
    if (locations.size > 1) {
      const sortedSessions = sessions.sort(
        (a, b) => b.lastActiveAt.getTime() - a.lastActiveAt.getTime()
      );

      const currentSession = sortedSessions[0];
      const sessionsToRevoke = sortedSessions.slice(1);

      for (const session of sessionsToRevoke) {
        await SessionRepository.revoke(session.id);
      }

      // Notify user
      await notificationService.send(userId, {
        type: 'security',
        title: 'Suspicious activity detected',
        message: `We've detected sign-ins from multiple locations. All other sessions have been revoked.`,
        severity: 'warning',
      });
    }
  }

  async detectSessionAnomalies(userId: string): Promise<Anomaly[]> {
    const sessions = await this.getActiveSessions(userId);
    const anomalies: Anomaly[] = [];

    // Check for impossible travel
    for (let i = 0; i < sessions.length; i++) {
      for (let j = i + 1; j < sessions.length; j++) {
        const s1 = sessions[i];
        const s2 = sessions[j];

        const distance = this.calculateDistance(
          s1.location,
          s2.location
        );

        const timeDiff = Math.abs(
          s1.lastActiveAt.getTime() - s2.lastActiveAt.getTime()
        );

        // If distance > 1000km in < 1 hour, suspicious
        if (distance > 1000 && timeDiff < 3600000) {
          anomalies.push({
            type: 'impossible_travel',
            severity: 'high',
            message: `Sessions from ${s1.location?.city} and ${s2.location?.city} were active within ${timeDiff / 60000} minutes`,
            sessionIds: [s1.id, s2.id],
          });
        }
      }
    }

    return anomalies;
  }
}
```

---

## Password Security

### Password Policy

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASSWORD POLICY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Minimum Length:        8 characters                            │
│  Maximum Length:        128 characters                          │
│  Required:              At least one lowercase                  │
│                         At least one uppercase                  │
│                         At least one number                      │
│                         At least one special character          │
│                                                                  │
│  Blocked:                Common passwords (top 10k)             │
│                          Previously used passwords              │
│                          Passwords containing email/name        │
│                                                                  │
│  Expiry:                 90 days (optional, by agency policy)   │
│  History:                Last 5 passwords not reusable          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Password Hashing

```typescript
import bcrypt from 'bcrypt';
import { PasswordHistory } from './models';

export class PasswordService {
  private readonly SALT_ROUNDS = 12;
  private readonly COMMON_PASSWORDS = new Set([
    'password', '123456', '12345678', 'qwerty', 'abc123',
    // ... top 10k common passwords
  ]);

  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, this.SALT_ROUNDS);
  }

  async verifyPassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  async validatePassword(password: string, user?: User): Promise<ValidationResult> {
    const errors: string[] = [];

    // Length check
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters');
    }
    if (password.length > 128) {
      errors.push('Password must be less than 128 characters');
    }

    // Complexity check
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    if (!/[^a-zA-Z0-9]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }

    // Common password check
    if (this.COMMON_PASSWORDS.has(password.toLowerCase())) {
      errors.push('This password is too common. Please choose a more secure password');
    }

    // User-specific checks
    if (user) {
      // Check if password contains email
      if (password.toLowerCase().includes(user.email.split('@')[0].toLowerCase())) {
        errors.push('Password cannot contain your email address');
      }

      // Check if password contains name
      const nameParts = user.name.toLowerCase().split(' ');
      for (const part of nameParts) {
        if (part.length > 2 && password.toLowerCase().includes(part)) {
          errors.push('Password cannot contain your name');
          break;
        }
      }

      // Check password history
      const history = await PasswordHistory.findRecent(user.id, 5);
      for (const entry of history) {
        if (await this.verifyPassword(password, entry.hash)) {
          errors.push('You cannot reuse your recent passwords');
          break;
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  async setPassword(user: User, newPassword: string): Promise<void> {
    // Validate password
    const validation = await this.validatePassword(newPassword, user);
    if (!validation.valid) {
      throw new ValidationError('INVALID_PASSWORD', validation.errors);
    }

    // Hash new password
    const hash = await this.hashPassword(newPassword);

    // Start transaction
    await database.transaction(async (trx) => {
      // Update user password
      await UserRepository.update(user.id, { passwordHash: hash }, trx);

      // Save to password history
      await PasswordHistory.create({
        userId: user.id,
        hash,
        setAt: new Date(),
      }, trx);

      // Revoke all existing sessions (force re-login)
      await SessionRepository.revokeAllForUser(user.id, undefined, trx);
    });

    // Send password change notification
    await notificationService.send(user.id, {
      type: 'security',
      title: 'Password changed',
      message: 'Your password was successfully changed. If you did not make this change, please contact support immediately.',
      severity: 'info',
    });
  }
}
```

---

## Multi-Factor Authentication

### MFA Methods

```typescript
type MfaMethod = 'totp' | 'sms' | 'email' | 'hardware';

interface MfaSetup {
  userId: string;
  method: MfaMethod;
  secret?: string;        // TOTP secret
  phone?: string;         // SMS number
  email?: string;         // Backup email
  deviceKey?: string;     // Hardware key
  verified: boolean;
  backupCodes?: string[]; // Recovery codes
}

export class MfaService {
  // TOTP Setup
  async setupTotp(user: User): Promise<{ secret: string; qrCode: string }> {
    // Generate secret
    const secret = authenticator.generateSecret();

    // Generate QR code for authenticator app
    const qrCode = await qrcode.toDataURL(
      `otpauth://totp/TravelAgency:${user.email}?secret=${secret}&issuer=TravelAgency`
    );

    // Store unverified
    await MfaRepository.create({
      userId: user.id,
      method: 'totp',
      secret,
      verified: false,
    });

    return { secret, qrCode };
  }

  async verifyTotpSetup(user: User, token: string): Promise<void> {
    const setup = await MfaRepository.findUnverified(user.id, 'totp');
    if (!setup) {
      throw new ValidationError('INVALID_SETUP', 'TOTP setup not found');
    }

    // Verify token
    const isValid = authenticator.verify({
      token,
      secret: setup.secret!,
    });

    if (!isValid) {
      throw new ValidationError('INVALID_TOKEN', 'Invalid verification code');
    }

    // Mark as verified and generate backup codes
    const backupCodes = this.generateBackupCodes();
    await MfaRepository.update(setup.id, {
      verified: true,
      backupCodes,
    });

    // Send backup codes to user
    await notificationService.send(user.id, {
      type: 'security',
      title: 'Two-factor authentication enabled',
      message: 'Save these backup codes in a safe place. You can use them to access your account if you lose your authenticator device.',
      data: { backupCodes },
      severity: 'info',
    });
  }

  // SMS MFA
  async sendSmsCode(user: User, phone: string): Promise<void> {
    const code = this.generateOtpCode();

    // Store code (hashed) with expiry
    await OtpRepository.create({
      userId: user.id,
      type: 'mfa_sms',
      code: await this.hashOtp(code),
      phone,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes
    });

    // Send SMS
    await smsService.send(phone, `Your verification code is: ${code}`);
  }

  // Email MFA
  async sendEmailCode(user: User): Promise<void> {
    const code = this.generateOtpCode();

    await OtpRepository.create({
      userId: user.id,
      type: 'mfa_email',
      code: await this.hashOtp(code),
      expiresAt: new Date(Date.now() + 5 * 60 * 1000),
    });

    await emailService.send({
      to: user.email,
      subject: 'Your verification code',
      template: 'mfa-code',
      data: { code },
    });
  }

  // Verify MFA during login
  async verifyMfa(
    user: User,
    method: MfaMethod,
    code: string
  ): Promise<boolean> {
    switch (method) {
      case 'totp': {
        const setup = await MfaRepository.findVerified(user.id, 'totp');
        if (!setup) return false;

        return authenticator.verify({
          token: code,
          secret: setup.secret!,
        });
      }

      case 'sms':
      case 'email': {
        const otp = await OtpRepository.findValid(user.id, `mfa_${method}`);
        if (!otp) return false;

        const isValid = await bcrypt.compare(code, otp.code);
        if (isValid) {
          await OtpRepository.consume(otp.id);
        }
        return isValid;
      }

      case 'hardware':
        // WebAuthn verification
        return this.verifyHardwareKey(user, code);

      default:
        return false;
    }
  }

  // Verify backup code
  async verifyBackupCode(user: User, code: string): Promise<boolean> {
    const setup = await MfaRepository.findVerified(user.id);
    if (!setup?.backupCodes) return false;

    const codeIndex = setup.backupCodes.indexOf(code);
    if (codeIndex === -1) return false;

    // Remove used backup code
    setup.backupCodes.splice(codeIndex, 1);
    await MfaRepository.update(setup.id, {
      backupCodes: setup.backupCodes,
    });

    return true;
  }

  private generateOtpCode(): string {
    return Math.floor(100000 + Math.random() * 900000).toString();
  }

  private generateBackupCodes(): string[] {
    return Array.from({ length: 10 }, () =>
      Math.random().toString(36).substring(2, 12).toUpperCase()
    );
  }

  private async hashOtp(code: string): Promise<string> {
    return bcrypt.hash(code, 10);
  }

  private async verifyHardwareKey(user: User, credential: string): Promise<boolean> {
    // WebAuthn verification implementation
    const verification = await webAuthn.verifyAuthentication({
      credential,
      expectedChallenge: await WebAuthnChallenge.get(user.id),
      expectedOrigin: process.env.APP_URL,
      expectedRPID: process.env.RP_ID,
      authenticator: await WebAuthnCredential.findByUser(user.id),
    });

    return verification.verified;
  }
}
```

### MFA Login Flow

```typescript
export class AuthService {
  async loginWithMfa(
    email: string,
    password: string,
    mfaCode?: string,
    backupCode?: string
  ): Promise<LoginResult> {
    // Verify credentials
    const user = await UserRepository.findByEmail(email);
    if (!user || !await passwordService.verifyPassword(password, user.passwordHash)) {
      // Prevent timing attacks
      await bcrypt.hash('dummy', 10);
      throw new AuthError('INVALID_CREDENTIALS', 'Invalid email or password');
    }

    // Check if MFA is enabled
    const mfaSetup = await MfaRepository.findVerified(user.id);
    const mfaRequired = !!mfaSetup;

    if (mfaRequired) {
      if (!mfaCode && !backupCode) {
        // MFA required but not provided - return challenge
        return {
          status: 'mfa_required',
          methods: mfaSetup.map((s) => s.method),
          user: { id: user.id, email: user.email },
        };
      }

      // Verify MFA code
      let mfaValid = false;
      let mfaMethod: MfaMethod | undefined;

      if (mfaCode) {
        for (const setup of mfaSetup) {
          if (await mfaService.verifyMfa(user, setup.method, mfaCode)) {
            mfaValid = true;
            mfaMethod = setup.method;
            break;
          }
        }
      } else if (backupCode) {
        mfaValid = await mfaService.verifyBackupCode(user, backupCode);
        mfaMethod = 'backup';
      }

      if (!mfaValid) {
        throw new AuthError('INVALID_MFA', 'Invalid verification code');
      }
    }

    // Create session
    const sessionResult = await sessionService.createSession(
      user,
      this.getDeviceInfo(),
      mfaRequired // MFA verified
    );

    return {
      status: 'success',
      user: this.sanitizeUser(user),
      tokens: sessionResult.tokens,
      session: {
        id: sessionResult.session.id,
        deviceInfo: sessionResult.session.deviceInfo,
      },
    };
  }
}
```

---

## Single Sign-On

### OAuth 2.0 / OpenID Connect

```typescript
export class SsoService {
  // Google SSO
  async getGoogleAuthUrl(state: string): Promise<string> {
    const params = new URLSearchParams({
      client_id: process.env.GOOGLE_CLIENT_ID!,
      redirect_uri: `${process.env.APP_URL}/auth/callback/google`,
      response_type: 'code',
      scope: 'openid email profile',
      state,
    });

    return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }

  async handleGoogleCallback(code: string): Promise<SsoProfile> {
    // Exchange code for tokens
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        redirect_uri: `${process.env.APP_URL}/auth/callback/google`,
        grant_type: 'authorization_code',
      }),
    });

    const tokens = await tokenResponse.json();

    // Get user info
    const userResponse = await fetch(
      'https://www.googleapis.com/oauth2/v2/userinfo',
      {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      }
    );

    const profile = await userResponse.json();

    return {
      provider: 'google',
      providerId: profile.id,
      email: profile.email,
      name: profile.name,
      picture: profile.picture,
      verified: profile.verified_email,
    };
  }

  // Microsoft SSO
  async getMicrosoftAuthUrl(state: string): Promise<string> {
    const params = new URLSearchParams({
      client_id: process.env.MICROSOFT_CLIENT_ID!,
      redirect_uri: `${process.env.APP_URL}/auth/callback/microsoft`,
      response_type: 'code',
      scope: 'openid email profile',
      response_mode: 'query',
      state,
    });

    return `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?${params}`;
  }

  async handleMicrosoftCallback(code: string): Promise<SsoProfile> {
    // Similar to Google callback
    // ...
  }

  // Link or create user from SSO profile
  async handleSsoLogin(profile: SsoProfile, deviceInfo: DeviceInfo): Promise<LoginResult> {
    // Find existing user by SSO identity
    let user = await UserRepository.findBySsoIdentity(profile.provider, profile.providerId);

    if (!user) {
      // Check if email already exists
      user = await UserRepository.findByEmail(profile.email);

      if (user) {
        // Link SSO identity to existing account
        await UserIdentityRepository.create({
          userId: user.id,
          provider: profile.provider,
          providerId: profile.providerId,
        });
      } else {
        // Create new user
        user = await this.createUserFromSso(profile);
      }
    }

    // Create session
    const sessionResult = await sessionService.createSession(user, deviceInfo, true);

    return {
      status: 'success',
      user: this.sanitizeUser(user),
      tokens: sessionResult.tokens,
      isNew: !user.lastLoginAt,
    };
  }

  private async createUserFromSso(profile: SsoProfile): Promise<User> {
    // Create agency for new user (or assign to default)
    const agency = await AgencyRepository.findOrCreateDefault();

    return UserRepository.create({
      email: profile.email,
      name: profile.name,
      avatarUrl: profile.picture,
      agencyId: agency.id,
      role: 'agent',
      emailVerified: profile.verified,
      passwordHash: '', // No password for SSO-only users
      signupSource: `sso_${profile.provider}`,
    });
  }
}
```

---

## Token Lifecycle

### Refresh Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOKEN REFRESH FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client                                    Server               │
│    │                                        │                    │
│    │  1. Access Token Expired              │                    │
│    │  ──────────────────────────────────►  │                    │
│    │                                        │                    │
│    │  2. Refresh Token                     │                    │
│    │  ──────────────────────────────────►  │                    │
│    │                                        │                    │
│    │                            ┌──────────┴──────────┐         │
│    │                            │ Verify Refresh Token│         │
│    │                            │ Check Session Valid │         │
│    │                            │ Rotate Token        │         │
│    │                            └──────────┬──────────┘         │
│    │                                        │                    │
│    │  3. New Access Token                  │                    │
│    │  4. New Refresh Token (rotated)       │                    │
│    │  ◄──────────────────────────────────  │                    │
│    │                                        │                    │
│    │  5. Discard Old Refresh Token         │                    │
│    │                                        │                    │
└─────────────────────────────────────────────────────────────────┘
```

### Token Revocation

```typescript
export class TokenRevocationService {
  // Revoke specific session
  async revokeSession(sessionId: string, userId: string): Promise<void> {
    await SessionRepository.revoke(sessionId, userId);
  }

  // Revoke all sessions for user
  async revokeAllUserSessions(userId: string): Promise<void> {
    await SessionRepository.revokeAllForUser(userId);
    await cache.deletePattern(`user:${userId}:sessions:*`);
  }

  // Revoke all sessions for agency
  async revokeAllAgencySessions(agencyId: string): Promise<void> {
    const sessions = await SessionRepository.findByAgency(agencyId);
    for (const session of sessions) {
      await this.revokeSession(session.id, session.userId);
    }
  }

  // Revoke by device type
  async revokeDeviceSessions(userId: string, deviceType: string): Promise<void> {
    const sessions = await SessionRepository.findActiveByUser(userId);
    for (const session of sessions) {
      if (session.deviceInfo.type === deviceType) {
        await this.revokeSession(session.id, userId);
      }
    }
  }

  // Check token blacklist (for immediate revocation)
  async isTokenRevoked(jti: string): Promise<boolean> {
    const revoked = await cache.get(`revoked:${jti}`);
    return !!revoked;
  }

  // Add token to blacklist
  async addToRevocationList(jti: string, exp: number): Promise<void> {
    const ttl = exp - Math.floor(Date.now() / 1000);
    if (ttl > 0) {
      await cache.set(`revoked:${jti}`, '1', { ttl });
    }
  }
}
```

---

## Account Recovery

### Password Reset Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASSWORD RESET FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User requests reset → Enter email                           │
│     └─ Send reset link with token (15min expiry)                │
│                                                                  │
│  2. User clicks link → Verify token                             │
│     └─ Show new password form                                   │
│                                                                  │
│  3. User submits new password                                   │
│     └─ Validate against password policy                         │
│     └─ Update password hash                                     │
│     └─ Revoke all sessions (force re-login)                     │
│     └─ Send confirmation email                                  │
│                                                                  │
│  4. User can login with new password                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```typescript
export class RecoveryService {
  async initiatePasswordReset(email: string): Promise<void> {
    const user = await UserRepository.findByEmail(email);

    // Always return success to prevent email enumeration
    if (!user) return;

    // Generate reset token
    const token = crypto.randomBytes(32).toString('hex');
    const hashedToken = createHash('sha256').update(token).digest('hex');

    // Store token with expiry
    await PasswordResetRepository.create({
      userId: user.id,
      token: hashedToken,
      expiresAt: new Date(Date.now() + 15 * 60 * 1000), // 15 minutes
    });

    // Send reset email
    const resetUrl = `${process.env.APP_URL}/reset-password?token=${token}`;
    await emailService.send({
      to: user.email,
      subject: 'Reset your password',
      template: 'password-reset',
      data: {
        resetUrl,
        expiresAt: '15 minutes',
      },
    });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    // Find valid reset token
    const hashedToken = createHash('sha256').update(token).digest('hex');
    const resetRequest = await PasswordResetRepository.findValid(hashedToken);

    if (!resetRequest) {
      throw new ValidationError('INVALID_TOKEN', 'Invalid or expired reset link');
    }

    // Get user
    const user = await UserRepository.findById(resetRequest.userId);

    // Validate and set new password
    await passwordService.setPassword(user!, newPassword);

    // Consume reset token
    await PasswordResetRepository.consume(resetRequest.id);
  }

  async initiateAccountRecovery(email: string): Promise<void> {
    const user = await UserRepository.findByEmail(email);
    if (!user) return;

    // Check if user has any MFA methods
    const mfaMethods = await MfaRepository.findVerified(user.id);

    if (mfaMethods.length === 0) {
      // No MFA - use email verification
      return this.initiatePasswordReset(email);
    }

    // Has MFA - initiate account recovery with multiple verification steps
    const recoveryToken = crypto.randomBytes(32).toString('hex');
    const hashedToken = createHash('sha256').update(recoveryToken).digest('hex');

    await AccountRecoveryRepository.create({
      userId: user.id,
      token: hashedToken,
      steps: [
        { type: 'email', completed: false },
        { type: 'mfa', completed: false },
      ],
      expiresAt: new Date(Date.now() + 60 * 60 * 1000), // 1 hour
    });

    // Send email with recovery link
    const recoveryUrl = `${process.env.APP_URL}/account-recovery?token=${recoveryToken}`;
    await emailService.send({
      to: user.email,
      subject: 'Account recovery',
      template: 'account-recovery',
      data: { recoveryUrl },
    });
  }

  async verifyRecoveryStep(
    token: string,
    step: 'email' | 'mfa',
    code: string
  ): Promise<RecoveryStatus> {
    const hashedToken = createHash('sha256').update(token).digest('hex');
    const recovery = await AccountRecoveryRepository.findValid(hashedToken);

    if (!recovery) {
      throw new ValidationError('INVALID_TOKEN', 'Invalid recovery token');
    }

    // Verify based on step type
    if (step === 'email') {
      const otp = await OtpRepository.findValid(recovery.userId, 'recovery_email');
      if (!otp || !(await bcrypt.compare(code, otp.code))) {
        throw new ValidationError('INVALID_CODE', 'Invalid verification code');
      }
    } else if (step === 'mfa') {
      const user = await UserRepository.findById(recovery.userId);
      const valid = await mfaService.verifyBackupCode(user!, code);
      if (!valid) {
        throw new ValidationError('INVALID_CODE', 'Invalid backup code');
      }
    }

    // Mark step as completed
    const stepIndex = recovery.steps.findIndex((s) => s.type === step);
    recovery.steps[stepIndex].completed = true;
    await AccountRecoveryRepository.update(recovery.id, {
      steps: recovery.steps,
    });

    // Check if all steps completed
    const allCompleted = recovery.steps.every((s) => s.completed);

    return {
      completed: allCompleted,
      remainingSteps: recovery.steps.filter((s) => !s.completed).map((s) => s.type),
    };
  }

  async completeAccountRecovery(token: string, newPassword: string): Promise<void> {
    const hashedToken = createHash('sha256').update(token).digest('hex');
    const recovery = await AccountRecoveryRepository.findValid(hashedToken);

    if (!recovery || !recovery.steps.every((s) => s.completed)) {
      throw new ValidationError('RECOVERY_INCOMPLETE', 'Complete all verification steps first');
    }

    const user = await UserRepository.findById(recovery.userId);
    await passwordService.setPassword(user!, newPassword);

    // Consume recovery token
    await AccountRecoveryRepository.consume(recovery.id);
  }
}
```

---

**Last Updated:** 2026-04-25

**Next:** SECURITY_02 — Authorization Deep Dive (RBAC, permissions, policies)
