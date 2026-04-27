# Accommodation Catalog 02: Property Management

> Property catalog CRUD, content management, amenities, and verification

---

## Overview

This document details the property management subsystem, covering the full lifecycle of accommodation properties from ingestion and content enrichment to verification and ongoing maintenance. Properties are the core entities of the accommodation catalog, representing hotels, resorts, villas, and other lodging establishments.

**Key Capabilities:**
- Property CRUD operations
- Multi-language content management
- Amenity taxonomy and mapping
- Location and geospatial data
- Image processing and management
- Property verification and quality scoring

---

## Table of Contents

1. [Property Lifecycle](#property-lifecycle)
2. [Property CRUD](#property-crud)
3. [Content Management](#content-management)
4. [Amenity Management](#amenity-management)
5. [Location Management](#location-management)
6. [Image Management](#image-management)
7. [Property Verification](#property-verification)
8. [Quality Scoring](#quality-scoring)

---

## Property Lifecycle

### State Machine

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INGESTED  │───▶│  PENDING    │───▶│   ACTIVE    │───▶│  INACTIVE   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                                     │
                          ▼                                     │
                   ┌─────────────┐                             │
                   │  REJECTED   │◄────────────────────────────┘
                   └─────────────┘
```

### State Transitions

| From | To | Trigger |
|------|-----|----------|
| `INGESTED` | `PENDING` | Initial data received |
| `PENDING` | `ACTIVE` | Verification passed |
| `PENDING` | `REJECTED` | Verification failed |
| `ACTIVE` | `INACTIVE` | Supplier deactivation |
| `INACTIVE` | `ACTIVE` | Supplier reactivation |
| `ACTIVE` | `PENDING` | Data quality concerns |

---

## Property CRUD

### Property Creation

```typescript
export class PropertyService {
  async createFromSupplier(
    supplierId: string,
    rawProperty: RawProperty
  ): Promise<Property> {
    // 1. Normalize property data
    const property = await this.normalizer.normalizeProperty(
      rawProperty,
      supplierId
    );

    // 2. Check for duplicates
    const duplicate = await this.findDuplicate(property);
    if (duplicate) {
      // Merge instead of creating new
      return await this.mergeProperties(duplicate.id, property);
    }

    // 3. Validate property data
    await this.validator.validate(property);

    // 4. Geocode location
    property.location = await this.geocode(property.location);

    // 5. Save to database
    const created = await this.propertyRepository.create(property);

    // 6. Index for search
    await this.searchService.index(created);

    // 7. Trigger content enrichment
    await this.enrichmentService.enqueue(created.id);

    return created;
  }

  async updateProperty(
    id: string,
    updates: Partial<Property>,
    options: UpdateOptions = {}
  ): Promise<Property> {
    const existing = await this.propertyRepository.findById(id);

    if (!existing) {
      throw new NotFoundError('Property not found');
    }

    // Track changes for audit
    if (options.audit !== false) {
      await this.auditService.recordChanges(existing, updates);
    }

    // Apply updates
    const updated = await this.propertyRepository.update(id, {
      ...updates,
      updatedAt: new Date(),
    });

    // Re-index if searchable fields changed
    if (this.affectsSearchability(updates)) {
      await this.searchService.reindex(id);
    }

    // Invalidate caches
    await this.cacheService.delete(`property:${id}`);

    return updated;
  }

  async deleteProperty(id: string, options: DeleteOptions = {}): Promise<void> {
    const property = await this.propertyRepository.findById(id);

    if (!property) {
      throw new NotFoundError('Property not found');
    }

    // Check for active bookings
    if (!options.force) {
      const hasBookings = await this.bookingService.hasActiveBookings(id);
      if (hasBookings) {
        throw new ConflictError(
          'Cannot delete property with active bookings'
        );
      }
    }

    // Soft delete by default
    if (options.hard !== true) {
      await this.propertyRepository.update(id, {
        status: 'deleted',
        isActive: false,
        deletedAt: new Date(),
      });
    } else {
      // Hard delete
      await this.propertyRepository.delete(id);
      await this.searchService.delete(id);
    }
  }

  async getProperty(
    id: string,
    options: GetOptions = {}
  ): Promise<Property> {
    const cacheKey = `property:${id}`;

    // Check cache first
    if (options.cache !== false) {
      const cached = await this.cacheService.get<Property>(cacheKey);
      if (cached) return cached;
    }

    const property = await this.propertyRepository.findById(id);

    if (!property || property.status === 'deleted') {
      throw new NotFoundError('Property not found');
    }

    // Include related data if requested
    if (options.include) {
      if (options.include.includes('roomTypes')) {
        property.roomTypes = await this.roomTypeService.findByPropertyId(id);
      }
      if (options.include.includes('availability')) {
        property.availability = await this.availabilityService.getCurrent(id);
      }
    }

    // Cache the result
    if (options.cache !== false) {
      await this.cacheService.set(cacheKey, property, 3600); // 1 hour
    }

    return property;
  }

  private async findDuplicate(property: Property): Promise<Property | null> {
    // 1. Check by supplier code
    const bySupplier = await this.propertyRepository.findBySupplier(
      property.supplierId,
      property.supplierCode
    );
    if (bySupplier) return bySupplier;

    // 2. Check by name and location (fuzzy match)
    const byNameLocation = await this.propertyRepository.findBySimilarNameLocation(
      property.name.en,
      property.location.coordinates,
      0.001 // ~100m radius
    );

    if (byNameLocation.length > 0) {
      return byNameLocation[0];
    }

    return null;
  }

  private async mergeProperties(
    existingId: string,
    newData: Property
  ): Promise<Property> {
    const existing = await this.propertyRepository.findById(existingId);

    // Merge strategies:
    // - Keep the highest quality images
    // - Merge amenity lists
    // - Update content if newer
    const merged: Partial<Property> = {
      roomTypes: this.mergeRoomTypes(existing.roomTypes, newData.roomTypes),
      content: this.selectBestContent(existing.content, newData.content),
    };

    return await this.updateProperty(existingId, merged);
  }

  private affectsSearchability(updates: Partial<Property>): boolean {
    return !!(
      updates.name ||
      updates.location ||
      updates.type ||
      updates.category ||
      updates.amenities ||
      updates.rating
    );
  }
}
```

### Property Listing

```typescript
export class PropertyListingService {
  async listProperties(
    criteria: PropertyListCriteria
  ): Promise<PaginatedResult<PropertySummary>> {
    const {
      page = 1,
      limit = 20,
      sort = 'name',
      order = 'asc',
      filters = {},
    } = criteria;

    // Build query
    const query = this.buildListQuery(filters);

    // Execute with pagination
    const [results, total] = await Promise.all([
      this.propertyRepository.find(query, {
        skip: (page - 1) * limit,
        take: limit,
        order: { [sort]: order },
      }),
      this.propertyRepository.count(query),
    ]);

    // Map to summaries
    const summaries = results.map(p => this.toSummary(p));

    return {
      data: summaries,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }

  private buildListQuery(filters: PropertyFilters): QueryBuilder {
    const query = this.queryBuilder.where('isActive', true);

    // Status filter
    if (filters.status) {
      query.andWhere('status', filters.status);
    }

    // Type filter
    if (filters.types?.length) {
      query.andWhereIn('type', filters.types);
    }

    // Category filter
    if (filters.categories?.length) {
      query.andWhereIn('category', filters.categories);
    }

    // Country filter
    if (filters.countries?.length) {
      query.andWhereIn('countryCode', filters.countries);
    }

    // City filter
    if (filters.cities?.length) {
      query.andWhereIn('city', filters.cities);
    }

    // Star rating filter
    if (filters.starRating) {
      query.andWhere('starRating', '>=', filters.starRating);
    }

    // Supplier filter
    if (filters.suppliers?.length) {
      query.andWhereIn('supplierId', filters.suppliers);
    }

    // Quality score filter
    if (filters.minQuality) {
      query.andWhere('metadata.sourceQuality', '>=', filters.minQuality);
    }

    return query;
  }

  private toSummary(property: Property): PropertySummary {
    return {
      id: property.id,
      name: property.name,
      type: property.type,
      category: property.category,
      starRating: property.rating.stars,
      location: {
        city: property.location.area?.city?.en,
        country: property.location.area?.country?.en,
        coordinates: property.location.coordinates,
      },
      images: property.content.images.slice(0, 3).map(i => ({
        url: i.url,
        thumbnailUrl: i.thumbnailUrl,
      })),
      amenities: property.amenities.slice(0, 5).map(a => ({
        id: a.id,
        name: a.name,
      })),
      qualityScore: property.metadata.sourceQuality,
    };
  }
}
```

---

## Content Management

### Multi-Language Content

```typescript
export class PropertyContentService {
  async updateDescriptions(
    propertyId: string,
    descriptions: Partial<PropertyContent['descriptions']>,
    locale?: string
  ): Promise<void> {
    const property = await this.propertyService.getProperty(propertyId);

    // If locale specified, only update that locale
    if (locale) {
      for (const [key, value] of Object.entries(descriptions)) {
        if (property.content.descriptions[key]) {
          property.content.descriptions[key][locale] = value as string;
        }
      }
    } else {
      // Full replace
      Object.assign(property.content.descriptions, descriptions);
    }

    // Validate content quality
    await this.validateContent(property.content);

    // Save
    await this.propertyService.updateProperty(propertyId, {
      content: property.content,
    });
  }

  async translateContent(
    propertyId: string,
    targetLocales: string[],
    autoTranslate = false
  ): Promise<void> {
    const property = await this.propertyService.getProperty(propertyId);
    const content = property.content;

    for (const locale of targetLocales) {
      // Skip if already exists
      if (content.descriptions.short[locale]) {
        continue;
      }

      if (autoTranslate) {
        // Use translation service
        const translated = await this.translationService.translate(
          content.descriptions,
          'en',
          locale
        );

        await this.updateDescriptions(propertyId, translated, locale);
      } else {
        // Create translation task
        await this.translationTaskService.create({
          propertyId,
          locale,
          source: 'en',
          status: 'pending',
        });
      }
    }
  }

  private async validateContent(content: PropertyContent): Promise<void> {
    // Check minimum length
    const shortLength = content.descriptions.short.en?.length || 0;
    if (shortLength < 50) {
      throw new ValidationError('Short description must be at least 50 characters');
    }

    const longLength = content.descriptions.long.en?.length || 0;
    if (longLength < 200) {
      throw new ValidationError('Long description must be at least 200 characters');
    }

    // Check for spam/gibberish
    const quality = await this.contentQualityService.assess(
      content.descriptions.long.en
    );

    if (quality.score < 0.5) {
      throw new ValidationError('Content quality is too low');
    }
  }
}
```

### Policy Management

```typescript
export class PropertyPolicyService {
  async updatePolicies(
    propertyId: string,
    policies: Partial<PropertyPolicies>
  ): Promise<void> {
    const property = await this.propertyService.getProperty(propertyId);

    // Validate policy consistency
    this.validatePolicies(policies);

    // Merge with existing
    const updated = {
      ...property.content.policies,
      ...policies,
    };

    await this.propertyService.updateProperty(propertyId, {
      content: {
        ...property.content,
        policies: updated,
      },
    });
  }

  private validatePolicies(policies: Partial<PropertyPolicies>): void<void> {
    // Validate children policy
    if (policies.children) {
      if (policies.children.allowed && policies.children.minAge !== undefined) {
        if (policies.children.minAge < 0 || policies.children.minAge > 18) {
          throw new ValidationError('Invalid minimum age for children');
        }
      }

      if (policies.children.extraBeds?.maxPerRoom !== undefined) {
        if (policies.children.extraBeds.maxPerRoom < 0) {
          throw new ValidationError('Invalid maximum extra beds');
        }
      }
    }

    // Validate check-in/out times
    if (policies.checkIn) {
      const { from, until } = policies.checkIn;
      if (from >= until) {
        throw new ValidationError('Check-in from time must be before until time');
      }
    }

    if (policies.checkOut) {
      const { from, until } = policies.checkOut;
      if (from >= until) {
        throw new ValidationError('Check-out from time must be before until time');
      }
    }

    // Validate cancellation policy
    if (policies.cancellation) {
      if (policies.cancellation.deadline) {
        if (policies.cancellation.deadline.amount <= 0) {
          throw new ValidationError('Cancellation deadline amount must be positive');
        }
      }
    }
  }

  async getPoliciesSummary(
    propertyId: string,
    locale = 'en'
  ): Promise<PolicySummary> {
    const property = await this.propertyService.getProperty(propertyId);
    const policies = property.content.policies;

    return {
      cancellation: {
        type: policies.cancellation.type,
        description: policies.cancellation.description[locale],
        freeCancellationBefore: policies.cancellation.deadline
          ? `${policies.cancellation.deadline.amount} ${policies.cancellation.deadline.unit} before check-in`
          : undefined,
      },
      checkIn: {
        from: policies.checkIn.from,
        until: policies.checkIn.until,
        instructions: policies.checkIn.instructions?.[locale],
      },
      checkOut: {
        from: policies.checkOut.from,
        until: policies.checkOut.until,
        instructions: policies.checkOut.instructions?.[locale],
      },
      children: {
        allowed: policies.children.allowed,
        ages: policies.children.allowed
          ? `${policies.children.minAge || 0}-${policies.children.maxAge || 17} years`
          : undefined,
        cots: policies.children.cots.available
          ? `${policies.children.cots.available ? 'Available' : 'Not available'}`
          : undefined,
      },
      pets: {
        allowed: policies.pets.allowed,
        charge: policies.pets.charge
          ? `${policies.pets.charge.amount} ${policies.pets.charge.currency}`
          : undefined,
      },
    };
  }
}
```

---

## Amenity Management

### Amenity Taxonomy

```typescript
export class AmenityService {
  private readonly taxonomy: AmenityTaxonomy;

  constructor() {
    this.taxonomy = this.loadTaxonomy();
  }

  async getPropertyAmenities(propertyId: string): Promise<Amenity[]> {
    const property = await this.propertyService.getProperty(propertyId);

    // Group by type
    const grouped = this.groupByType(property.amenities);

    // Sort within groups
    for (const group of Object.values(grouped)) {
      group.sort((a, b) => this.sortOrder(a.code) - this.sortOrder(b.code));
    }

    return property.amenities;
  }

  async updatePropertyAmenities(
    propertyId: string,
    amenities: AmenityUpdate[]
  ): Promise<void> {
    const property = await this.propertyService.getProperty(propertyId);

    // Map amenity codes to internal IDs
    const mapped = await Promise.all(
      amenities.map(async a => {
        const internal = await this.mapAmenityCode(a.code, a.type);
        return {
          ...internal,
          complimentary: a.complimentary ?? true,
          available: a.available ?? true,
        };
      })
    );

    // Save
    await this.propertyService.updateProperty(propertyId, {
      amenities: mapped,
    });

    // Update search index
    await this.searchService.updateAmenities(propertyId, mapped);
  }

  async searchAmenities(query: string): Promise<Amenity[]> {
    const results = await this.amenityRepository.search(query);

    return results.map(a => ({
      id: a.id,
      code: a.code,
      type: a.type,
      name: a.name,
      icon: a.icon,
    }));
  }

  private groupByType(amenities: Amenity[]): Record<string, Amenity[]> {
    return amenities.reduce((acc, amenity) => {
      if (!acc[amenity.type]) {
        acc[amenity.type] = [];
      }
      acc[amenity.type].push(amenity);
      return acc;
    }, {} as Record<string, Amenity[]>);
  }

  private sortOrder(code: string): number {
    const priority: Record<string, number> = {
      'wifi': 1,
      'parking': 2,
      'pool': 3,
      'restaurant': 4,
      'gym': 5,
      'spa': 6,
    };
    return priority[code] ?? 99;
  }
}
```

### Amenity Mapping

```typescript
export class AmenityMapper {
  private readonly mappings: Map<string, Map<string, string>>;

  constructor() {
    this.mappings = this.loadMappings();
  }

  async mapAmenityCode(
    supplierCode: string,
    supplierId: string
  ): Promise<Amenity | null> {
    // 1. Check direct mapping
    const internalCode = this.mappings.get(supplierId)?.get(supplierCode);
    if (internalCode) {
      return await this.amenityRepository.findByCode(internalCode);
    }

    // 2. Try fuzzy matching
    const match = await this.fuzzyMatch(supplierCode);
    if (match) {
      return match;
    }

    // 3. Create new amenity if needed
    return null;
  }

  private async fuzzyMatch(code: string): Promise<Amenity | null> {
    const normalized = this.normalizeCode(code);

    // Find similar existing amenity
    const all = await this.amenityRepository.findAll();

    for (const amenity of all) {
      const amenityNormalized = this.normalizeCode(amenity.code);
      const similarity = this.calculateSimilarity(normalized, amenityNormalized);

      if (similarity > 0.85) {
        return amenity;
      }
    }

    return null;
  }

  private normalizeCode(code: string): string {
    return code
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '')
      .replace(/_/g, '');
  }

  private calculateSimilarity(a: string, b: string): number {
    // Levenshtein distance
    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    const distance = matrix[b.length][a.length];
    const maxLen = Math.max(a.length, b.length);

    return 1 - distance / maxLen;
  }
}
```

---

## Location Management

### Geocoding

```typescript
export class LocationService {
  async geocode(address: Partial<Address>): Promise<Location> {
    // 1. Format address
    const formatted = this.formatAddress(address);

    // 2. Call geocoding API
    const results = await this.geocodingClient.geocode(formatted);

    if (results.length === 0) {
      throw new ValidationError('Address not found');
    }

    const best = results[0];

    return {
      address: {
        line1: address.line1 || best.address.line1,
        line2: address.line2,
        city: best.address.city || address.city,
        state: best.address.state || address.state,
        postalCode: best.address.postalCode || address.postalCode,
        countryCode: best.address.countryCode || address.countryCode,
      },
      coordinates: {
        latitude: best.location.latitude,
        longitude: best.location.longitude,
      },
      geohash: this.encodeGeohash(best.location.latitude, best.location.longitude),
      timezone: await this.getTimezone(best.location.latitude, best.location.longitude),
      area: await this.buildAreaInfo(best.address, best.location),
    };
  }

  async reverseGeocode(
    latitude: number,
    longitude: number
  ): Promise<Location> {
    const results = await this.geocodingClient.reverseGeocode(latitude, longitude);

    if (results.length === 0) {
      throw new ValidationError('Location not found');
    }

    const best = results[0];

    return {
      address: {
        line1: best.address.line1 || '',
        line2: best.address.line2,
        city: best.address.city,
        state: best.address.state,
        postalCode: best.address.postalCode,
        countryCode: best.address.countryCode,
      },
      coordinates: { latitude, longitude },
      geohash: this.encodeGeohash(latitude, longitude),
      timezone: await this.getTimezone(latitude, longitude),
      area: await this.buildAreaInfo(best.address, { latitude, longitude }),
    };
  }

  private formatAddress(address: Partial<Address>): string {
    const parts = [
      address.line1,
      address.line2,
      address.city,
      address.state,
      address.postalCode,
      address.countryCode,
    ].filter(Boolean);

    return parts.join(', ');
  }

  private encodeGeohash(latitude: number, longitude: number): string {
    // Geohash encoding with 12 characters precision (~3m)
    return geohash.encode(latitude, longitude, 12);
  }

  private async getTimezone(latitude: number, longitude: number): Promise<string> {
    const result = await this.timezoneClient.getTimeZone(latitude, longitude);
    return result.timeZoneId;
  }

  private async buildAreaInfo(
    address: GeocodedAddress,
    location: Coordinates
  ): Promise<AreaInfo> {
    return {
      country: await this.getCountryName(address.countryCode),
      region: address.state ? { en: address.state } : undefined,
      city: { en: address.city },
      district: address.district ? { en: address.district } : undefined,
      landmarks: await this.findNearbyLandmarks(location),
    };
  }

  async findNearbyLandmarks(
    location: Coordinates,
    radiusKm = 5
  ): Promise<string[]> {
    // Find nearby points of interest
    const results = await this.placesService.nearby({
      location,
      radius: radiusKm * 1000,
      types: ['tourist_attraction', 'landmark', 'point_of_interest'],
    });

    return results.slice(0, 5).map(r => r.name);
  }
}
```

### Location Search

```typescript
export class LocationSearchService {
  async searchByLocation(
    coordinates: Coordinates,
    radius: number,
    criteria: PropertySearchCriteria = {}
  ): Promise<Property[]> {
    // Use PostGIS for geo-spatial query
    const properties = await this.propertyRepository.findByLocation({
      coordinates,
      radius,
      ...criteria,
    });

    return properties;
  }

  async searchByArea(
    area: AreaIdentifier,
    criteria: PropertySearchCriteria = {}
  ): Promise<Property[]> {
    const { country, region, city, district } = area;

    return this.propertyRepository.findByArea({
      country,
      region,
      city,
      district,
      ...criteria,
    });
  }

  async suggestLocations(
    query: string
  ): Promise<LocationSuggestion[]> {
    // 1. Try city search
    const cities = await this.cityRepository.search(query);

    // 2. Try landmark search
    const landmarks = await this.landmarkRepository.search(query);

    // 3. Try geocoding
    const geocoded = await this.geocodingService.geocode({ query });

    return [
      ...cities.map(c => ({
        type: 'city',
        name: `${c.name}, ${c.countryCode}`,
        coordinates: { latitude: c.latitude, longitude: c.longitude },
        area: { country: c.countryCode, city: c.name },
      })),
      ...landmarks.map(l => ({
        type: 'landmark',
        name: l.name,
        coordinates: l.coordinates,
        area: l.area,
      })),
    ].slice(0, 10);
  }
}
```

---

## Image Management

### Image Upload and Processing

```typescript
export class PropertyImageService {
  async uploadImages(
    propertyId: string,
    files: FileUpload[],
    metadata: ImageMetadata[]
  ): Promise<MediaItem[]> {
    const results: MediaItem[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const meta = metadata[i];

      // 1. Validate image
      this.validateImage(file);

      // 2. Process image
      const processed = await this.processImage(file);

      // 3. Detect category
      const category = meta.category
        || await this.detectCategory(processed);

      // 4. Upload to CDN
      const url = await this.uploadToCDN(propertyId, processed);

      // 5. Save to database
      const image: MediaItem = {
        id: crypto.randomUUID(),
        url,
        thumbnailUrl: processed.thumbnails.medium.url,
        type: 'photo',
        category,
        caption: meta.caption ? this.localizeText(meta.caption) : undefined,
        width: processed.width,
        height: processed.height,
        order: meta.order ?? results.length,
        createdAt: new Date(),
      };

      await this.imageRepository.create(propertyId, image);
      results.push(image);
    }

    // Update property image cache
    await this.updatePropertyImageCache(propertyId, results);

    return results;
  }

  async deleteImage(propertyId: string, imageId: string): Promise<void> {
    const image = await this.imageRepository.findById(imageId);

    if (!image || image.propertyId !== propertyId) {
      throw new NotFoundError('Image not found');
    }

    // Delete from CDN
    await this.cdnService.delete(image.url);

    // Delete from database
    await this.imageRepository.delete(imageId);

    // Update cache
    await this.invalidatePropertyImageCache(propertyId);
  }

  async reorderImages(
    propertyId: string,
    imageIds: string[]
  ): Promise<void> {
    for (let i = 0; i < imageIds.length; i++) {
      await this.imageRepository.update(imageIds[i], {
        order: i,
      });
    }

    await this.invalidatePropertyImageCache(propertyId);
  }

  private async detectCategory(
    image: ProcessedImage
  ): Promise<MediaCategory> {
    // Use ML model to classify
    const classification = await this.imageClassifier.classify(image.buffer);

    const categoryMap: Record<string, MediaCategory> = {
      'exterior': 'exterior',
      'lobby': 'lobby',
      'room_bedroom': 'room',
      'room_bathroom': 'bathroom',
      'pool': 'pool',
      'restaurant': 'restaurant',
      'gym': 'gym',
      'view_from_room': 'view',
    };

    return categoryMap[classification.label] || 'other';
  }

  private validateImage(file: FileUpload): void {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.mimetype)) {
      throw new ValidationError('Invalid image type');
    }

    if (file.size > maxSize) {
      throw new ValidationError('Image too large (max 10MB)');
    }

    // Validate image dimensions
    const { width, height } = this.getImageDimensions(file.buffer);
    if (width < 800 || height < 600) {
      throw new ValidationError('Image too small (min 800x600)');
    }
  }

  private async processImage(file: FileUpload): Promise<ProcessedImage> {
    // 1. Convert to WebP for better compression
    const webp = await this.imageProcessor.convertToWebP(file.buffer, {
      quality: 85,
    });

    // 2. Resize if needed
    const resized = await this.imageProcessor.resize(webp, {
      maxWidth: 1920,
      maxHeight: 1080,
    });

    // 3. Generate thumbnails
    const thumbnails = {
      small: await this.imageProcessor.resize(resized, {
        width: 150,
        height: 150,
        fit: 'cover',
      }),
      medium: await this.imageProcessor.resize(resized, {
        width: 400,
        height: 300,
        fit: 'cover',
      }),
      large: await this.imageProcessor.resize(resized, {
        width: 1200,
        height: 800,
        fit: 'inside',
      }),
    };

    // 4. Extract metadata
    const { width, height } = this.getImageDimensions(resized);

    return {
      buffer: resized,
      width,
      height,
      thumbnails: {
        small: { url: '', buffer: thumbnails.small },
        medium: { url: '', buffer: thumbnails.medium },
        large: { url: '', buffer: thumbnails.large },
      },
    };
  }

  private async uploadToCDN(
    propertyId: string,
    image: ProcessedImage
  ): Promise<string> {
    const key = `properties/${propertyId}/${crypto.randomUUID()}.webp`;

    // Upload main image
    const url = await this.cdnService.upload(key, image.buffer, {
      contentType: 'image/webp',
    });

    // Upload thumbnails
    for (const [size, thumb] of Object.entries(image.thumbnails)) {
      const thumbKey = `properties/${propertyId}/thumbnails/${size}_${crypto.randomUUID()}.webp`;
      await this.cdnService.upload(thumbKey, thumb.buffer, {
        contentType: 'image/webp',
      });
    }

    return url;
  }
}
```

---

## Property Verification

### Verification Process

```typescript
export class PropertyVerificationService {
  async verifyProperty(propertyId: string): Promise<VerificationResult> {
    const property = await this.propertyService.getProperty(propertyId);

    const checks: VerificationCheck[] = [
      await this.checkBasicInfo(property),
      await this.checkLocation(property),
      await this.checkContent(property),
      await this.checkImages(property),
      await this.checkAmenities(property),
      await this.checkRoomTypes(property),
    ];

    const passed = checks.every(c => c.passed);
    const score = this.calculateScore(checks);

    const result: VerificationResult = {
      propertyId,
      passed,
      score,
      checks,
      verifiedAt: new Date(),
    };

    // Update property
    await this.propertyService.updateProperty(propertyId, {
      status: passed ? 'active' : 'pending',
      verifiedAt: new Date(),
    });

    // Save verification record
    await this.verificationRepository.create(result);

    return result;
  }

  private async checkBasicInfo(property: Property): Promise<VerificationCheck> {
    const issues: string[] = [];

    // Required fields
    if (!property.name?.en) issues.push('Missing name');
    if (!property.type) issues.push('Missing type');
    if (!property.location.address) issues.push('Missing address');
    if (!property.contact) issues.push('Missing contact info');

    // Valid values
    if (!Object.values(PropertyType).includes(property.type)) {
      issues.push('Invalid property type');
    }

    return {
      name: 'Basic Information',
      passed: issues.length === 0,
      issues,
    };
  }

  private async checkLocation(property: Property): Promise<VerificationCheck> {
    const issues: string[] = [];

    // Coordinates present and valid
    const { latitude, longitude } = property.location.coordinates;
    if (!latitude || !longitude) {
      issues.push('Missing coordinates');
    } else if (
      latitude < -90 || latitude > 90 ||
      longitude < -180 || longitude > 180
    ) {
      issues.push('Invalid coordinates');
    }

    // Address completeness
    const { address } = property.location;
    if (!address.line1) issues.push('Missing address line 1');
    if (!address.city) issues.push('Missing city');
    if (!address.countryCode) issues.push('Missing country code');

    // Geohash present
    if (!property.location.geohash) {
      issues.push('Missing geohash');
    }

    return {
      name: 'Location',
      passed: issues.length === 0,
      issues,
    };
  }

  private async checkContent(property: Property): Promise<VerificationCheck> {
    const issues: string[] = [];
    const { descriptions } = property.content;

    // Description length
    if (!descriptions.short.en || descriptions.short.en.length < 50) {
      issues.push('Short description too short (min 50 chars)');
    }

    if (!descriptions.long.en || descriptions.long.en.length < 200) {
      issues.push('Long description too short (min 200 chars)');
    }

    // Content quality
    const quality = await this.contentQualityService.assess(
      descriptions.long.en
    );

    if (quality.score < 0.6) {
      issues.push(`Content quality too low (${quality.score.toFixed(2)})`);
    }

    // Policies present
    if (!property.content.policies) {
      issues.push('Missing policies');
    } else {
      if (!property.content.policies.cancellation) {
        issues.push('Missing cancellation policy');
      }
      if (!property.content.policies.checkIn) {
        issues.push('Missing check-in policy');
      }
    }

    return {
      name: 'Content',
      passed: issues.length === 0,
      issues,
    };
  }

  private async checkImages(property: Property): Promise<VerificationCheck> {
    const issues: string[] = [];
    const images = property.content.images;

    // Minimum image count
    if (images.length < 3) {
      issues.push('Too few images (min 3)');
    }

    // Image categories
    const categories = new Set(images.map(i => i.category));
    if (!categories.has('exterior')) {
      issues.push('Missing exterior image');
    }

    // Image quality
    const lowQuality = images.filter(i => i.width < 800 || i.height < 600);
    if (lowQuality.length > 0) {
      issues.push(`${lowQuality.length} low quality images`);
    }

    return {
      name: 'Images',
      passed: issues.length === 0,
      issues,
    };
  }

  private calculateScore(checks: VerificationCheck[]): number {
    const passed = checks.filter(c => c.passed).length;
    return passed / checks.length;
  }
}
```

---

## Quality Scoring

### Quality Metrics

```typescript
export class PropertyQualityService {
  async calculateQualityScore(propertyId: string): Promise<QualityScore> {
    const property = await this.propertyService.getProperty(propertyId);

    const scores = {
      content: this.scoreContent(property),
      images: this.scoreImages(property),
      location: this.scoreLocation(property),
      completeness: this.scoreCompleteness(property),
      engagement: this.scoreEngagement(property),
    };

    const overall = this.calculateWeightedScore(scores);

    return {
      propertyId,
      overall,
      breakdown: scores,
      calculatedAt: new Date(),
    };
  }

  private scoreContent(property: Property): number {
    let score = 0;

    // Description quality
    const descLength = property.content.descriptions.long.en.length;
    if (descLength >= 500) score += 0.3;
    else if (descLength >= 200) score += 0.15;

    // Has marketing description
    if (property.content.descriptions.marketing?.en) {
      score += 0.1;
    }

    // Has policies
    if (property.content.policies) score += 0.2;

    // Multi-language
    const locales = this.countLocales(property.content.descriptions.long);
    if (locales >= 3) score += 0.2;
    else if (locales >= 2) score += 0.1;

    // Content quality assessment
    // (from ML-based quality service)
    const quality = property.metadata.sourceQuality;
    score += quality * 0.2;

    return Math.min(score, 1);
  }

  private scoreImages(property: Property): number {
    const images = property.content.images;
    let score = 0;

    // Image count
    if (images.length >= 10) score += 0.3;
    else if (images.length >= 5) score += 0.2;
    else if (images.length >= 3) score += 0.1;

    // Category coverage
    const categories = new Set(images.map(i => i.category));
    const requiredCategories = ['exterior', 'room', 'lobby'];
    const covered = requiredCategories.filter(c => categories.has(c)).length;
    score += (covered / requiredCategories.length) * 0.3;

    // Image resolution
    const highRes = images.filter(i => i.width >= 1920 && i.height >= 1080);
    score += Math.min(highRes.length / images.length, 1) * 0.2;

    // Has captions
    const withCaptions = images.filter(i => i.caption);
    score += (withCaptions.length / images.length) * 0.2;

    return Math.min(score, 1);
  }

  private scoreLocation(property: Property): number {
    let score = 0;

    // Has coordinates
    if (property.location.coordinates.latitude) {
      score += 0.3;
    }

    // Has geohash
    if (property.location.geohash) {
      score += 0.1;
    }

    // Address completeness
    const { address } = property.location;
    if (address.line1 && address.city && address.countryCode) {
      score += 0.3;
    }

    // Has area info
    if (property.location.area) {
      score += 0.2;
    }

    // Has timezone
    if (property.location.timezone) {
      score += 0.1;
    }

    return Math.min(score, 1);
  }

  private scoreCompleteness(property: Property): number {
    return property.metadata.completeness;
  }

  private scoreEngagement(property: Property): number {
    // Based on views, bookings, reviews
    // This would come from analytics
    return 0.5; // Placeholder
  }

  private calculateWeightedScore(scores: QualityBreakdown): number {
    const weights = {
      content: 0.25,
      images: 0.25,
      location: 0.15,
      completeness: 0.2,
      engagement: 0.15,
    };

    return Object.entries(weights).reduce(
      (sum, [key, weight]) => sum + scores[key] * weight,
      0
    );
  }
}
```

---

## API Endpoints

### Property CRUD Endpoints

```
GET    /accommodations/properties
POST   /accommodations/properties
GET    /accommodations/properties/:id
PATCH  /accommodations/properties/:id
DELETE /accommodations/properties/:id
```

### Content Endpoints

```
GET    /accommodations/properties/:id/content
PATCH  /accommodations/properties/:id/content
POST   /accommodations/properties/:id/content/translate
```

### Amenity Endpoints

```
GET    /accommodations/properties/:id/amenities
PATCH  /accommodations/properties/:id/amenities
GET    /accommodations/amenities/search?q=
```

### Image Endpoints

```
GET    /accommodations/properties/:id/images
POST   /accommodations/properties/:id/images
DELETE /accommodations/properties/:id/images/:imageId
PATCH  /accommodations/properties/:id/images/reorder
```

### Verification Endpoints

```
POST   /accommodations/properties/:id/verify
GET    /accommodations/properties/:id/verification
GET    /accommodations/properties/:id/quality-score
```

---

**Next:** [Inventory & Pricing](./ACCOMMODATION_CATALOG_03_INVENTORY_PRICING.md) — Room types, availability, and rate plans
