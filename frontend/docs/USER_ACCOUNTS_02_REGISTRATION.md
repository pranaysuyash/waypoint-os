# User Accounts — Registration

> Signup flows, email verification, social authentication, and onboarding

**Series:** User Accounts | **Document:** 2 of 5 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Registration Flow](#registration-flow)
3. [Email Verification](#email-verification)
4. [Social Authentication](#social-authentication)
5. [Onboarding Experience](#onboarding-experience)
6. [Data Collection Strategy](#data-collection-strategy)
7. [Verification & Compliance](#verification--compliance)
8. [Security Best Practices](#security-best-practices)

---

## Overview

User registration is the critical first touchpoint for customers. The registration process must balance security, friction reduction, and data collection needs.

### Registration Goals

| Goal | Description | Metric |
|------|-------------|--------|
| **Low Friction** | Minimize barriers to entry | <2 min to sign up |
| **High Security** | Prevent fraud and bots | <1% fraudulent accounts |
| **Data Capture** | Collect essential info | 80% complete profile |
| **Verification** | Confirm identity | 90% email verified |
| **Engagement** | Drive immediate action | 50% browse products |

---

## Registration Flow

### Multi-Step Registration

```typescript
// ============================================================================
// REGISTRATION FLOW
// ============================================================================

interface RegistrationStep {
  id: string;
  name: string;
  required: boolean;
  fields: RegistrationField[];
  validation: ValidationRules;
  skipIf?: (context: RegistrationContext) => boolean;
}

interface RegistrationField {
  name: string;
  type: 'text' | 'email' | 'password' | 'select' | 'checkbox' | 'date';
  label: string;
  placeholder?: string;
  options?: SelectOption[];
  validation?: FieldValidation;
  icon?: string;
  helpText?: string;
}

interface RegistrationContext {
  source: 'web' | 'mobile' | 'agent' | 'social';
  referrer?: string;
  campaign?: string;
  prefillData?: Record<string, unknown>;
}

class RegistrationFlow {
  private steps: RegistrationStep[] = [
    {
      id: 'account',
      name: 'Account Details',
      required: true,
      fields: [
        {
          name: 'email',
          type: 'email',
          label: 'Email address',
          placeholder: 'you@example.com',
          validation: {
            required: true,
            pattern: 'email',
          },
          icon: 'email',
        },
        {
          name: 'password',
          type: 'password',
          label: 'Create password',
          placeholder: 'Min 8 characters',
          validation: {
            required: true,
            minLength: 8,
          },
          icon: 'lock',
          helpText: 'Must include uppercase, lowercase, and numbers',
        },
      ],
      validation: {
        emailUnique: true,
        passwordStrength: 'medium',
      },
    },
    {
      id: 'personal',
      name: 'Personal Information',
      required: true,
      fields: [
        {
          name: 'firstName',
          type: 'text',
          label: 'First name',
          placeholder: 'John',
          validation: { required: true, minLength: 2 },
        },
        {
          name: 'lastName',
          type: 'text',
          label: 'Last name',
          placeholder: 'Doe',
          validation: { required: true, minLength: 2 },
        },
        {
          name: 'dateOfBirth',
          type: 'date',
          label: 'Date of birth',
          validation: {
            required: true,
            minAge: 18,
            maxAge: 120,
          },
          helpText: 'You must be 18 or older to book',
        },
        {
          name: 'nationality',
          type: 'select',
          label: 'Nationality',
          options: COUNTRY_OPTIONS,
          validation: { required: true },
        },
      ],
      validation: {
        legalName: true,
      },
    },
    {
      id: 'preferences',
      name: 'Your Preferences',
      required: false,
      fields: [
        {
          name: 'language',
          type: 'select',
          label: 'Preferred language',
          options: LANGUAGE_OPTIONS,
          defaultValue: 'en',
        },
        {
          name: 'currency',
          type: 'select',
          label: 'Preferred currency',
          options: CURRENCY_OPTIONS,
          defaultValue: 'USD',
        },
        {
          name: 'newsletter',
          type: 'checkbox',
          label: 'I want to receive travel deals and inspiration',
          defaultValue: false,
        },
      ],
      validation: {},
      skipIf: (ctx) => ctx.source === 'social',
    },
    {
      id: 'verify',
      name: 'Verify Your Email',
      required: true,
      fields: [],
      validation: {
        emailVerified: true,
      },
    },
  ];

  async processRegistration(
    input: RegistrationInput,
    context: RegistrationContext
  ): Promise<RegistrationResult> {
    // Step 1: Validate all data
    const validation = await this.validateRegistration(input);
    if (!validation.valid) {
      return {
        success: false,
        errors: validation.errors,
      };
    }

    // Step 2: Check for existing accounts
    const existing = await this.checkExistingAccounts(input);
    if (existing) {
      return this.handleExistingAccount(existing, input);
    }

    // Step 3: Create user account
    const user = await this.createUserAccount(input, context);

    // Step 4: Create profile
    const profile = await this.createProfile(user, input);

    // Step 5: Create primary traveler
    const traveler = await this.createPrimaryTraveler(user, input);

    // Step 6: Send verification email
    await this.sendVerificationEmail(user, context);

    // Step 7: Track registration event
    await this.trackRegistration(user, context);

    // Step 8: Return result
    return {
      success: true,
      user: this.sanitizeUser(user),
      profile,
      requiresVerification: true,
      nextStep: 'check_email',
    };
  }

  private async validateRegistration(
    input: RegistrationInput
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];

    // Validate email
    if (!this.isValidEmail(input.email)) {
      errors.push({
        field: 'email',
        message: 'Please enter a valid email address',
      });
    }

    // Validate password
    const passwordValidation = await new PasswordValidator().validate(input.password);
    if (!passwordValidation.valid) {
      errors.push(...passwordValidation.errors.map(e => ({
        field: 'password',
        message: e,
      })));
    }

    // Validate personal info
    if (input.firstName?.length < 2) {
      errors.push({ field: 'firstName', message: 'First name is required' });
    }

    if (input.lastName?.length < 2) {
      errors.push({ field: 'lastName', message: 'Last name is required' });
    }

    if (input.dateOfBirth) {
      const age = this.calculateAge(input.dateOfBirth);
      if (age < 18) {
        errors.push({ field: 'dateOfBirth', message: 'You must be 18 or older' });
      }
    }

    // Validate terms acceptance
    if (!input.acceptTerms) {
      errors.push({
        field: 'acceptTerms',
        message: 'You must accept the terms and conditions',
      });
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  private async checkExistingAccounts(
    input: RegistrationInput
  ): Promise<User | null> {
    // Check by email
    const byEmail = await User.findOne({
      email: input.email.toLowerCase(),
      deletedAt: null,
    });

    if (byEmail) {
      return byEmail;
    }

    // Check by phone if provided
    if (input.phone) {
      const byPhone = await User.findOne({
        phone: input.phone,
        deletedAt: null,
      });

      if (byPhone) {
        return byPhone;
      }
    }

    return null;
  }

  private handleExistingAccount(
    existing: User,
    input: RegistrationInput
  ): RegistrationResult {
    // Account exists - provide helpful message
    if (!existing.emailVerified) {
      // Resend verification email
      this.resendVerificationEmail(existing);
      return {
        success: false,
        requiresVerification: true,
        message: 'An account exists but is not verified. Check your email for verification link.',
      };
    }

    if (existing.status === 'suspended') {
      return {
        success: false,
        message: 'This account has been suspended. Please contact support.',
      };
    }

    return {
      success: false,
      message: 'An account with this email already exists. Please log in.',
      loginSuggested: true,
    };
  }

  private async createUserAccount(
    input: RegistrationInput,
    context: RegistrationContext
  ): Promise<User> {
    const passwordHash = await bcrypt.hash(input.password, 12);

    const user = await User.create({
      email: input.email.toLowerCase(),
      passwordHash,
      authProvider: 'email',
      status: 'pending',
      tier: 'standard',
      emailVerified: false,
      passwordChangedAt: new Date(),
      metadata: {
        source: context.source,
        referrer: context.referrer,
        campaign: context.campaign,
      },
    });

    return user;
  }

  private async createProfile(
    user: User,
    input: RegistrationInput
  ): Promise<UserProfile> {
    const profile = await UserProfile.create({
      userId: user.id,
      firstName: input.firstName,
      lastName: input.lastName,
      displayName: `${input.firstName} ${input.lastName}`,
      email: user.email,
      dateOfBirth: input.dateOfBirth,
      nationality: input.nationality,
      language: input.language || 'en',
      currency: input.currency || 'USD',
      timezone: input.timezone || 'UTC',
      preferences: {
        travel: {},
        communication: {
          emailEnabled: true,
          smsEnabled: false,
          pushEnabled: true,
          marketingEmails: input.newsletter || false,
          promotionalSms: false,
        },
        display: {
          currency: input.currency || 'USD',
          distanceUnit: 'km',
          dateFormat: 'DD/MM/YYYY',
        },
      },
      privacy: {
        profileVisibility: 'private',
        showTravelHistory: false,
        showReviews: false,
        allowTagging: false,
        dataSharing: {
          analytics: true,
          personalization: true,
          thirdParty: false,
        },
      },
      marketing: {
        newsletter: input.newsletter || false,
        offers: false,
        newDestinations: false,
        travelTips: false,
        partnerOffers: false,
      },
    });

    return profile;
  }

  private async createPrimaryTraveler(
    user: User,
    input: RegistrationInput
  ): Promise<TravelerProfile> {
    const traveler = await TravelerProfile.create({
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

    await UserTraveler.create({
      userId: user.id,
      travelerId: traveler.id,
      isPrimary: true,
    });

    return traveler;
  }

  private async sendVerificationEmail(
    user: User,
    context: RegistrationContext
  ): Promise<void> {
    const token = crypto.randomBytes(32).toString('hex');
    const tokenHash = createHash('sha256').update(token).digest('hex');

    await EmailVerification.create({
      userId: user.id,
      email: user.email,
      tokenHash,
      expiresAt: addHours(new Date(), 24),
    });

    // Send email
    await EmailService.send({
      to: user.email,
      subject: 'Verify your email address',
      template: 'email-verification',
      data: {
        firstName: user.profile?.firstName || 'there',
        verificationUrl: `${process.env.APP_URL}/verify?token=${token}`,
        expiresIn: 24,
      },
    });
  }

  private async trackRegistration(
    user: User,
    context: RegistrationContext
  ): Promise<void> {
    await Analytics.track('user_registered', {
      userId: user.id,
      source: context.source,
      referrer: context.referrer,
      campaign: context.campaign,
      timestamp: new Date(),
    });

    // Sync to marketing platforms
    if (context.source !== 'agent') {
      await this.syncToMarketingPlatforms(user);
    }
  }

  private isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  private calculateAge(dateOfBirth: Date): number {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    return age;
  }

  private sanitizeUser(user: User): Partial<User> {
    const { passwordHash, ...sanitized } = user;
    return sanitized;
  }
}

interface RegistrationInput {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  title?: string;
  dateOfBirth?: Date;
  nationality?: string;
  phone?: string;
  language?: string;
  currency?: string;
  timezone?: string;
  newsletter?: boolean;
  acceptTerms: boolean;
  acceptMarketing?: boolean;
}

interface RegistrationResult {
  success: boolean;
  user?: Partial<User>;
  profile?: UserProfile;
  requiresVerification?: boolean;
  nextStep?: string;
  errors?: ValidationError[];
  message?: string;
  loginSuggested?: boolean;
}
```

---

## Email Verification

### Verification Flow

```typescript
// ============================================================================
// EMAIL VERIFICATION
// ============================================================================

class EmailVerificationService {
  async verifyEmail(token: string): Promise<VerificationResult> {
    // Find verification record
    const tokenHash = createHash('sha256').update(token).digest('hex');
    const verification = await EmailVerification.findOne({
      tokenHash,
      verified: false,
    });

    if (!verification) {
      return {
        success: false,
        error: 'invalid_token',
        message: 'This verification link is invalid or has expired.',
      };
    }

    // Check expiry
    if (verification.expiresAt < new Date()) {
      return {
        success: false,
        error: 'expired',
        message: 'This verification link has expired. Please request a new one.',
      };
    }

    // Get user
    const user = await User.findById(verification.userId);

    if (!user || user.deletedAt) {
      return {
        success: false,
        error: 'user_not_found',
        message: 'User account not found.',
      };
    }

    // Mark as verified
    verification.verified = true;
    verification.verifiedAt = new Date();
    await verification.save();

    // Update user
    user.emailVerified = true;
    user.status = 'active'; // Activate account
    await user.save();

    // Send welcome email
    await this.sendWelcomeEmail(user);

    // Track event
    await Analytics.track('email_verified', {
      userId: user.id,
      timestamp: new Date(),
    });

    return {
      success: true,
      user: this.sanitizeUser(user),
    };
  }

  async resendVerification(email: string): Promise<void> {
    const user = await User.findOne({
      email: email.toLowerCase(),
      deletedAt: null,
    });

    if (!user) {
      // Don't reveal if email exists
      return;
    }

    if (user.emailVerified) {
      return;
    }

    // Delete old verification tokens
    await EmailVerification.deleteMany({
      userId: user.id,
      verified: false,
    });

    // Create new token
    const token = crypto.randomBytes(32).toString('hex');
    const tokenHash = createHash('sha256').update(token).digest('hex');

    await EmailVerification.create({
      userId: user.id,
      email: user.email,
      tokenHash,
      expiresAt: addHours(new Date(), 24),
    });

    // Send email
    await EmailService.send({
      to: user.email,
      subject: 'Verify your email address',
      template: 'email-verification',
      data: {
        firstName: user.profile?.firstName || 'there',
        verificationUrl: `${process.env.APP_URL}/verify?token=${token}`,
        expiresIn: 24,
      },
    });

    // Rate limit check
    await this.checkRateLimit(user.id);
  }

  private async sendWelcomeEmail(user: User): Promise<void> {
    await EmailService.send({
      to: user.email,
      subject: 'Welcome to our travel platform!',
      template: 'welcome-email',
      data: {
        firstName: user.profile?.firstName,
        loginUrl: `${process.env.APP_URL}/login`,
        browseUrl: `${process.env.APP_URL}/destinations`,
      },
    });
  }

  private async checkRateLimit(userId: string): Promise<void> {
    // Limit resend to once per hour
    const hourAgo = subHours(new Date(), 1);
    const recentSends = await EmailVerification.countDocuments({
      userId,
      createdAt: { $gte: hourAgo },
    });

    if (recentSends >= 3) {
      throw new RateLimitError('Too many verification emails sent. Please try again later.');
    }
  }

  private sanitizeUser(user: User): Partial<User> {
    const { passwordHash, ...sanitized } = user;
    return sanitized;
  }
}

interface VerificationResult {
  success: boolean;
  user?: Partial<User>;
  error?: string;
  message?: string;
}
```

---

## Social Authentication

### OAuth Integration

```typescript
// ============================================================================
// SOCIAL AUTHENTICATION
// ============================================================================

interface SocialAuthProvider {
  name: 'google' | 'apple' | 'facebook';
  scopes: string[];
  authorizationUrl: string;
  tokenUrl: string;
  userInfoUrl: string;
}

class SocialAuthService {
  private providers: Record<string, SocialAuthProvider> = {
    google: {
      name: 'google',
      scopes: ['openid', 'email', 'profile'],
      authorizationUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
      tokenUrl: 'https://oauth2.googleapis.com/token',
      userInfoUrl: 'https://www.googleapis.com/oauth2/v2/userinfo',
    },
    apple: {
      name: 'apple',
      scopes: ['email', 'name'],
      authorizationUrl: 'https://appleid.apple.com/auth/authorize',
      tokenUrl: 'https://appleid.apple.com/auth/token',
      userInfoUrl: '', // Apple provides user info in initial response
    },
    facebook: {
      name: 'facebook',
      scopes: ['email', 'public_profile'],
      authorizationUrl: 'https://www.facebook.com/v18.0/dialog/oauth',
      tokenUrl: 'https://graph.facebook.com/v18.0/oauth/access_token',
      userInfoUrl: 'https://graph.facebook.com/v18.0/me',
    },
  };

  async getAuthorizationUrl(
    provider: string,
    redirectUri: string,
    state: string
  ): Promise<string> {
    const config = this.providers[provider];

    if (!config) {
      throw new UnsupportedProviderError(provider);
    }

    const params = new URLSearchParams({
      client_id: process.env[`${provider.toUpperCase()}_CLIENT_ID`]!,
      redirect_uri: redirectUri,
      scope: config.scopes.join(' '),
      response_type: 'code',
      state,
    });

    if (provider === 'apple') {
      params.append('response_mode', 'form_post');
    }

    return `${config.authorizationUrl}?${params.toString()}`;
  }

  async authenticate(
    provider: string,
    code: string,
    redirectUri: string
  ): Promise<SocialAuthResult> {
    const config = this.providers[provider];

    if (!config) {
      throw new UnsupportedProviderError(provider);
    }

    // Exchange code for access token
    const tokenResponse = await this.exchangeCodeForToken(
      provider,
      code,
      redirectUri
    );

    // Get user info
    const userInfo = await this.getUserInfo(
      provider,
      tokenResponse.access_token
    );

    // Check if user exists
    let user = await User.findOne({
      authProvider: provider,
      authProviderId: userInfo.id,
      deletedAt: null,
    });

    if (!user) {
      // Check if email matches existing user
      user = await User.findOne({
        email: userInfo.email,
        deletedAt: null,
      });

      if (user) {
        // Link social account to existing user
        user.authProvider = provider;
        user.authProviderId = userInfo.id;
        await user.save();
      } else {
        // Create new user
        user = await this.createSocialUser(provider, userInfo);
      }
    }

    // Generate session tokens
    const session = await this.createSession(user);
    const tokens = await this.generateTokens(user, session);

    // Track login
    await Analytics.track('social_login', {
      userId: user.id,
      provider,
      timestamp: new Date(),
    });

    return {
      success: true,
      user: this.sanitizeUser(user),
      ...tokens,
      isNewUser: !user.lastLoginAt,
    };
  }

  private async exchangeCodeForToken(
    provider: string,
    code: string,
    redirectUri: string
  ): Promise<TokenResponse> {
    const config = this.providers[provider];

    const response = await fetch(config.tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: process.env[`${provider.toUpperCase()}_CLIENT_ID`]!,
        client_secret: process.env[`${provider.toUpperCase()}_CLIENT_SECRET`]!,
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
      }),
    });

    if (!response.ok) {
      throw new TokenExchangeError(provider);
    }

    return await response.json();
  }

  private async getUserInfo(
    provider: string,
    accessToken: string
  ): Promise<SocialUserInfo> {
    const config = this.providers[provider];

    if (provider === 'apple') {
      // Apple provides info in JWT id_token
      const decoded = jwt.decode(accessToken) as AppleJWT;
      return {
        id: decoded.sub,
        email: decoded.email,
        firstName: decoded.given_name,
        lastName: decoded.family_name,
      };
    }

    const response = await fetch(
      `${config.userInfoUrl}?access_token=${accessToken}`
    );

    if (!response.ok) {
      throw new UserInfoError(provider);
    }

    const data = await response.json();

    if (provider === 'google') {
      return {
        id: data.id,
        email: data.email,
        firstName: data.given_name,
        lastName: data.family_name,
        picture: data.picture,
      };
    }

    if (provider === 'facebook') {
      return {
        id: data.id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name,
        picture: data.picture?.data?.url,
      };
    }

    throw new UnsupportedProviderError(provider);
  }

  private async createSocialUser(
    provider: string,
    userInfo: SocialUserInfo
  ): Promise<User> {
    const user = await User.create({
      email: userInfo.email,
      authProvider: provider,
      authProviderId: userInfo.id,
      status: 'active',
      tier: 'standard',
      emailVerified: true, // Social accounts come pre-verified
      passwordChangedAt: new Date(),
    });

    // Create profile
    await UserProfile.create({
      userId: user.id,
      firstName: userInfo.firstName || '',
      lastName: userInfo.lastName || '',
      displayName: `${userInfo.firstName || ''} ${userInfo.lastName || ''}`.trim() || userInfo.email.split('@')[0],
      email: userInfo.email,
      avatar: userInfo.picture,
      language: 'en',
      currency: 'USD',
      timezone: 'UTC',
      preferences: this.getDefaultPreferences(),
      privacy: this.getDefaultPrivacy(),
      marketing: this.getDefaultMarketing(),
      metadata: {
        source: 'social',
        provider,
      },
    });

    // Create primary traveler
    await this.createPrimaryTraveler(user, userInfo);

    return user;
  }

  private async createSession(user: User): Promise<UserSession> {
    return await UserSession.create({
      userId: user.id,
      accessToken: '',
      refreshToken: '',
      accessTokenExpiresAt: new Date(),
      refreshTokenExpiresAt: new Date(),
      device: { type: 'desktop', os: 'unknown' },
      location: {},
      ipAddress: '',
      userAgent: '',
      active: true,
      lastActivityAt: new Date(),
    });
  }

  private async generateTokens(
    user: User,
    session: UserSession
  ): Promise<{ accessToken: string; refreshToken: string }> {
    const tokenService = new TokenService();
    return {
      accessToken: tokenService.generateAccessToken(user, session),
      refreshToken: tokenService.generateRefreshToken(user, session),
    };
  }

  private sanitizeUser(user: User): Partial<User> {
    const { passwordHash, ...sanitized } = user;
    return sanitized;
  }
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  id_token?: string;
}

interface SocialUserInfo {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  picture?: string;
}

interface AppleJWT {
  sub: string;
  email: string;
  email_verified: string;
  given_name?: string;
  family_name?: string;
}

interface SocialAuthResult {
  success: boolean;
  user?: Partial<User>;
  accessToken?: string;
  refreshToken?: string;
  isNewUser?: boolean;
  error?: string;
}
```

---

## Onboarding Experience

### Progressive Onboarding

```typescript
// ============================================================================
// ONBOARDING FLOW
// ============================================================================

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  type: 'preference' | 'profile' | 'education' | 'action';
  required: boolean;
  skippable: boolean;
  component: string;
  estimatedTime: number; // seconds
}

class OnboardingFlow {
  private steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to Travel Platform',
      description: 'Let\'s get you set up for amazing travel experiences',
      type: 'education',
      required: true,
      skippable: false,
      component: 'WelcomeStep',
      estimatedTime: 30,
    },
    {
      id: 'interests',
      title: 'What interests you?',
      description: 'Tell us about your travel preferences',
      type: 'preference',
      required: false,
      skippable: true,
      component: 'InterestsStep',
      estimatedTime: 60,
    },
    {
      id: 'travelers',
      title: 'Who do you travel with?',
      description: 'Add frequent travel companions',
      type: 'profile',
      required: false,
      skippable: true,
      component: 'TravelersStep',
      estimatedTime: 90,
    },
    {
      id: 'search',
      title: 'Try a search',
      description: 'Explore our destinations and experiences',
      type: 'action',
      required: false,
      skippable: true,
      component: 'SearchStep',
      estimatedTime: 120,
    },
  ];

  async getOnboardingState(userId: string): Promise<OnboardingState> {
    const user = await User.findById(userId);
    const profile = await UserProfile.findByUserId(userId);

    return {
      completed: user.onboardingCompleted || false,
      currentStep: user.onboardingCurrentStep || 'welcome',
      completedSteps: user.onboardingCompletedSteps || [],
      skippedSteps: user.onboardingSkippedSteps || [],
      totalSteps: this.steps.length,
    };
  }

  async completeStep(
    userId: string,
    stepId: string,
    data: Record<string, unknown>
  ): Promise<void> {
    const user = await User.findById(userId);
    const stepIndex = this.steps.findIndex(s => s.id === stepId);

    if (stepIndex === -1) {
      throw new InvalidStepError(stepId);
    }

    // Save step data
    await OnboardingData.create({
      userId,
      stepId,
      data,
    });

    // Update user progress
    const completedSteps = user.onboardingCompletedSteps || [];
    completedSteps.push(stepId);

    user.onboardingCompletedSteps = completedSteps;

    // Move to next step
    if (stepIndex < this.steps.length - 1) {
      user.onboardingCurrentStep = this.steps[stepIndex + 1].id;
    } else {
      // Onboarding complete
      user.onboardingCompleted = true;
      user.onboardingCompletedAt = new Date();
      await this.handleOnboardingComplete(user);
    }

    await user.save();
  }

  async skipStep(userId: string, stepId: string): Promise<void> {
    const user = await User.findById(userId);
    const step = this.steps.find(s => s.id === stepId);

    if (!step || !step.skippable) {
      throw new StepNotSkippableError(stepId);
    }

    // Mark as skipped
    const skippedSteps = user.onboardingSkippedSteps || [];
    skippedSteps.push(stepId);
    user.onboardingSkippedSteps = skippedSteps;

    // Move to next step
    const stepIndex = this.steps.findIndex(s => s.id === stepId);
    if (stepIndex < this.steps.length - 1) {
      user.onboardingCurrentStep = this.steps[stepIndex + 1].id;
    } else {
      user.onboardingCompleted = true;
      user.onboardingCompletedAt = new Date();
      await this.handleOnboardingComplete(user);
    }

    await user.save();
  }

  private async handleOnboardingComplete(user: User): Promise<void> {
    // Update tier based on profile completeness
    const profile = await UserProfile.findByUserId(user.id);
    const completeness = this.calculateProfileCompleteness(profile);

    if (completeness >= 80) {
      user.tier = 'silver'; // Bonus tier for complete profiles
      await user.save();

      await this.sendTierUpgradeEmail(user, 'silver');
    }

    // Send onboarding completion email
    await this.sendOnboardingCompleteEmail(user);

    // Track event
    await Analytics.track('onboarding_completed', {
      userId: user.id,
      completedSteps: user.onboardingCompletedSteps.length,
      skippedSteps: user.onboardingSkippedSteps.length,
    });
  }

  private calculateProfileCompleteness(profile: UserProfile): number {
    let score = 0;
    const maxScore = 100;

    // Basic info (40 points)
    if (profile.firstName) score += 10;
    if (profile.lastName) score += 10;
    if (profile.dateOfBirth) score += 10;
    if (profile.nationality) score += 10;

    // Contact (20 points)
    if (profile.email) score += 10;
    if (profile.phone) score += 10;

    // Preferences (20 points)
    if (profile.preferences.travel.seatPreference) score += 5;
    if (profile.preferences.travel.mealPreference) score += 5;
    if (profile.preferences.communication.emailEnabled !== undefined) score += 5;
    if (profile.preferences.display.currency) score += 5;

    // Travelers (20 points)
    // Checked separately via traveler count

    return score;
  }

  private async sendTierUpgradeEmail(user: User, tier: CustomerTier): Promise<void> {
    await EmailService.send({
      to: user.email,
      subject: `Congratulations! You've been upgraded to ${tier} tier`,
      template: 'tier-upgrade',
      data: {
        firstName: user.profile?.firstName,
        tier,
        benefits: this.getTierBenefits(tier),
      },
    });
  }

  private async sendOnboardingCompleteEmail(user: User): Promise<void> {
    await EmailService.send({
      to: user.email,
      subject: 'You\'re all set up! 🎉',
      template: 'onboarding-complete',
      data: {
        firstName: user.profile?.firstName,
        exploreUrl: `${process.env.APP_URL}/destinations`,
      },
    });
  }

  private getTierBenefits(tier: CustomerTier): string[] {
    const benefits = {
      silver: [
        'Priority customer support',
        'Exclusive deals and offers',
        'Early access to new features',
      ],
    };

    return benefits[tier] || [];
  }
}

interface OnboardingState {
  completed: boolean;
  currentStep: string;
  completedSteps: string[];
  skippedSteps: string[];
  totalSteps: number;
}
```

---

## Data Collection Strategy

### Progressive Profiling

```typescript
// ============================================================================
// PROGRESSIVE PROFILING
// ============================================================================

class DataCollectionStrategy {
  // Core data collected at registration
  private coreFields = [
    'email',
    'password',
    'firstName',
    'lastName',
    'acceptTerms',
  ];

  // Extended data collected during onboarding
  private onboardingFields = [
    'dateOfBirth',
    'nationality',
    'phone',
    'interests',
    'travelCompanions',
  ];

  // Enhanced data collected over time
  private enhancedFields = [
    'passportDetails',
    'travelHistory',
    'preferences',
    'loyaltyPrograms',
  ];

  // Determine what to ask for based on context
  getRequiredFields(context: BookingContext): string[] {
    const fields = [...this.coreFields];

    // Add phone if booking flights (required for airlines)
    if (context.hasFlights) {
      fields.push('phone');
    }

    // Add passport if international travel
    if (context.isInternational) {
      fields.push('passportDetails');
    }

    // Add date of birth if not provided
    if (context.needsAgeVerification) {
      fields.push('dateOfBirth');
    }

    return fields;
  }

  // Prompt for missing data at optimal time
  getDataPrompts(user: User): DataPrompt[] {
    const prompts: DataPrompt[] = [];
    const profile = user.profile;

    // Phone number prompt
    if (!profile.phone) {
      prompts.push({
        field: 'phone',
        message: 'Add your phone number for booking confirmations and updates',
        priority: 'high',
        trigger: 'before_booking',
      });
    }

    // Passport prompt
    if (!profile.hasValidPassport && this.hasUpcomingInternationalTrip(user)) {
      prompts.push({
        field: 'passportDetails',
        message: 'Add your passport details for smoother check-ins',
        priority: 'high',
        trigger: 'before_international_flight',
      });
    }

    // Preferences prompt
    if (!profile.preferences.travel.seatPreference) {
      prompts.push({
        field: 'seatPreference',
        message: 'Set your seat preference for better flight experiences',
        priority: 'medium',
        trigger: 'after_first_booking',
      });
    }

    return prompts;
  }

  private hasUpcomingInternationalTrip(user: User): boolean {
    // Check user's upcoming bookings
    return false;
  }
}

interface BookingContext {
  hasFlights: boolean;
  isInternational: boolean;
  needsAgeVerification: boolean;
}

interface DataPrompt {
  field: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
  trigger: string;
}
```

---

## Verification & Compliance

### KYC Requirements

```typescript
// ============================================================================
// VERIFICATION REQUIREMENTS
// ============================================================================

interface VerificationRequirement {
  type: 'email' | 'phone' | 'identity' | 'address' | 'passport';
  requiredFor: string[];
  verificationMethod: 'automated' | 'manual' | 'third_party';
  expiry?: number; // days
}

class ComplianceService {
  private requirements: VerificationRequirement[] = [
    {
      type: 'email',
      requiredFor: ['all'],
      verificationMethod: 'automated',
    },
    {
      type: 'phone',
      requiredFor: ['flights', 'high_value'],
      verificationMethod: 'automated',
    },
    {
      type: 'passport',
      requiredFor: ['international_flights'],
      verificationMethod: 'manual',
      expiry: 365, // Re-verify annually
    },
    {
      type: 'identity',
      requiredFor: ['high_value', 'suspicious_activity'],
      verificationMethod: 'third_party',
    },
  ];

  async checkVerificationRequirements(
    userId: string,
    bookingType: string
  ): Promise<VerificationCheckResult> {
    const user = await User.findById(userId);
    const profile = await UserProfile.findByUserId(userId);

    const required: string[] = [];
    const verified: string[] = [];

    if (user.emailVerified) {
      verified.push('email');
    } else {
      required.push('email');
    }

    if (this.requiresPhone(bookingType)) {
      if (profile.phoneVerified) {
        verified.push('phone');
      } else {
        required.push('phone');
      }
    }

    if (this.requiresPassport(bookingType)) {
      const hasValidPassport = await this.hasValidPassport(userId);
      if (hasValidPassport) {
        verified.push('passport');
      } else {
        required.push('passport');
      }
    }

    return {
      allVerified: required.length === 0,
      required,
      verified,
    };
  }

  private requiresPhone(bookingType: string): boolean {
    return ['flights', 'high_value'].includes(bookingType);
  }

  private requiresPassport(bookingType: string): boolean {
    return bookingType === 'international_flights';
  }

  private async hasValidPassport(userId: string): Promise<boolean> {
    const travelers = await TravelerProfile.find({
      userId,
      type: 'primary',
    });

    for (const traveler of travelers) {
      for (const doc of traveler.documents) {
        if (doc.type === 'passport' && doc.verified) {
          if (!doc.expiryDate || doc.expiryDate > new Date()) {
            return true;
          }
        }
      }
    }

    return false;
  }
}

interface VerificationCheckResult {
  allVerified: boolean;
  required: string[];
  verified: string[];
}
```

---

## Security Best Practices

### Registration Security

```typescript
// ============================================================================
// SECURITY MEASURES
// ============================================================================

class RegistrationSecurity {
  // Rate limiting
  private rateLimits = {
    registration: { max: 3, window: 3600000 }, // 3 per hour per IP
    verification: { max: 5, window: 3600000 },  // 5 per hour per email
    login: { max: 10, window: 3600000 },       // 10 per hour per IP
  };

  async checkRateLimit(
    type: keyof typeof this.rateLimits,
    identifier: string
  ): Promise<boolean> {
    const limit = this.rateLimits[type];

    const key = `ratelimit:${type}:${identifier}`;
    const count = await Redis.incr(key);

    if (count === 1) {
      await Redis.expire(key, limit.window / 1000);
    }

    return count <= limit.max;
  }

  // Bot detection
  async detectBot(request: RegistrationRequest): Promise<number> {
    let score = 0;

    // Check timing (too fast = bot)
    if (request.timestamp < Date.now() - 2000) {
      score += 30;
    }

    // Check for bot signatures in user agent
    if (this.isBotUserAgent(request.userAgent)) {
      score += 50;
    }

    // Check email domain
    if (this.isSuspiciousEmail(request.email)) {
      score += 20;
    }

    // Check IP reputation
    if (await this.isSuspiciousIP(request.ipAddress)) {
      score += 40;
    }

    return score;
  }

  // CAPTCHA integration
  async verifyCaptcha(token: string): Promise<boolean> {
    const response = await fetch(
      `https://www.google.com/recaptcha/api/siteverify`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          secret: process.env.RECAPTCHA_SECRET_KEY!,
          response: token,
        }),
      }
    );

    const data = await response.json();
    return data.success && data.score > 0.5;
  }

  // Email verification link security
  generateVerificationToken(): string {
    // Use cryptographically secure random token
    return crypto.randomBytes(32).toString('hex');
  }

  async hashVerificationToken(token: string): Promise<string> {
    return createHash('sha256').update(token).digest('hex');
  }

  private isBotUserAgent(userAgent: string): boolean {
    const botPatterns = [
      /bot/i,
      /crawler/i,
      /spider/i,
      /scraper/i,
      /curl/i,
      /wget/i,
    ];

    return botPatterns.some(pattern => pattern.test(userAgent));
  }

  private isSuspiciousEmail(email: string): boolean {
    // Check for disposable email domains
    const disposableDomains = [
      'tempmail.com',
      'guerrillamail.com',
      'mailinator.com',
    ];

    const domain = email.split('@')[1]?.toLowerCase();
    return disposableDomains.includes(domain);
  }

  private async isSuspiciousIP(ip: string): Promise<boolean> {
    // Check against IP blacklist
    // For now, just check if it's a known VPN/Tor exit node
    return false;
  }
}
```

---

**Next:** [Authentication](./USER_ACCOUNTS_03_AUTHENTICATION.md) — Login, sessions, MFA, and SSO
