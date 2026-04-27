# Accommodation Catalog 04: Search & Discovery

> Search architecture, filtering, relevance scoring, and recommendations

---

## Overview

This document details the search and discovery subsystem for accommodations, covering full-text search, filtering and faceting, relevance scoring, map-based search, and personalized recommendations. The search system is built on Elasticsearch for fast, flexible querying with advanced ranking capabilities.

**Key Capabilities:**
- Full-text property search
- Multi-criteria filtering
- Faceted navigation
- Geo-spatial search
- Relevance scoring
- Personalized recommendations
- Auto-complete and suggestions

---

## Table of Contents

1. [Search Architecture](#search-architecture)
2. [Query Building](#query-building)
3. [Filtering & Faceting](#filtering--faceting)
4. [Relevance Scoring](#relevance-scoring)
5. [Map Search](#map-search)
6. [Recommendations](#recommendations)
7. [Auto-Complete](#auto-complete)

---

## Search Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCOMMODATION SEARCH                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│  │   CLIENT    │───▶│  API GATEWAY│───▶│  SEARCH     │───▶│ ELASTICSEARCH││
│  │  REQUESTS   │    │             │    │  SERVICE    │    │   CLUSTER    ││
│  └─────────────┘    └─────────────┘    └──────┬──────┘    └─────────────┘│
│                                                 │                           │
│                                                 │                           │
│                           ┌─────────────────────┼─────────────────┐         │
│                           │                     │                 │         │
│                    ┌──────▼──────┐     ┌───────▼──────┐  ┌────▼─────────┐│
│                    │ QUERY       │     │ SCORING      │  │ RESULT       ││
│                    │ BUILDER     │     │ ENGINE       │  │ ENRICHER     ││
│                    └─────────────┘     └──────────────┘  └──────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CACHE LAYER (Redis)                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Popular  │  │ Recent   │  │ Facet    │  │ Geo      │          │   │
│  │  │ Queries  │  │ Results  │  │ Counts   │  │ Queries  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Index Mapping

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "property_name": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "property_synonym"
          ]
        },
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "ngram"
          ]
        }
      },
      "filter": {
        "property_synonym": {
          "type": "synonym",
          "synonyms": [
            "hotel, motel, lodge, inn",
            "resort, retreat, spa",
            "villa, house, vacation rental"
          ]
        },
        "ngram": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 15
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "supplier_id": { "type": "keyword" },
      "name": {
        "type": "text",
        "analyzer": "property_name",
        "fields": {
          "keyword": { "type": "keyword" },
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete"
          },
          "english": {
            "type": "text",
            "analyzer": "english"
          }
        }
      },
      "name_suggest": {
        "type": "completion",
        "contexts": [
          { "name": "type", "path": "type" },
          { "name": "country", "path": "address.country_code" }
        ]
      },
      "location": {
        "type": "geo_point"
      },
      "geohash": { "type": "keyword" },
      "address": {
        "properties": {
          "city": { "type": "keyword" },
          "city_full": { "type": "text" },
          "state": { "type": "keyword" },
          "country_code": { "type": "keyword" },
          "country": { "type": "keyword" }
        }
      },
      "type": { "type": "keyword" },
      "category": { "type": "keyword" },
      "chain": { "type": "keyword" },
      "star_rating": { "type": "integer" },
      "guest_rating": { "type": "double" },
      "review_count": { "type": "integer" },
      "amenities": { "type": "keyword" },
      "amenities_count": { "type": "integer" },
      "room_types": {
        "properties": {
          "id": { "type": "keyword" },
          "type": { "type": "keyword" },
          "min_price": { "type": "integer" }
        }
      },
      "price_range": {
        "type": "integer_range"
      },
      "quality_score": { "type": "double" },
      "popularity_score": {
        "type": "rank_feature",
        "positive_score_impact": true
      },
      "booking_velocity": {
        "type": "rank_feature",
        "positive_score_impact": true
      },
      "image_count": { "type": "integer" },
      "description_length": { "type": "integer" },
      "has_pool": { "type": "boolean" },
      "has_spa": { "type": "boolean" },
      "has_gym": { "type": "boolean" },
      "has_restaurant": { "type": "boolean" },
      "pet_friendly": { "type": "boolean" },
      "family_friendly": { "type": "boolean" },
      "beach_access": { "type": "boolean" },
      "city_center": { "type": "boolean" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

## Query Building

### Search Request Schema

```typescript
interface AccommodationSearchRequest {
  // Location
  destination?: string; // Free text location
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  radius?: number; // km

  // Dates
  checkIn?: Date;
  checkOut?: Date;

  // Occupancy
  adults?: number;
  children?: number;
  rooms?: number;

  // Filters
  filters: {
    types?: PropertyType[];
    categories?: PropertyCategory[];
    starRating?: {
      min?: number;
      max?: number;
    };
    guestRating?: {
      min?: number;
    };
    priceRange?: {
      min?: number;
      max?: number;
    };
    amenities?: string[];
    facilities?: {
      pool?: boolean;
      spa?: boolean;
      gym?: boolean;
      restaurant?: boolean;
      beachAccess?: boolean;
    };
    policies?: {
      petFriendly?: boolean;
      freeCancellation?: boolean;
    };
    chains?: string[];
  };

  // Pagination
  page?: number;
  limit?: number;

  // Sorting
  sortBy?: SearchSortType;
  sortOrder?: 'asc' | 'desc';

  // Personalization
  userId?: string;
  sessionId?: string;
}

type SearchSortType =
  | 'recommended'
  | 'price'
  | 'rating'
  | 'popularity'
  | 'distance'
  | 'reviews'
  | 'quality';
```

### Query Builder

```typescript
export class AccommodationSearchQueryBuilder {
  buildQuery(
    request: AccommodationSearchRequest,
    context: SearchContext
  ): ElasticsearchQuery {
    const must: QueryClause[] = [];
    const filter: QueryClause[] = [];
    const should: QueryClause[] = [];

    // 1. Location query
    if (request.destination) {
      filter.push(this.buildLocationQuery(request.destination));
    } else if (request.coordinates) {
      filter.push({
        geo_distance: {
          distance: `${request.radius || 50}km`,
          location: {
            lat: request.coordinates.latitude,
            lon: request.coordinates.longitude,
          },
        },
      });
    }

    // 2. Basic filters
    filter.push({ term: { is_active: true } });
    filter.push({ term: { status: 'active' } });

    // 3. Type filter
    if (request.filters.types?.length) {
      filter.push({ terms: { type: request.filters.types } });
    }

    // 4. Category filter
    if (request.filters.categories?.length) {
      filter.push({ terms: { category: request.filters.categories } });
    }

    // 5. Star rating filter
    if (request.filters.starRating) {
      const range: RangeQuery = {};
      if (request.filters.starRating.min !== undefined) {
        range.gte = request.filters.starRating.min;
      }
      if (request.filters.starRating.max !== undefined) {
        range.lte = request.filters.starRating.max;
      }
      filter.push({ range: { star_rating: range } });
    }

    // 6. Guest rating filter
    if (request.filters.guestRating?.min) {
      filter.push({
        range: { guest_rating: { gte: request.filters.guestRating.min } },
      });
    }

    // 7. Price range filter
    if (request.filters.priceRange) {
      const range: RangeQuery = {};
      if (request.filters.priceRange.min !== undefined) {
        range.gte = request.filters.priceRange.min;
      }
      if (request.filters.priceRange.max !== undefined) {
        range.lte = request.filters.priceRange.max;
      }
      filter.push({ range: { 'price_range.min': range } });
    }

    // 8. Amenities filter
    if (request.filters.amenities?.length) {
      filter.push({
        terms: { amenities: request.filters.amenities },
      });
    }

    // 9. Facility filters
    if (request.filters.facilities?.pool) {
      filter.push({ term: { has_pool: true } });
    }
    if (request.filters.facilities?.spa) {
      filter.push({ term: { has_spa: true } });
    }
    if (request.filters.facilities?.gym) {
      filter.push({ term: { has_gym: true } });
    }
    if (request.filters.facilities?.restaurant) {
      filter.push({ term: { has_restaurant: true } });
    }
    if (request.filters.facilities?.beachAccess) {
      filter.push({ term: { beach_access: true } });
    }

    // 10. Policy filters
    if (request.filters.policies?.petFriendly) {
      filter.push({ term: { pet_friendly: true } });
    }

    // 11. Chain filter
    if (request.filters.chains?.length) {
      filter.push({ terms: { chain: request.filters.chains } });
    }

    // 12. Relevance scoring
    should.push(
      { rank_feature: { field: 'popularity_score', boost: 0.3 } },
      { rank_feature: { field: 'booking_velocity', boost: 0.2 } },
      {
        field_value_factor: {
          field: 'guest_rating',
          factor: 0.1,
          modifier: 'log2p',
          boost: 0.3,
        },
      },
      {
        field_value_factor: {
          field: 'quality_score',
          factor: 1,
          boost: 0.2,
        },
      }
    );

    // 13. Personalization
    if (context.userId) {
      const personalization = await this.buildPersonalizationQuery(
        context.userId
      );
      should.push(...personalization);
    }

    // 14. Distance scoring (if coordinates provided)
    if (request.coordinates) {
      should.push({
        gauss: {
          location: {
            origin: {
              lat: request.coordinates.latitude,
              lon: request.coordinates.longitude,
            },
            scale: `${request.radius || 50}km`,
            decay: 0.5,
            offset: '5km',
          },
        },
      });
    }

    return {
      query: {
        bool: {
          must: must.length ? must : undefined,
          filter,
          should,
        },
      },
      from: ((request.page || 1) - 1) * (request.limit || 20),
      size: request.limit || 20,
      sort: this.buildSort(request),
      aggs: this.buildAggregations(),
    };
  }

  private buildLocationQuery(destination: string): QueryClause {
    // Multi-match for city name, country, or property name
    return {
      bool: {
        should: [
          {
            multi_match: {
              query: destination,
              fields: [
                'address.city_full^3',
                'address.city^3',
                'address.country^2',
                'name^2',
              ],
              fuzziness: 'AUTO',
            },
          },
          {
            match: {
              'name.autocomplete': {
                query: destination,
                fuzziness: 1,
              },
            },
          },
        ],
        minimum_should_match: 1,
      },
    };
  }

  private buildSort(request: AccommodationSearchRequest): SortClause[] {
    switch (request.sortBy) {
      case 'price':
        return [
          {
            'price_range.min': {
              order: request.sortOrder || 'asc',
              unmapped_type: 'integer',
            },
          },
        ];

      case 'rating':
        return [
          { guest_rating: { order: request.sortOrder || 'desc' } },
          { review_count: { order: 'desc' } },
        ];

      case 'popularity':
        return [
          { popularity_score: { order: 'desc' } },
          { booking_velocity: { order: 'desc' } },
        ];

      case 'reviews':
        return [
          { review_count: { order: request.sortOrder || 'desc' } },
        ];

      case 'quality':
        return [
          { quality_score: { order: request.sortOrder || 'desc' } },
        ];

      case 'distance':
        if (request.coordinates) {
          return [
            {
              _geo_distance: {
                location: {
                  lat: request.coordinates.latitude,
                  lon: request.coordinates.longitude,
                },
                order: request.sortOrder || 'asc',
                unit: 'km',
              },
            },
          ];
        }
        return [{ _score: 'desc' }];

      case 'recommended':
      default:
        return [{ _score: 'desc' }];
    }
  }

  private buildAggregations(): AggregationSpec {
    return {
      types: {
        terms: { field: 'type', size: 20 },
      },
      categories: {
        terms: { field: 'category', size: 10 },
      },
      star_ratings: {
        terms: { field: 'star_rating', size: 6 },
      },
      guest_rating_ranges: {
        range: {
          field: 'guest_rating',
          ranges: [
            { key: 'excellent', to: 9 },
            { key: 'very_good', from: 8, to: 9 },
            { key: 'good', from: 7, to: 8 },
            { key: 'fair', from: 6, to: 7 },
            { key: 'poor', from: 0, to: 6 },
          ],
        },
      },
      price_ranges: {
        range: {
          field: 'price_range.min',
          ranges: [
            { key: 'budget', to: 100 },
            { key: 'economy', from: 100, to: 150 },
            { key: 'mid_range', from: 150, to: 250 },
            { key: 'upscale', from: 250, to: 400 },
            { key: 'luxury', from: 400 },
          ],
        },
      },
      amenities: {
        terms: { field: 'amenities', size: 30 },
      },
      chains: {
        terms: { field: 'chain', size: 20 },
      },
      geo_bounds: {
        geo_bounds: {
          field: 'location',
        },
      },
    };
  }

  private async buildPersonalizationQuery(
    userId: string
  ): Promise<QueryClause[]> {
    // Get user preferences
    const user = await this.userService.getUser(userId);
    const preferences = user.preferences;

    const should: QueryClause[] = [];

    // Boost preferred types
    if (preferences.preferredTypes?.length) {
      should.push({
        terms: {
          type: preferences.preferredTypes,
          boost: 1.5,
        },
      });
    }

    // Boost preferred amenities
    if (preferences.preferredAmenities?.length) {
      should.push({
        terms: {
          amenities: preferences.preferredAmenities,
          boost: 1.2,
        },
      });
    }

    // Boost previously booked properties
    const booked = await this.bookingService.getUserBookedProperties(userId);
    if (booked.length > 0) {
      should.push({
        terms: {
          id: booked,
          boost: 1.3,
        },
      });
    }

    return should;
  }
}
```

---

## Filtering & Faceting

### Facet Builder

```typescript
export class SearchFacetService {
  async buildFacets(
    aggregationResults: AggregationResults,
    request: AccommodationSearchRequest
  ): Promise<SearchFacets> {
    return {
      types: this.buildTypeFacet(aggregationResults.types, request),
      categories: this.buildCategoryFacet(aggregationResults.categories, request),
      starRatings: this.buildStarRatingFacet(aggregationResults.star_ratings, request),
      guestRatings: this.buildGuestRatingFacet(aggregationResults.guest_rating_ranges, request),
      priceRanges: this.buildPriceRangeFacet(aggregationResults.price_ranges, request),
      amenities: this.buildAmenityFacet(aggregationResults.amenities, request),
      facilities: this.buildFacilityFacets(aggregationResults, request),
      chains: this.buildChainFacet(aggregationResults.chains, request),
    };
  }

  private buildTypeFacet(
    aggregation: BucketAggregation,
    request: AccommodationSearchRequest
  ): TypeFacet {
    const options = aggregation.buckets.map(bucket => ({
      value: bucket.key,
      label: this.formatPropertyType(bucket.key),
      count: bucket.doc_count,
      selected: request.filters.types?.includes(bucket.key) ?? false,
    }));

    return {
      name: 'Property Type',
      type: 'checkbox',
      options: options.sort((a, b) => b.count - a.count),
    };
  }

  private buildStarRatingFacet(
    aggregation: BucketAggregation,
    request: AccommodationSearchRequest
  ): StarRatingFacet {
    const ratings = [5, 4, 3, 2, 1];

    return {
      name: 'Star Rating',
      type: 'checkbox',
      options: ratings.map(stars => {
        const bucket = aggregation.buckets.find(b => b.key === stars);
        return {
          value: stars,
          label: `${stars} Stars`,
          count: bucket?.doc_count || 0,
          selected: request.filters.starRating?.min === stars,
        };
      }).filter(o => o.count > 0),
    };
  }

  private buildGuestRatingFacet(
    aggregation: RangeAggregation,
    request: AccommodationSearchRequest
  ): GuestRatingFacet {
    return {
      name: 'Guest Rating',
      type: 'checkbox',
      options: aggregation.buckets.map(bucket => ({
        value: bucket.key,
        label: this.formatRatingLabel(bucket.key),
        count: bucket.doc_count,
        selected: request.filters.guestRating?.min === this.getMinRatingForRange(bucket.key),
      })),
    };
  }

  private buildAmenityFacet(
    aggregation: BucketAggregation,
    request: AccommodationSearchRequest
  ): AmenityFacet {
    const amenityGroups = this.groupAmenitiesByType(aggregation.buckets);

    return {
      name: 'Amenities',
      type: 'grouped_checkbox',
      groups: Object.entries(amenityGroups).map(([type, amenities]) => ({
        type,
        label: this.formatAmenityType(type),
        options: amenities.map(a => ({
          value: a.key,
          label: this.formatAmenityName(a.key),
          count: a.doc_count,
          selected: request.filters.amenities?.includes(a.key) ?? false,
        })).sort((a, b) => b.count - a.count).slice(0, 10),
      })),
    };
  }

  private groupAmenitiesByType(
    buckets: Bucket[]
  ): Record<string, Bucket[]> {
    return buckets.reduce((acc, bucket) => {
      const amenity = this.amenityRepository.findByCode(bucket.key);
      const type = amenity?.type || 'other';

      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(bucket);

      return acc;
    }, {} as Record<string, Bucket[]>);
  }

  private formatPropertyType(type: string): string {
    const labels: Record<string, string> = {
      hotel: 'Hotel',
      resort: 'Resort',
      villa: 'Villa',
      apartment: 'Apartment',
      hostel: 'Hostel',
      boutique: 'Boutique Hotel',
    };
    return labels[type] || this.toTitleCase(type);
  }

  private formatRatingLabel(key: string): string {
    const labels: Record<string, string> = {
      excellent: 'Excellent (9+)',
      very_good: 'Very Good (8-9)',
      good: 'Good (7-8)',
      fair: 'Fair (6-7)',
      poor: 'Poor (<6)',
    };
    return labels[key] || key;
  }

  private formatAmenityType(type: string): string {
    return this.toTitleCase(type.replace('_', ' '));
  }

  private formatAmenityName(code: string): string {
    const amenity = this.amenityRepository.findByCode(code);
    return amenity?.name?.en || this.toTitleCase(code.replace(/_/g, ' '));
  }

  private toTitleCase(str: string): string {
    return str
      .toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
}
```

---

## Relevance Scoring

### Scoring Function

```typescript
export class RelevanceScoringService {
  async calculateScore(
    property: Property,
    query: AccommodationSearchRequest,
    context: SearchContext
  ): Promise<RelevanceScore> {
    const components: ScoreComponent[] = [];

    // 1. Text match score
    const textScore = this.calculateTextScore(property, query);
    components.push({ name: 'text_match', score: textScore, weight: 0.3 });

    // 2. Location proximity score
    const locationScore = await this.calculateLocationScore(property, query);
    components.push({ name: 'location', score: locationScore, weight: 0.2 });

    // 3. Price competitiveness score
    const priceScore = await this.calculatePriceScore(property, query);
    components.push({ name: 'price', score: priceScore, weight: 0.15 });

    // 4. Quality score
    const qualityScore = this.calculateQualityScore(property);
    components.push({ name: 'quality', score: qualityScore, weight: 0.15 });

    // 5. Popularity score
    const popularityScore = await this.calculatePopularityScore(property);
    components.push({ name: 'popularity', score: popularityScore, weight: 0.1 });

    // 6. Personalization score
    if (context.userId) {
      const personalScore = await this.calculatePersonalizationScore(
        property,
        context.userId
      );
      components.push({ name: 'personalization', score: personalScore, weight: 0.1 });
    }

    // Calculate weighted total
    const total = components.reduce(
      (sum, component) => sum + component.score * component.weight,
      0
    );

    return {
      total,
      components,
    };
  }

  private calculateTextScore(property: Property, query: AccommodationSearchRequest): number {
    if (!query.destination) return 0.5;

    const destination = query.destination.toLowerCase();
    const name = property.name.en.toLowerCase();
    const city = property.location.area?.city?.en.toLowerCase() || '';
    const country = property.location.area?.country?.en.toLowerCase() || '';

    // Exact name match
    if (name.includes(destination)) return 1;

    // City match
    if (city.includes(destination) || destination.includes(city)) return 0.9;

    // Country match
    if (country.includes(destination) || destination.includes(country)) return 0.7;

    // Partial match
    if (
      name.includes(destination.substring(0, 3)) ||
      city.includes(destination.substring(0, 3))
    ) {
      return 0.5;
    }

    return 0;
  }

  private async calculateLocationScore(
    property: Property,
    query: AccommodationSearchRequest
  ): Promise<number> {
    if (!query.coordinates) return 0.5;

    const distance = this.calculateDistance(
      property.location.coordinates,
      query.coordinates
    );

    const radius = query.radius || 50;

    // Score decreases with distance
    return Math.max(0, 1 - distance / radius);
  }

  private async calculatePriceScore(
    property: Property,
    query: AccommodationSearchRequest
  ): Promise<number> {
    // Get average price for similar properties
    const avgPrice = await this.pricingService.getAveragePrice(
      property.location,
      query.filters?.types
    );

    const propertyPrice = await this.pricingService.getStartingPrice(property.id);

    if (!propertyPrice) return 0.5;

    // Score based on competitiveness
    const ratio = propertyPrice / avgPrice;

    if (ratio <= 0.8) return 1; // Very competitive
    if (ratio <= 0.9) return 0.8;
    if (ratio <= 1.1) return 0.6;
    if (ratio <= 1.3) return 0.4;

    return 0.2; // Expensive
  }

  private calculateQualityScore(property: Property): number {
    return property.metadata.sourceQuality || 0.5;
  }

  private async calculatePopularityScore(property: Property): Promise<number> {
    const stats = await this.analyticsService.getPropertyStats(property.id);

    // Normalize bookings to 0-1 range
    const maxBookings = 1000; // Configurable
    const bookingScore = Math.min(stats.recentBookings / maxBookings, 1);

    // Weight with rating
    const ratingScore = (property.rating.guestRating || 0) / 10;

    return (bookingScore * 0.6) + (ratingScore * 0.4);
  }

  private async calculatePersonalizationScore(
    property: Property,
    userId: string
  ): Promise<number> {
    const user = await this.userService.getUser(userId);
    const prefs = user.preferences;

    let score = 0;

    // Preferred types
    if (prefs.preferredTypes?.includes(property.type)) {
      score += 0.3;
    }

    // Preferred amenities
    const matchedAmenities = property.amenities.filter(a =>
      prefs.preferredAmenities?.includes(a.id)
    );
    if (prefs.preferredAmenities?.length > 0) {
      score += (matchedAmenities.length / prefs.preferredAmenities.length) * 0.3;
    }

    // Previously booked
    const booked = await this.bookingService.hasUserBooked(userId, property.id);
    if (booked) {
      score += 0.2;
    }

    // Wishlist
    const wishlisted = await this.wishlistService.hasWishlisted(userId, property.id);
    if (wishlisted) {
      score += 0.2;
    }

    return Math.min(score, 1);
  }

  private calculateDistance(
    coords1: Coordinates,
    coords2: Coordinates
  ): number {
    const R = 6371; // Earth's radius in km
    const dLat = this.toRad(coords2.latitude - coords1.latitude);
    const dLon = this.toRad(coords2.longitude - coords1.longitude);

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(coords1.latitude)) *
      Math.cos(this.toRad(coords2.latitude)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  private toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
  }
}
```

---

## Map Search

### Map Query Service

```typescript
export class MapSearchService {
  async searchInBounds(
    bounds: MapBounds,
    filters: PropertyFilters,
    zoom: number
  ): Promise<MapSearchResult> {
    // Determine clustering based on zoom level
    const clusterSize = this.getClusterSizeForZoom(zoom);

    if (zoom < 10) {
      // Return clustered results
      return this.clusterProperties(bounds, filters, clusterSize);
    } else {
      // Return individual properties
      return this.getPropertiesInBounds(bounds, filters);
    }
  }

  private async clusterProperties(
    bounds: MapBounds,
    filters: PropertyFilters,
    clusterSize: number
  ): Promise<ClusteredResult> {
    // Get all properties in bounds
    const properties = await this.propertyRepository.findByBounds(bounds, filters);

    // Group by geohash precision (cluster size)
    const precision = Math.max(1, 7 - Math.log2(clusterSize));

    const clusters = new Map<string, PropertyCluster>();

    for (const property of properties) {
      const geohash = property.location.geohash?.substring(0, precision) || '';

      if (!clusters.has(geohash)) {
        clusters.set(geohash, {
          id: geohash,
          position: this.calculateClusterCenter(geohash),
          count: 0,
          propertyIds: [],
          priceRange: { min: Infinity, max: -Infinity },
        });
      }

      const cluster = clusters.get(geohash)!;
      cluster.count++;
      cluster.propertyIds.push(property.id);

      // Update price range
      const price = await this.pricingService.getStartingPrice(property.id);
      if (price) {
        cluster.priceRange.min = Math.min(cluster.priceRange.min, price);
        cluster.priceRange.max = Math.max(cluster.priceRange.max, price);
      }
    }

    return {
      type: 'clustered',
      clusters: Array.from(clusters.values()),
    };
  }

  private async getPropertiesInBounds(
    bounds: MapBounds,
    filters: PropertyFilters
  ): Promise<IndividualResult> {
    const properties = await this.propertyRepository.findByBounds(bounds, filters);

    return {
      type: 'individual',
      properties: await Promise.all(
        properties.map(async p => ({
          id: p.id,
          name: p.name,
          position: p.location.coordinates,
          type: p.type,
          starRating: p.rating.stars,
          guestRating: p.rating.guestRating,
          price: await this.pricingService.getStartingPrice(p.id),
          thumbnail: p.content.images[0]?.thumbnailUrl,
        }))
      ),
    };
  }

  private getClusterSizeForZoom(zoom: number): number {
    // Zoom to cluster size (km) mapping
    if (zoom < 5) return 500;
    if (zoom < 7) return 200;
    if (zoom < 9) return 100;
    if (zoom < 11) return 50;
    if (zoom < 13) return 20;
    return 10;
  }

  private calculateClusterCenter(geohash: string): Coordinates {
    // Decode geohash to get center point
    const decoded = geohash.decode(geohash);
    return {
      latitude: decoded.latitude,
      longitude: decoded.longitude,
    };
  }
}
```

---

## Recommendations

### Recommendation Engine

```typescript
export class AccommodationRecommendationService {
  async getRecommendations(
    context: RecommendationContext
  ): Promise<RecommendedProperty[]> {
    const strategies = [
      this.collaborativeFiltering(context),
      this.contentBasedFiltering(context),
      this.trendBasedRecommendation(context),
      this.locationBasedRecommendation(context),
    ];

    const results = await Promise.all(strategies);

    // Combine and score
    const combined = this.combineRecommendations(results);

    // Remove already seen
    const filtered = this.filterSeen(combined, context.seenPropertyIds);

    // Rank and limit
    return filtered
      .sort((a, b) => b.score - a.score)
      .slice(0, context.limit || 20);
  }

  private async collaborativeFiltering(
    context: RecommendationContext
  ): Promise<RecommendationScore[]> {
    if (!context.userId) {
      return [];
    }

    // Find similar users based on booking history
    const similarUsers = await this.userSimilarityService.findSimilar(
      context.userId,
      20
    );

    // Get properties booked by similar users
    const recommendations = new Map<string, number>();

    for (const similarUser of similarUsers) {
      const bookings = await this.bookingService.getUserBookings(similarUser.userId);

      for (const booking of bookings) {
        const score = similarUser.similarity * (booking.rating || 0.5);
        recommendations.set(
          booking.propertyId,
          (recommendations.get(booking.propertyId) || 0) + score
        );
      }
    }

    return Array.from(recommendations.entries()).map(([propertyId, score]) => ({
      propertyId,
      score,
      source: 'collaborative',
    }));
  }

  private async contentBasedFiltering(
    context: RecommendationContext
  ): Promise<RecommendationScore[]> {
    if (!context.userId && !context.propertyId) {
      return [];
    }

    let profile: UserProfile;

    if (context.propertyId) {
      // Use property as profile
      const property = await this.propertyService.getProperty(context.propertyId);
      profile = this.propertyToProfile(property);
    } else {
      // Use user preferences
      profile = await this.userProfileService.buildProfile(context.userId!);
    }

    // Find similar properties
    const similar = await this.propertyRepository.findByProfile(profile, 50);

    return similar.map(s => ({
      propertyId: s.id,
      score: s.similarity,
      source: 'content',
    }));
  }

  private async trendBasedRecommendation(
    context: RecommendationContext
  ): Promise<RecommendationScore[]> {
    // Get trending properties in the area
    const trending = await this.trendingService.getTrendingProperties(
      context.location,
      7 // days
    );

    return trending.map((t, index) => ({
      propertyId: t.propertyId,
      score: 1 - (index / trending.length), // Decay by position
      source: 'trending',
    }));
  }

  private async locationBasedRecommendation(
    context: RecommendationContext
  ): Promise<RecommendationScore[]> {
    if (!context.location) {
      return [];
    }

    // Find highly-rated properties nearby
    const nearby = await this.propertyRepository.findNearbyHighRated(
      context.location,
      20
    );

    return nearby.map((n, index) => ({
      propertyId: n.id,
      score: (1 - index / nearby.length) * n.rating,
      source: 'location',
    }));
  }

  private combineRecommendations(
    results: RecommendationScore[][]
  ): RecommendationScore[] {
    const combined = new Map<string, RecommendationScore>();

    for (const result of results) {
      for (const item of result) {
        const existing = combined.get(item.propertyId);

        if (existing) {
          existing.score = Math.max(existing.score, item.score);
          existing.sources.push(item.source);
        } else {
          combined.set(item.propertyId, {
            ...item,
            sources: [item.source],
          });
        }
      }
    }

    // Boost items with multiple sources
    for (const item of combined.values()) {
      if (item.sources.length > 1) {
        item.score *= 1 + (item.sources.length - 1) * 0.1;
      }
    }

    return Array.from(combined.values());
  }
}
```

---

## Auto-Complete

### Suggestion Service

```typescript
export class AutoCompleteService {
  async getSuggestions(
    query: string,
    context: SuggestionContext
  ): Promise<Suggestion[]> {
    if (query.length < 2) {
      return [];
    }

    const [
      destinations,
      properties,
      landmarks,
    ] = await Promise.all([
      this.getDestinationSuggestions(query, context),
      this.getPropertySuggestions(query, context),
      this.getLandmarkSuggestions(query, context),
    ]);

    return [
      ...destinations.map(d => ({ ...d, type: 'destination' })),
      ...properties.map(p => ({ ...p, type: 'property' })),
      ...landmarks.map(l => ({ ...l, type: 'landmark' })),
    ]
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }

  private async getDestinationSuggestions(
    query: string,
    context: SuggestionContext
  ): Promise<DestinationSuggestion[]> {
    const results = await this.elasticsearch.search({
      index: 'destinations',
      body: {
        query: {
          bool: {
            should: [
              {
                match: {
                  name: {
                    query,
                    fuzziness: 'AUTO',
                    boost: 3,
                  },
                },
              },
              {
                match: {
                  name_autocomplete: {
                    query,
                    fuzziness: 1,
                  },
                },
              },
              {
                match: {
                  country: {
                    query,
                    boost: 2,
                  },
                },
              },
            ],
            minimum_should_match: 1,
          },
        },
        size: 5,
      },
    });

    return results.hits.hits.map(hit => ({
      id: hit._id,
      name: hit._source.name,
      country: hit._source.country,
      coordinates: hit._source.location,
      type: 'city',
      score: hit._score || 0,
    }));
  }

  private async getPropertySuggestions(
    query: string,
    context: SuggestionContext
  ): Promise<PropertySuggestion[]> {
    const results = await this.elasticsearch.search({
      index: 'properties',
      body: {
        query: {
          bool: {
            must: [
              { term: { is_active: true } },
              {
                bool: {
                  should: [
                    {
                      match: {
                        'name.autocomplete': {
                          query,
                          fuzziness: 1,
                        },
                      },
                    },
                    {
                      match_phrase_prefix: {
                        'name.keyword': {
                          query,
                        },
                      },
                    },
                  ],
                  minimum_should_match: 1,
                },
              },
            ],
          },
        },
        size: 3,
      },
    });

    return results.hits.hits.map(hit => ({
      id: hit._id,
      name: hit._source.name.en,
      type: hit._source.type,
      coordinates: hit._source.location,
      thumbnail: hit._source.images?.[0]?.thumbnail,
      score: hit._score || 0,
    }));
  }

  private async getLandmarkSuggestions(
    query: string,
    context: SuggestionContext
  ): Promise<LandmarkSuggestion[]> {
    // Search for nearby landmarks if location provided
    if (!context.coordinates) {
      return [];
    }

    const landmarks = await this.placesService.autocomplete({
      query,
      location: context.coordinates,
      radius: 50000, // 50km
    });

    return landmarks.slice(0, 3).map(l => ({
      id: l.id,
      name: l.name,
      vicinity: l.vicinity,
      coordinates: l.location,
      score: 1 - (landmarks.indexOf(l) / landmarks.length),
    }));
  }
}
```

---

## API Endpoints

### Search Endpoints

```
POST   /accommodations/search
GET    /accommodations/search/suggest
POST   /accommodations/search/facets
```

### Map Endpoints

```
POST   /accommodations/map/search
GET    /accommodations/map/clusters
```

### Recommendation Endpoints

```
POST   /accommodations/recommendations
GET    /accommodations/recommendations/trending
```

---

**Next:** [Booking Integration](./ACCOMMODATION_CATALOG_05_BOOKING.md) — Reservations, modifications, and cancellations
