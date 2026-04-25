# Supplier Integration 02: Data Deep Dive

> Complete guide to supplier data models, field mapping, and normalization

---

## Document Overview

**Series:** Supplier Integration Deep Dive (Document 2 of 4)
**Focus:** Data — Supplier data models, field mapping, normalization, category standards
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Standard Data Model](#standard-data-model)
3. [Field Mapping](#field-mapping)
4. [Category Normalization](#category-normalization)
5. [Room Type Mapping](#room-type-mapping)
6. [Amenity Standardization](#amenity-standardization)
7. [Price Normalization](#price-normalization)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

Each supplier has different data formats and field names. The data layer normalizes all supplier responses into a standard model, enabling consistent application logic regardless of source. This includes mapping hotel categories, room types, amenities, prices, and availability statuses.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Standard Model** | Unified schema for all supplier data |
| **Field Mapping** | Supplier-specific field to standard field mapping |
| **Category Mapping** | Star ratings, property types normalized |
| **Room Type Mapping** | Room categories standardized |
| **Amenity Mapping** | Free-form amenities to standardized set |
| **Price Normalization** | Different price structures to common format |

---

## Standard Data Model

### Hotel Model

```typescript
// models/hotel.model.ts

export interface StandardHotel {
  // Identification
  id: string;                 // Our internal ID
  supplierId: string;         // Supplier's hotel ID
  supplierCode: string;       // Supplier: tbo|tb|12345

  // Basic info
  name: string;
  nameLocal?: string;         // Local language name
  description: string;
  shortDescription?: string;

  // Location
  location: {
    address: string;
    city: string;
    state?: string;
    country: string;
    postalCode?: string;
    coordinates?: {
      latitude: number;
      longitude: number;
    };
    landmarks?: Array<{
      name: string;
      distance: number;  // in km
      distanceUnit: 'km' | 'miles';
    }>;
  };

  // Classification
  category: HotelCategory;
  starRating: number;         // 1-5
  supplierRating?: number;    // Supplier's own rating

  // Contact
  contact: {
    phone?: string;
    email?: string;
    website?: string;
  };

  // Media
  images: HotelImage[];
  videos?: HotelVideo[];

  // Amenities
  amenities: {
    general: Amenity[];
    room: Amenity[];
    property: Amenity[];
  };

  // Rooms
  rooms: StandardRoom[];

  // Pricing
  pricing?: {
    currency: string;
    taxRate: number;
    serviceCharge?: number;
  };

  // Policies
  policies: {
    checkIn: CheckInPolicy;
    checkOut: CheckOutPolicy;
    cancellation: CancellationPolicy[];
    payment: PaymentPolicy[];
    childPolicy?: string;
    petPolicy?: string;
  };

  // Metadata
  metadata: {
    supplier: string;
    lastUpdated: Date;
    isActive: boolean;
    commissionRate?: number;
    contractType?: 'net' | 'commission';
  };
}

export interface StandardRoom {
  id: string;
  supplierRoomId: string;
  name: string;
  type: RoomType;
  occupancy: {
    maxAdults: number;
    maxChildren?: number;
    maxGuests: number;
  };
  beds: Bed[];
  size?: number;              // sq ft
  amenities: Amenity[];
  images: HotelImage[];
  pricing?: RoomPricing;
}

export enum HotelCategory {
  HOTEL = 'hotel',
  RESORT = 'resort',
  APARTMENT = 'apartment',
  VILLA = 'villa',
  HOSTEL = 'hostel',
  GUEST_HOUSE = 'guest_house',
  BOUTIQUE = 'boutique',
  HERITAGE = 'heritage',
}

export enum RoomType {
  STANDARD = 'standard',
  DELUXE = 'deluxe',
  SUITE = 'suite',
  PREMIER = 'premier',
  EXECUTIVE = 'executive',
  FAMILY = 'family',
  CONNECTING = 'connecting',
  ADJOINING = 'adjoining',
}

export interface Amenity {
  id: string;
  name: string;
  category: 'general' | 'room' | 'property';
  icon?: string;
  included: boolean;
}

export interface HotelImage {
  url: string;
  type: ' exterior' | 'lobby' | 'room' | 'bathroom' | 'dining' | 'other';
  caption?: string;
  width?: number;
  height?: number;
}
```

### Search Response Model

```typescript
// models/search.model.ts

export interface StandardSearchResponse {
  searchId: string;
  timestamp: Date;
  results: StandardSearchResult[];
  totalCount: number;
  hasMore: boolean;
  searchParams: SearchParams;
  suppliers: string[];
  duration: number;  // ms
}

export interface StandardSearchResult {
  hotel: Pick<StandardHotel,
    'id' | 'supplierId' | 'name' | 'category' | 'starRating' |
    'location' | 'images' | 'amenities'
  >;
  rooms: RoomResult[];
  pricing: {
    basePrice: number;
    taxes: number;
    fees: number;
    totalPrice: number;
    currency: string;
    pricePerNight: number;
    numberOfNights: number;
  };
  availability: {
    status: 'available' | 'limited' | 'sold_out';
    roomsLeft?: number;
  };
  supplier: {
    id: string;
    name: string;
    inclusion: 'all_inclusive' | 'breakfast' | 'room_only';
  };
  ranking: {
    score: number;
    relevance: number;
    popularity: number;
  };
}
```

---

## Field Mapping

### Common Field Mappings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOTEL FIELD MAPPINGS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STANDARD FIELD         │ TBO                    │ TravelBoutique         │
│  ───────────────────────┼────────────────────────┼─────────────────────────│
│  id                     │ HotelCode              │ HotelCode               │
│  name                   │ HotelName              │ HotelName               │
│  description            │ HotelDescription       │ Description             │
│  starRating             │ StarRating             │ StarRating              │
│  address                │ HotelAddress           │ Address                 │
│  city                   │ CityCode               │ CityCode                │
│  latitude               │ Latitude               │ Latitude                │
│  longitude              │ Longitude              │ Longitude               │
│  images                 │ HotelPictures          │ Images                  │
│  amenities              │ HotelFacilities        │ Facilities              │
│  checkIn                │ CheckInTime            │ CheckIn                 │
│  checkOut               │ CheckOutTime           │ CheckOut                │
│  cancellationPolicy     │ CancellationPolicy     │ CancellationPolicy     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mapping Configuration

```typescript
// config/field-mappings.config.ts

export const FIELD_MAPPINGS: Record<string, FieldMappingConfig> = {
  tbo: {
    supplierId: 'tbo',
    mappings: {
      hotel: {
        id: 'HotelCode',
        name: 'HotelName',
        description: 'HotelDescription',
        starRating: 'StarRating',
        address: 'HotelAddress',
        city: 'CityCode',
        images: 'HotelPictures',
        amenities: 'HotelFacilities',
      },
      room: {
        id: 'RoomIndex',
        name: 'RoomType',
        type: 'RoomTypeName',
        maxOccupancy: 'MaxOccupancy',
      },
      pricing: {
        basePrice: 'Price.Price',
        taxes: 'Price.Tax',
        totalPrice: 'Price.TotalFare',
        currency: 'Price.Currency',
      },
    },
    transformers: {
      images: transformTBOImages,
      amenities: transformTBOAmenities,
      address: transformTBOAddress,
    },
  },

  travelboutique: {
    supplierId: 'travelboutique',
    mappings: {
      hotel: {
        id: 'HotelCode',
        name: 'HotelName',
        description: 'Description',
        starRating: 'StarRating',
        address: 'Address',
        city: 'CityCode',
        images: 'Images',
        amenities: 'Facilities',
      },
      room: {
        id: 'RoomIndex',
        name: 'RoomType',
        type: 'RoomCategory',
        maxOccupancy: 'Occupancy',
      },
      pricing: {
        basePrice: 'Price.BasePrice',
        taxes: 'Price.Tax',
        totalPrice: 'Price.TotalPrice',
        currency: 'Price.CurrencyCode',
      },
    },
    transformers: {
      images: transformTBImages,
      amenities: transformTBAmenities,
      address: transformTBAddress,
    },
  },
};
```

### Field Mapper Implementation

```typescript
// services/field-mapper.service.ts

export class FieldMapperService {
  private mappings: Map<string, FieldMappingConfig>;

  constructor() {
    this.mappings = new Map(
      Object.entries(FIELD_MAPPINGS)
    );
  }

  mapHotel(
    supplierId: string,
    sourceData: any
  ): StandardHotel {
    const config = this.mappings.get(supplierId);
    if (!config) {
      throw new Error(`No mapping config for supplier: ${supplierId}`);
    }

    const mapped: Partial<StandardHotel> = {};

    // Map direct fields
    for (const [standardField, sourceField] of Object.entries(
      config.mappings.hotel
    )) {
      const value = this.getNestedValue(sourceData, sourceField);
      if (value !== undefined) {
        mapped[standardField] = value;
      }
    }

    // Apply transformers
    if (config.transformers.images) {
      mapped.images = config.transformers.images(
        this.getNestedValue(sourceData, config.mappings.hotel.images)
      );
    }

    if (config.transformers.amenities) {
      mapped.amenities = config.transformers.amenities(
        this.getNestedValue(sourceData, config.mappings.hotel.amenities)
      );
    }

    // Add metadata
    mapped.metadata = {
      supplier: supplierId,
      lastUpdated: new Date(),
      isActive: true,
    };

    return mapped as StandardHotel;
  }

  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      return current?.[key];
    }, obj);
  }
}
```

---

## Category Normalization

### Star Rating Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STAR RATING NORMALIZATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SUPPLIER RATING    │ NORMALIZED RATING │ NOTES                           │
│  ────────────────────┼──────────────────┼─────────────────────────────    │
│  5 Star             │ 5                  │ Direct match                   │
│  4 Star             │ 4                  │ Direct match                   │
│  3 Star             │ 3                  │ Direct match                   │
│  2 Star             │ 2                  │ Direct match                   │
│  1 Star             │ 1                  │ Direct match                   │
│  5 Star Deluxe      │ 5                  │ Map to 5                      │
│  4 Star Deluxe      │ 4                  │ Map to 4                      │
│  4.5 Star           │ 5                  │ Round up                      │
│  3.5 Star           │ 4                  │ Round up                      │
│  First Class        │ 4                  │ Industry standard              │
│  Second Class       │ 3                  │ Industry standard              │
│  Third Class        │ 2                  │ Industry standard              │
│  Luxury             │ 5                  │ Map to 5                      │
│  Budget             │ 2                  │ Map to 2                      │
│  Economy            │ 2                  │ Map to 2                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Property Type Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROPERTY TYPE MAPPING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STANDARD CATEGORY      │ TBO           │ TravelBoutique │ MakCorp       │
│  ────────────────────────┼───────────────┼────────────────┼──────────────│
│  hotel                   │ Hotel         │ Hotel          │ Hotel         │
│  resort                  │ Resort        │ Resort         │ Resort        │
│  apartment               │ Apartment     │ Apartment      │ Apt           │
│  villa                   │ Villa         │ Villa          │ Villa         │
│  hostel                  │ Hostel        │ Hostel         │ -             │
│  guest_house             │ Guest House   │ Guest House    │ GuestHouse    │
│  boutique                │ Boutique      │ Boutique       │ -             │
│  heritage                │ Heritage      │ Heritage       │ -             │
│  serviced_apartment      │ Serviced Apt  │ Serviced Apt   │ ServicedApt   │
│  motel                   │ -             │ Motel          │ Motel         │
│  camp                    │ -             │ Camp Site      │ -             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Category Mapper

```typescript
// services/category-mapper.service.ts

export const CATEGORY_MAPPINGS: Record<string, Record<string, HotelCategory>> = {
  tbo: {
    'hotel': HotelCategory.HOTEL,
    'resort': HotelCategory.RESORT,
    'apartment': HotelCategory.APARTMENT,
    'villa': HotelCategory.VILLA,
    'guest house': HotelCategory.GUEST_HOUSE,
    'boutique': HotelCategory.BOUTIQUE,
    'heritage': HotelCategory.HERITAGE,
  },

  travelboutique: {
    'hotel': HotelCategory.HOTEL,
    'resort': HotelCategory.RESORT,
    'apartment': HotelCategory.APARTMENT,
    'villa': HotelCategory.VILLA,
    'hostel': HotelCategory.HOSTEL,
    'guest house': HotelCategory.GUEST_HOUSE,
    'boutique hotel': HotelCategory.BOUTIQUE,
  },

  makcorp: {
    'hotel': HotelCategory.HOTEL,
    'resort': HotelCategory.RESORT,
    'apt': HotelCategory.APARTMENT,
    'villa': HotelCategory.VILLA,
    'guesthouse': HotelCategory.GUEST_HOUSE,
    'servicedapt': HotelCategory.APARTMENT,
    'motel': HotelCategory.HOTEL,  // Map motel to hotel
  },
};

export class CategoryMapperService {
  normalizeCategory(
    supplierId: string,
    supplierCategory: string
  ): HotelCategory {
    const mappings = CATEGORY_MAPPINGS[supplierId];
    if (!mappings) {
      return HotelCategory.HOTEL;  // Default
    }

    const normalized = mappings[supplierCategory.toLowerCase()];
    return normalized || HotelCategory.HOTEL;
  }
}
```

---

## Room Type Mapping

### Standard Room Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ROOM TYPE MAPPING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STANDARD TYPE      │ TBO VARIATIONS                            │ TB VARIATIONS │
│  ────────────────────┼───────────────────────────────────────────────────│
│  standard           │ Standard Room, Standard, Basic                   │ Standard      │
│  deluxe             │ Deluxe Room, Deluxe, Superior                   │ Deluxe        │
│  suite              │ Suite, Suite Room, Junior Suite                  │ Suite         │
│  premier            │ Premier Room, Premier, Premium                  │ Premium       │
│  executive          │ Executive Room, Executive, Club                 │ Executive     │
│  family             │ Family Room, Family, Family Suite                │ Family        │
│  connecting         │ Connecting Rooms, Connecting                   │ Connecting   │
│  adjoining          │ Adjoining Rooms, Adjoining                       │ -             │
│  studio             │ Studio Room, Studio                             │ Studio        │
│  penthouse          │ Penthouse, Penthouse Suite                       │ -             │
│  presidential       │ Presidential Suite, Presidential                 │ Presidential  │
│  royal              │ Royal Suite, Royal                              │ -             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Room Type Mapper

```typescript
// services/room-type-mapper.service.ts

export const ROOM_TYPE_MAPPINGS: Record<string, Record<string, RoomType>> = {
  tbo: {
    'standard room': RoomType.STANDARD,
    'deluxe room': RoomType.DELUXE,
    'suite': RoomType.SUITE,
    'junior suite': RoomType.SUITE,
    'executive suite': RoomType.EXECUTIVE,
    'presidential suite': RoomType.SUITE,
    'family room': RoomType.FAMILY,
    'family suite': RoomType.FAMILY,
    'connecting rooms': RoomType.CONNECTING,
    'studio room': RoomType.STANDARD,
    'premier room': RoomType.PREMIER,
  },

  travelboutique: {
    'standard': RoomType.STANDARD,
    'deluxe': RoomType.DELUXE,
    'suite': RoomType.SUITE,
    'premium': RoomType.PREMIER,
    'executive': RoomType.EXECUTIVE,
    'family': RoomType.FAMILY,
    'connecting': RoomType.CONNECTING,
    'studio': RoomType.STANDARD,
  },
};

export class RoomTypeMapperService {
  normalizeRoomType(
    supplierId: string,
    supplierRoomType: string
  ): RoomType {
    const mappings = ROOM_TYPE_MAPPINGS[supplierId];
    if (!mappings) {
      return RoomType.STANDARD;  // Default
    }

    const normalized = mappings[supplierRoomType.toLowerCase()];
    return normalized || RoomType.STANDARD;
  }

  getRoomTypeOrder(roomType: RoomType): number {
    // For sorting results by room type quality
    const order = {
      [RoomType.PRESIDENTIAL]: 10,
      [RoomType.ROYAL]: 9,
      [RoomType.SUITE]: 8,
      [RoomType.EXECUTIVE]: 7,
      [RoomType.PREMIER]: 6,
      [RoomType.DELUXE]: 5,
      [RoomType.FAMILY]: 4,
      [RoomType.STANDARD]: 3,
      [RoomType.CONNECTING]: 2,
      [RoomType.ADJJOINING]: 1,
    };
    return order[roomType] || 0;
  }
}
```

---

## Amenity Standardization

### Amenity Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AMENITY STANDARDIZATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GENERAL AMENITIES                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  wifi                          │ Free WiFi, Internet, Wireless Internet│   │
│  │  parking                       │ Parking, Car Parking                │   │
│  │  restaurant                    │ Restaurant, On-site Restaurant      │   │
│  │  bar                           │ Bar, Lounge Bar                   │   │
│  │  pool                          │ Swimming Pool, Pool               │   │
│  │  fitness                       │ Fitness Center, Gym               │   │
│  │  spa                           │ Spa, Wellness Center              │   │
│  │  air_conditioning              │ AC, Air Conditioning              │   │
│  │  elevator                      │ Lift, Elevator                    │   │
│  │  reception_24h                │ 24-hour Reception, 24/7 Front Desk │   │
│  │  room_service                  │ Room Service                      │   │
│  │  laundry                       │ Laundry Service                    │   │
│  │  conference_room               │ Meeting Room, Conference Room     │   │
│  │  business_center               │ Business Center                   │   │
│  │  garden                        │ Garden, Landscaped Garden          │   │
│  │  terrace                       │ Terrace, Sun Terrace               │   │
│  │  balcony                       │ Balcony (room-specific)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROOM AMENITIES                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  tv                            │ Television, Cable TV               │   │
│  │  minibar                       │ Mini Bar, Minibar                 │   │
│  │  safe                          │ Room Safe, Safe Deposit Box       │   │
│  │  tea_coffee                    │ Tea/Coffee Maker                  │   │
│  │  hairdryer                    │ Hair Dryer                       │   │
│  │  bathtub                      │ Bathtub, Jacuzzi                  │   │
│  │  shower                       │ Shower                           │   │
│  │  workdesk                     │ Work Desk, Desk                  │   │
│  │  iron                          │ Iron & Ironing Board              │   │
│  │  fridge                        │ Refrigerator                      │   │
│  │  microwave                    │ Microwave                         │   │
│  │  kitchen                       │ Kitchenette                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Amenity Mapper

```typescript
// services/amenity-mapper.service.ts

export const AMENITY_MAPPINGS: Record<string, AmenityMapping> = {
  // General amenities
  'free wifi': { id: 'wifi', name: 'Free WiFi', category: 'general', icon: 'wifi' },
  'wifi': { id: 'wifi', name: 'WiFi', category: 'general', icon: 'wifi' },
  'internet': { id: 'wifi', name: 'Internet', category: 'general', icon: 'wifi' },
  'parking': { id: 'parking', name: 'Parking', category: 'general', icon: 'car' },
  'swimming pool': { id: 'pool', name: 'Swimming Pool', category: 'general', icon: 'pool' },
  'pool': { id: 'pool', name: 'Pool', category: 'general', icon: 'pool' },
  'fitness center': { id: 'fitness', name: 'Fitness Center', category: 'general', icon: 'fitness' },
  'gym': { id: 'fitness', name: 'Gym', category: 'general', icon: 'fitness' },
  'spa': { id: 'spa', name: 'Spa', category: 'general', icon: 'spa' },
  'restaurant': { id: 'restaurant', name: 'Restaurant', category: 'general', icon: 'restaurant' },
  'bar': { id: 'bar', name: 'Bar', category: 'general', icon: 'bar' },
  'air conditioning': { id: 'ac', name: 'Air Conditioning', category: 'general', icon: 'ac' },
  'ac': { id: 'ac', name: 'AC', category: 'general', icon: 'ac' },
  'elevator': { id: 'elevator', name: 'Elevator', category: 'general', icon: 'elevator' },
  'lift': { id: 'elevator', name: 'Lift', category: 'general', icon: 'elevator' },
  '24-hour reception': { id: 'reception_24h', name: '24-Hour Reception', category: 'general', icon: 'clock' },

  // Room amenities
  'television': { id: 'tv', name: 'Television', category: 'room', icon: 'tv' },
  'tv': { id: 'tv', name: 'TV', category: 'room', icon: 'tv' },
  'mini bar': { id: 'minibar', name: 'Mini Bar', category: 'room', icon: 'minibar' },
  'minibar': { id: 'minibar', name: 'Mini Bar', category: 'room', icon: 'minibar' },
  'room safe': { id: 'safe', name: 'Room Safe', category: 'room', icon: 'safe' },
  'safe': { id: 'safe', name: 'Safe', category: 'room', icon: 'safe' },
  'tea coffee maker': { id: 'tea_coffee', name: 'Tea/Coffee Maker', category: 'room', icon: 'coffee' },
  'hair dryer': { id: 'hairdryer', name: 'Hair Dryer', category: 'room', icon: 'hairdryer' },
};

export class AmenityMapperService {
  normalizeAmenities(
    supplierAmenities: string[]
  ): Amenity[] {
    const normalized: Amenity[] = [];
    const seen = new Set<string>();

    for (const amenity of supplierAmenities) {
      const key = amenity.toLowerCase().trim();
      const mapping = this.findMapping(key);

      if (mapping && !seen.has(mapping.id)) {
        normalized.push({
          id: mapping.id,
          name: mapping.name,
          category: mapping.category,
          icon: mapping.icon,
          included: this.isIncluded(key),
        });
        seen.add(mapping.id);
      }
    }

    return normalized;
  }

  private findMapping(key: string): AmenityMapping | null {
    // Direct match
    if (AMENITY_MAPPINGS[key]) {
      return AMENITY_MAPPINGS[key];
    }

    // Partial match
    for (const [mappingKey, mapping] of Object.entries(AMENITY_MAPPINGS)) {
      if (key.includes(mappingKey) || mappingKey.includes(key)) {
        return mapping;
      }
    }

    return null;
  }

  private isIncluded(key: string): boolean {
    // Check if amenity is included or charged extra
    const excluded = ['paid', 'charge', 'extra', 'surcharge'];
    return !excluded.some(word => key.includes(word));
  }
}
```

---

## Price Normalization

### Price Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRICE NORMALIZATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TBO PRICE STRUCTURE                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                  │   │
│  │    "Price": {                                                        │   │
│  │      "Currency": "INR",                                              │   │
│  │      "BasePrice": 40000,              │ Room cost                      │   │
│  │      "Tax": 7200,                     │ Taxes                          │   │
│  │      "OtherCharges": 1200,             │ Service charges               │   │
│  │      "TotalFare": 48400,               │ Final price                   │   │
│  │      "Markup": 5000,                   │ Our markup                     │   │
│  │      "PublishFare": 53400              │ Price to customer             │   │
│  │    }                                                                 │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NORMALIZED PRICE                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                  │   │
│  │    "basePrice": 40000,                │ Cost from supplier             │   │
│  │    "taxes": 7200,                     │ All taxes                      │   │
│  │    "fees": 1200,                      │ Service fees, other charges     │   │
│  │    "totalPrice": 48400,               │ Cost to us                     │   │
│  │    "margin": 5000,                    │ Our markup                     │   │
│  │    "sellingPrice": 53400,              │ Price to customer             │   │
│  │    "currency": "INR",                  │ Standardized to INR/USD         │   │
│  │    "pricePerNight": 10680,             │ For display                    │   │
│  │    "breakdown": {                     │ Detailed breakdown             │   │
│  │      "roomRate": 8000,                 │ Per night room rate            │   │
│  │      "taxRate": 18,                   │ Tax percentage                  │   │
│  │      "serviceCharge": 3                │ Service charge %              │   │
│  │    }                                                                 │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Price Mapper

```typescript
// services/price-mapper.service.ts

export class PriceMapperService {
  normalizePrice(
    supplierId: string,
    supplierPrice: any,
    numberOfNights: number
  ): NormalizedPrice {
    let basePrice = 0;
    let taxes = 0;
    let fees = 0;
    let totalPrice = 0;
    let currency = 'INR';

    switch (supplierId) {
      case 'tbo':
        basePrice = supplierPrice.Price?.BasePrice || 0;
        taxes = supplierPrice.Price?.Tax || 0;
        fees = supplierPrice.Price?.OtherCharges || 0;
        totalPrice = supplierPrice.Price?.TotalFare || 0;
        currency = supplierPrice.Price?.Currency || 'INR';
        break;

      case 'travelboutique':
        basePrice = supplierPrice.Price?.BasePrice || 0;
        taxes = supplierPrice.Price?.Tax || 0;
        fees = supplierPrice.Price?.ServiceFee || 0;
        totalPrice = supplierPrice.Price?.TotalPrice || 0;
        currency = supplierPrice.Price?.CurrencyCode || 'INR';
        break;

      default:
        // Generic extraction
        basePrice = supplierPrice.basePrice || supplierPrice.price || 0;
        taxes = supplierPrice.tax || 0;
        fees = supplierPrice.fee || 0;
        totalPrice = supplierPrice.total || supplierPrice.totalPrice || 0;
        currency = supplierPrice.currency || 'INR';
    }

    // Convert to INR if needed
    if (currency !== 'INR') {
      const rate = await this.getExchangeRate(currency, 'INR');
      basePrice = basePrice * rate;
      taxes = taxes * rate;
      fees = fees * rate;
      totalPrice = totalPrice * rate;
      currency = 'INR';
    }

    // Add our margin
    const margin = this.calculateMargin(totalPrice);
    const sellingPrice = totalPrice + margin;

    return {
      basePrice,
      taxes,
      fees,
      totalPrice,
      margin,
      sellingPrice,
      currency,
      pricePerNight: Math.ceil(sellingPrice / numberOfNights),
      breakdown: {
        roomRate: Math.ceil(basePrice / numberOfNights),
        taxRate: taxes > 0 ? Math.round((taxes / basePrice) * 100) : 0,
        serviceCharge: fees > 0 ? Math.round((fees / basePrice) * 100) : 0,
        marginRate: Math.round((margin / totalPrice) * 100),
      },
    };
  }

  private calculateMargin(cost: number): number {
    // Margin rules based on cost
    if (cost < 10000) return 500;      // Flat ₹500 for budget
    if (cost < 50000) return cost * 0.10; // 10% for mid-range
    return cost * 0.08;                   // 8% for premium
  }
}
```

---

## Summary

The Supplier Data layer provides:

- **Standard Model**: Unified schema for hotels, rooms, pricing
- **Field Mapping**: Supplier-specific fields to standard fields
- **Category Normalization**: Star ratings, property types standardized
- **Room Type Mapping**: Various room types to standard categories
- **Amenity Standardization**: Free-form amenities to standardized set
- **Price Normalization**: Different price structures to common format

This completes the Data Deep Dive. The next document covers Caching strategies.

---

**Related Documents:**
- [Technical Deep Dive](./SUPPLIER_INTEGRATION_01_TECHNICAL_DEEP_DIVE.md) — Architecture
- [Caching Deep Dive](./SUPPLIER_INTEGRATION_03_CACHING_DEEP_DIVE.md) — Cache strategies
- [Error Handling Deep Dive](./SUPPLIER_INTEGRATION_04_ERROR_HANDLING_DEEP_DIVE.md) — Fallback patterns

**Master Index:** [Supplier Integration Deep Dive Master Index](./SUPPLIER_INTEGRATION_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
