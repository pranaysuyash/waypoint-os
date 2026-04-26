# Internationalization Part 4: Regional Compliance

> GDPR, data privacy, and regulatory requirements for global travel operations

**Series:** Internationalization and Localization
**Previous:** [Part 3: Currency and Payments](./INTERNATIONALIZATION_03_CURRENCY.md)
**Next:** N/A (Series Complete)

---

## Table of Contents

1. [Overview](#overview)
2. [GDPR and Data Privacy](#gdpr-and-data-privacy)
3. [Consumer Protection Laws](#consumer-protection-laws)
4. [Travel Industry Regulations](#travel-industry-regulations)
5. [Tax Compliance](#tax-compliance)
6. [Data Residency](#data-residency)
7. [Cookie Consent](#cookie-consent)
8. [Age Verification](#age-verification)
9. [Accessibility Standards](#accessibility-standards)
10. [Implementation](#implementation)

---

## Overview

Travel agencies operating globally must navigate a complex web of regional regulations:

| Region | Key Concerns |
|--------|--------------|
| **EU/UK** | GDPR, Package Travel Regulations, VAT |
| **US** | CCPA, state privacy laws, seller of travel |
| **India** | DPDP Act, TCS, GST |
| **Brazil** | LGPD, consumer code |
| **China** | PIPL, data localization |
| **Australia** | Privacy Act, ACL |

---

## GDPR and Data Privacy

### GDPR Compliance Framework

```typescript
// lib/compliance/gdpr/gdpr-manager.ts

interface GDPRComplianceConfig {
  regions: GDPRRegion[];
  consentManager: ConsentManagerConfig;
  dataSubjectRights: DataSubjectRightsConfig;
  breachDetection: BreachDetectionConfig;
}

interface GDPRRegion {
  code: 'EU' | 'UK' | 'NON_EU';
  requiresExplicitConsent: boolean;
  dataBreacherNotificationThreshold: number; // hours
  dpiaRequired: boolean;
  representativeRequired: boolean;
}

class GDPRManager {
  private config: GDPRComplianceConfig;
  private consentStore: ConsentStore;
  private dataMapper: GDPRDataMapper;

  /**
   * Check if GDPR applies to current user
   */
  isGDPRApplicable(userId: string): boolean {
    const user = this.getUser(userId);
    const region = this.detectRegion(user);

    return ['EU', 'UK'].includes(region);
  }

  /**
   * Get lawful basis for processing
   *
   * Legal bases:
   * - consent: Freely given, specific, informed, unambiguous
   * - contract: Performance of contract
   * - legal_obligation: Compliance with law
   * - vital_interests: Protect life
   * - public_task: Public interest task
   * - legitimate_interestes: Permitted business interests
   */
  getLawfulBasis(dataType: DataType, purpose: DataPurpose): LawfulBasis {
    const basisMatrix: Record<DataType, Record<DataPurpose, LawfulBasis>> = {
      personal: {
        booking: 'contract',
        marketing: 'consent',
        analytics: 'legitimate_interests',
        support: 'contract',
        payment: 'contract',
      },
      financial: {
        booking: 'contract',
        marketing: 'consent',
        analytics: 'legitimate_interests',
        support: 'contract',
        payment: 'legal_obligation', // AML, tax reporting
      },
      travel: {
        booking: 'contract',
        marketing: 'consent',
        analytics: 'legitimate_interests',
        support: 'contract',
        payment: 'contract',
      },
      biometric: {
        booking: 'consent', // Explicit consent required
        marketing: 'consent',
        analytics: 'consent',
        support: 'consent',
        payment: 'not_allowed',
      },
    };

    return basisMatrix[dataType]?.[purpose] || 'consent';
  }

  /**
   * Handle data subject access request (DSAR)
   */
  async handleAccessRequest(userId: string, requestId: string): Promise<DataSubjectReport> {
    // 1. Verify identity
    const verified = await this.verifyIdentity(userId, requestId);
    if (!verified) {
      throw new Error('Identity verification failed');
    }

    // 2. Collect all personal data
    const userData = await this.collectAllUserData(userId);

    // 3. Get processing activities
    const processingActivities = await this.getProcessingActivities(userId);

    // 4. Get data sources
    const dataSources = await this.getDataSources(userId);

    // 5. Get recipients
    const recipients = await this.getDataRecipients(userId);

    // 6. Get retention periods
    const retentionPeriods = await this.getRetentionPeriods(userId);

    // 7. Generate report (machine-readable format preferred)
    return {
      requestId,
      generatedAt: new Date().toISOString(),
      subject: userData,
      processingActivities,
      dataSources,
      recipients,
      retentionPeriods,
      automatedDecisions: await this.getAutomatedDecisions(userId),
    };
  }

  /**
   * Handle right to erasure (right to be forgotten)
   */
  async handleErasureRequest(userId: string, requestId: string): Promise<ErasureReport> {
    const verified = await this.verifyIdentity(userId, requestId);
    if (!verified) {
      throw new Error('Identity verification failed');
    }

    const erasures: ErasureResult[] = [];

    // Check for legal holds or retention requirements
    const canErase = await this.checkErasureEligibility(userId);
    if (!canErase.eligible) {
      throw new Error(`Erasure not permitted: ${canErase.reason}`);
    }

    // Erase from all systems
    const systems = ['database', 'analytics', 'cdn', 'backup', 'logs'];

    for (const system of systems) {
      try {
        const result = await this.eraseFromSystem(system, userId);
        erasures.push(result);
      } catch (error) {
        erasures.push({
          system,
          success: false,
          error: error.message,
        });
      }
    }

    // Verify erasure
    const remainingData = await this.scanForRemainingData(userId);

    return {
      requestId,
      erasures,
      remainingData,
      completedAt: new Date().toISOString(),
    };
  }

  /**
   * Handle right to rectification
   */
  async handleRectificationRequest(
    userId: string,
    corrections: DataCorrection[]
  ): Promise<RectificationReport> {
    const results: RectificationResult[] = [];

    for (const correction of corrections) {
      try {
        // Validate correction
        const validated = await this.validateCorrection(correction);

        // Apply correction
        await this.applyCorrection(userId, validated);

        // Log change
        await this.logDataChange(userId, correction);

        results.push({
          field: correction.field,
          success: true,
          previousValue: correction.previousValue,
          newValue: correction.newValue,
        });
      } catch (error) {
        results.push({
          field: correction.field,
          success: false,
          error: error.message,
        });
      }
    }

    return {
      userId,
      results,
      completedAt: new Date().toISOString(),
    };
  }

  /**
   * Handle right to portability
   */
  async handlePortabilityRequest(userId: string, format: 'json' | 'xml' | 'csv'): Promise<PortableData> {
    const userData = await this.collectAllUserData(userId);

    // Structure in common, machine-readable format
    const portableData = {
      personal: this.sanitizePersonalData(userData.personal),
      bookings: userData.bookings,
      payments: userData.payments,
      preferences: userData.preferences,
      documents: userData.documents,
    };

    // Generate in requested format
    switch (format) {
      case 'json':
        return JSON.stringify(portableData, null, 2);
      case 'xml':
        return this.toXML(portableData);
      case 'csv':
        return this.toCSV(portableData);
    }
  }

  /**
   * Handle right to object
   */
  async handleObjectionRequest(
    userId: string,
    processingActivities: string[]
  ): Promise<ObjectionReport> {
    const results: ObjectionResult[] = [];

    for (const activity of processingActivities) {
      // Check if objection is valid
      const canObject = await this.canObjectToProcessing(userId, activity);

      if (canObject.allowed) {
        await this.stopProcessing(userId, activity);
        results.push({
          activity,
          success: true,
          action: 'stopped',
        });
      } else {
        results.push({
          activity,
          success: false,
          reason: canObject.reason,
        });
      }
    }

    return {
      userId,
      results,
      completedAt: new Date().toISOString(),
    };
  }

  /**
   * Data Protection Impact Assessment (DPIA)
   */
  async conductDPIA(project: DataProcessingProject): Promise<DPIAReport> {
    // High-risk processing requires DPIA:
    // - Systematic monitoring
    // - Large scale processing of special categories
    // - Biometric data
    // - Genetic data
    // - Profiling with legal effects

    const riskLevel = await this.assessRiskLevel(project);

    if (riskLevel === 'low') {
      return {
        project,
        riskLevel,
        requiresDPIA: false,
        recommendation: 'Standard safeguards sufficient',
      };
    }

    // Full DPIA required
    return {
      project,
      riskLevel,
      requiresDPIA: true,
      assessment: {
        processingDescription: project.description,
        purposes: project.purposes,
        dataTypes: project.dataTypes,
        subjects: project.subjects,
        recipients: project.recipients,
        transfers: project.transfers,
        risks: await this.identifyRisks(project),
        mitigations: await this.identifyMitigations(project),
        likelihood: await this.assessLikelihood(project),
        severity: await this.assessSeverity(project),
        residualRisk: await this.calculateResidualRisk(project),
      },
    };
  }
}
```

### Consent Management

```typescript
// lib/compliance/consent/consent-manager.ts

interface ConsentConfiguration {
  version: string;
  lastUpdated: string;
  purposes: ConsentPurpose[];
  vendors: ConsentVendor[];
  legitimateInterests: LegitimateInterest[];
}

interface ConsentPurpose {
  id: string;
  name: string;
  description: string;
  category: 'essential' | 'functional' | 'analytics' | 'marketing';
  required: boolean;
  retentionPeriod?: number; // days
  regions: string[];
}

class ConsentManager {
  /**
   * Initialize consent banner
   */
  initializeBanner(config: ConsentBannerConfig): void {
    const shouldShow = this.shouldShowBanner(config);

    if (shouldShow) {
      this.renderBanner(config);
    }
  }

  /**
   * Check if banner should be shown
   */
  private shouldShowBanner(config: ConsentBannerConfig): boolean {
    // Don't show if already consented
    const existingConsent = this.getStoredConsent();
    if (existingConsent && this.isConsentValid(existingConsent)) {
      return false;
    }

    // Check if user is in region requiring consent
    const userRegion = this.detectUserRegion();
    const requiresConsent = this.regionRequiresConsent(userRegion);

    return requiresConsent;
  }

  /**
   * Get required consents by region
   */
  getRequiredConsents(region: string): ConsentPurpose[] {
    const regionMap: Record<string, string[]> = {
      EU: ['essential', 'functional', 'analytics', 'marketing'],
      UK: ['essential', 'functional', 'analytics', 'marketing'],
      US: ['essential'],
      CA: ['essential', 'functional'],
      BR: ['essential', 'functional', 'analytics'],
      IN: ['essential'],
    };

    const requiredCategories = regionMap[region] || ['essential'];

    return this.config.purposes.filter(p =>
      requiredCategories.includes(p.category)
    );
  }

  /**
   * Grant consent
   */
  async grantConsent(
    userId: string,
    consents: Record<string, boolean>,
    metadata: ConsentMetadata
  ): Promise<void> {
    // Record timestamp
    const grantedAt = new Date().toISOString();

    // Store consents
    await this.storeConsent({
      userId,
      consents,
      grantedAt,
      metadata,
      version: this.config.version,
      ip: metadata.ip,
      userAgent: metadata.userAgent,
    });

    // Fire consent granted events
    for (const [purpose, granted] of Object.entries(consents)) {
      if (granted) {
        this.emitConsentEvent(purpose, 'granted');
      }
    }

    // Update tracking scripts
    this.updateTrackingScripts(consents);
  }

  /**
   * Withdraw consent
   */
  async withdrawConsent(
    userId: string,
    purpose: string,
    metadata: ConsentMetadata
  ): Promise<void> {
    // Update consent record
    await this.updateConsent(userId, purpose, false);

    // Fire withdrawal event
    this.emitConsentEvent(purpose, 'withdrawn');

    // Handle data deletion if required
    if (this.purposeRequiresDeletion(purpose)) {
      await this.deleteDataForPurpose(userId, purpose);
    }

    // Update tracking scripts
    const currentConsents = this.getCurrentConsents(userId);
    this.updateTrackingScripts(currentConsents);
  }

  /**
   * Check if consent exists for purpose
   */
  hasConsent(userId: string, purpose: string): boolean {
    const consent = this.getStoredConsent();

    if (!consent) {
      // Check if essential (doesn't require explicit consent)
      const purposeConfig = this.config.purposes.find(p => p.id === purpose);
      return purposeConfig?.category === 'essential';
    }

    return consent.consents[purpose] === true;
  }

  /**
   * Get granular consent status
   */
  getConsentStatus(userId: string): ConsentStatus {
    const consent = this.getStoredConsent();

    if (!consent) {
      return {
        status: 'pending',
        purposes: this.config.purposes.map(p => ({
          id: p.id,
          granted: p.category === 'essential',
          grantedAt: null,
        })),
      };
    }

    return {
      status: 'granted',
      purposes: this.config.purposes.map(p => ({
        id: p.id,
        granted: consent.consents[p.id],
        grantedAt: consent.consents[p.id] ? consent.grantedAt : null,
      })),
      version: consent.version,
      grantedAt: consent.grantedAt,
    };
  }
}
```

### Data Breach Management

```typescript
// lib/compliance/breach/breach-manager.ts

interface DataBreach {
  id: string;
  detectedAt: Date;
  severity: 'low' | 'medium' | 'high';
  dataTypes: DataType[];
  affectedUsers: number;
  description: string;
  rootCause: string;
  containmentActions: string[];
  mitigationActions: string[];
  notificationStatus: NotificationStatus;
}

class DataBreachManager {
  /**
   * Report and manage data breach
   */
  async handleBreach(breach: Omit<DataBreach, 'id'>): Promise<string> {
    const breachId = this.generateBreachId();

    // 1. Immediate containment
    await this.containBreach(breach);

    // 2. Assess severity and risk
    const riskAssessment = await this.assessRisk(breach);

    // 3. Determine notification requirements
    const notificationReq = this.getNotificationRequirements(breach, riskAssessment);

    // 4. Notify supervisory authority (72 hours for GDPR)
    if (notificationReq.authority) {
      await this.notifyAuthority(breachId, breach, notificationReq.authority);
    }

    // 5. Notify affected data subjects
    if (notificationReq.subjects) {
      await this.notifySubjects(breach, notificationReq.subjects);
    }

    // 6. Document all actions
    await this.documentBreach(breachId, {
      breach,
      riskAssessment,
      notificationReq,
      actionsTaken: [],
    });

    return breachId;
  }

  /**
   * Get notification requirements by region
   */
  private getNotificationRequirements(
    breach: DataBreach,
    risk: RiskAssessment
  ): NotificationRequirements {
    const requirements: NotificationRequirements = {
      authority: null,
      subjects: null,
      timeline: null,
    };

    // GDPR: 72 hours for authority, "without undue delay" for subjects
    if (this.affectsEU(breach)) {
      if (this.isHighRisk(risk)) {
        requirements.authority = {
          deadline: '72 hours',
          format: 'GDPR_breach_notification',
          recipient: this.getSupervisoryAuthority(),
        };
        requirements.subjects = {
          deadline: 'without undue delay',
          format: 'GDPR_subject_notification',
          threshold: this.getSubjectNotificationThreshold(risk),
        };
      }
    }

    // CCPA: No breach notification (state laws vary)
    // Many US states have breach notification laws

    // LGPD (Brazil): 2 working days for authority
    if (this.affectsBrazil(breach)) {
      requirements.authority = {
        deadline: '2 working days',
        format: 'LGPD_breach_notification',
        recipient: 'ANPD',
      };
    }

    // PIPL (China): Immediate notification
    if (this.affectsChina(breach)) {
      requirements.authority = {
        deadline: 'immediate',
        format: 'PIPL_breach_notification',
        recipient: 'CAC',
      };
    }

    return requirements;
  }

  /**
   * Assess breach risk
   */
  private async assessRisk(breach: DataBreach): Promise<RiskAssessment> {
    let score = 0;

    // Data type sensitivity
    const sensitivityScores: Record<DataType, number> = {
      biometric: 100,
      financial: 80,
      health: 90,
      travel: 60,
      personal: 40,
      contact: 20,
    };

    for (const type of breach.dataTypes) {
      score += sensitivityScores[type] || 0;
    }

    // Volume of affected users
    if (breach.affectedUsers > 10000) score += 50;
    else if (breach.affectedUsers > 1000) score += 30;
    else if (breach.affectedUsers > 100) score += 10;

    // Data accessibility
    if (breach.description.includes('unencrypted')) score += 40;
    if (breach.description.includes('publicly accessible')) score += 50;

    // Special categories
    if (breach.dataTypes.includes('biometric')) score += 30;

    return {
      score,
      level: this.calculateRiskLevel(score),
      likelihood: this.assessLikelihood(breach),
      severity: this.assessSeverity(breach),
    };
  }
}
```

---

## Consumer Protection Laws

### EU Consumer Rights

```typescript
// lib/compliance/consumer/eu-consumer-rights.ts

interface EUConsumerRightsConfig {
  withdrawalPeriod: number; // 14 days default
  refundTimeframe: number; // 14 days
  informationRequirements: InformationRequirement[];
  priceIndication: PriceIndicationConfig;
}

class EUConsumerRightsManager {
  /**
   * Right of withdrawal for online purchases
   */
  async handleWithdrawalRequest(
    bookingId: string,
    reason: string
  ): Promise<WithdrawalResponse> {
    const booking = await this.getBooking(bookingId);

    // Check if within withdrawal period
    const withinPeriod = this.isWithinWithdrawalPeriod(booking);

    if (!withinPeriod) {
      return {
        eligible: false,
        reason: 'Withdrawal period has expired (14 days from booking)',
      };
    }

    // Check exceptions (customized, travel services within cancellation period)
    if (this.isException(booking)) {
      return {
        eligible: false,
        reason: 'This booking type is exempt from withdrawal rights',
      };
    }

    // Process withdrawal
    const refund = await this.processWithdrawal(bookingId);

    return {
      eligible: true,
      refundAmount: refund.amount,
      refundMethod: refund.method,
      refundTimeline: '14 days from withdrawal date',
    };
  }

  /**
   * Price transparency requirements
   */
  validatePriceDisplay(price: PriceDisplay): ValidationResult {
    const errors: string[] = [];

    // Must show total price including all taxes and fees
    if (!price.includesAllTaxes) {
      errors.push('Total price must include all mandatory taxes and fees');
    }

    // Must indicate if additional charges may apply
    if (price.hasOptionalCharges && !price.optionalChargesDisclosed) {
      errors.push('Optional charges must be clearly disclosed');
    }

    // Single price must be most prominent
    if (price.promotesPriceWithoutTaxes) {
      errors.push('Price excluding taxes must not be more prominent than total price');
    }

    // Currency must be clear
    if (!price.currency) {
      errors.push('Currency must be clearly indicated');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Pre-contractual information requirements
   */
  getRequiredInformation(bookingType: BookingType): RequiredInformation[] {
    return [
      {
        category: 'main_characteristics',
        items: [
          'Destination(s)',
          'Duration',
          'Accommodation details',
          'Transport details',
          'Meal arrangements',
        ],
        timing: 'before_booking',
      },
      {
        category: 'price',
        items: [
          'Total price including taxes',
          'Payment schedule',
          'Additional costs',
          'Currency',
        ],
        timing: 'before_booking',
      },
      {
        category: 'cancellation',
        items: [
          'Cancellation policy',
          'Withdrawal rights',
          'Refund policy',
        ],
        timing: 'before_booking',
      },
      {
        category: 'complaints',
        items: [
          'Complaints procedure',
          'Alternative dispute resolution',
          'Contact details',
        ],
        timing: 'before_booking',
      },
    ];
  }
}
```

### Package Travel Regulations

```typescript
// lib/compliance/travel/package-travel-regulations.ts

/**
 * EU Package Travel Directive (PTD) 2015/2302
 *
 * A package is:
 * - Combined transport + accommodation + other service
 * - Sold at inclusive price
 * - Covered by single contract
 * - For same trip or holiday
 */

interface PackageTravelConfig {
  organiserLiability: LiabilityConfig;
  insolvencyProtection: InsolvencyConfig;
  informationRequirements: PTDInformationConfig;
}

class PackageTravelManager {
  /**
   * Check if booking constitutes a package
   */
  isPackage(booking: Booking): boolean {
    const hasTransport = booking.services.some(s =>
      ['flight', 'train', 'bus', 'rental_car'].includes(s.type)
    );
    const hasAccommodation = booking.services.some(s =>
      ['hotel', 'apartment', 'resort'].includes(s.type)
    );
    const hasOtherService = booking.services.some(s =>
      ['excursion', 'tour', 'activity', 'rental'].includes(s.type)
    );

    // Package = transport + accommodation OR transport + other service
    // (if other service accounts for 25%+ of value)
    return (hasTransport && hasAccommodation) ||
           (hasTransport && hasOtherService && this.hasSignificantOtherService(booking));
  }

  /**
   * Package information requirements
   */
  async generatePackageInformation(booking: Booking): Promise<PackageInformation> {
    return {
      organiser: {
        name: booking.organiser.name,
        address: booking.organiser.address,
        contact: booking.organiser.contact,
        email: booking.organiser.email,
      },
      destination: {
        places: booking.services.map(s => s.destination).filter(Boolean),
        itinerary: booking.itinerary,
        duration: booking.duration,
        accommodation: this.getAccommodationDetails(booking),
        transport: this.getTransportDetails(booking),
        meals: this.getMealDetails(booking),
      },
      price: {
        total: booking.totalPrice,
        currency: booking.currency,
        includes: booking.includedItems,
        excludes: booking.excludedItems,
        additionalCharges: booking.additionalCharges,
      },
      payments: {
        schedule: booking.paymentSchedule,
        methods: booking.acceptedMethods,
      },
      cancellation: {
        policy: booking.cancellationPolicy,
        withdrawalRights: this.getWithdrawalRights(booking),
      },
      assistance: {
        emergencyContact: booking.emergencyContact,
        languages: booking.supportedLanguages,
      },
      insurance: {
        travelInsuranceRequired: booking.requiresInsurance,
        offeredInsurance: booking.insuranceOptions,
      },
      insolvencyProtection: {
        protector: booking.insolvencyProtector,
        contact: booking.insolvencyContact,
      },
    };
  }

  /**
   * Package organiser liability
   */
  async handlePackageClaim(claim: PackageClaim): Promise<ClaimResponse> {
    // Organiser is liable for proper performance
    // regardless of whether third parties perform services

    const liability = await this.assessLiability(claim);

    if (liability.organiserLiable) {
      return {
        accepted: true,
        basis: 'Package Travel Directive Article 12',
        remedy: this.determineRemedy(claim),
      };
    }

    // Check for force majeure or extraordinary circumstances
    if (this.isForceMajeure(claim)) {
      return {
        accepted: false,
        reason: 'Extraordinary circumstances beyond organiser control',
      };
    }

    return {
      accepted: false,
      reason: 'Service performed as contracted',
    };
  }
}
```

---

## Travel Industry Regulations

### Seller of Travel Registration

```typescript
// lib/compliance/travel/seller-of-travel.ts

interface SellerOfTravelConfig {
  registrations: StateRegistration[];
  bondRequirements: BondRequirement[];
  disclosureRequirements: DisclosureRequirement[];
}

interface StateRegistration {
  state: string;
  registrationNumber: string;
  expiresAt: Date;
  bondAmount?: number;
  bondCompany?: string;
  trustAccount?: string;
}

class SellerOfTravelManager {
  /**
   * US states requiring Seller of Travel registration
   */
  private readonly requiredStates = [
    'CA', // California - Seller of Travel
    'FL', // Florida - Seller of Travel
    'HI', // Hawaii - Travel Agency
    'IA', // Iowa - Travel Agency
    'NV', // Nevada - Retail Seller of Travel
    'OH', // Ohio - Travel Agency
    'OR', // Oregon - Travel Agency
    'RI', // Rhode Island - Tour Planner
    'VA', // Virginia - Travel Agency
    'WA', // Washington - Travel Agency
  ];

  /**
   * Get required registration for user's state
   */
  getRequiredRegistration(state: string): StateRegistration | null {
    if (!this.requiredStates.includes(state)) {
      return null;
    }

    return this.registrations.find(r => r.state === state) || null;
  }

  /**
   * Generate required disclosures
   */
  generateDisclosures(state: string): Disclosure[] {
    const disclosures: Disclosure[] = [];

    // California disclosure
    if (state === 'CA') {
      disclosures.push({
        type: 'seller_of_travel',
        text: `California Seller of Travel Registration Number ${this.getRegistrationNumber('CA')}`,
        placement: 'footer',
        required: true,
      });
    }

    // Florida disclosure
    if (state === 'FL') {
      disclosures.push({
        type: 'seller_of_travel',
        text: `Florida Seller of Travel Ref. No. ${this.getRegistrationNumber('FL')}`,
        placement: 'footer',
        required: true,
      });
    }

    // General consumer disclosures
    disclosures.push({
      type: 'consumer_rights',
      text: 'As a travel agency, we act as an intermediary for travel suppliers. We are not responsible for the acts, errors, omissions, or default of those suppliers.',
      placement: 'booking_confirmation',
      required: true,
    });

    return disclosures;
  }

  /**
   * Validate compliance for state
   */
  async validateStateCompliance(state: string): Promise<ComplianceStatus> {
    const registration = this.getRequiredRegistration(state);

    if (!registration) {
      return {
        compliant: true,
        message: 'No registration required for this state',
      };
    }

    if (!registration) {
      return {
        compliant: false,
        message: `Seller of Travel registration required for ${state}`,
        requirements: [
          `Submit registration to ${state} regulatory authority`,
          `Post bond if required (${registration.bondAmount || 'N/A'})`,
          `Display registration number on all materials`,
        ],
      };
    }

    if (new Date() > registration.expiresAt) {
      return {
        compliant: false,
        message: `Registration expired on ${registration.expiresAt}`,
        requirements: [
          `Renew registration before expiration`,
        ],
      };
    }

    return {
      compliant: true,
      registrationNumber: registration.registrationNumber,
      expiresAt: registration.expiresAt,
    };
  }
}
```

### IATA and Airline Regulations

```typescript
// lib/compliance/travel/aviation-regulations.ts

class AviationComplianceManager {
  /**
   * Passenger Name Record (PNR) data requirements
   * for Advance Passenger Information (API)
   */
  async validatePNRData(pnr: PNRData): Promise<ValidationResult> {
    const errors: string[] = [];
    const required = [
      'firstName',
      'lastName',
      'dob',
      'gender',
      'nationality',
      'documentNumber',
      'documentExpiry',
      'issuingCountry',
    ];

    for (const field of required) {
      if (!pnr[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    // Validate document expiry
    if (pnr.documentExpiry && new Date(pnr.documentExpiry) < new Date()) {
      errors.push('Travel document has expired');
    }

    // Validate date of birth
    if (pnr.dob && new Date(pnr.dob) > new Date()) {
      errors.push('Date of birth cannot be in the future');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Air passenger rights by region
   */
  getPassengerRights(region: string, flight: Flight): PassengerRights {
    const rights: PassengerRights = {
      compensation: [],
      assistance: [],
      rerouting: [],
      refund: [],
    };

    // EU Regulation 261/2004
    if (region === 'EU' || this.isEUFlight(flight)) {
      rights.compensation = [
        {
          condition: 'Flight cancelled < 14 days before departure',
          amount: this.getEUCompensation(flight.distance),
          currency: 'EUR',
        },
        {
          condition: 'Flight delayed 3+ hours',
          amount: this.getEUCompensation(flight.distance),
          currency: 'EUR',
        },
        {
          condition: 'Denied boarding',
          amount: this.getEUCompensation(flight.distance),
          currency: 'EUR',
        },
      ];

      rights.assistance = [
        'Refreshments and meals',
        'Communication (email, phone)',
        'Accommodation if overnight stay required',
        'Transport to/from accommodation',
      ];

      rights.rerouting = [
        'Re-routing to final destination at earliest opportunity',
        'Re-routing at later date at passenger convenience',
      ];

      rights.refund = [
        'Full refund of unused ticket',
        'Full refund of used ticket if flight no longer serves purpose',
        'Return to origin if outbound leg completed',
      ];
    }

    // US Department of Transportation rules
    if (region === 'US') {
      rights.compensation = [
        {
          condition: 'Denied boarding (involuntary)',
          amount: this.getUSDOTCompensation(flight.delay),
          currency: 'USD',
        },
      ];

      rights.assistance = [
        'Food and water for tarmac delays 2+ hours',
        'Adequate ventilation and temperature control',
        'Restroom access for tarmac delays',
      ];

      rights.refund = [
        'Full refund if flight cancelled or significantly delayed',
        'Refund within 7 business days for credit card',
        'Refund within 20 days for other payment methods',
      ];
    }

    return rights;
  }
}
```

---

## Tax Compliance

### VAT/GST Registration and Collection

```typescript
// lib/compliance/tax/vat-gst-manager.ts

interface VATConfig {
  registrations: VATRegistration[];
  thresholds: VATThreshold[];
  rates: VATRate[];
}

interface VATRegistration {
  country: string;
  vatNumber: string;
  effectiveFrom: Date;
  status: 'active' | 'suspended' | 'revoked';
  scheme: 'oss' | 'ioss' | 'domestic'; // One Stop Shop, Import One Stop Shop
}

class VATManager {
  /**
   * Determine VAT registration requirement
   */
  async checkRegistrationRequirement(
    country: string,
    annualRevenue: number,
    transactionType: 'b2b' | 'b2c'
  ): Promise<RegistrationRequirement> {
    const threshold = this.thresholds.find(t => t.country === country);

    if (!threshold) {
      return {
        required: false,
        reason: 'No VAT in this country',
      };
    }

    // B2C cross-border: register if exceeding distance selling threshold
    if (transactionType === 'b2c') {
      if (annualRevenue > threshold.distanceSelling) {
        return {
          required: true,
          scheme: 'oss',
          threshold: threshold.distanceSelling,
          reason: `Exceeded distance selling threshold of ${threshold.distanceSelling} ${threshold.currency}`,
        };
      }
    }

    // B2B: reverse charge usually applies
    if (transactionType === 'b2b') {
      return {
        required: false,
        reason: 'B2B: Reverse charge applies',
      };
    }

    return {
      required: false,
      reason: 'Below registration threshold',
    };
  }

  /**
   * Get applicable VAT rate
   */
  getVATRate(
    country: string,
    serviceType: ServiceType,
    customerType: 'business' | 'consumer'
  ): VATRateInfo {
    const rate = this.rates.find(r =>
      r.country === country &&
      r.serviceTypes.includes(serviceType)
    );

    if (!rate) {
      return {
        rate: 0,
        exempt: true,
        reason: 'No VAT rate found for this service/country combination',
      };
    }

    // Check for reverse charge (B2B cross-border)
    if (customerType === 'business' && this.isCrossBorder(country)) {
      return {
        rate: 0,
        reverseCharge: true,
        reason: 'Reverse charge applies for cross-border B2B',
      };
    }

    return {
      rate: rate.standard,
      reducedRates: {
        reduced: rate.reduced,
        superReduced: rate.superReduced,
        parking: rate.parking,
      },
    };
  }

  /**
   * Generate VAT invoice
   */
  async generateVATInvoice(
    booking: Booking,
    vatCountry: string
  ): Promise<VATInvoice> {
    const registration = this.getRegistration(vatCountry);
    const rateInfo = this.getVATRate(vatCountry, booking.serviceType, booking.customerType);

    return {
      invoiceNumber: booking.invoiceNumber,
      issueDate: new Date().toISOString(),
      supplier: {
        name: booking.supplier.name,
        address: booking.supplier.address,
        vatNumber: registration.vatNumber,
      },
      customer: {
        name: booking.customer.name,
        address: booking.customer.address,
        vatNumber: booking.customer.vatNumber || null,
      },
      details: booking.lineItems.map(item => ({
        description: item.description,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        vatRate: rateInfo.rate,
        vatAmount: this.calculateVAT(item.unitPrice * item.quantity, rateInfo.rate),
        total: item.total,
      })),
      totals: {
        netAmount: booking.netAmount,
        vatAmount: booking.vatAmount,
        grossAmount: booking.grossAmount,
        vatBreakdown: this.getVATBreakdown(booking),
      },
      vatSummary: {
        countryCode: vatCountry,
        vatNumber: registration.vatNumber,
        scheme: registration.scheme,
        reverseCharge: rateInfo.reverseCharge || false,
      },
    };
  }
}
```

### India TCS (Tax Collected at Source)

```typescript
// lib/compliance/tax/tcs-manager.ts

/**
 * India TCS for outbound travel
 * - 5% TCS on international travel packages
 * - 20% TCS on remittances under RBI's Liberalized Remittance Scheme (LRS)
 * - Credit available against income tax
 */

interface TCSConfig {
  rate: number;
  lrsRate: number;
  threshold: number; // INR 7 lakhs
  exemptions: TCSExemption[];
}

class TCSManager {
  /**
   * Calculate TCS on travel booking
   */
  calculateTCS(booking: Booking, panCard: string): TCSBreakdown {
    const baseAmount = booking.totalAmountINR;
    const tcs: TCSBreakdown = {
      applicable: false,
      rate: 0,
      amount: 0,
      creditAvailable: 0,
    };

    // Check if PAN is provided
    if (!panCard) {
      // Higher rate (20%) without PAN
      tcs.applicable = true;
      tcs.rate = 0.20; // 20%
      tcs.amount = baseAmount * 0.20;
      tcs.panProvided = false;
      return tcs;
    }

    // Check exemption
    if (this.isExempt(booking)) {
      tcs.exemptReason = this.getExemptionReason(booking);
      return tcs;
    }

    // Standard TCS rate
    const threshold = this.config.threshold;
    const taxableAmount = Math.max(0, baseAmount - threshold);

    if (taxableAmount > 0) {
      tcs.applicable = true;
      tcs.rate = this.config.rate; // 5%
      tcs.amount = taxableAmount * this.config.rate;
      tcs.creditAvailable = tcs.amount; // Full credit available
      tcs.panProvided = true;
    }

    return tcs;
  }

  /**
   * Generate TCS certificate
   */
  async generateTCSCertificate(
    bookingId: string,
    quarter: string,
    year: number
  ): Promise<TCSCertificate> {
    const bookings = await this.getBookingsForQuarter(quarter, year);

    return {
      certificateNumber: this.generateCertificateNumber(),
      period: { quarter, year },
      collector: {
        name: 'Travel Agency Name',
        tan: 'Tax Collection Account Number',
      },
      deductee: {
        name: bookings[0].customer.name,
        pan: bookings[0].customer.pan,
      },
      details: bookings.map(b => ({
        bookingId: b.id,
        travelDate: b.travelDate,
        amount: b.totalAmountINR,
        tcsRate: b.tcs.rate,
        tcsAmount: b.tcs.amount,
      })),
      totals: {
        totalAmount: bookings.reduce((sum, b) => sum + b.totalAmountINR, 0),
        totalTCS: bookings.reduce((sum, b) => sum + b.tcs.amount, 0),
      },
      generatedAt: new Date().toISOString(),
    };
  }
}
```

---

## Data Residency

### Data Localization by Region

```typescript
// lib/compliance/residency/data-residency-manager.ts

interface DataResidencyConfig {
  regions: DataRegion[];
  storageMapping: StorageMapping[];
  transferRules: TransferRule[];
}

interface DataRegion {
  code: string;
  requiresDataLocalization: boolean;
  permittedCountries: string[];
  dataCategories: string[];
  retentionPeriod: number; // days
  crossBorderTransferRequired: boolean;
}

class DataResidencyManager {
  /**
   * Determine where data must be stored
   */
  async determineStorageLocation(
    dataType: DataType,
    userCountry: string
  ): Promise<StorageLocation> {
    const region = this.getRegion(userCountry);

    if (!region) {
      return { region: 'default', locations: ['us-east-1'] };
    }

    // Check data localization requirements
    if (region.requiresDataLocalization) {
      return {
        region: userCountry,
        locations: this.getLocalLocations(userCountry),
        restriction: 'Data must remain within country borders',
      };
    }

    return {
      region: this.getOptimalRegion(userCountry),
      locations: this.getRegionLocations(userCountry),
    };
  }

  /**
   * Check if cross-border transfer is permitted
   */
  async canTransferData(
    dataType: DataType,
    fromCountry: string,
    toCountry: string
  ): Promise<TransferDecision> {
    // GDPR: Adequacy decision required
    const hasAdequacy = await this.checkAdequacyDecision(toCountry);
    if (!hasAdequacy) {
      return {
        permitted: false,
        reason: 'No adequacy decision for destination country',
        alternatives: [
          'Standard Contractual Clauses (SCCs)',
          'Binding Corporate Rules (BCRs)',
          'Explicit consent',
        ],
      };
    }

    // PIPL (China): Security assessment required for certain transfers
    if (fromCountry === 'CN') {
      const assessmentRequired = await this.checkIfAssessmentRequired(dataType);
      if (assessmentRequired) {
        return {
          permitted: false,
          reason: 'Security assessment by CAC required',
          requirements: [
            'Complete CAC security assessment',
            'Obtain individual consent',
            'Ensure overseas recipient protection level',
          ],
        };
      }
    }

    return {
      permitted: true,
      safeguards: this.getRequiredSafeguards(fromCountry, toCountry),
    };
  }

  /**
   * Get data retention period by region and type
   */
  getRetentionPeriod(dataType: DataType, country: string): RetentionPeriod {
    // GDPR: storage limitation principle
    const gdprLimits: Record<DataType, number> = {
      personal: 365 * 7, // 7 years after account closure
      financial: 365 * 10, // 10 years for tax purposes
      travel: 365 * 7, // 7 years
      support: 365 * 3, // 3 years
      analytics: 365 * 2, // 2 years if anonymized
      marketing: 365 * 2, // 2 years after opt-out
    };

    // LGPD (Brazil): Similar to GDPR
    // PIPL (China): Must specify retention period, cannot extend without consent

    return {
      days: gdprLimits[dataType] || 365 * 5,
      justification: this.getRetentionJustification(dataType),
      anonymizationOption: this.supportsAnonymization(dataType),
    };
  }

  /**
   * Handle data deletion request
   */
  async deleteData(
    userId: string,
    dataType: DataType,
    country: string
  ): Promise<DeletionResult> {
    // Check for retention requirements
    const retention = this.getRetentionPeriod(dataType, country);

    // Check for legal holds
    const legalHold = await this.checkLegalHold(userId);
    if (legalHold) {
      return {
        deleted: false,
        reason: 'Legal hold prevents deletion',
        holdExpiry: legalHold.expiry,
      };
    }

    // Check for tax/compliance requirements
    const mustRetain = await this.checkRetentionRequirement(userId, dataType);
    if (mustRetain) {
      return {
        deleted: false,
        reason: 'Regulatory retention requirement',
        canAnonymize: true,
      };
    }

    // Proceed with deletion
    await this.deleteFromAllRegions(userId, dataType);

    return {
      deleted: true,
      regions: await this.getDeletionRegions(userId),
    };
  }
}
```

---

## Cookie Consent

### Regional Cookie Requirements

```typescript
// lib/compliance/cookies/cookie-manager.ts

interface CookieConsentConfig {
  regions: CookieRegion[];
  categories: CookieCategory[];
  scripts: CookieScript[];
}

interface CookieRegion {
  code: string;
  requiresConsent: boolean;
  consentType: 'opt_in' | 'opt_out';
      'implicit' | 'explicit';
  categories: string[];
  expirationDays: number;
}

class CookieConsentManager {
  /**
   * Get cookie requirements by region
   */
  getCookieRequirements(countryCode: string): CookieRequirements {
    const region = this.config.regions.find(r => r.code === countryCode);

    if (!region) {
      // Default: no consent required
      return {
        requiresConsent: false,
        consentType: 'implicit',
        categories: ['essential'],
      };
    }

    return {
      requiresConsent: region.requiresConsent,
      consentType: region.consentType,
      categories: region.categories,
      expirationDays: region.expirationDays,
    };
  }

  /**
   * Render cookie banner
   */
  renderBanner(requirements: CookieRequirements): BannerConfig {
    if (!requirements.requiresConsent) {
      return null;
    }

    const config: BannerConfig = {
      position: 'bottom',
      layout: requirements.consentType === 'opt_in' ? 'categories' : 'simple',
      categories: this.getCategories(requirements.categories),
      buttons: this.getButtons(requirements.consentType),
      links: this.getLinks(requirements),
    };

    // GDPR: Must have granular control
    if (requirements.consentType === 'explicit') {
      config.vendors = true; // Show vendor list
      config.purposes = true; // Show purpose list
      config legitimateInterests = true; // Show legitimate interests
      config.withdrawalButton = true; // Always visible withdrawal option
    }

    // CCPA: Do Not Sell option
    if (requirements.categories.includes('do_not_sell')) {
      config.doNotSell = true;
    }

    return config;
  }

  /**
   * Update cookie settings
   */
  async updateConsent(
    userId: string,
    consents: Record<string, boolean>
  ): Promise<void> {
    // Store consent
    await this.storeConsent({
      userId,
      consents,
      timestamp: new Date().toISOString(),
      version: this.config.version,
    });

    // Update cookies based on consent
    for (const [category, granted] of Object.entries(consents)) {
      const scripts = this.getScriptsForCategory(category);

      if (granted) {
        // Enable scripts
        for (const script of scripts) {
          this.enableScript(script);
        }
      } else {
        // Disable scripts and clear related cookies
        for (const script of scripts) {
          this.disableScript(script);
          this.clearCookies(script.cookieDomains);
        }
      }
    }

    // Fire consent event
    this.fireConsentEvent(consents);
  }

  /**
   * Clear cookies for privacy
   */
  async clearCookies(
    categories: string[],
    userId: string
  ): Promise<ClearedCookies> {
    const cleared: string[] = [];

    for (const category of categories) {
      const scripts = this.getScriptsForCategory(category);

      for (const script of scripts) {
        // Clear cookies from all domains
        for (const domain of script.cookieDomains) {
          for (const cookieName of script.cookieNames) {
            this.deleteCookie(cookieName, domain);
            cleared.push(`${cookieName}@${domain}`);
          }
        }
      }
    }

    // Update consent state
    await this.updateConsentState(userId, categories, false);

    return {
      userId,
      cleared,
      timestamp: new Date().toISOString(),
    };
  }
}
```

---

## Age Verification

### Regional Age Requirements

```typescript
// lib/compliance/age/age-verification-manager.ts

interface AgeVerificationConfig {
  regions: AgeRegion[];
  methods: VerificationMethod[];
}

interface AgeRegion {
  code: string;
  minimumAge: number;
  verificationRequired: boolean;
  verificationMethod: VerificationMethod[];
  parentalConsentAge?: number;
}

class AgeVerificationManager {
  /**
   * Get age requirements for region
   */
  getAgeRequirements(countryCode: string): AgeRequirements {
    const region = this.config.regions.find(r => r.code === countryCode);

    if (!region) {
      return {
        minimumAge: 18,
        verificationRequired: false,
      };
    }

    return {
      minimumAge: region.minimumAge,
      verificationRequired: region.verificationRequired,
      methods: region.verificationMethod,
      parentalConsentRequired: region.parentalConsentAge,
    };
  }

  /**
   * Verify user age
   */
  async verifyAge(
    userId: string,
    dateOfBirth: Date,
    method: VerificationMethod
  ): Promise<VerificationResult> {
    const age = this.calculateAge(dateOfBirth);
    const requirements = this.getAgeRequirements(this.getUserCountry(userId));

    // Check if age requirement met
    if (age < requirements.minimumAge) {
      // Check if parental consent option available
      if (requirements.parentalConsentRequired && age >= requirements.parentalConsentRequired) {
        return {
          verified: false,
          requiresParentalConsent: true,
          minimumAge: requirements.minimumAge,
          currentAge: age,
        };
      }

      return {
        verified: false,
        reason: `User is ${age}. Minimum age is ${requirements.minimumAge}`,
        minimumAge: requirements.minimumAge,
        currentAge: age,
      };
    }

    // Perform verification if required
    if (requirements.verificationRequired) {
      const methodResult = await this.verifyWithMethod(method, userId);

      if (!methodResult.verified) {
        return {
          verified: false,
          reason: 'Age verification failed',
          canRetry: methodResult.canRetry,
        };
      }

      // Store verification result
      await this.storeVerification(userId, {
        method,
        verifiedAt: new Date().toISOString(),
        age,
      });
    }

    return {
      verified: true,
      age,
    };
  }

  /**
   * Handle parental consent
   */
  async handleParentalConsent(
    userId: string,
    parentInfo: ParentInfo,
    consentMethod: 'electronic' | 'paper'
  ): Promise<ConsentResult> {
    // Validate parent information
    const parentValid = await this.validateParentInfo(parentInfo);
    if (!parentValid) {
      return {
        granted: false,
        reason: 'Parent information could not be verified',
      };
    }

    // Obtain consent
    if (consentMethod === 'electronic') {
      // Send electronic consent request
      await this.sendElectronicConsent(parentInfo.email, userId);
    } else {
      // Generate paper consent form
      const form = await this.generatePaperConsentForm(userId, parentInfo);
      return {
        granted: false,
        requiresPaperSignature: true,
        form,
      };
    }

    return {
      granted: true,
      expiresAt: this.getConsentExpiry(),
    };
  }
}
```

---

## Accessibility Standards

### WCAG 2.1 Compliance

```typescript
// lib/compliance/accessibility/wcag-manager.ts

interface WCAGConfig {
  level: 'A' | 'AA' | 'AAA';
  localization: AccessibilityLocalization[];
}

class WCAGManager {
  /**
   * Validate component for WCAG compliance
   */
  validateComponent(component: ComponentInfo): WCAGValidationResult {
    const issues: WCAGIssue[] = [];

    // Perceivable
    issues.push(...this.checkColorContrast(component));
    issues.push(...this.checkAltText(component));
    issues.push(...this.checkCaptions(component));
    issues.push(...this.checkResizableText(component));

    // Operable
    issues.push(...this.checkKeyboardAccess(component));
    issues.push(...this.checkFocusIndicator(component));
    issues.push(...this.checkTiming(component));
    issues.push(...this.checkSeizures(component));

    // Understandable
    issues.push(...this.checkLanguage(component));
    issues.push(...this.checkConsistentNavigation(component));
    issues.push(...this.checkErrorIdentification(component));
    issues.push(...this.checkLabels(component));

    // Robust
    issues.push(...this.checkMarkup(component));
    issues.push(...this.checkARIA(component));

    return {
      compliant: issues.filter(i => i.level === this.config.level).length === 0,
      issues,
      level: this.config.level,
    };
  }

  /**
   * Check color contrast
   */
  private checkColorContrast(component: ComponentInfo): WCAGIssue[] {
    const issues: WCAGIssue[] = [];
    const minContrast = {
      A: { normal: 3, large: 3 },
      AA: { normal: 4.5, large: 3 },
      AAA: { normal: 7, large: 4.5 },
    };

    for (const [fg, bg] of component.colorPairs) {
      const contrast = this.calculateContrastRatio(fg, bg);
      const isLarge = component.isLargeText;
      const required = isLarge
        ? minContrast[this.config.level].large
        : minContrast[this.config.level].normal;

      if (contrast < required) {
        issues.push({
          criterion: '1.4.3',
          level: this.config.level,
          description: `Insufficient color contrast: ${contrast.toFixed(2)}:1 (required: ${required}:1)`,
          element: component.element,
        });
      }
    }

    return issues;
  }

  /**
   * Generate accessible language switcher
   */
  generateAccessibleLanguageSwitcher(
    currentLocale: string,
    availableLocales: string[]
  ): LanguageSwitcherConfig {
    return {
      component: 'select',
      label: this.getTranslation('language.select_label', currentLocale),
      currentLocale,
      options: availableLocales.map(locale => ({
        value: locale,
        label: this.getLocaleLabel(locale),
        lang: locale, // For lang attribute
        dir: this.isRTL(locale) ? 'rtl' : 'ltr',
      })),
      attributes: {
        'aria-label': this.getTranslation('language.select_aria', currentLocale),
        'aria-describedby': 'language-help',
      },
      helpText: {
        id: 'language-help',
        text: this.getTranslation('language.help_text', currentLocale),
      },
      onChange: (newLocale) => this.handleLocaleChange(newLocale),
    };
  }

  /**
   * Localized ARIA labels
   */
  getARIALabels(
    component: string,
    locale: string
  ): Record<string, string> {
    const labels: Record<string, Record<string, string>> = {
      navigation: {
        menu: this.getTranslation('nav.menu', locale),
        skip: this.getTranslation('nav.skip_to_content', locale),
        search: this.getTranslation('nav.search', locale),
        account: this.getTranslation('nav.account', locale),
      },
      booking: {
        startDate: this.getTranslation('booking.start_date', locale),
        endDate: this.getTranslation('booking.end_date', locale),
        guests: this.getTranslation('booking.guests', locale),
        search: this.getTranslation('booking.search', locale),
      },
      currency: {
        selector: this.getTranslation('currency.select', locale),
        current: this.getTranslation('currency.current', locale),
      },
    };

    return labels[component] || {};
  }
}
```

---

## Implementation

### Compliance Checklist

```typescript
// lib/compliance/compliance-checklist.ts

interface ComplianceChecklist {
  region: string;
  items: ChecklistItem[];
}

class ComplianceChecklistManager {
  /**
   * Get compliance checklist for region
   */
  getChecklist(region: string): ComplianceChecklist {
    const checklists: Record<string, ComplianceChecklist> = {
      EU: {
        region: 'EU',
        items: [
          {
            category: 'GDPR',
            items: [
              { task: 'Implement consent management platform', priority: 'critical' },
              { task: 'Create data processing records', priority: 'critical' },
              { task: 'Implement data subject rights (access, erasure, portability)', priority: 'critical' },
              { task: 'Conduct DPIA for high-risk processing', priority: 'high' },
              { task: 'Appoint EU representative', priority: 'high' },
              { task: 'Implement data breach detection and notification', priority: 'critical' },
              { task: 'Establish lawful basis for all data processing', priority: 'critical' },
            ],
          },
          {
            category: 'Consumer Rights',
            items: [
              { task: 'Implement 14-day withdrawal period', priority: 'critical' },
              { task: 'Display all-inclusive pricing', priority: 'critical' },
              { task: 'Provide pre-contractual information', priority: 'critical' },
              { task: 'Implement alternative dispute resolution', priority: 'high' },
            ],
          },
          {
            category: 'VAT',
            items: [
              { task: 'Register for OSS scheme', priority: 'high' },
              { task: 'Display VAT numbers on invoices', priority: 'critical' },
              { task: 'Implement VAT rate detection by country', priority: 'critical' },
            ],
          },
        ],
      },
      US: {
        region: 'US',
        items: [
          {
            category: 'Privacy',
            items: [
              { task: 'Implement CCPA Do Not Sell', priority: 'high' },
              { task: 'Create privacy policy', priority: 'critical' },
              { task: 'Implement data access requests', priority: 'high' },
            ],
          },
          {
            category: 'Seller of Travel',
            items: [
              { task: 'Register in required states', priority: 'critical' },
              { task: 'Display registration numbers', priority: 'critical' },
              { task: 'Post bond if required', priority: 'high' },
            ],
          },
        ],
      },
      IN: {
        region: 'IN',
        items: [
          {
            category: 'TCS',
            items: [
              { task: 'Implement 5% TCS collection', priority: 'critical' },
              { task: 'Validate PAN cards', priority: 'critical' },
              { task: 'Generate TCS certificates', priority: 'high' },
            ],
          },
          {
            category: 'GST',
            items: [
              { task: 'Register for GST', priority: 'critical' },
              { task: 'Collect GST on domestic bookings', priority: 'critical' },
              { task: 'File GSTR-1 returns', priority: 'critical' },
            ],
          },
        ],
      },
    };

    return checklists[region] || this.getDefaultChecklist();
  }
}
```

### Regional Compliance Configuration

```typescript
// config/compliance.config.ts

export const complianceConfig = {
  // GDPR regions
  gdprRegions: ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'CH', 'UK'],

  // Data residency requirements
  dataResidency: {
    CN: { localizationRequired: true, permittedLocations: ['cn'] },
    RU: { localizationRequired: true, permittedLocations: ['ru'] },
    SA: { localizationRequired: true, permittedLocations: ['sa'] },
    IN: { localizationRequired: false, recommended: true },
  },

  // VAT registrations
  vatRegistrations: {
    EU: { scheme: 'oss', number: 'EU123456789' },
    GB: { scheme: 'domestic', number: 'GB123456789' },
  },

  // Seller of Travel
  sellerOfTravel: {
    CA: { number: 'CST1234567-10', expires: '2026-12-31' },
    FL: { number: 'ST12345', expires: '2026-12-31' },
  },

  // Age verification
  ageVerification: {
    US: { minimumAge: 18, verificationRequired: false },
    GB: { minimumAge: 18, verificationRequired: true },
    IN: { minimumAge: 18, verificationRequired: false },
  },

  // Cookie consent
  cookieConsent: {
    EU: { type: 'explicit', expirationDays: 365 },
    UK: { type: 'explicit', expirationDays: 365 },
    US: { type: 'implicit', expirationDays: 395 },
  },
};
```

---

## Summary

This document covers regional compliance requirements for a global travel platform:

- **GDPR/Data Privacy**: Consent management, data subject rights, DPIA, breach notification
- **Consumer Protection**: EU withdrawal rights, price transparency, package travel regulations
- **Travel Regulations**: Seller of Travel registration, IATA compliance, passenger rights
- **Tax Compliance**: VAT/GST collection, TCS for India, tax invoicing
- **Data Residency**: Localization requirements, cross-border transfers, retention periods
- **Cookie Consent**: Regional requirements, granular control, withdrawal
- **Age Verification**: Regional age requirements, parental consent
- **Accessibility**: WCAG 2.1 compliance, localized ARIA labels

---

**Next Steps:**

1. Complete INTERNATIONALIZATION_MASTER_INDEX.md update
2. Update EXPLORATION_TRACKER.md with series completion
