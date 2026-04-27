# User Accounts 05: Traveler Management

> Traveler profiles, document storage, companions, and loyalty programs

---

## Overview

This document details the traveler management subsystem, covering traveler profiles separate from the main user account, secure document storage (passports, visas), companion/dependent management, and loyalty program integration. Each booking references traveler profiles for simplified checkout and regulatory compliance.

**Key Capabilities:**
- Multiple traveler profiles per account
- Secure document storage with encryption
- Companion and dependent management
- Loyalty program integration
- Travel history tracking
- Automated document expiration alerts

---

## Table of Contents

1. [Traveler Data Model](#traveler-data-model)
2. [Traveler Profiles](#traveler-profiles)
3. [Document Management](#document-management)
4. [Companion Management](#companion-management)
5. [Loyalty Programs](#loyalty-programs)
6. [Travel History](#travel-history)
7. [Regulatory Compliance](#regulatory-compliance)

---

## Traveler Data Model

### Core Entities

```typescript
interface TravelerProfile {
  id: string;
  userId: string; // Owner of this traveler profile
  type: TravelerType;
  relationship: 'self' | 'spouse' | 'child' | 'parent' | 'friend' | 'other';

  // Basic Information
  firstName: string;
  lastName: string;
  middleName?: string;
  dateOfBirth: Date;
  gender: 'male' | 'female' | 'non-binary' | 'prefer_not_to_say';
  nationality: string;
  citizenship: string;

  // Contact Information
  email?: string;
  phoneNumber?: string;

  // Travel Documents
  documents: TravelerDocument[];

  // Preferences
  mealPreference: MealPreference;
  seatPreference: SeatPreference;
  accessibilityNeeds?: string[];

  // Loyalty Programs
  loyaltyMemberships: LoyaltyMembership[];

  // Metadata
  isPrimary: boolean; // For users with multiple self-profiles
  avatarUrl?: string;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

type TravelerType = 'adult' | 'child' | 'infant';

interface TravelerDocument {
  id: string;
  travelerId: string;
  type: DocumentType;
  documentNumber: string;
  issuingCountry: string;

  // Dates
  issuanceDate: Date;
  expirationDate: Date;

  // Encrypted Storage
  encryptedData: string; // Full document details encrypted

  // Document Images (encrypted storage references)
  frontImageStorageKey?: string;
  backImageStorageKey?: string;

  // Verification
  isVerified: boolean;
  verifiedAt?: Date;
  verificationMethod?: 'manual' | 'ocr' | 'third_party';

  // Alerts
  expirationAlertSent: boolean;

  // Metadata
  createdAt: Date;
  updatedAt: Date;
}

type DocumentType =
  | 'passport'
  | 'national_id'
  | 'drivers_license'
  | 'visa'
  | 'residence_permit'
  | 'birth_certificate';

interface LoyaltyMembership {
  id: string;
  travelerId: string;
  program: LoyaltyProgram;
  membershipNumber: string;
  tier: string;
  points: number;
  status: 'active' | 'inactive' | 'suspended';

  // Preferences
  isPrimary: boolean;

  // Metadata
  lastSyncedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

interface LoyaltyProgram {
  id: string;
  name: string;
  code: string; // e.g., 'AA' for American Airlines
  type: 'airline' | 'hotel' | 'car_rental' | 'other';
  iconUrl: string;
  websiteUrl: string;
}
```

### Database Schema

```sql
-- Traveler Profiles
CREATE TABLE traveler_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL,
  relationship VARCHAR(20) NOT NULL,

  -- Basic Information
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100),
  date_of_birth DATE NOT NULL,
  gender VARCHAR(20) NOT NULL,
  nationality CHAR(2) NOT NULL,
  citizenship CHAR(2) NOT NULL,

  -- Contact Information
  email VARCHAR(255),
  phone_number VARCHAR(50),

  -- Preferences
  meal_preference VARCHAR(20) DEFAULT 'any',
  seat_preference VARCHAR(20) DEFAULT 'any',
  accessibility_needs TEXT[],

  -- Metadata
  is_primary BOOLEAN DEFAULT false,
  avatar_url TEXT,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_traveler_user_id (user_id),
  INDEX idx_traveler_full_name (first_name, last_name),
  INDEX idx_traveler_date_of_birth (date_of_birth)
);

-- Traveler Documents
CREATE TABLE traveler_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  traveler_id UUID NOT NULL REFERENCES traveler_profiles(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  document_number VARCHAR(100) NOT NULL,
  issuing_country CHAR(2) NOT NULL,

  -- Dates
  issuance_date DATE NOT NULL,
  expiration_date DATE NOT NULL,

  -- Encrypted Data (contains sensitive fields)
  encrypted_data TEXT NOT NULL,

  -- Document Images (references to encrypted storage)
  front_image_storage_key VARCHAR(255),
  back_image_storage_key VARCHAR(255),

  -- Verification
  is_verified BOOLEAN DEFAULT false,
  verified_at TIMESTAMP WITH TIME ZONE,
  verification_method VARCHAR(20),

  -- Alerts
  expiration_alert_sent BOOLEAN DEFAULT false,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_traveler_docs_traveler_id (traveler_id),
  INDEX idx_traveler_docs_type (type),
  INDEX idx_traveler_docs_expiration (expiration_date)
);

-- Loyalty Memberships
CREATE TABLE loyalty_memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  traveler_id UUID NOT NULL REFERENCES traveler_profiles(id) ON DELETE CASCADE,
  program_id VARCHAR(50) NOT NULL,
  membership_number VARCHAR(100) NOT NULL,
  tier VARCHAR(50),
  points INTEGER DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',
  is_primary BOOLEAN DEFAULT false,
  last_synced_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (traveler_id, program_id, membership_number),
  INDEX idx_loyalty_traveler_id (traveler_id),
  INDEX idx_loyalty_program_id (program_id)
);

-- Loyalty Programs (reference data)
CREATE TABLE loyalty_programs (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  code VARCHAR(10) NOT NULL UNIQUE,
  type VARCHAR(20) NOT NULL,
  icon_url TEXT,
  website_url TEXT,
  supported_countries CHAR(2)[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Travel History (aggregated from bookings)
CREATE TABLE travel_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  traveler_id UUID NOT NULL REFERENCES traveler_profiles(id) ON DELETE CASCADE,
  booking_id UUID NOT NULL REFERENCES bookings(id),

  -- Trip Details
  destination_country CHAR(2) NOT NULL,
  destination_city VARCHAR(100),
  departure_date DATE NOT NULL,
  return_date DATE,

  -- Trip Type
  trip_type VARCHAR(50), -- leisure, business, etc.

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_travel_history_traveler_id (traveler_id),
  INDEX idx_travel_history_destination (destination_country),
  INDEX idx_travel_history_dates (departure_date, return_date)
);

-- Document Sharing (for temporary access by agents/admins)
CREATE TABLE document_shares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES traveler_documents(id) ON DELETE CASCADE,
  shared_by UUID NOT NULL REFERENCES users(id),
  access_token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  access_count INTEGER DEFAULT 0,
  max_access_count INTEGER DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_document_shares_token (access_token),
  INDEX idx_document_shares_expires (expires_at)
);
```

---

## Traveler Profiles

### Profile Management

```typescript
export class TravelerProfileService {
  async getProfiles(userId: string): Promise<TravelerProfile[]> {
    return this.travelerRepository.findByUserId(userId);
  }

  async getProfile(
    userId: string,
    travelerId: string
  ): Promise<TravelerProfile> {
    const profile = await this.travelerRepository.findById(travelerId);

    if (!profile || profile.userId !== userId) {
      throw new NotFoundError('Traveler profile not found');
    }

    return profile;
  }

  async createProfile(
    userId: string,
    data: Omit<TravelerProfile, 'id' | 'userId' | 'createdAt' | 'updatedAt'>
  ): Promise<TravelerProfile> {
    // Validate traveler count limit
    const existing = await this.travelerRepository.countByUserId(userId);
    if (existing >= this.MAX_TRAVELERS_PER_USER) {
      throw new ValidationError(
        `Maximum ${this.MAX_TRAVELERS_PER_USER} traveler profiles allowed`
      );
    }

    // Validate date of birth based on type
    this.validateTravelerType(data.type, data.dateOfBirth);

    // If primary, remove primary from others
    if (data.isPrimary) {
      await this.travelerRepository.clearPrimary(userId);
    }

    // Create profile
    const profile = await this.travelerRepository.create({
      ...data,
      userId,
    });

    // Trigger document requirement check
    await this.checkDocumentRequirements(profile);

    return profile;
  }

  async updateProfile(
    userId: string,
    travelerId: string,
    updates: Partial<TravelerProfile>
  ): Promise<TravelerProfile> {
    const profile = await this.getProfile(userId, travelerId);

    // Validate updates
    if (updates.type && updates.dateOfBirth) {
      this.validateTravelerType(updates.type, updates.dateOfBirth);
    }

    // Apply updates
    const updated = await this.travelerRepository.update(travelerId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Check if document updates are needed
    if (updates.nationality || updates.citizenship || updates.dateOfBirth) {
      await this.checkDocumentRequirements(updated);
    }

    return updated;
  }

  async deleteProfile(
    userId: string,
    travelerId: string
  ): Promise<void> {
    const profile = await this.getProfile(userId, travelerId);

    // Check for active or upcoming bookings
    const hasBookings = await this.bookingRepository.hasTravelerInActiveBookings(
      travelerId
    );

    if (hasBookings) {
      throw new ConflictError(
        'Cannot delete traveler profile with active or upcoming bookings'
      );
    }

    // Delete profile (cascade will delete documents and memberships)
    await this.travelerRepository.delete(travelerId);
  }

  async setPrimary(
    userId: string,
    travelerId: string
  ): Promise<void> {
    const profile = await this.getProfile(userId, travelerId);

    // Clear existing primary
    await this.travelerRepository.clearPrimary(userId);

    // Set new primary
    await this.travelerRepository.update(travelerId, {
      isPrimary: true,
    });
  }

  private validateTravelerType(type: TravelerType, dateOfBirth: Date): void {
    const today = new Date();
    const age = this.calculateAge(dateOfBirth, today);

    switch (type) {
      case 'infant':
        if (age > 2) {
          throw new ValidationError('Infant must be under 2 years old');
        }
        break;
      case 'child':
        if (age < 2 || age >= 12) {
          throw new ValidationError('Child must be between 2-11 years old');
        }
        break;
      case 'adult':
        if (age < 12) {
          throw new ValidationError('Adult must be 12 years or older');
        }
        break;
    }
  }

  private calculateAge(birthDate: Date, currentDate: Date): number {
    let age = currentDate.getFullYear() - birthDate.getFullYear();
    const monthDiff = currentDate.getMonth() - birthDate.getMonth();

    if (
      monthDiff < 0 ||
      (monthDiff === 0 && currentDate.getDate() < birthDate.getDate())
    ) {
      age--;
    }

    return age;
  }

  private async checkDocumentRequirements(
    profile: TravelerProfile
  ): Promise<void> {
    const requiredDocs = this.getRequiredDocuments(profile);

    for (const docType of requiredDocs) {
      const hasDoc = profile.documents.some(d => d.type === docType);

      if (!hasDoc) {
        await this.notificationService.send({
          userId: profile.userId,
          type: 'document_required',
          channel: 'email',
          priority: 'low',
          data: {
            travelerName: `${profile.firstName} ${profile.lastName}`,
            documentType: docType,
          },
        });
      }
    }
  }

  private getRequiredDocuments(profile: TravelerProfile): DocumentType[] {
    const docs: DocumentType[] = [];

    // Always need passport for international travel
    docs.push('passport');

    // Visa requirements depend on nationality (checked during booking)
    // based on destination country

    return docs;
  }
}
```

### Profile Search and Selection

```typescript
export class TravelerSelectionService {
  async searchProfiles(
    userId: string,
    query: string
  ): Promise<TravelerProfile[]> {
    const profiles = await this.travelerRepository.findByUserId(userId);

    const searchTerm = query.toLowerCase();

    return profiles.filter(p =>
      p.firstName.toLowerCase().includes(searchTerm) ||
      p.lastName.toLowerCase().includes(searchTerm) ||
      `${p.firstName} ${p.lastName}`.toLowerCase().includes(searchTerm)
    );
  }

  async suggestProfiles(
    userId: string,
    bookingContext: BookingContext
  ): Promise<TravelerSuggestion[]> {
    const profiles = await this.travelerRepository.findByUserId(userId);
    const suggestions: TravelerSuggestion[] = [];

    for (const profile of profiles) {
      const score = this.calculateSuggestionScore(profile, bookingContext);

      if (score > 0) {
        suggestions.push({
          profile,
          score,
          reasons: this.getSuggestionReasons(profile, bookingContext),
        });
      }
    }

    return suggestions
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
      .map(s => s.profile);
  }

  private calculateSuggestionScore(
    profile: TravelerProfile,
    context: BookingContext
  ): number {
    let score = 0;

    // Primary profile gets boost
    if (profile.isPrimary) score += 10;

    // Previous travelers to same destination
    const hasVisited = this.hasVisitedDestination(profile, context.destination);
    if (hasVisited) score += 5;

    // Appropriate for trip type
    if (this.isAppropriateForTrip(profile, context)) score += 3;

    // Has required documents
    if (this.hasRequiredDocuments(profile, context)) score += 5;

    // Matching loyalty programs
    if (this.hasMatchingLoyaltyProgram(profile, context)) score += 2;

    return score;
  }

  private hasVisitedDestination(
    profile: TravelerProfile,
    destination: Destination
  ): boolean {
    return profile.travelHistory?.some(
      trip => trip.destinationCountry === destination.countryCode
    ) ?? false;
  }

  private isAppropriateForTrip(
    profile: TravelerProfile,
    context: BookingContext
  ): boolean {
    // Adults only for business trips
    if (context.tripType === 'business' && profile.type !== 'adult') {
      return false;
    }

    return true;
  }

  private hasRequiredDocuments(
    profile: TravelerProfile,
    context: BookingContext
  ): boolean {
    // Check for valid passport
    const validPassport = profile.documents.find(
      d => d.type === 'passport' &&
      d.expirationDate > context.departureDate &&
      d.isVerified
    );

    return !!validPassport;
  }

  private hasMatchingLoyaltyProgram(
    profile: TravelerProfile,
    context: BookingContext
  ): boolean {
    if (!context.supplierLoyaltyPrograms) return false;

    return profile.loyaltyMemberships.some(m =>
      context.supplierLoyaltyPrograms!.includes(m.program.code)
    );
  }
}
```

---

## Document Management

### Secure Document Storage

```typescript
import crypto from 'crypto';

export class DocumentService {
  private readonly ENCRYPTION_ALGORITHM = 'aes-256-gcm';
  private readonly ENCRYPTION_KEY = Buffer.from(
    process.env.DOCUMENT_ENCRYPTION_KEY!,
    'hex'
  );

  async addDocument(
    userId: string,
    travelerId: string,
    document: Omit<TravelerDocument, 'id' | 'travelerId' | 'createdAt' | 'updatedAt'>,
    images?: DocumentImages
  ): Promise<TravelerDocument> {
    // Verify ownership
    const profile = await this.travelerService.getProfile(userId, travelerId);

    // Check for duplicate document
    const existing = profile.documents.find(
      d => d.type === document.type &&
      d.documentNumber === document.documentNumber
    );

    if (existing) {
      throw new ConflictError('Document already exists');
    }

    // Validate document data
    await this.validateDocument(document);

    // Encrypt sensitive data
    const encryptedData = this.encryptData({
      documentNumber: document.documentNumber,
      issuingCountry: document.issuingCountry,
      issuanceDate: document.issuanceDate,
      expirationDate: document.expirationDate,
    });

    // Upload images if provided
    let frontImageKey: string | undefined;
    let backImageKey: string | undefined;

    if (images?.front) {
      frontImageKey = await this.uploadDocumentImage(
        travelerId,
        document.type,
        images.front,
        'front'
      );
    }

    if (images?.back) {
      backImageKey = await this.uploadDocumentImage(
        travelerId,
        document.type,
        images.back,
        'back'
      );
    }

    // Create document record
    const newDocument = await this.documentRepository.create({
      travelerId,
      type: document.type,
      documentNumber: document.documentNumber, // Also in encrypted data
      issuingCountry: document.issuingCountry,
      issuanceDate: document.issuanceDate,
      expirationDate: document.expirationDate,
      encryptedData,
      frontImageStorageKey: frontImageKey,
      backImageStorageKey: backImageKey,
      isVerified: false,
      expirationAlertSent: false,
    });

    // Schedule expiration alert
    await this.scheduleExpirationAlert(newDocument);

    return newDocument;
  }

  async updateDocument(
    userId: string,
    documentId: string,
    updates: Partial<TravelerDocument>
  ): Promise<TravelerDocument> {
    const document = await this.getDocument(userId, documentId);

    // Re-encrypt if sensitive data changed
    if (
      updates.documentNumber ||
      updates.issuingCountry ||
      updates.issuanceDate ||
      updates.expirationDate
    ) {
      const currentData = this.decryptData(document.encryptedData);
      const newData = {
        documentNumber: updates.documentNumber || currentData.documentNumber,
        issuingCountry: updates.issuingCountry || currentData.issuingCountry,
        issuanceDate: updates.issuanceDate || currentData.issuanceDate,
        expirationDate: updates.expirationDate || currentData.expirationDate,
      };

      updates.encryptedData = this.encryptData(newData);
    }

    const updated = await this.documentRepository.update(documentId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Reschedule expiration alert if date changed
    if (updates.expirationDate) {
      await this.scheduleExpirationAlert(updated);
    }

    return updated;
  }

  async deleteDocument(
    userId: string,
    documentId: string
  ): Promise<void> {
    const document = await this.getDocument(userId, documentId);

    // Check if document is required for active bookings
    const hasActiveBookings =
      await this.bookingRepository.hasActiveBookingsRequiringDocument(
        documentId
      );

    if (hasActiveBookings) {
      throw new ConflictError(
        'Cannot delete document required for active bookings'
      );
    }

    // Delete images from storage
    if (document.frontImageStorageKey) {
      await this.storageService.delete(document.frontImageStorageKey);
    }

    if (document.backImageStorageKey) {
      await this.storageService.delete(document.backImageStorageKey);
    }

    await this.documentRepository.delete(documentId);
  }

  async verifyDocument(
    userId: string,
    documentId: string,
    verificationData: DocumentVerificationData
  ): Promise<TravelerDocument> {
    const document = await this.getDocument(userId, documentId);

    // Perform OCR verification if images provided
    let ocrResult: OCRResult | null = null;

    if (verificationData.ocrData) {
      ocrResult = await this.ocrService.verify(
        document,
        verificationData.ocrData
      );
    }

    // Manual verification by admin
    if (verificationData.adminVerified) {
      return await this.documentRepository.update(documentId, {
        isVerified: true,
        verifiedAt: new Date(),
        verificationMethod: 'manual',
      });
    }

    // Auto-verify if OCR confidence is high
    if (ocrResult && ocrResult.confidence > 0.95) {
      return await this.documentRepository.update(documentId, {
        isVerified: true,
        verifiedAt: new Date(),
        verificationMethod: 'ocr',
      });
    }

    return document;
  }

  async getDocumentImage(
    userId: string,
    documentId: string,
    side: 'front' | 'back',
    shareToken?: string
  ): Promise<string> {
    const document = await this.getDocument(userId, documentId);

    // Check if share token is provided (for temporary access)
    if (shareToken) {
      const share = await this.documentShareRepository.findByToken(shareToken);

      if (!share || share.documentId !== documentId || share.expiresAt < new Date()) {
        throw new UnauthorizedError('Invalid or expired share token');
      }

      // Increment access count
      await this.documentShareRepository.incrementAccess(share.id);

      if (share.accessCount >= share.maxAccessCount) {
        await this.documentShareRepository.delete(share.id);
      }
    }

    // Get image from storage
    const storageKey = side === 'front'
      ? document.frontImageStorageKey
      : document.backImageStorageKey;

    if (!storageKey) {
      throw new NotFoundError('Image not found');
    }

    // Generate signed URL with short expiry
    return await this.storageService.getSignedUrl(storageKey, {
      expiresIn: 300, // 5 minutes
    });
  }

  async createShareLink(
    userId: string,
    documentId: string,
    expiresIn: number = 3600
  ): Promise<string> {
    const document = await this.getDocument(userId, documentId);

    const token = crypto.randomBytes(32).toString('hex');

    await this.documentShareRepository.create({
      documentId,
      sharedBy: userId,
      accessToken: token,
      expiresAt: new Date(Date.now() + expiresIn * 1000),
      maxAccessCount: 1,
    });

    return `${process.env.APP_URL}/documents/shared/${token}`;
  }

  private encryptData(data: Record<string, unknown>): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(
      this.ENCRYPTION_ALGORITHM,
      this.ENCRYPTION_KEY,
      iv
    );

    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  private decryptData(encrypted: string): Record<string, unknown> {
    const [ivHex, authTagHex, encryptedData] = encrypted.split(':');

    const iv = Buffer.from(ivHex, 'hex');
    const authTag = Buffer.from(authTagHex, 'hex');

    const decipher = crypto.createDecipheriv(
      this.ENCRYPTION_ALGORITHM,
      this.ENCRYPTION_KEY,
      iv
    );

    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return JSON.parse(decrypted);
  }

  private async uploadDocumentImage(
    travelerId: string,
    docType: DocumentType,
    image: Buffer,
    side: string
  ): Promise<string> {
    const key = `documents/${travelerId}/${docType}/${side}_${crypto.randomUUID()}.png`;

    await this.storageService.upload(key, image, {
      contentType: 'image/png',
      encryption: true,
    });

    return key;
  }

  private async validateDocument(document: Partial<TravelerDocument>): Promise<void> {
    // Validate required fields
    if (!document.type || !document.documentNumber || !document.issuingCountry) {
      throw new ValidationError('Missing required document fields');
    }

    // Validate expiration date is in the future
    if (document.expirationDate && document.expirationDate <= new Date()) {
      throw new ValidationError('Document has expired');
    }

    // Validate document number format based on type
    const isValidFormat = this.validateDocumentNumber(
      document.type,
      document.documentNumber,
      document.issuingCountry
    );

    if (!isValidFormat) {
      throw new ValidationError('Invalid document number format');
    }
  }

  private validateDocumentNumber(
    type: DocumentType,
    number: string,
    country: string
  ): boolean {
    // Passport: Typically 6-9 alphanumeric characters
    if (type === 'passport') {
      return /^[A-Z0-9]{6,9}$/.test(number.toUpperCase());
    }

    // Add validation for other document types
    return true;
  }

  private async scheduleExpirationAlert(document: TravelerDocument): Promise<void> {
    const alertDate = new Date(document.expirationDate);
    alertDate.setMonth(alertDate.getMonth() - 3); // Alert 3 months before

    if (alertDate > new Date()) {
      await this.schedulerService.schedule({
        job: 'documentExpirationAlert',
        at: alertDate,
        data: { documentId: document.id },
      });
    }
  }
}
```

### Document Expiration Monitoring

```typescript
export class DocumentExpirationService {
  async checkExpiringDocuments(): Promise<void> {
    const threeMonthsFromNow = new Date();
    threeMonthsFromNow.setMonth(threeMonthsFromNow.getMonth() + 3);

    const expiringDocuments =
      await this.documentRepository.findExpiringBefore(threeMonthsFromNow);

    for (const document of expiringDocuments) {
      if (!document.expirationAlertSent) {
        await this.sendExpirationAlert(document);

        await this.documentRepository.update(document.id, {
          expirationAlertSent: true,
        });
      }
    }
  }

  private async sendExpirationAlert(document: TravelerDocument): Promise<void> {
    const traveler = await this.travelerRepository.findById(document.travelerId);

    const monthsUntilExpiry = this.getMonthsUntil(new Date(), document.expirationDate);

    await this.notificationService.send({
      userId: traveler.userId,
      type: 'document_expiring',
      channel: 'email',
      priority: monthsUntilExpiry <= 1 ? 'high' : 'medium',
      data: {
        travelerName: `${traveler.firstName} ${traveler.lastName}`,
        documentType: document.type,
        expirationDate: document.expirationDate,
        monthsUntilExpiry,
        renewalUrl: `${process.env.APP_URL}/travelers/${traveler.id}/documents/${document.id}`,
      },
    });
  }

  private getMonthsUntil(from: Date, to: Date): number {
    const months = (to.getFullYear() - from.getFullYear()) * 12;
    return months + to.getMonth() - from.getMonth();
  }
}
```

---

## Companion Management

### Companion Profiles

Companions are travelers with a "self" relationship to the user, allowing users to maintain profiles for family members and frequent travel companions.

```typescript
export class CompanionService {
  async addCompanion(
    userId: string,
    data: Omit<TravelerProfile, 'id' | 'userId' | 'createdAt' | 'updatedAt'>
  ): Promise<TravelerProfile> {
    // Set relationship explicitly
    const profile = await this.travelerService.createProfile(userId, {
      ...data,
      relationship: data.relationship || 'other',
      isPrimary: false,
    });

    return profile;
  }

  async linkCompanion(
    userId: string,
    email: string,
    relationship: TravelerProfile['relationship']
  ): Promise<TravelerProfile> {
    // Find existing user by email
    const otherUser = await this.userService.findByEmail(email);

    if (!otherUser) {
      throw new NotFoundError('User not found');
    }

    // Check if already linked
    const existing = await this.travelerRepository.findByUserIdAndLinkedUser(
      userId,
      otherUser.id
    );

    if (existing) {
      throw new ConflictError('User already linked as companion');
    }

    // Create companion profile linking to other user
    const profile = await this.travelerRepository.create({
      userId,
      type: 'adult',
      relationship,
      linkedUserId: otherUser.id,
      firstName: otherUser.firstName,
      lastName: otherUser.lastName,
      email: otherUser.email,
      dateOfBirth: otherUser.dateOfBirth,
      nationality: otherUser.nationality,
      citizenship: otherUser.citizenship,
    });

    // Send notification to other user
    await this.notificationService.send({
      userId: otherUser.id,
      type: 'companion_link_request',
      channel: 'email',
      data: {
        requestorName: await this.getUserName(userId),
        relationship,
      },
    });

    return profile;
  }

  async unlinkCompanion(
    userId: string,
    travelerId: string
  ): Promise<void> {
    const profile = await this.travelerService.getProfile(userId, travelerId);

    if (!profile.linkedUserId) {
      throw new ValidationError('Not a linked companion');
    }

    await this.travelerRepository.delete(travelerId);
  }
}
```

### Dependent Management

Special handling for children and other dependents with additional safety features.

```typescript
export class DependentService {
  async addChild(
    userId: string,
    data: Omit<TravelerProfile, 'id' | 'userId' | 'createdAt' | 'updatedAt' | 'type'> & {
      type: 'child' | 'infant';
    }
  ): Promise<TravelerProfile> {
    // Validate child/infant specific requirements
    this.validateChildData(data);

    // Set relationship to child
    const profile = await this.travelerService.createProfile(userId, {
      ...data,
      type: data.type,
      relationship: 'child',
    });

    // Add parental consent reminder for minors
    if (this.isMinor(data.dateOfBirth)) {
      await this.scheduleParentalConsentReminder(profile);
    }

    return profile;
  }

  async updateGuardianInformation(
    userId: string,
    travelerId: string,
    guardianData: GuardianInformation
  ): Promise<void> {
    const profile = await this.travelerService.getProfile(userId, travelerId);

    if (profile.relationship !== 'child') {
      throw new ValidationError('Guardian info only for child profiles');
    }

    await this.travelerRepository.update(travelerId, {
      guardianData: this.encryptGuardianData(guardianData),
    });
  }

  private validateChildData(data: Partial<TravelerProfile>): void {
    if (!data.dateOfBirth) {
      throw new ValidationError('Date of birth required for children');
    }

    const age = this.calculateAge(data.dateOfBirth, new Date());

    if (age > 17) {
      throw new ValidationError('Use adult profile for travelers 18+');
    }

    // For international travel, children need passports
    if (!data.documents?.some(d => d.type === 'passport')) {
      // This will trigger a document requirement notification
    }
  }

  private isMinor(dateOfBirth: Date): boolean {
    const age = this.calculateAge(dateOfBirth, new Date());
    return age < 18;
  }

  private async scheduleParentalConsentReminder(profile: TravelerProfile): Promise<void> {
    // Reminder for unaccompanied minor travel consent
    await this.schedulerService.schedule({
      job: 'parentalConsentReminder',
      at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 1 week
      data: { travelerId: profile.id },
    });
  }

  private calculateAge(birthDate: Date, currentDate: Date): number {
    let age = currentDate.getFullYear() - birthDate.getFullYear();
    const monthDiff = currentDate.getMonth() - birthDate.getMonth();

    if (
      monthDiff < 0 ||
      (monthDiff === 0 && currentDate.getDate() < birthDate.getDate())
    ) {
      age--;
    }

    return age;
  }

  private encryptGuardianData(data: GuardianInformation): string {
    // Encrypt guardian information for privacy
    return this.cryptoService.encrypt(JSON.stringify(data));
  }
}
```

---

## Loyalty Programs

### Loyalty Membership Management

```typescript
export class LoyaltyService {
  async getMemberships(travelerId: string): Promise<LoyaltyMembership[]> {
    return this.loyaltyRepository.findByTravelerId(travelerId);
  }

  async addMembership(
    userId: string,
    travelerId: string,
    data: Omit<LoyaltyMembership, 'id' | 'travelerId' | 'createdAt' | 'updatedAt'>
  ): Promise<LoyaltyMembership> {
    // Verify ownership
    await this.travelerService.getProfile(userId, travelerId);

    // Validate program exists
    const program = await this.programRepository.findById(data.program);
    if (!program) {
      throw new ValidationError('Invalid loyalty program');
    }

    // Check for duplicate
    const existing = await this.loyaltyRepository.findExisting(
      travelerId,
      data.program,
      data.membershipNumber
    );

    if (existing) {
      throw new ConflictError('Membership already exists');
    }

    // If primary, clear others
    if (data.isPrimary) {
      await this.loyaltyRepository.clearPrimary(travelerId, data.program);
    }

    return this.loyaltyRepository.create({
      ...data,
      travelerId,
    });
  }

  async syncMembership(
    userId: string,
    membershipId: string
  ): Promise<LoyaltyMembership> {
    const membership = await this.getMembership(userId, membershipId);
    const program = await this.programRepository.findById(membership.program);

    // Fetch latest data from loyalty program API
    const syncData = await this.loyaltyApiService.fetchMembershipData(
      program.code,
      membership.membershipNumber
    );

    // Update membership
    const updated = await this.loyaltyRepository.update(membershipId, {
      tier: syncData.tier,
      points: syncData.points,
      status: syncData.status,
      lastSyncedAt: new Date(),
    });

    return updated;
  }

  async getMatchingPrograms(
    userId: string,
    bookingContext: BookingContext
  ): Promise<LoyaltyProgramMatch[]> {
    const profiles = await this.travelerRepository.findByUserId(userId);
    const matches: LoyoyaltyProgramMatch[] = [];

    for (const profile of profiles) {
      for (const membership of profile.loyaltyMemberships) {
        const program = await this.programRepository.findById(membership.program);

        // Check if program applies to this booking
        if (this.isProgramApplicable(program, bookingContext)) {
          matches.push({
            program,
            membership,
            travelerId: profile.id,
            benefits: this.getBenefitsForTier(membership),
          });
        }
      }
    }

    return matches;
  }

  async applyLoyaltyBenefits(
    bookingId: string,
    memberships: LoyaltyMembership[]
  ): Promise<AppliedBenefit[]> {
    const benefits: AppliedBenefit[] = [];

    for (const membership of memberships) {
      const program = await this.programRepository.findById(membership.program);
      const tierBenefits = this.getBenefitsForTier(membership);

      for (const benefit of tierBenefits) {
        if (benefit.type === 'points_earn') {
          // Calculate points earned
          const points = this.calculatePointsEarned(bookingId, benefit.multiplier);
          benefits.push({
            program: program.name,
            type: 'points_earn',
            value: points,
            description: `Earn ${points} ${program.name} points`,
          });
        } else if (benefit.type === 'discount') {
          // Apply discount
          const discount = await this.applyDiscount(bookingId, benefit);
          benefits.push({
            program: program.name,
            type: 'discount',
            value: discount.amount,
            description: `${discount.percent}% discount applied`,
          });
        }
      }
    }

    return benefits;
  }

  private isProgramApplicable(
    program: LoyaltyProgram,
    context: BookingContext
  ): boolean {
    // Check if program type matches booking
    if (context.suppliers) {
      const relevantSuppliers = {
        airline: context.suppliers.filter(s => s.type === 'airline'),
        hotel: context.suppliers.filter(s => s.type === 'hotel'),
        car_rental: context.suppliers.filter(s => s.type === 'car_rental'),
      };

      switch (program.type) {
        case 'airline':
          return relevantSuppliers.airline.length > 0;
        case 'hotel':
          return relevantSuppliers.hotel.length > 0;
        case 'car_rental':
          return relevantSuppliers.car_rental.length > 0;
      }
    }

    return false;
  }

  private getBenefitsForTier(membership: LoyaltyMembership): Benefit[] {
    // Benefits are defined per program and tier
    return this.benefitRepository.findByProgramAndTier(
      membership.program,
      membership.tier
    );
  }

  private calculatePointsEarned(bookingId: string, multiplier: number): number {
    // Calculate base points from booking value
    const booking = await this.bookingRepository.findById(bookingId);
    const basePoints = Math.floor(booking.totalPrice / 10); // Example: 1 point per $10

    return Math.floor(basePoints * multiplier);
  }

  private async applyDiscount(
    bookingId: string,
    benefit: Benefit
  ): Promise<{ amount: number; percent: number }> {
    // Apply loyalty discount to booking
    return this.pricingService.applyLoyaltyDiscount(
      bookingId,
      benefit.discountPercent
    );
  }
}
```

### Supported Loyalty Programs

```typescript
// Pre-configured loyalty programs
const LOYALTY_PROGRAMS: LoyaltyProgram[] = [
  {
    id: 'aa-aadvantage',
    name: 'AAdvantage',
    code: 'AA',
    type: 'airline',
    iconUrl: '/loyalty/aa.png',
    websiteUrl: 'https://www.aa.com',
  },
  {
    id: 'delta-skymiles',
    name: 'SkyMiles',
    code: 'DL',
    type: 'airline',
    iconUrl: '/loyalty/delta.png',
    websiteUrl: 'https://www.delta.com',
  },
  {
    id: 'united-mileageplus',
    name: 'MileagePlus',
    code: 'UA',
    type: 'airline',
    iconUrl: '/loyalty/united.png',
    websiteUrl: 'https://www.united.com',
  },
  {
    id: 'marriott-bonvoy',
    name: 'Bonvoy',
    code: 'MR',
    type: 'hotel',
    iconUrl: '/loyalty/marriott.png',
    websiteUrl: 'https://www.marriott.com',
  },
  {
    id: 'hilton-honors',
    name: 'Hilton Honors',
    code: 'HH',
    type: 'hotel',
    iconUrl: '/loyalty/hilton.png',
    websiteUrl: 'https://www.hilton.com',
  },
  {
    id: 'hertz-gold-plus',
    name: 'Gold Plus Rewards',
    code: 'HZ',
    type: 'car_rental',
    iconUrl: '/loyalty/hertz.png',
    websiteUrl: 'https://www.hertz.com',
  },
];
```

---

## Travel History

### History Tracking

```typescript
export class TravelHistoryService {
  async getHistory(
    travelerId: string,
    options: HistoryQueryOptions = {}
  ): Promise<TravelHistoryEntry[]> {
    const { limit = 20, offset = 0, year, country } = options;

    return this.historyRepository.findByTravelerId(travelerId, {
      limit,
      offset,
      filters: {
        year,
        country,
      },
      orderBy: 'departureDate',
      order: 'desc',
    });
  }

  async getStats(travelerId: string): Promise<TravelStats> {
    const history = await this.historyRepository.findByTravelerId(travelerId);

    const countries = new Set<string>();
    const cities = new Set<string>();
    const tripsByYear = new Map<number, number>();
    const tripsByType = new Map<string, number>();

    for (const entry of history) {
      countries.add(entry.destinationCountry);
      cities.add(`${entry.destinationCity}, ${entry.destinationCountry}`);

      const year = entry.departureDate.getFullYear();
      tripsByYear.set(year, (tripsByYear.get(year) || 0) + 1);

      tripsByType.set(
        entry.tripType || 'unknown',
        (tripsByType.get(entry.tripType || 'unknown') || 0) + 1
      );
    }

    return {
      totalTrips: history.length,
      countriesVisited: countries.size,
      citiesVisited: cities.size,
      tripsByYear: Array.from(tripsByYear.entries()).map(([year, count]) => ({
        year,
        count,
      })),
      tripsByType: Array.from(tripsByType.entries()).map(([type, count]) => ({
        type,
        count,
      })),
    };
  }

  async addToHistory(
    travelerId: string,
    bookingId: string
  ): Promise<void> {
    const booking = await this.bookingRepository.findById(bookingId);

    // Extract trip information from booking
    const destinations = booking.destinations;

    for (const destination of destinations) {
      await this.historyRepository.create({
        travelerId,
        bookingId,
        destinationCountry: destination.countryCode,
        destinationCity: destination.city,
        departureDate: destination.startDate,
        returnDate: destination.endDate,
        tripType: booking.tripType,
      });
    }
  }

  async getDestinationRankings(
    travelerId: string
  ): Promise<DestinationRanking[]> {
    const history = await this.historyRepository.findByTravelerId(travelerId);

    const rankings = new Map<string, number>();

    for (const entry of history) {
      const key = `${entry.destinationCity}, ${entry.destinationCountry}`;
      rankings.set(key, (rankings.get(key) || 0) + 1);
    }

    return Array.from(rankings.entries())
      .map(([destination, visits]) => ({ destination, visits }))
      .sort((a, b) => b.visits - a.visits)
      .slice(0, 10);
  }
}
```

---

## Regulatory Compliance

### Document Requirements by Destination

```typescript
export class ComplianceService {
  async getRequiredDocuments(
    travelerId: string,
    destinationCountry: string,
    tripDate: Date
  ): Promise<RequiredDocument[]> {
    const traveler = await this.travelerRepository.findById(travelerId);
    const requirements: RequiredDocument[] = [];

    // Passport requirement
    const passport = traveler.documents.find(d => d.type === 'passport');
    const passportRequirement = this.getPassportRequirement(
      traveler.nationality,
      destinationCountry,
      tripDate
    );

    requirements.push({
      type: 'passport',
      required: true,
      description: passportRequirement.description,
      validityPeriod: passportRequirement.validityMonths,
      hasValidDocument: this.isDocumentValid(passport, tripDate, passportRequirement.validityMonths),
    });

    // Visa requirement
    const visaRequirement = await this.getVisaRequirement(
      traveler.nationality,
      destinationCountry,
      traveler.type
    );

    if (visaRequirement.required) {
      const visa = traveler.documents.find(d =>
        d.type === 'visa' &&
        d.issuingCountry === destinationCountry
      );

      requirements.push({
        type: 'visa',
        required: true,
        description: visaRequirement.description,
        validityPeriod: visaRequirement.validityMonths,
        hasValidDocument: this.isDocumentValid(visa, tripDate, 0),
        applicationUrl: visaRequirement.applicationUrl,
      });
    }

    // Additional documents based on traveler type
    if (traveler.type === 'child' && !traveler.linkedUserId) {
      requirements.push({
        type: 'parental_consent',
        required: true,
        description: 'Parental consent for minor travel',
        hasValidDocument: false,
      });
    }

    return requirements;
  }

  private getPassportRequirement(
    nationality: string,
    destination: string,
    tripDate: Date
  ): PassportRequirement {
    // Passport validity requirements by destination
    const requirements: Record<string, number> = {
      // Schengen countries: 3 months beyond departure
      'AT': 3, 'BE': 3, 'HR': 3, 'CZ': 3, 'DK': 3, 'EE': 3, 'FI': 3,
      'FR': 3, 'DE': 3, 'GR': 3, 'HU': 3, 'IS': 3, 'IT': 3, 'LV': 3,
      'LT': 3, 'LU': 3, 'MT': 3, 'NL': 3, 'NO': 3, 'PL': 3, 'PT': 3,
      'SK': 3, 'SI': 3, 'ES': 3, 'SE': 3, 'CH': 3,

      // Asia: 6 months
      'CN': 6, 'JP': 6, 'TH': 6, 'VN': 6, 'ID': 6,

      // Default: 6 months
    };

    const months = requirements[destination] || 6;

    return {
      description: `Passport must be valid for at least ${months} months beyond departure date`,
      validityMonths: months,
    };
  }

  private async getVisaRequirement(
    nationality: string,
    destination: string,
    travelerType: TravelerType
  ): Promise<VisaRequirement> {
    // Check visa requirements database
    const requirement = await this.visaRepository.find({
      nationality,
      destination,
    });

    if (requirement) {
      return {
        required: requirement.required,
        description: requirement.description,
        validityMonths: requirement.validityMonths,
        applicationUrl: requirement.applicationUrl,
      };
    }

    // Default: check if same as nationality (no visa needed)
    return {
      required: nationality !== destination,
      description: nationality === destination
        ? 'No visa required for citizens'
        : 'Visa may be required - check with embassy',
      validityMonths: 0,
    };
  }

  private isDocumentValid(
    document: TravelerDocument | undefined,
    tripDate: Date,
    additionalMonths: number
  ): boolean {
    if (!document || !document.isVerified) {
      return false;
    }

    const requiredDate = new Date(tripDate);
    requiredDate.setMonth(requiredDate.getMonth() + additionalMonths);

    return document.expirationDate > requiredDate;
  }
}
```

---

## API Endpoints

### Traveler Profile Endpoints

```
GET    /travelers
POST   /travelers
GET    /travelers/:travelerId
PATCH  /travelers/:travelerId
DELETE /travelers/:travelerId
POST   /travelers/:travelerId/primary
GET    /travelers/search?q=
GET    /travelers/suggestions
```

### Document Endpoints

```
GET    /travelers/:travelerId/documents
POST   /travelers/:travelerId/documents
GET    /travelers/:travelerId/documents/:documentId
PATCH  /travelers/:travelerId/documents/:documentId
DELETE /travelers/:travelerId/documents/:documentId
POST   /travelers/:travelerId/documents/:documentId/verify
GET    /travelers/:travelerId/documents/:documentId/images/:side
POST   /travelers/:travelerId/documents/:documentId/share
```

### Loyalty Endpoints

```
GET    /travelers/:travelerId/loyalty
POST   /travelers/:travelerId/loyalty
PATCH  /travelers/:travelerId/loyalty/:membershipId
DELETE /travelers/:travelerId/loyalty/:membershipId
POST   /travelers/:travelerId/loyalty/:membershipId/sync
```

### Travel History Endpoints

```
GET    /travelers/:travelerId/history
GET    /travelers/:travelerId/history/stats
GET    /travelers/:travelerId/history/rankings
```

### Compliance Endpoints

```
GET    /travelers/:travelerId/compliance/:destination?date=
```

---

**Series Complete:** The User Accounts series (5 documents) is now complete. Next series: [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md)
