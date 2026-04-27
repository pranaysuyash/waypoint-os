# Accommodation Catalog 01: Architecture

> System design, data model, integrations, and infrastructure

---

## Overview

The Accommodation Catalog is a comprehensive inventory management system for hotels, resorts, villas, and other lodging properties. It aggregates content from multiple suppliers, normalizes data, provides real-time availability and pricing, and powers search and discovery for customers.

**Key Capabilities:**
- Multi-supplier content aggregation
- Real-time inventory synchronization
- Flexible pricing and rate plans
- Geo-spatial search
- Rich content management

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Domain Model](#domain-model)
3. [Supplier Integration](#supplier-integration)
4. [Content Management](#content-management)
5. [Pricing Architecture](#pricing-architecture)
6. [Search Infrastructure](#search-infrastructure)
7. [Data Synchronization](#data-synchronization)

---

## System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACCOMMODATION CATALOG                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   API GATEWAY   │    │  SEARCH SERVICE │    │  PRICING ENGINE │         │
│  │   (REST/GraphQL)│    │  (Elasticsearch)│    │   (Rules Engine)│         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┴──────────────────────┘                   │
│                                  │                                          │
│                     ┌────────────┴────────────┐                             │
│                     │   CATALOG SERVICE       │                             │
│                     │  (Business Logic)       │                             │
│                     └────────────┬────────────┘                             │
│                                  │                                          │
│           ┌──────────────────────┼──────────────────────┐                  │
│           │                      │                      │                   │
│  ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐          │
│  │ PROPERTY STORE  │   │ INVENTORY CACHE │   │  CONTENT STORE  │          │
│  │  (PostgreSQL)   │   │    (Redis)      │   │    (S3/CDN)     │          │
│  │  + PostGIS      │   │                 │   │                 │          │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                      SUPPLIER ADAPTERS                          │       │
│  ├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤       │
│  │  HotelBeds│  Expedia │  Booking │  GTA    │  Agoda   │  Direct │       │
│  └────┬─────┴─────┬────┴─────┬────┴─────┬────┴─────┬────┴────┬────┘       │
│       │           │           │           │           │         │           │
│       └───────────┴───────────┴───────────┴───────────┴─────────┘           │
│                                  │                                          │
│                        SUPPLIER API LAYER                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **API Gateway** | Request routing, auth, rate limiting | Node.js/Express |
| **Catalog Service** | Business logic, orchestration | TypeScript |
| **Search Service** | Full-text search, faceting | Elasticsearch |
| **Pricing Engine** | Rate calculation, discounts | Python/Node.js |
| **Property Store** | Master property data | PostgreSQL + PostGIS |
| **Inventory Cache** | Real-time availability | Redis |
| **Content Store** | Images, documents | AWS S3 + CloudFront |
| **Supplier Adapters** | External API integration | TypeScript |

---

## Domain Model

### Core Entities

```typescript
interface Property {
  // Identity
  id: string;
  supplierId: string;
  supplierCode: string;
  internalCode: string;

  // Basic Info
  name: LocalizedText;
  type: PropertyType;
  category: PropertyCategory;
  chain?: string;
  brand?: string;

  // Location
  location: {
    address: Address;
    coordinates: {
      latitude: number;
      longitude: number;
    };
    geohash?: string;
    timezone: string;
    area?: AreaInfo;
  };

  // Contact
  contact: {
    phone?: string;
    email?: string;
    website?: string;
    fax?: string;
  };

  // Content
  content: PropertyContent;

  // Classification
  rating: {
    stars?: number; // 1-5
    category?: string; // e.g., "Tourist", "Superior"
    officialRating?: string;
  };

  // Amenities
  amenities: Amenity[];

  // Room Types
  roomTypes: RoomType[];

  // Status
  status: PropertyStatus;
  isActive: boolean;
  verifiedAt?: Date;

  // Metadata
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastSyncedAt: Date;
    sourceQuality: number; // 0-1
    completeness: number; // 0-1
  };
}

type PropertyType =
  | 'hotel'
  | 'motel'
  | 'resort'
  | 'villa'
  | 'apartment'
  | 'hostel'
  | 'guesthouse'
  | 'boutique'
  | 'camping'
  | 'aparthotel'
  | 'condo'
  | 'ryokan'
  | 'other';

type PropertyCategory =
  | 'luxury'
  | 'upper_upscale'
  | 'upscale'
  | 'upper_midscale'
  | 'midscale'
  | 'economy'
  | 'budget';

type PropertyStatus =
  | 'active'
  | 'inactive'
  | 'pending'
  | 'suspended'
  | 'deleted';

interface LocalizedText {
  en: string;
  [locale: string]: string;
}

interface Address {
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postalCode: string;
  countryCode: string;
}

interface AreaInfo {
  country: LocalizedText;
  region?: LocalizedText;
  city: LocalizedText;
  district?: LocalizedText;
  landmarks?: string[];
}

interface PropertyContent {
  descriptions: {
    short: LocalizedText; // 1-2 sentences
    long: LocalizedText; // Full description
    marketing?: LocalizedText;
  };
  images: MediaItem[];
  videos?: MediaItem[];
  floorPlans?: MediaItem[];
  policies: PropertyPolicies;
  checkIn: CheckInOutInfo;
  checkOut: CheckInOutInfo;
}

interface MediaItem {
  id: string;
  url: string;
  thumbnailUrl: string;
  type: 'photo' | 'video' | 'floor_plan' | 'logo';
  category?: MediaCategory;
  caption?: LocalizedText;
  width: number;
  height: number;
  order: number;
  createdAt: Date;
}

type MediaCategory =
  | 'exterior'
  | 'lobby'
  | 'room'
  | 'bathroom'
  | 'pool'
  | 'restaurant'
  | 'gym'
  | 'view'
  | 'other';

interface PropertyPolicies {
  cancellation: CancellationPolicy;
  children: ChildrenPolicy;
  payment: PaymentPolicy;
  pets: PetPolicy;
  smoking: SmokingPolicy;
  checkIn: {
    from: string; // "14:00"
    until: string; //_until: "00:00"
    instructions?: LocalizedText;
  };
  checkOut: {
    from: string; // "07:00"
    until: string; // "12:00"
    instructions?: LocalizedText;
  };
  special?: LocalizedText; // Other important policies
}

interface ChildrenPolicy {
  allowed: boolean;
  minAge?: number;
  maxAge?: number;
  freeUntil?: number; // Age
  cots: {
    available: boolean;
    charge?: PriceInfo;
  };
  extraBeds: {
    available: boolean;
    charge?: PriceInfo;
    maxPerRoom?: number;
  };
}

interface PetPolicy {
  allowed: boolean;
  types?: string[]; // "dogs", "cats", etc.
  sizeRestriction?: string;
  charge?: PriceInfo;
  restrictions?: LocalizedText;
}

interface CheckInOutInfo {
  instructions: LocalizedText;
  receptionHours?: {
    [day: string]: { open: string; close: string } | '24/7' | 'closed';
  };
  earlyCheckIn?: {
    available: boolean;
    charge?: PriceInfo;
  };
  lateCheckOut?: {
    available: boolean;
    charge?: PriceInfo;
  };
}

interface Amenity {
  id: string;
  code: string;
  type: AmenityType;
  name: LocalizedText;
  description?: LocalizedText;
  icon?: string;
  complimentary: boolean;
  available?: boolean; // For seasonal/temporary amenities
}

type AmenityType =
  | 'general'      // WiFi, parking, etc.
  | 'room'         // In-room amenities
  | 'food_drink'   // Restaurant, bar, etc.
  | 'wellness'     // Pool, spa, gym
  | 'service'      // Reception, concierge
  | 'facility'     // Meeting rooms, business center
  | 'outdoor'      // Garden, terrace
  | 'activities'   // Tours, equipment rental
  | 'accessibility'; // Accessibility features

interface RoomType {
  id: string;
  propertyId: string;
  code: string;
  name: LocalizedText;
  description?: LocalizedText;
  type: RoomTypeType;
  sizeMeters?: number;
  bedConfiguration: BedConfiguration[];
  occupancy: OccupancyLimits;
  views: string[];
  amenities: Amenity[];
  images: MediaItem[];
  status: RoomTypeStatus;
}

type RoomTypeType =
  | 'single'
  | 'double'
  | 'twin'
  | 'suite'
  | 'studio'
  | 'apartment'
  | 'family'
  | 'accessible'
  | 'penthouse'
  | 'villa';

interface BedConfiguration {
  type: BedType;
  count: number;
  size?: BedSize;
}

type BedType = 'single' | 'double' | 'queen' | 'king' | 'bunk' | 'sofa_bed' | 'cot';
type BedSize = 'twin' | 'full' | 'queen' | 'king' | 'california_king';

interface OccupancyLimits {
  maxAdults: number;
  maxChildren: number;
  maxTotal: number;
  minAdults?: number;
}

type RoomTypeStatus = 'active' | 'inactive' | 'sold_out';

interface RatePlan {
  id: string;
  roomTypeId: string;
  propertyId: string;
  code: string;
  name: LocalizedText;
  description?: LocalizedText;

  // Pricing
  pricing: {
    type: PricingType;
    baseRate?: Money;
    tax?: TaxInfo;
    fees?: FeeInfo[];
    inclusive: boolean; // If taxes/fees included
  };

  // Availability
  availability: {
    minStay?: number; // Nights
    maxStay?: number; // Nights
    availableDays: number[]; // 0-6 (Sun-Sat)
    closedToArrival: boolean;
    closedToDeparture: boolean;
  };

  // Constraints
  constraints: {
    bookable?: DateRange;
    cancellationPolicy: CancellationPolicy;
    guarantee: GuaranteeRequirement;
    deposit?: DepositRequirement;
  };

  // Promotions
  promotions?: Promotion[];

  status: RatePlanStatus;
}

type PricingType = 'static' | 'dynamic' | 'request';
type RatePlanStatus = 'active' | 'inactive' | 'sold_out' | 'restricted';

interface Money {
  amount: number;
  currency: string;
}

interface TaxInfo {
  amount: number;
  currency: string;
  inclusive: boolean;
  percentage?: number;
  description?: LocalizedText;
}

interface FeeInfo {
  name: LocalizedText;
  amount: Money;
  type: 'fixed' | 'percentage' | 'per_night' | 'per_stay';
  mandatory: boolean;
  payableAt: 'booking' | 'check_in' | 'check_out' | 'property';
}

interface DateRange {
  start: Date;
  end: Date;
}

interface CancellationPolicy {
  type: 'free' | 'flexible' | 'moderate' | 'strict' | 'non_refundable';
  description: LocalizedText;
  deadline?: {
    amount: number;
    unit: 'hours' | 'days';
    before: 'check_in' | 'arrival';
  };
  penalty?: {
    type: 'fixed' | 'percentage' | 'nights';
    amount?: number;
    nights?: number;
  };
}

interface GuaranteeRequirement {
  type: 'none' | 'credit_card' | 'deposit';
  cardTypes?: string[];
}

interface DepositRequirement {
  amount: Money;
  type: 'fixed' | 'percentage' | 'nights';
  dueAt: 'booking' | 'check_in';
  refundable: boolean;
  refundConditions?: LocalizedText;
}

interface Promotion {
  id: string;
  code: string;
  type: 'early_booking' | 'long_stay' | 'last_minute' | 'flash_sale';
  discount: {
    type: 'percentage' | 'fixed' | 'nights_free';
    amount: number;
  };
  conditions: {
    minStay?: number;
    bookBy?: Date;
    travelBy?: Date;
    travelAfter?: Date;
    blackouts?: DateRange[];
  };
}

interface Availability {
  propertyId: string;
  roomTypeId: string;
  ratePlanId: string;
  date: Date; // LocalDate
  available: number;
  total: number;
  price?: Money;
  status: 'available' | 'limited' | 'sold_out';
}
```

### Database Schema

```sql
-- Properties
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  supplier_id VARCHAR(50) NOT NULL,
  supplier_code VARCHAR(100) NOT NULL,
  internal_code VARCHAR(100) UNIQUE,

  -- Basic Info
  name JSONB NOT NULL,
  type VARCHAR(50) NOT NULL,
  category VARCHAR(50),
  chain VARCHAR(100),
  brand VARCHAR(100),

  -- Location
  address_line1 VARCHAR(255) NOT NULL,
  address_line2 VARCHAR(255),
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100),
  postal_code VARCHAR(20) NOT NULL,
  country_code CHAR(2) NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  geohash CHAR(12),
  timezone VARCHAR(50),

  -- Contact
  phone VARCHAR(50),
  email VARCHAR(255),
  website VARCHAR(500),
  fax VARCHAR(50),

  -- Classification
  star_rating INTEGER CHECK (star_rating BETWEEN 1 AND 5),
  category_rating VARCHAR(50),
  official_rating VARCHAR(100),

  -- Status
  status VARCHAR(20) DEFAULT 'active',
  is_active BOOLEAN DEFAULT true,
  verified_at TIMESTAMP WITH TIME ZONE,

  -- Metadata
  source_quality DECIMAL(3, 2) DEFAULT 0,
  completeness DECIMAL(3, 2) DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (supplier_id, supplier_code),

  INDEX idx_properties_country (country_code),
  INDEX idx_properties_city (city),
  INDEX idx_properties_type (type),
  INDEX idx_properties_category (category),
  INDEX idx_properties_status (status, is_active),
  INDEX idx_properties_location (latitude, longitude),
  INDEX idx_properties_geohash (geohash)
);

-- Add PostGIS extension for geo queries
CREATE EXTENSION IF NOT EXISTS postgis;
ALTER TABLE properties ADD COLUMN location GEOGRAPHY(POINT, 4326);
CREATE INDEX idx_properties_geography ON properties USING GIST (location);

-- Property Content
CREATE TABLE property_content (
  property_id UUID PRIMARY KEY REFERENCES properties(id) ON DELETE CASCADE,
  descriptions_short JSONB NOT NULL,
  descriptions_long JSONB NOT NULL,
  descriptions_marketing JSONB,
  policies JSONB NOT NULL,
  check_in_info JSONB,
  check_out_info JSONB,

  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property Images
CREATE TABLE property_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500),
  type VARCHAR(20) NOT NULL,
  category VARCHAR(50),
  caption JSONB,
  width INTEGER,
  height INTEGER,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_property_images_property (property_id),
  INDEX idx_property_images_type (type)
);

-- Room Types
CREATE TABLE room_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  code VARCHAR(100) NOT NULL,
  name JSONB NOT NULL,
  description JSONB,
  type VARCHAR(50) NOT NULL,
  size_meters DECIMAL(8, 2),
  occupancy_max_adults INTEGER NOT NULL,
  occupancy_max_children INTEGER DEFAULT 0,
  occupancy_max_total INTEGER NOT NULL,
  views TEXT[],
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (property_id, code),
  INDEX idx_room_types_property (property_id),
  INDEX idx_room_types_type (type),
  INDEX idx_room_types_status (status)
);

-- Room Type Images
CREATE TABLE room_type_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500),
  category VARCHAR(50),
  caption JSONB,
  width INTEGER,
  height INTEGER,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_room_type_images_room (room_type_id)
);

-- Bed Configurations
CREATE TABLE room_type_beds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  count INTEGER NOT NULL,
  size VARCHAR(50),
  sort_order INTEGER DEFAULT 0
);

-- Amenities (Taxonomy)
CREATE TABLE amenities (
  id VARCHAR(100) PRIMARY KEY,
  type VARCHAR(50) NOT NULL,
  name JSONB NOT NULL,
  description JSONB,
  icon VARCHAR(100),
  parent_id VARCHAR(100) REFERENCES amenities(id),

  INDEX idx_amenities_type (type),
  INDEX idx_amenities_parent (parent_id)
);

-- Property Amenities
CREATE TABLE property_amenities (
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  amenity_id VARCHAR(100) NOT NULL REFERENCES amenities(id),
  complimentary BOOLEAN DEFAULT true,
  available BOOLEAN DEFAULT true,

  PRIMARY KEY (property_id, amenity_id),
  INDEX idx_property_amenities_property (property_id)
);

-- Room Type Amenities
CREATE TABLE room_type_amenities (
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  amenity_id VARCHAR(100) NOT NULL REFERENCES amenities(id),
  complimentary BOOLEAN DEFAULT true,

  PRIMARY KEY (room_type_id, amenity_id),
  INDEX idx_room_type_amenities_room (room_type_id)
);

-- Rate Plans
CREATE TABLE rate_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  property_id UUID NOT NULL,
  code VARCHAR(100) NOT NULL,
  name JSONB NOT NULL,
  description JSONB,

  -- Pricing
  pricing_type VARCHAR(20) NOT NULL,
  base_rate_amount DECIMAL(12, 2),
  base_rate_currency CHAR(3),
  tax_inclusive BOOLEAN DEFAULT false,
  tax_amount DECIMAL(12, 2),
  tax_percentage DECIMAL(5, 2),

  -- Availability
  min_stay INTEGER,
  max_stay INTEGER,
  available_days INTEGER[], -- 0-6
  closed_to_arrival BOOLEAN DEFAULT false,
  closed_to_departure BOOLEAN DEFAULT false,

  -- Constraints
  bookable_start DATE,
  bookable_end DATE,
  guarantee_type VARCHAR(20),
  deposit_type VARCHAR(20),
  deposit_amount DECIMAL(12, 2),

  -- Cancellation
  cancellation_type VARCHAR(20) NOT NULL,
  cancellation_deadline_amount INTEGER,
  cancellation_deadline_unit VARCHAR(10),
  cancellation_before VARCHAR(20),

  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE (property_id, code),
  INDEX idx_rate_plans_room (room_type_id),
  INDEX idx_rate_plans_property (property_id),
  INDEX idx_rate_plans_status (status)
);

-- Availability (Partitioned by date range)
CREATE TABLE availability (
  property_id UUID NOT NULL,
  room_type_id UUID NOT NULL,
  rate_plan_id UUID NOT NULL,
  date DATE NOT NULL,
  available INTEGER NOT NULL,
  total INTEGER NOT NULL,
  price_amount DECIMAL(12, 2),
  price_currency CHAR(3),
  status VARCHAR(20) DEFAULT 'available',

  PRIMARY KEY (property_id, room_type_id, rate_plan_id, date),
  INDEX idx_availability_date (date),
  INDEX idx_availability_property (property_id, date)
) PARTITION BY RANGE (date);

-- Create partitions for availability
CREATE TABLE availability_2026_q1 PARTITION OF availability
  FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');

CREATE TABLE availability_2026_q2 PARTITION OF availability
  FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

-- Additional partitions created as needed
```

---

## Supplier Integration

### Integration Architecture

```typescript
export interface SupplierAdapter {
  // Identity
  readonly supplierId: string;
  readonly name: string;

  // Capabilities
  readonly capabilities: SupplierCapabilities;

  // Content
  fetchProperties(criteria: FetchCriteria): Promise<Property[]>;
  fetchPropertyDetails(propertyCode: string): Promise<PropertyDetails>;
  fetchImages(propertyCode: string): Promise<MediaItem[]>;

  // Inventory
  fetchAvailability(
    propertyCode: string,
    dates: DateRange,
    occupancy: Occupancy
  ): Promise<Availability[]>;

  // Pricing
  fetchPricing(
    propertyCode: string,
    dates: DateRange,
    occupancy: Occupancy,
    ratePlanCode?: string
  ): Promise<PricingQuote>;

  // Booking
  createReservation(bookingRequest: BookingRequest): Promise<Reservation>;
  cancelReservation(reservationId: string): Promise<Cancellation>;
  fetchReservation(reservationId: string): Promise<Reservation>;

  // Webhooks
  handleWebhook(event: SupplierEvent): Promise<void>;
}

interface SupplierCapabilities {
  content: {
    fullDescriptions: boolean;
    images: boolean;
    amenities: boolean;
    roomTypes: boolean;
    policies: boolean;
  };
  inventory: {
    realTimeAvailability: boolean;
    batchAvailability: boolean;
    availabilityCache: number; // TTL in seconds
  };
  pricing: {
    realTimePricing: boolean;
    dynamicPricing: boolean;
    promotions: boolean;
  };
  booking: {
    create: boolean;
    modify: boolean;
    cancel: boolean;
    statusCheck: boolean;
  };
  webhooks: {
    supported: boolean;
    events: string[];
  };
}
```

### Normalization Pipeline

```typescript
export class ContentNormalizer {
  async normalizeProperty(
    rawProperty: RawProperty,
    supplier: string
  ): Promise<Property> {
    // 1. Map property type
    const type = this.mapPropertyType(rawProperty.type, supplier);

    // 2. Normalize location
    const location = await this.normalizeLocation(rawProperty.location);

    // 3. Translate amenities
    const amenities = await this.normalizeAmenities(
      rawProperty.amenities,
      supplier
    );

    // 4. Normalize images
    const images = await this.normalizeImages(rawProperty.images);

    // 5. Map room types
    const roomTypes = await this.normalizeRoomTypes(
      rawProperty.roomTypes,
      supplier
    );

    // 6. Extract and normalize rating
    const rating = this.normalizeRating(rawProperty.rating);

    return {
      id: this.generateId(supplier, rawProperty.code),
      supplierId: supplier,
      supplierCode: rawProperty.code,
      internalCode: this.generateInternalCode(supplier, rawProperty.code),
      name: this.localizeText(rawProperty.name),
      type,
      category: this.determineCategory(type, rating),
      location,
      contact: rawProperty.contact,
      content: this.normalizeContent(rawProperty.content),
      rating,
      amenities,
      roomTypes,
      status: 'active',
      isActive: true,
      metadata: {
        createdAt: new Date(),
        updatedAt: new Date(),
        lastSyncedAt: new Date(),
        sourceQuality: this.assessSourceQuality(rawProperty),
        completeness: this.calculateCompleteness(rawProperty),
      },
    };
  }

  private mapPropertyType(
    rawType: string,
    supplier: string
  ): PropertyType {
    const mappings: Record<string, Record<string, PropertyType>> = {
      hotelbeds: {
        'Hotel': 'hotel',
        'Apartment': 'apartment',
        'Hostel': 'hostel',
        'Villa': 'villa',
      },
      expedia: {
        'hotel': 'hotel',
        'vacation_rental': 'villa',
        'hostel': 'hostel',
      },
    };

    return mappings[supplier]?.[rawType] || 'hotel';
  }

  private async normalizeAmenities(
    rawAmenities: RawAmenity[],
    supplier: string
  ): Promise<Amenity[]> {
    const result: Amenity[] = [];

    for (const raw of rawAmenities) {
      // Map to internal amenity code
      const mapped = await this.amenityMapper.map(raw.code, supplier);

      if (mapped) {
        result.push({
          id: mapped.id,
          code: mapped.code,
          type: mapped.type,
          name: mapped.name,
          description: mapped.description,
          icon: mapped.icon,
          complimentary: raw.complimentary ?? true,
          available: raw.available,
        });
      }
    }

    return result;
  }

  private assessSourceQuality(data: RawProperty): number {
    let score = 0;

    // Has images
    if (data.images?.length > 0) score += 0.2;
    if (data.images?.length >= 5) score += 0.1;

    // Has description
    if (data.description?.length > 100) score += 0.2;

    // Has amenities
    if (data.amenities?.length > 0) score += 0.1;

    // Has room types
    if (data.roomTypes?.length > 0) score += 0.2;

    // Has coordinates
    if (data.latitude && data.longitude) score += 0.1;

    // Has contact info
    if (data.phone || data.email || data.website) score += 0.1;

    return Math.min(score, 1);
  }

  private calculateCompleteness(data: RawProperty): number {
    const required = [
      'name', 'description', 'images', 'amenities',
      'roomTypes', 'latitude', 'longitude', 'address'
    ];

    const present = required.filter(field =>
      data[field] && (
        Array.isArray(data[field]) ? data[field].length > 0 : true
      )
    );

    return present.length / required.length;
  }
}
```

---

## Content Management

### Image Processing Pipeline

```typescript
export class ImageProcessingService {
  async processPropertyImages(
    propertyId: string,
    images: RawImage[],
    source: string
  ): Promise<MediaItem[]> {
    const results: MediaItem[] = [];

    for (const raw of images) {
      // 1. Download original
      const original = await this.downloadImage(raw.url);

      // 2. Validate image
      if (!this.isValidImage(original)) {
        continue;
      }

      // 3. Generate thumbnails
      const thumbnails = await this.generateThumbnails(original);

      // 4. Optimize for web
      const optimized = await this.optimizeImage(original);

      // 5. Detect category (ML)
      const category = await this.detectImageCategory(optimized);

      // 6. Upload to CDN
      const storageKey = `properties/${propertyId}/${crypto.randomUUID()}.webp`;
      const cdnUrl = await this.cdnService.upload(storageKey, optimized.buffer);

      // 7. Store metadata
      const mediaItem: MediaItem = {
        id: crypto.randomUUID(),
        url: cdnUrl,
        thumbnailUrl: thumbnails.small.url,
        type: 'photo',
        category,
        caption: raw.caption ? this.localizeText(raw.caption) : undefined,
        width: optimized.width,
        height: optimized.height,
        order: raw.order ?? results.length,
        createdAt: new Date(),
      };

      results.push(mediaItem);
    }

    // Sort and re-order
    return this.sortImages(results);
  }

  private async generateThumbnails(
    image: ImageBuffer
  ): Promise<{ small: Thumbnail; medium: Thumbnail; large: Thumbnail }> {
    return {
      small: await this.resize(image, 150, 150),
      medium: await this.resize(image, 400, 300),
      large: await this.resize(image, 1200, 800),
    };
  }

  private async detectImageCategory(
    image: ImageBuffer
  ): Promise<MediaCategory | undefined> {
    // Use ML model to classify image
    const classification = await this.imageClassifier.classify(image.buffer);

    const mapping: Record<string, MediaCategory> = {
      'exterior': 'exterior',
      'lobby': 'lobby',
      'room_bedroom': 'room',
      'room_bathroom': 'bathroom',
      'pool': 'pool',
      'restaurant': 'restaurant',
      'gym': 'gym',
      'view': 'view',
    };

    return mapping[classification.label];
  }

  private sortImages(images: MediaItem[]): MediaItem[] {
    // Priority order for property images
    const categoryPriority: Record<MediaCategory, number> = {
      'exterior': 1,
      'lobby': 2,
      'room': 3,
      'view': 4,
      'pool': 5,
      'restaurant': 6,
      'gym': 7,
      'bathroom': 8,
      'other': 99,
    };

    return images.sort((a, b) => {
      const priorityA = categoryPriority[a.category || 'other'] ?? 99;
      const priorityB = categoryPriority[b.category || 'other'] ?? 99;
      return priorityA - priorityB || a.order - b.order;
    });
  }
}
```

---

## Pricing Architecture

### Pricing Engine

```typescript
export class AccommodationPricingEngine {
  async calculatePrice(
    request: PricingRequest
  ): Promise<PricingResult> {
    const { propertyId, roomTypeId, dates, occupancy, ratePlanCode } = request;

    // 1. Get base rate
    const baseRate = await this.getBaseRate(roomTypeId, dates);

    // 2. Apply length-of-stay adjustments
    const losRate = this.applyLOSAdjustment(baseRate, dates);

    // 3. Apply occupancy adjustments
    const occupancyRate = this.applyOccupancyAdjustment(
      losRate,
      occupancy,
      roomTypeId
    );

    // 4. Add taxes
    const withTax = await this.applyTaxes(occupancyRate, propertyId);

    // 5. Add fees
    const withFees = await this.applyFees(withTax, propertyId);

    // 6. Apply promotions
    const discounted = await this.applyPromotions(
      withFees,
      request
    );

    // 7. Apply markup (agency margin)
    const finalRate = this.applyMarkup(discounted);

    return {
      baseRate,
      taxes: this.calculateTaxBreakdown(finalRate, propertyId),
      fees: this.calculateFeeBreakdown(finalRate, propertyId),
      discounts: this.calculateDiscountBreakdown(discounted),
      total: finalRate,
      currency: baseRate.currency,
      breakdown: this.generateBreakdown(finalRate, dates),
    };
  }

  private applyLOSAdjustment(
    rate: DailyRate[],
    dates: DateRange
  ): DailyRate[] {
    const nights = this.countNights(dates);

    return rate.map(r => {
      let multiplier = 1;

      // Discount for longer stays
      if (nights >= 7) multiplier = 0.9; // 10% off
      else if (nights >= 4) multiplier = 0.95; // 5% off
      // Premium for very short stays
      else if (nights === 1) multiplier = 1.1; // 10% premium

      return {
        ...r,
        amount: r.amount * multiplier,
      };
    });
  }

  private async applyPromotions(
    rate: DailyRate[],
    request: PricingRequest
  ): Promise<DailyRate[]> {
    const applicable = await this.promotionService.findApplicable(request);

    let adjusted = rate;

    for (const promo of applicable) {
      switch (promo.type) {
        case 'early_booking':
          adjusted = this.applyEarlyBookingDiscount(adjusted, promo);
          break;
        case 'long_stay':
          adjusted = this.applyLongStayDiscount(adjusted, promo);
          break;
        case 'last_minute':
          adjusted = this.applyLastMinuteDiscount(adjusted, promo);
          break;
        case 'flash_sale':
          adjusted = this.applyFlashSaleDiscount(adjusted, promo);
          break;
      }
    }

    return adjusted;
  }

  private applyMarkup(rate: DailyRate[]): DailyRate[] {
    const markup = this.agencyMarkup.getMarkup('accommodation');

    return rate.map(r => ({
      ...r,
      amount: r.amount * (1 + markup),
    }));
  }
}
```

---

## Search Infrastructure

### Elasticsearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "supplier_id": { "type": "keyword" },
      "name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" },
          "english": {
            "type": "text",
            "analyzer": "english"
          },
          "fuzzy": {
            "type": "text",
            "analyzer": "standard"
          }
        }
      },
      "location": {
        "type": "geo_point"
      },
      "geohash": { "type": "keyword" },
      "address": {
        "properties": {
          "city": { "type": "keyword" },
          "country_code": { "type": "keyword" },
          "state": { "type": "keyword" }
        }
      },
      "type": { "type": "keyword" },
      "category": { "type": "keyword" },
      "star_rating": { "type": "integer" },
      "amenities": { "type": "keyword" },
      "price_range": {
        "type": "integer_range"
      },
      "quality_score": { "type": "double" },
      "popularity_score": { "type": "double" },
      "guest_rating": {
        "type": "double"
      },
      "review_count": { "type": "integer" }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "autocomplete_filter"]
        }
      },
      "filter": {
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20
        }
      }
    }
  }
}
```

### Search Query Builder

```typescript
export class AccommodationSearchBuilder {
  buildSearchQuery(criteria: SearchCriteria): ElasticsearchQuery {
    const must: QueryClause[] = [];
    const filter: QueryClause[] = [];
    const should: QueryClause[] = [];

    // 1. Basic filters
    if (criteria.destination) {
      filter.push({
        bool: {
          should: [
            { match: { "address.city": criteria.destination } },
            { match: { "name.english": criteria.destination } },
            {
              geo_distance: {
                distance: `${criteria.radius || 50}km`,
                location: criteria.coordinates
              }
            }
          ]
        }
      });
    }

    // 2. Dates and availability
    if (criteria.checkIn && criteria.checkOut) {
      filter.push({
        range: {
          "price_range": {
            gte: criteria.minPrice,
            lte: criteria.maxPrice
          }
        }
      });
    }

    // 3. Property type
    if (criteria.types?.length) {
      filter.push({ terms: { type: criteria.types } });
    }

    // 4. Star rating
    if (criteria.starRating) {
      filter.push({
        range: { star_rating: { gte: criteria.starRating } }
      });
    }

    // 5. Amenities
    if (criteria.amenities?.length) {
      filter.push({
        terms: { amenities: criteria.amenities }
      });
    }

    // 6. Guest rating
    if (criteria.minGuestRating) {
      filter.push({
        range: { guest_rating: { gte: criteria.minGuestRating } }
      });
    }

    // 7. Price range
    if (criteria.minPrice !== undefined || criteria.maxPrice !== undefined) {
      filter.push({
        range: {
          "price_range": {
            gte: criteria.minPrice || 0,
            lte: criteria.maxPrice || 10000
          }
        }
      });
    }

    // 8. Scoring - relevance based on multiple factors
    should.push(
      { rank_feature: { field: "quality_score", boost: 0.3 } },
      { rank_feature: { field: "popularity_score", boost: 0.2 } },
      { rank_feature: { field: "guest_rating", boost: 0.5 } }
    );

    // 9. Distance scoring (if coordinates provided)
    if (criteria.coordinates) {
      should.push({
        gauss: {
          location: {
            origin: criteria.coordinates,
            scale: `${criteria.radius || 50}km`,
            decay: 0.5
          }
        }
      });
    }

    return {
      query: {
        bool: {
          must: must.length ? must : undefined,
          filter,
          should
        }
      },
      from: criteria.offset || 0,
      size: criteria.limit || 20,
      sort: this.buildSortCriteria(criteria),
      aggs: this.buildAggregations()
    };
  }

  private buildSortCriteria(criteria: SearchCriteria): SortClause[] {
    switch (criteria.sortBy) {
      case 'price_asc':
        return [{ 'price_range.min': 'asc' }];
      case 'price_desc':
        return [{ 'price_range.max': 'desc' }];
      case 'rating':
        return [{ guest_rating: 'desc' }];
      case 'popularity':
        return [{ popularity_score: 'desc' }];
      case 'distance':
        return [
          { _geo_distance: { location: criteria.coordinates, order: 'asc' } }
        ];
      case 'recommended':
      default:
        return [{ _score: 'desc' }];
    }
  }

  private buildAggregations(): AggregationSpec {
    return {
      types: { terms: { field: 'type' } },
      star_ratings: { terms: { field: 'star_rating' } },
      price_ranges: {
        range: {
          field: 'price_range.min',
          ranges: [
            { to: 100, key: 'budget' },
            { from: 100, to: 200, key: 'mid_range' },
            { from: 200, key: 'luxury' }
          ]
        }
      },
      amenities: { terms: { field: 'amenities', size: 20 } }
    };
  }
}
```

---

## Data Synchronization

### Sync Strategy

```typescript
export class InventorySyncService {
  async syncPropertyAvailability(
    propertyId: string,
    dateRange: DateRange
  ): Promise<void> {
    const property = await this.propertyRepository.findById(propertyId);

    // 1. Fetch from supplier
    const availability = await this.supplierAdapter.fetchAvailability(
      property.supplierCode,
      dateRange,
      { adults: 2, children: 0 }
    );

    // 2. Upsert to cache (Redis)
    for (const record of availability) {
      const key = this.cacheKey(propertyId, record.date, record.ratePlanId);
      await this.redis.setex(
        key,
        this.CACHE_TTL,
        JSON.stringify(record)
      );
    }

    // 3. Update PostgreSQL (for reporting/analytics)
    await this.availabilityRepository.bulkUpsert(availability);

    // 4. Update search index if needed
    await this.updateSearchIndex(propertyId, availability);
  }

  async syncMultipleProperties(
    propertyIds: string[],
    dateRange: DateRange
  ): Promise<void> {
    // Parallel sync with rate limiting
    const batches = this.chunk(propertyIds, 10);

    for (const batch of batches) {
      await Promise.allSettled(
        batch.map(id => this.syncPropertyAvailability(id, dateRange))
      );

      // Rate limit delay
      await this.delay(100);
    }
  }

  private cacheKey(propertyId: string, date: Date, ratePlanId: string): string {
    const dateStr = date.toISOString().split('T')[0];
    return `availability:${propertyId}:${ratePlanId}:${dateStr}`;
  }

  private readonly CACHE_TTL = 300; // 5 minutes
}
```

### Webhook Handler

```typescript
export class SupplierWebhookHandler {
  async handleWebhook(
    supplierId: string,
    event: SupplierWebhookEvent
  ): Promise<void> {
    switch (event.type) {
      case 'availability.changed':
        await this.handleAvailabilityChange(event);
        break;

      case 'pricing.changed':
        await this.handlePricingChange(event);
        break;

      case 'property.updated':
        await this.handlePropertyUpdate(event);
        break;

      case 'booking.created':
      case 'booking.cancelled':
      case 'booking.modified':
        await this.handleBookingEvent(event);
        break;

      default:
        this.logger.warn(`Unknown event type: ${event.type}`);
    }
  }

  private async handleAvailabilityChange(event: SupplierWebhookEvent): Promise<void> {
    const { propertyCode, dateRange } = event.data;

    // Invalidate cache
    await this.invalidateAvailabilityCache(propertyCode, dateRange);

    // Trigger refresh
    await this.syncService.syncPropertyAvailability(
      propertyCode,
      dateRange
    );
  }

  private async invalidateAvailabilityCache(
    propertyCode: string,
    dateRange: DateRange
  ): Promise<void> {
    const property = await this.propertyRepository.findBySupplierCode(
      event.supplierId,
      propertyCode
    );

    const dates = this.eachDate(dateRange);

    for (const date of dates) {
      const pattern = `availability:${property.id}:*:${date}`;
      await this.redis.delPattern(pattern);
    }
  }
}
```

---

## API Endpoints

### Property Endpoints

```
GET    /accommodations/properties
GET    /accommodations/properties/:id
GET    /accommodations/properties/:id/room-types
GET    /accommodations/properties/:id/amenities
GET    /accommodations/properties/:id/images
```

### Search Endpoints

```
POST   /accommodations/search
GET    /accommodations/autocomplete
POST   /accommodations/map-search
GET    /accommodations/facets
```

### Availability & Pricing Endpoints

```
POST   /accommodations/availability
POST   /accommodations/pricing
GET    /accommodations/properties/:id/rate-plans
```

---

**Next:** [Property Management](./ACCOMMODATION_CATALOG_02_PROPERTIES.md) — Property CRUD, content, and amenities
