# User Accounts 04: User Profiles

> Profile management, preferences, settings, and privacy controls

---

## Overview

This document details the user profile subsystem, covering profile CRUD operations, preference management, communication settings, privacy controls, and account deletion. User profiles store extended information beyond authentication credentials and support progressive data collection.

**Key Capabilities:**
- Comprehensive profile management
- Granular preference settings
- Communication channel controls
- Privacy and data export (GDPR)
- Account deletion and anonymization

---

## Table of Contents

1. [Profile Data Model](#profile-data-model)
2. [Profile Management](#profile-management)
3. [Preferences System](#preferences-system)
4. [Communication Settings](#communication-settings)
5. [Privacy Controls](#privacy-controls)
6. [Account Deletion](#account-deletion)
7. [Profile Validation](#profile-validation)

---

## Profile Data Model

### Core Entities

The user profile is split into multiple entities for optimal data organization and privacy compliance.

```typescript
interface User {
  id: string;
  email: string;
  authProvider: 'email' | 'google' | 'apple' | 'facebook' | 'sso';
  status: UserStatus;
  tier: CustomerTier;
  emailVerified: boolean;
  phoneVerified: boolean;
  mfaEnabled: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface UserProfile {
  id: string;
  userId: string;
  firstName: string;
  lastName: string;
  middleName?: string;
  displayName?: string;
  dateOfBirth?: Date;
  gender?: 'male' | 'female' | 'non-binary' | 'prefer_not_to_say';
  nationality?: string;
  language: string;
  currency: string;
  timezone: string;
  avatarUrl?: string;
  bio?: string;
  interests?: string[];
  createdAt: Date;
  updatedAt: Date;
}

interface UserAddress {
  id: string;
  userId: string;
  type: 'home' | 'work' | 'billing' | 'shipping';
  isPrimary: boolean;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  stateProvince: string;
  postalCode: string;
  countryCode: string;
  createdAt: Date;
  updatedAt: Date;
}

interface UserPreferences {
  id: string;
  userId: string;
  travelStyle: TravelStyle;
  accommodationType: AccommodationType[];
  mealPreference: MealPreference;
  seatPreference: SeatPreference;
  budgetRange: BudgetRange;
  tripInterests: string[];
  accessibilityNeeds?: string[];
  createdAt: Date;
  updatedAt: Date;
}

interface CommunicationSettings {
  id: string;
  userId: string;
  marketingEmails: boolean;
  transactionalEmails: boolean;
  marketingSms: boolean;
  transactionalSms: boolean;
  pushNotifications: boolean;
  WhatsAppUpdates: boolean;
  phoneCalls: boolean;
  preferredChannel: 'email' | 'sms' | 'push' | 'whatsapp';
  quietHoursStart?: string; // HH:MM format
  quietHoursEnd?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface PrivacySettings {
  id: string;
  userId: string;
  profileVisibility: 'public' | 'registered_only' | 'private';
  showTravelHistory: boolean;
  showUpcomingTrips: boolean;
  allowDataSharing: boolean;
  allowAnalytics: boolean;
  allowPersonalization: boolean;
  dataRetention: 'forever' | '2_years' | '5_years';
}

type UserStatus = 'pending' | 'active' | 'suspended' | 'banned' | 'locked';
type CustomerTier = 'standard' | 'silver' | 'gold' | 'platinum';

type TravelStyle = 'adventure' | 'leisure' | 'business' | 'cultural' | 'luxury';
type AccommodationType = 'hotel' | 'resort' | 'villa' | 'hostel' | 'apartment' | 'boutique';
type MealPreference = 'any' | 'vegetarian' | 'vegan' | 'halal' | 'kosher' | 'gluten_free';
type SeatPreference = 'any' | 'window' | 'aisle' | 'extra_legroom';

interface BudgetRange {
  min: number;
  max: number;
  currency: string;
}
```

### Database Schema

```sql
-- User Profiles
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100),
  display_name VARCHAR(100),
  date_of_birth DATE,
  gender VARCHAR(20),
  nationality CHAR(2),
  language VARCHAR(10) NOT NULL DEFAULT 'en',
  currency VARCHAR(3) NOT NULL DEFAULT 'USD',
  timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
  avatar_url TEXT,
  bio TEXT,
  interests TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (user_id),
  INDEX idx_user_profiles_full_name (first_name, last_name)
);

-- User Addresses
CREATE TABLE user_addresses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL,
  is_primary BOOLEAN DEFAULT false,
  address_line1 VARCHAR(255) NOT NULL,
  address_line2 VARCHAR(255),
  city VARCHAR(100) NOT NULL,
  state_province VARCHAR(100),
  postal_code VARCHAR(20) NOT NULL,
  country_code CHAR(2) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_user_addresses_user_id (user_id),
  INDEX idx_user_addresses_type (type)
);

-- User Preferences
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  travel_style VARCHAR(20),
  accommodation_types TEXT[],
  meal_preference VARCHAR(20) DEFAULT 'any',
  seat_preference VARCHAR(20) DEFAULT 'any',
  budget_min DECIMAL(10, 2),
  budget_max DECIMAL(10, 2),
  budget_currency VARCHAR(3) DEFAULT 'USD',
  trip_interests TEXT[],
  accessibility_needs TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (user_id)
);

-- Communication Settings
CREATE TABLE communication_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  marketing_emails BOOLEAN DEFAULT true,
  transactional_emails BOOLEAN DEFAULT true,
  marketing_sms BOOLEAN DEFAULT false,
  transactional_sms BOOLEAN DEFAULT true,
  push_notifications BOOLEAN DEFAULT true,
  whatsapp_updates BOOLEAN DEFAULT false,
  phone_calls BOOLEAN DEFAULT false,
  preferred_channel VARCHAR(20) DEFAULT 'email',
  quiet_hours_start TIME,
  quiet_hours_end TIME,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (user_id)
);

-- Privacy Settings
CREATE TABLE privacy_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_visibility VARCHAR(20) DEFAULT 'private',
  show_travel_history BOOLEAN DEFAULT false,
  show_upcoming_trips BOOLEAN DEFAULT false,
  allow_data_sharing BOOLEAN DEFAULT false,
  allow_analytics BOOLEAN DEFAULT true,
  allow_personalization BOOLEAN DEFAULT true,
  data_retention VARCHAR(20) DEFAULT 'forever',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (user_id)
);

-- Profile Change History (audit log)
CREATE TABLE profile_change_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  table_name VARCHAR(50) NOT NULL,
  field_name VARCHAR(50) NOT NULL,
  old_value TEXT,
  new_value TEXT,
  changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  changed_by UUID, -- NULL for self-changes, set for admin changes

  INDEX idx_profile_history_user_id (user_id),
  INDEX idx_profile_history_changed_at (changed_at)
);
```

---

## Profile Management

### Profile CRUD Operations

```typescript
export class UserProfileService {
  async getProfile(userId: string): Promise<UserProfile> {
    const profile = await this.profileRepository.findByUserId(userId);

    if (!profile) {
      // Auto-create profile if missing
      return await this.createDefaultProfile(userId);
    }

    return profile;
  }

  async updateProfile(
    userId: string,
    updates: Partial<UserProfile>,
    options: UpdateOptions = {}
  ): Promise<UserProfile> {
    const existing = await this.getProfile(userId);

    // Validate changes
    await this.validateProfileUpdates(userId, updates);

    // Track changes for audit
    const changes = this.detectChanges(existing, updates);
    if (changes.length > 0 && options.audit !== false) {
      await this.recordProfileChanges(userId, 'user_profiles', changes);
    }

    // Apply updates
    const updated = await this.profileRepository.update(userId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Invalidate cache
    await this.cacheService.delete(`profile:${userId}`);

    return updated;
  }

  async uploadAvatar(
    userId: string,
    file: FileUpload
  ): Promise<string> {
    // Validate file
    this.validateAvatarFile(file);

    // Upload to storage
    const key = `avatars/${userId}/${crypto.randomUUID()}`;
    const url = await this.storageService.upload(key, file.buffer, {
      contentType: file.mimetype,
      resize: { width: 400, height: 400, fit: 'cover' },
    });

    // Update profile
    await this.updateProfile(userId, { avatarUrl: url });

    return url;
  }

  async deleteAvatar(userId: string): Promise<void> {
    const profile = await this.getProfile(userId);

    if (profile.avatarUrl) {
      // Delete from storage
      await this.storageService.delete(profile.avatarUrl);
    }

    await this.updateProfile(userId, { avatarUrl: null });
  }

  private validateAvatarFile(file: FileUpload): void {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (!allowedTypes.includes(file.mimetype)) {
      throw new ValidationError('Invalid file type. Use JPEG, PNG, or WebP');
    }

    if (file.size > maxSize) {
      throw new ValidationError('File too large. Maximum size is 5MB');
    }
  }

  private createDefaultProfile(userId: string): UserProfile {
    const user = await this.userService.findById(userId);

    return this.profileRepository.create({
      userId,
      firstName: user.firstName || '',
      lastName: user.lastName || '',
      language: 'en',
      currency: 'USD',
      timezone: 'UTC',
    });
  }
}
```

### Address Management

```typescript
export class AddressService {
  async getAddresses(userId: string): Promise<UserAddress[]> {
    return this.addressRepository.findByUserId(userId);
  }

  async addAddress(
    userId: string,
    address: Omit<UserAddress, 'id' | 'userId' | 'createdAt' | 'updatedAt'>
  ): Promise<UserAddress> {
    // If setting as primary, remove primary from others of same type
    if (address.isPrimary) {
      await this.addressRepository.clearPrimary(userId, address.type);
    }

    // Validate address
    await this.validateAddress(address);

    return this.addressRepository.create({
      ...address,
      userId,
    });
  }

  async updateAddress(
    userId: string,
    addressId: string,
    updates: Partial<UserAddress>
  ): Promise<UserAddress> {
    const address = await this.addressRepository.findById(addressId);

    if (!address || address.userId !== userId) {
      throw new NotFoundError('Address not found');
    }

    // If setting as primary, clear others
    if (updates.isPrimary) {
      await this.addressRepository.clearPrimary(userId, address.type);
    }

    return this.addressRepository.update(addressId, updates);
  }

  async deleteAddress(userId: string, addressId: string): Promise<void> {
    const address = await this.addressRepository.findById(addressId);

    if (!address || address.userId !== userId) {
      throw new NotFoundError('Address not found');
    }

    await this.addressRepository.delete(addressId);
  }

  async setPrimary(
    userId: string,
    addressId: string,
    type: AddressType
  ): Promise<void> {
    // Clear existing primary
    await this.addressRepository.clearPrimary(userId, type);

    // Set new primary
    await this.addressRepository.update(addressId, {
      isPrimary: true,
      type,
    });
  }

  private async validateAddress(address: Partial<UserAddress>): Promise<void> {
    // Validate required fields
    if (!address.addressLine1 || !address.city || !address.postalCode) {
      throw new ValidationError('Missing required address fields');
    }

    // Validate country code
    const isValidCountry = await this.countryService.isValidCode(
      address.countryCode
    );
    if (!isValidCountry) {
      throw new ValidationError('Invalid country code');
    }

    // Validate postal code format for country
    const isValidPostal = await this.postalCodeService.isValidFormat(
      address.postalCode,
      address.countryCode
    );
    if (!isValidPostal) {
      throw new ValidationError('Invalid postal code format');
    }
  }
}
```

---

## Preferences System

### Preference Management

```typescript
export class PreferencesService {
  async getPreferences(userId: string): Promise<UserPreferences> {
    let prefs = await this.preferencesRepository.findByUserId(userId);

    if (!prefs) {
      prefs = await this.createDefaultPreferences(userId);
    }

    return prefs;
  }

  async updatePreferences(
    userId: string,
    updates: Partial<UserPreferences>
  ): Promise<UserPreferences> {
    const existing = await this.getPreferences(userId);

    // Validate preference values
    this.validatePreferences(updates);

    // Merge and update
    const updated = await this.preferencesRepository.update(userId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Recalculate personalization scores
    await this.personalizationService.recalculateUserScores(userId);

    return updated;
  }

  async updateTripInterests(
    userId: string,
    interests: string[]
  ): Promise<void> {
    const validInterests = await this.getValidInterests();

    const invalid = interests.filter(i => !validInterests.includes(i));
    if (invalid.length > 0) {
      throw new ValidationError(`Invalid interests: ${invalid.join(', ')}`);
    }

    await this.updatePreferences(userId, { tripInterests: interests });
  }

  async getPersonalizedRecommendations(
    userId: string,
    context: RecommendationContext
  ): Promise<Recommendation[]> {
    const prefs = await this.getPreferences(userId);

    return this.recommendationEngine.generate({
      travelStyle: prefs.travelStyle,
      interests: prefs.tripInterests,
      budgetRange: {
        min: prefs.budgetMin,
        max: prefs.budgetMax,
        currency: prefs.budgetCurrency,
      },
      accommodationTypes: prefs.accommodationTypes,
      ...context,
    });
  }

  private validatePreferences(updates: Partial<UserPreferences>): void {
    if (updates.travelStyle) {
      const validStyles = ['adventure', 'leisure', 'business', 'cultural', 'luxury'];
      if (!validStyles.includes(updates.travelStyle)) {
        throw new ValidationError('Invalid travel style');
      }
    }

    if (updates.budgetMin !== undefined && updates.budgetMax !== undefined) {
      if (updates.budgetMin > updates.budgetMax) {
        throw new ValidationError('Minimum budget cannot exceed maximum');
      }
    }

    if (updates.accommodationTypes) {
      const validTypes = ['hotel', 'resort', 'villa', 'hostel', 'apartment', 'boutique'];
      const invalid = updates.accommodationTypes.filter(t => !validTypes.includes(t));
      if (invalid.length > 0) {
        throw new ValidationError(`Invalid accommodation types: ${invalid.join(', ')}`);
      }
    }
  }

  private async createDefaultPreferences(userId: string): Promise<UserPreferences> {
    return this.preferencesRepository.create({
      userId,
      travelStyle: 'leisure',
      accommodationTypes: ['hotel'],
      mealPreference: 'any',
      seatPreference: 'any',
      budgetMin: 0,
      budgetMax: 10000,
      budgetCurrency: 'USD',
      tripInterests: [],
      accessibilityNeeds: [],
    });
  }
}
```

### Preference Schema Definition

```typescript
interface InterestCategory {
  id: string;
  name: string;
  subcategories: InterestSubcategory[];
}

interface InterestSubcategory {
  id: string;
  name: string;
  synonyms: string[];
}

// Available interests (managed by admin)
const INTEREST_CATEGORIES: InterestCategory[] = [
  {
    id: 'activities',
    name: 'Activities',
    subcategories: [
      { id: 'hiking', name: 'Hiking & Trekking', synonyms: ['walking', 'trekking'] },
      { id: 'water_sports', name: 'Water Sports', synonyms: ['surfing', 'diving', 'snorkeling'] },
      { id: 'skiing', name: 'Skiing & Snowboarding', synonyms: ['winter sports'] },
      { id: 'wildlife', name: 'Wildlife & Nature', synonyms: ['safari', 'nature'] },
      { id: 'cultural_tours', name: 'Cultural Tours', synonyms: ['museums', 'heritage'] },
    ],
  },
  {
    id: 'dining',
    name: 'Dining',
    subcategories: [
      { id: 'fine_dining', name: 'Fine Dining', synonyms: ['gourmet', 'upscale'] },
      { id: 'street_food', name: 'Street Food', synonyms: ['local cuisine', 'food tours'] },
      { id: 'vegetarian', name: 'Vegetarian/Vegan', synonyms: ['plant-based'] },
    ],
  },
  {
    id: 'accommodation',
    name: 'Accommodation Style',
    subcategories: [
      { id: 'luxury', name: 'Luxury', synonyms: ['5-star', 'premium'] },
      { id: 'boutique', name: 'Boutique', synonyms: ['charming', 'unique'] },
      { id: 'budget', name: 'Budget-Friendly', synonyms: ['affordable', 'value'] },
    ],
  },
];
```

---

## Communication Settings

### Channel Management

```typescript
export class CommunicationService {
  async getSettings(userId: string): Promise<CommunicationSettings> {
    let settings = await this.settingsRepository.findByUserId(userId);

    if (!settings) {
      settings = await this.createDefaultSettings(userId);
    }

    return settings;
  }

  async updateSettings(
    userId: string,
    updates: Partial<CommunicationSettings>
  ): Promise<CommunicationSettings> {
    const existing = await this.getSettings(userId);

    // Validate quiet hours if provided
    if (updates.quietHoursStart || updates.quietHoursEnd) {
      this.validateQuietHours({
        quietHoursStart: updates.quietHoursStart ?? existing.quietHoursStart,
        quietHoursEnd: updates.quietHoursEnd ?? existing.quietHoursEnd,
      });
    }

    // Validate at least one transactional channel is enabled
    const merged = { ...existing, ...updates };
    if (!merged.transactionalEmails && !merged.transactionalSms) {
      throw new ValidationError(
        'At least one transactional channel must be enabled'
      );
    }

    return this.settingsRepository.update(userId, {
      ...updates,
      updatedAt: new Date(),
    });
  }

  async canSendNow(
    userId: string,
    type: 'marketing' | 'transactional',
    channel: 'email' | 'sms' | 'push' | 'whatsapp'
  ): Promise<boolean> {
    const settings = await this.getSettings(userId);

    // Check if channel is enabled for type
    const channelEnabled = this.isChannelEnabled(settings, type, channel);
    if (!channelEnabled) {
      return false;
    }

    // Check quiet hours for marketing
    if (type === 'marketing' && this.isInQuietHours(settings)) {
      return false;
    }

    return true;
  }

  async send(
    userId: string,
    message: CommunicationMessage
  ): Promise<SendResult> {
    const settings = await this.getSettings(userId);

    // Check permission
    const canSend = await this.canSendNow(
      userId,
      message.type,
      message.channel
    );

    if (!canSend) {
      return { status: 'skipped', reason: 'channel_disabled_or_quiet_hours' };
    }

    // Send via appropriate provider
    switch (message.channel) {
      case 'email':
        return this.emailService.send({ ...message, userId });
      case 'sms':
        return this.smsService.send({ ...message, userId });
      case 'push':
        return this.pushService.send({ ...message, userId });
      case 'whatsapp':
        return this.whatsappService.send({ ...message, userId });
      default:
        throw new ValidationError(`Unsupported channel: ${message.channel}`);
    }
  }

  private isChannelEnabled(
    settings: CommunicationSettings,
    type: string,
    channel: string
  ): boolean {
    const key = `${type}_${channel}` as keyof CommunicationSettings;
    return Boolean(settings[key]);
  }

  private isInQuietHours(settings: CommunicationSettings): boolean {
    if (!settings.quietHoursStart || !settings.quietHoursEnd) {
      return false;
    }

    const now = this.getCurrentTimeInTimezone(settings);
    const [startHour, startMin] = settings.quietHoursStart.split(':').map(Number);
    const [endHour, endMin] = settings.quietHoursEnd.split(':').map(Number);

    const currentMinutes = now.hour * 60 + now.minute;
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;

    if (startMinutes < endMinutes) {
      return currentMinutes >= startMinutes && currentMinutes < endMinutes;
    } else {
      // Overnight quiet hours
      return currentMinutes >= startMinutes || currentMinutes < endMinutes;
    }
  }

  private validateQuietHours(settings: QuietHours): void {
    if (settings.quietHoursStart && settings.quietHoursEnd) {
      const [startHour] = settings.quietHoursStart.split(':').map(Number);
      const [endHour] = settings.quietHoursEnd.split(':').map(Number);

      if (startHour < 0 || startHour > 23 || endHour < 0 || endHour > 23) {
        throw new ValidationError('Invalid quiet hours');
      }
    }
  }

  private createDefaultSettings(userId: string): CommunicationSettings {
    return this.settingsRepository.create({
      userId,
      marketingEmails: true,
      transactionalEmails: true,
      marketingSms: false,
      transactionalSms: true,
      pushNotifications: true,
      whatsappUpdates: false,
      phoneCalls: false,
      preferredChannel: 'email',
    });
  }
}
```

### Communication Preferences UI Schema

```typescript
interface CommunicationSettingsSchema {
  sections: CommunicationSection[];
}

interface CommunicationSection {
  title: string;
  description: string;
  channels: ChannelSetting[];
}

interface ChannelSetting {
  channel: 'email' | 'sms' | 'push' | 'whatsapp' | 'phone';
  icon: string;
  marketing: {
    enabled: boolean;
    label: string;
    description: string;
  };
  transactional: {
    enabled: boolean;
    label: string;
    description: string;
    required: boolean;
  };
}

const COMMUNICATION_SCHEMA: CommunicationSettingsSchema = {
  sections: [
    {
      title: 'Email',
      description: 'Receive updates and offers via email',
      channels: [
        {
          channel: 'email',
          icon: 'mail',
          marketing: {
            enabled: true,
            label: 'Marketing emails',
            description: 'Deals, promotions, and travel inspiration',
          },
          transactional: {
            enabled: true,
            label: 'Booking updates',
            description: 'Confirmations, reminders, and itinerary changes',
            required: true,
          },
        },
      ],
    },
    {
      title: 'SMS',
      description: 'Get quick text message updates',
      channels: [
        {
          channel: 'sms',
          icon: 'message',
          marketing: {
            enabled: false,
            label: 'Marketing SMS',
            description: 'Exclusive deals via text message',
          },
          transactional: {
            enabled: true,
            label: 'Booking SMS',
            description: 'Urgent updates about your bookings',
            required: false,
          },
        },
      ],
    },
    // ... other channels
  ],
};
```

---

## Privacy Controls

### Privacy Settings

```typescript
export class PrivacyService {
  async getSettings(userId: string): Promise<PrivacySettings> {
    let settings = await this.privacyRepository.findByUserId(userId);

    if (!settings) {
      settings = await this.createDefaultSettings(userId);
    }

    return settings;
  }

  async updateSettings(
    userId: string,
    updates: Partial<PrivacySettings>
  ): Promise<PrivacySettings> {
    const existing = await this.getSettings(userId);

    return this.privacyRepository.update(userId, {
      ...updates,
      updatedAt: new Date(),
    });
  }

  async exportData(userId: string): Promise<DataExportResult> {
    // Collect all user data
    const data = await this.collectUserData(userId);

    // Generate export file
    const exportFile = await this.generateExportFile(data);

    // Store export with expiration
    const exportRecord = await this.dataExportRepository.create({
      userId,
      fileUrl: exportFile.url,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
    });

    // Send download link
    await this.notificationService.send({
      userId,
      type: 'data_export_ready',
      channel: 'email',
      data: { downloadLink: exportFile.url },
    });

    return {
      exportId: exportRecord.id,
      expiresAt: exportRecord.expiresAt,
      downloadLink: exportFile.url,
    };
  }

  private async collectUserData(userId: string): Promise<UserDataBundle> {
    const [user, profile, addresses, preferences, bookings, travelers] =
      await Promise.all([
        this.userService.findById(userId),
        this.profileRepository.findByUserId(userId),
        this.addressRepository.findByUserId(userId),
        this.preferencesRepository.findByUserId(userId),
        this.bookingRepository.findByUserId(userId),
        this.travelerRepository.findByUserId(userId),
      ]);

    return {
      account: { user, profile },
      addresses,
      preferences,
      bookings: bookings.map(b => this.sanitizeBooking(b)),
      travelers,
      exportedAt: new Date(),
    };
  }

  private async generateExportFile(data: UserDataBundle): Promise<{ url: string }> {
    const json = JSON.stringify(data, null, 2);
    const buffer = Buffer.from(json, 'utf-8');

    const key = `data-exports/${data.account.user.id}/${crypto.randomUUID()}.json`;
    const url = await this.storageService.upload(key, buffer, {
      contentType: 'application/json',
      encryption: true,
    });

    return { url };
  }
}
```

### Data Visibility

```typescript
export class ProfileVisibilityService {
  async getPublicProfile(
    userId: string,
    viewerId?: string
  ): Promise<PublicProfile | null> {
    const privacy = await this.privacyService.getSettings(userId);

    // Check visibility based on privacy settings
    if (privacy.profileVisibility === 'private') {
      return null;
    }

    if (privacy.profileVisibility === 'registered_only' && !viewerId) {
      return null;
    }

    const profile = await this.profileRepository.findByUserId(userId);
    if (!profile) {
      return null;
    }

    // Build public profile based on settings
    const publicProfile: PublicProfile = {
      displayName: profile.displayName || `${profile.firstName} ${profile.lastName}`,
      avatarUrl: profile.avatarUrl,
      bio: privacy.allowDataSharing ? profile.bio : undefined,
      location: privacy.allowDataSharing ? this.getUserLocation(userId) : undefined,
      memberSince: profile.createdAt,
    };

    // Add travel history if enabled
    if (privacy.showTravelHistory && privacy.allowDataSharing) {
      publicProfile.travelStats = await this.getTravelStats(userId);
    }

    // Add upcoming trips if enabled
    if (privacy.showUpcomingTrips && viewerId) {
      const isFriend = await this.friendService.areFriends(userId, viewerId);
      if (isFriend) {
        publicProfile.upcomingTrips = await this.getUpcomingTrips(userId);
      }
    }

    return publicProfile;
  }

  private async getTravelStats(userId: string): Promise<TravelStats> {
    const bookings = await this.bookingRepository.findCompletedByUserId(userId);

    return {
      totalTrips: bookings.length,
      countriesVisited: new Set(
        bookings.flatMap(b => b.destinations.map(d => d.countryCode))
      ).size,
      favoriteDestinations: await this.calculateFavoriteDestinations(bookings),
    };
  }
}
```

---

## Account Deletion

### Deletion Process

Account deletion supports both immediate deletion (after confirmation) and scheduled deletion (30-day grace period).

```typescript
export class AccountDeletionService {
  async requestDeletion(userId: string): Promise<DeletionRequestResult> {
    // Check if deletion is already pending
    const existing = await this.deletionRepository.findPending(userId);
    if (existing) {
      return {
        status: 'pending',
        scheduledFor: existing.scheduledFor,
        canCancelUntil: existing.scheduledFor,
      };
    }

    // Check for active bookings
    const activeBookings = await this.bookingRepository.findActiveByUserId(userId);
    if (activeBookings.length > 0) {
      throw new ConflictError(
        'Cannot delete account with active bookings. Please cancel or complete bookings first.'
      );
    }

    // Schedule deletion for 30 days from now
    const scheduledFor = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);

    const deletionRequest = await this.deletionRepository.create({
      userId,
      scheduledFor,
      status: 'pending',
    });

    // Send confirmation email with cancel link
    const user = await this.userService.findById(userId);
    await this.emailService.send({
      to: user.email,
      template: 'account_deletion_scheduled',
      data: {
        scheduledFor,
        cancelLink: `${process.env.APP_URL}/settings/account/cancel-deletion?token=${deletionRequest.id}`,
      },
    });

    return {
      status: 'pending',
      scheduledFor,
      canCancelUntil: scheduledFor,
    };
  }

  async cancelDeletion(userId: string, requestId: string): Promise<void> {
    const deletionRequest = await this.deletionRepository.findById(requestId);

    if (!deletionRequest || deletionRequest.userId !== userId) {
      throw new NotFoundError('Deletion request not found');
    }

    if (deletionRequest.status === 'completed') {
      throw new ConflictError('Account already deleted');
    }

    await this.deletionRepository.update(requestId, {
      status: 'cancelled',
      cancelledAt: new Date(),
    });

    // Send confirmation
    const user = await this.userService.findById(userId);
    await this.emailService.send({
      to: user.email,
      template: 'account_deletion_cancelled',
      data: { cancelledAt: new Date() },
    });
  }

  async executeDeletion(userId: string): Promise<void> {
    // Anonymize bookings (keep for financial records)
    await this.bookingRepository.anonymizeByUserId(userId);

    // Delete sensitive data
    await Promise.all([
      this.profileRepository.delete(userId),
      this.addressRepository.deleteByUserId(userId),
      this.preferencesRepository.deleteByUserId(userId),
      this.communicationSettingsRepository.deleteByUserId(userId),
      this.privacySettingsRepository.deleteByUserId(userId),
      this.travelerRepository.deleteByUserId(userId),
      this.sessionService.deleteAllForUser(userId),
    ]);

    // Mark user as deleted (soft delete)
    await this.userService.softDelete(userId);

    // Clear all caches
    await this.cacheService.deletePattern(`user:${userId}:*`);

    // Log deletion
    await this.auditLogService.record({
      action: 'account_deleted',
      userId,
      timestamp: new Date(),
    });
  }

  async processScheduledDeletions(): Promise<void> {
    const pendingDeletions = await this.deletionRepository.findDueForDeletion();

    for (const deletion of pendingDeletions) {
      try {
        await this.executeDeletion(deletion.userId);
        await this.deletionRepository.update(deletion.id, {
          status: 'completed',
          completedAt: new Date(),
        });
      } catch (error) {
        await this.deletionRepository.update(deletion.id, {
          status: 'failed',
          error: error.message,
        });
      }
    }
  }
}
```

### Anonymization Rules

```typescript
export class DataAnonymizationService {
  async anonymizeUser(userId: string): Promise<void> {
    const user = await this.userService.findById(userId);

    // Replace PII with anonymized values
    const anonymized = {
      email: `deleted-${userId}@anonymized.local`,
      firstName: 'Deleted',
      lastName: 'User',
      phoneNumber: null,
      // Preserve status, tier for records
    };

    await this.userService.update(userId, anonymized);
  }

  async anonymizeBookings(userId: string): Promise<void> {
    const bookings = await this.bookingRepository.findByUserId(userId);

    for (const booking of bookings) {
      await this.bookingRepository.update(booking.id, {
        customerEmail: `deleted-${booking.id}@anonymized.local`,
        customerName: 'Deleted User',
        customerPhone: null,
      });
    }
  }
}
```

---

## Profile Validation

### Validation Rules

```typescript
export class ProfileValidator {
  private readonly NAME_MIN_LENGTH = 1;
  private readonly NAME_MAX_LENGTH = 100;
  private readonly BIO_MAX_LENGTH = 500;
  private readonly INTERESTS_MAX_COUNT = 20;

  async validateProfileUpdate(
    userId: string,
    updates: Partial<UserProfile>
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];

    // Validate name fields
    if (updates.firstName !== undefined) {
      this.validateName('firstName', updates.firstName, errors);
    }

    if (updates.lastName !== undefined) {
      this.validateName('lastName', updates.lastName, errors);
    }

    // Validate bio
    if (updates.bio !== undefined && updates.bio.length > this.BIO_MAX_LENGTH) {
      errors.push({
        field: 'bio',
        message: `Bio must be ${this.BIO_MAX_LENGTH} characters or less`,
      });
    }

    // Validate date of birth
    if (updates.dateOfBirth !== undefined) {
      this.validateDateOfBirth(updates.dateOfBirth, errors);
    }

    // Validate interests
    if (updates.interests !== undefined) {
      this.validateInterests(updates.interests, errors);
    }

    // Validate nationality
    if (updates.nationality !== undefined) {
      const isValidCountry = await this.countryService.isValidCode(
        updates.nationality
      );
      if (!isValidCountry) {
        errors.push({
          field: 'nationality',
          message: 'Invalid country code',
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  private validateName(
    field: string,
    value: string,
    errors: ValidationError[]
  ): void {
    if (value.length < this.NAME_MIN_LENGTH) {
      errors.push({
        field,
        message: `${field} must be at least ${this.NAME_MIN_LENGTH} character`,
      });
    }

    if (value.length > this.NAME_MAX_LENGTH) {
      errors.push({
        field,
        message: `${field} must be ${this.NAME_MAX_LENGTH} characters or less`,
      });
    }

    // Check for invalid characters
    if (!/^[\p{L}\s'-]+$/u.test(value)) {
      errors.push({
        field,
        message: `${field} contains invalid characters`,
      });
    }
  }

  private validateDateOfBirth(dateOfBirth: Date, errors: ValidationError[]): void {
    const now = new Date();
    const minAge = 13;
    const maxAge = 150;

    const age = now.getFullYear() - dateOfBirth.getFullYear();

    if (dateOfBirth > now) {
      errors.push({
        field: 'dateOfBirth',
        message: 'Date of birth cannot be in the future',
      });
    }

    if (age < minAge) {
      errors.push({
        field: 'dateOfBirth',
        message: `You must be at least ${minAge} years old`,
      });
    }

    if (age > maxAge) {
      errors.push({
        field: 'dateOfBirth',
        message: 'Please enter a valid date of birth',
      });
    }
  }

  private validateInterests(interests: string[], errors: ValidationError[]): void {
    if (interests.length > this.INTERESTS_MAX_COUNT) {
      errors.push({
        field: 'interests',
        message: `Maximum ${this.INTERESTS_MAX_COUNT} interests allowed`,
      });
    }

    // Check for duplicates
    const unique = new Set(interests);
    if (unique.size !== interests.length) {
      errors.push({
        field: 'interests',
        message: 'Duplicate interests are not allowed',
      });
    }
  }
}
```

---

## API Endpoints

### Profile Endpoints

```
GET    /profile
PATCH  /profile
POST   /profile/avatar
DELETE /profile/avatar
```

### Address Endpoints

```
GET    /profile/addresses
POST   /profile/addresses
PATCH  /profile/addresses/:addressId
DELETE /profile/addresses/:addressId
POST   /profile/addresses/:addressId/primary
```

### Preferences Endpoints

```
GET    /profile/preferences
PATCH  /profile/preferences
GET    /profile/preferences/interests
PATCH  /profile/preferences/interests
GET    /profile/preferences/recommendations
```

### Communication Endpoints

```
GET    /profile/communication
PATCH  /profile/communication
POST   /profile/communication/test
```

### Privacy Endpoints

```
GET    /profile/privacy
PATCH  /profile/privacy
POST   /profile/privacy/export-data
GET    /profile/privacy/export/:exportId
```

### Account Deletion Endpoints

```
POST   /profile/account/request-deletion
POST   /profile/account/cancel-deletion
```

---

**Next:** [Traveler Management](./USER_ACCOUNTS_05_TRAVELERS.md) — Traveler profiles, documents, and companions
