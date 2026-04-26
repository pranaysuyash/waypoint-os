# Content Management Part 2: Content Modeling

> Schema design, field types, and content relationships

**Series:** Content Management
**Previous:** [Part 1: CMS Architecture](./CONTENT_MANAGEMENT_01_ARCHITECTURE.md)
**Next:** [Part 3: Content Delivery](./CONTENT_MANAGEMENT_03_DELIVERY.md)

---

## Table of Contents

1. [Schema Design Principles](#schema-design-principles)
2. [Core Content Types](#core-content-types)
3. [Field Types](#field-types)
4. [References and Relationships](#references-and-relationships)
5. [Localization](#localization)
6. [Rich Text and Blocks](#rich-text-and-blocks)

---

## Schema Design Principles

### Design Guidelines

```typescript
// Content modeling best practices

interface SchemaPrinciples {
  // 1. Structure over presentation
  structure: 'Separate content from display logic';

  // 2. Reusability
  reusability: 'Create portable content blocks';

  // 3. Extensibility
  extensibility: 'Design for future requirements';

  // 4. Validation
  validation: 'Enforce data quality at schema level';

  // 5. Performance
  performance: 'Optimize for query patterns';
}
```

### Schema Definition Pattern

```typescript
// Sanity schema definition

import { defineField, defineType } from 'sanity';

export const destination = defineType({
  name: 'destination',
  title: 'Destination',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      type: 'string',
      validation: (Rule) => Rule.required().min(2).max(100),
    }),
    defineField({
      name: 'slug',
      type: 'slug',
      options: { source: 'title' },
      validation: (Rule) => Rule.required(),
    }),
    // ... more fields
  ],
  preview: {
    select: {
      title: 'title',
      media: 'image',
    },
  },
});
```

---

## Core Content Types

### Destination Schema

```typescript
// Destination content type

export const destination = defineType({
  name: 'destination',
  title: 'Destination',
  type: 'document',
  fields: [
    // Identity
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: { source: 'title' },
      validation: (Rule) => Rule.required(),
    }),

    // Location
    defineField({
      name: 'country',
      title: 'Country',
      type: 'reference',
      to: [{ type: 'country' }],
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'region',
      title: 'Region',
      type: 'string',
    }),
    defineField({
      name: 'coordinates',
      title: 'Coordinates',
      type: 'geopoint',
      validation: (Rule) => Rule.required(),
    }),

    // Content
    defineField({
      name: 'summary',
      title: 'Summary',
      type: 'text',
      rows: 3,
      validation: (Rule) => Rule.required().max(300),
    }),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'array',
      of: [{ type: 'block' }],
    }),

    // Media
    defineField({
      name: 'heroImage',
      title: 'Hero Image',
      type: 'image',
      options: { hotspot: true },
      fields: [
        defineField({
          name: 'alt',
          title: 'Alt Text',
          type: 'string',
        }),
      ],
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'gallery',
      title: 'Gallery',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'image',
          options: { hotspot: true },
          fields: [
            defineField({
              name: 'alt',
              title: 'Alt Text',
              type: 'string',
            }),
            defineField({
              name: 'caption',
              title: 'Caption',
              type: 'string',
            }),
          ],
        }),
      ],
      validation: (Rule) => Rule.max(20),
    }),

    // Travel Info
    defineField({
      name: 'bestTimeToVisit',
      title: 'Best Time to Visit',
      type: 'array',
      of: [{ type: 'string' }],
    }),
    defineField({
      name: 'attractions',
      title: 'Attractions',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({ name: 'name', type: 'string' }),
            defineField({ name: 'description', type: 'text' }),
            defineField({ name: 'image', type: 'image' }),
          ],
        }),
      ],
    }),
    defineField({
      name: 'localInfo',
      title: 'Local Information',
      type: 'object',
      fields: [
        defineField({ name: 'currency', type: 'string' }),
        defineField({ name: 'language', type: 'string' }),
        defineField({ name: 'timezone', type: 'string' }),
        defineField({ name: 'visaRequired', type: 'boolean' }),
      ],
    }),

    // SEO
    defineField({
      name: 'seo',
      title: 'SEO',
      type: 'seo', // Custom SEO object type
    }),
  ],

  // Order by title in studio
  orderings: [
    {
      title: 'Title (A-Z)',
      by: [{ field: 'title', direction: 'asc' }],
    },
  ],
});
```

### Accommodation Schema

```typescript
// Accommodation content type

export const accommodation = defineType({
  name: 'accommodation',
  title: 'Accommodation',
  type: 'document',
  fields: [
    // Identity
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: { source: 'name' },
    }),

    // Classification
    defineField({
      name: 'type',
      title: 'Type',
      type: 'string',
      options: {
        list: [
          { title: 'Hotel', value: 'hotel' },
          { title: 'Resort', value: 'resort' },
          { title: 'Villa', value: 'villa' },
          { title: 'Apartment', value: 'apartment' },
          { title: 'Hostel', value: 'hostel' },
          { title: 'B&B', value: 'bandb' },
        ],
      },
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'starRating',
      title: 'Star Rating',
      type: 'number',
      options: {
        list: [1, 2, 3, 4, 5],
      },
    }),

    // Location
    defineField({
      name: 'destination',
      title: 'Destination',
      type: 'reference',
      to: [{ type: 'destination' }],
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'address',
      title: 'Address',
      type: 'object',
      fields: [
        defineField({ name: 'street', type: 'string' }),
        defineField({ name: 'city', type: 'string' }),
        defineField({ name: 'state', type: 'string' }),
        defineField({ name: 'postalCode', type: 'string' }),
        defineField({ name: 'country', type: 'string' }),
      ],
    }),
    defineField({
      name: 'coordinates',
      title: 'Coordinates',
      type: 'geopoint',
    }),

    // Content
    defineField({
      name: 'summary',
      title: 'Summary',
      type: 'text',
      rows: 3,
    }),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'array',
      of: [{ type: 'block' }],
    }),

    // Media
    defineField({
      name: 'images',
      title: 'Images',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'image',
          options: { hotspot: true },
          fields: [
            defineField({ name: 'alt', type: 'string' }),
            defineField({ name: 'category', type: 'string' }),
          ],
        }),
      ],
      validation: (Rule) => Rule.min(5).max(30),
    }),

    // Amenities
    defineField({
      name: 'amenities',
      title: 'Amenities',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'reference',
          to: [{ type: 'amenity' }],
        }),
      ],
    }),

    // Room Types
    defineField({
      name: 'roomTypes',
      title: 'Room Types',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({ name: 'name', type: 'string' }),
            defineField({ name: 'description', type: 'text' }),
            defineField({ name: 'maxOccupancy', type: 'number' }),
            defineField({ name: 'bedConfiguration', type: 'string' }),
            defineField({ name: 'images', type: 'array', of: [{ type: 'image' }] }),
          ],
        }),
      ],
    }),

    // Policies
    defineField({
      name: 'policies',
      title: 'Policies',
      type: 'object',
      fields: [
        defineField({ name: 'checkInTime', type: 'string' }),
        defineField({ name: 'checkOutTime', type: 'string' }),
        defineField({ name: 'cancellationPolicy', type: 'text' }),
        defineField({ name: 'childPolicy', type: 'text' }),
        defineField({ name: 'petPolicy', type: 'text' }),
      ],
    }),

    // Pricing Display (reference only - actual pricing in DB)
    defineField({
      name: 'startingPrice',
      title: 'Starting Price (Display)',
      type: 'object',
      fields: [
        defineField({ name: 'amount', type: 'number' }),
        defineField({ name: 'currency', type: 'string' }),
        defineField({ name: 'per', type: 'string' }), // night, week, etc.
      ],
    }),

    // External Reference
    defineField({
      name: 'supplierId',
      title: 'Supplier ID',
      type: 'string',
      description: 'Reference to external accommodation system',
    }),

    // SEO
    defineField({
      name: 'seo',
      title: 'SEO',
      type: 'seo',
    }),
  ],
});
```

### Deal/Promotion Schema

```typescript
// Deal content type

export const deal = defineType({
  name: 'deal',
  title: 'Deal / Promotion',
  type: 'document',
  fields: [
    // Identity
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: { source: 'title' },
    }),

    // Deal Type
    defineField({
      name: 'dealType',
      title: 'Deal Type',
      type: 'string',
      options: {
        list: [
          { title: 'Percentage Off', value: 'percentage' },
          { title: 'Fixed Amount', value: 'fixed' },
          { title: 'Free Upgrade', value: 'upgrade' },
          { title: 'Package Deal', value: 'package' },
          { title: 'Early Bird', value: 'earlyBird' },
          { title: 'Last Minute', value: 'lastMinute' },
        ],
      },
    }),

    // Discount
    defineField({
      name: 'discount',
      title: 'Discount',
      type: 'object',
      fields: [
        defineField({
          name: 'type',
          title: 'Type',
          type: 'string',
          options: {
            list: [
              { title: 'Percentage', value: 'percentage' },
              { title: 'Fixed', value: 'fixed' },
            ],
          },
        }),
        defineField({ name: 'value', type: 'number' }),
        defineField({ name: 'currency', type: 'string' }),
      ],
    }),

    // Validity
    defineField({
      name: 'validFrom',
      title: 'Valid From',
      type: 'datetime',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'validTo',
      title: 'Valid To',
      type: 'datetime',
      validation: (Rule) => Rule.required().min(
        // Must be after validFrom
        // (implemented in custom validation)
      ),
    }),

    // Applicability
    defineField({
      name: 'destinations',
      title: 'Applicable Destinations',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'reference',
          to: [{ type: 'destination' }],
        }),
      ],
      description: 'Leave empty for all destinations',
    }),
    defineField({
      name: 'accommodations',
      title: 'Applicable Accommodations',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'reference',
          to: [{ type: 'accommodation' }],
        }),
      ],
      description: 'Leave empty for all accommodations',
    }),

    // Promo Code
    defineField({
      name: 'promoCode',
      title: 'Promo Code',
      type: 'string',
      validation: (Rule) =>
        Rule.custom((value) => {
          if (value && !/^[A-Z0-9_-]+$/i.test(value)) {
            return 'Only alphanumeric, underscore, and hyphen allowed';
          }
          return true;
        }),
    }),

    // Content
    defineField({
      name: 'description',
      title: 'Description',
      type: 'array',
      of: [{ type: 'block' }],
    }),
    defineField({
      name: 'terms',
      title: 'Terms and Conditions',
      type: 'array',
      of: [{ type: 'block' }],
    }),

    // Media
    defineField({
      name: 'bannerImage',
      title: 'Banner Image',
      type: 'image',
      options: { hotspot: true },
    }),

    // Display Settings
    defineField({
      name: 'featured',
      title: 'Featured',
      type: 'boolean',
      description: 'Show on homepage',
    }),
    defineField({
      name: 'priority',
      title: 'Display Priority',
      type: 'number',
      description: 'Higher values shown first',
    }),

    // Limits
    defineField({
      name: 'usageLimit',
      title: 'Usage Limit',
      type: 'number',
      description: 'Maximum times this deal can be used',
    }),
    defineField({
      name: 'usageCount',
      title: 'Usage Count',
      type: 'number',
      readOnly: true,
    }),

    // SEO
    defineField({
      name: 'seo',
      title: 'SEO',
      type: 'seo',
    }),
  ],

  // Preview configuration
  preview: {
    select: {
      title: 'title',
      discount: 'discount.value',
      validTo: 'validTo',
      media: 'bannerImage',
    },
    prepare(selection) {
      const { title, discount, validTo } = selection;
      return {
        title,
        subtitle: `${discount}% off until ${new Date(validTo).toLocaleDateString()}`,
      };
    },
  },
});
```

---

## Field Types

### Built-in Field Types

```typescript
// Common Sanity field types

interface FieldTypes {
  // Text types
  text: {
    string: 'Single line text';
    text: 'Multi-line text';
    email: 'Email validation';
    url: 'URL validation';
  };

  // Numeric types
  number: 'Integer or decimal number';

  // Selection types
  select: 'Dropdown with predefined options';
  radio: 'Radio button selection';

  // Boolean
  boolean: 'True/false toggle';

  // Date/Time
  date: 'Date without time';
    datetime: 'Date and time';

  // Media
  image: 'Image with hotspot and crop';
  file: 'File upload (PDF, etc.)';

  // References
  reference: 'Link to another document';
  array: 'List of items';

  // Structured
  object: 'Nested fields';
  block: 'Rich text block';

  // Special
  slug: 'URL-friendly identifier';
  geopoint: 'Latitude/longitude';
  color: 'Color picker';
}
```

### Custom Field Types

```typescript
// Reusable field groups

// SEO field group
export const seo = defineType({
  name: 'seo',
  title: 'SEO',
  type: 'object',
  fields: [
    defineField({
      name: 'title',
      title: 'SEO Title',
      type: 'string',
      description: 'Recommended: 50-60 characters',
      validation: (Rule) => Rule.max(60),
    }),
    defineField({
      name: 'description',
      title: 'Meta Description',
      type: 'text',
      rows: 3,
      description: 'Recommended: 150-160 characters',
      validation: (Rule) => Rule.max(160),
    }),
    defineField({
      name: 'ogImage',
      title: 'Open Graph Image',
      type: 'image',
    }),
    defineField({
      name: 'noIndex',
      title: 'No Index',
      type: 'boolean',
      description: 'Prevent search engines from indexing',
    }),
  ],
});

// Image with alt text
export const imageWithAlt = defineType({
  name: 'imageWithAlt',
  title: 'Image with Alt Text',
  type: 'image',
  options: { hotspot: true },
  fields: [
    defineField({
      name: 'alt',
      title: 'Alt Text',
      type: 'string',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'caption',
      title: 'Caption',
      type: 'string',
    }),
  ],
});

// CTA Button
export const ctaButton = defineType({
  name: 'ctaButton',
  title: 'CTA Button',
  type: 'object',
  fields: [
    defineField({ name: 'text', type: 'string', validation: (Rule) => Rule.required() }),
    defineField({ name: 'href', type: 'url', validation: (Rule) => Rule.required() }),
    defineField({
      name: 'variant',
      title: 'Variant',
      type: 'string',
      options: {
        list: [
          { title: 'Primary', value: 'primary' },
          { title: 'Secondary', value: 'secondary' },
          { title: 'Outline', value: 'outline' },
        ],
      },
      initialValue: 'primary',
    }),
  ],
});
```

---

## References and Relationships

### Reference Fields

```typescript
// Single reference
defineField({
  name: 'destination',
  title: 'Destination',
  type: 'reference',
  to: [{ type: 'destination' }],
});

// Multiple references
defineField({
  name: 'destinations',
  title: 'Destinations',
  type: 'array',
  of: [
    defineArrayMember({
      type: 'reference',
      to: [{ type: 'destination' }],
    }),
  ],
});

// Polymorphic reference (to multiple types)
defineField({
  name: 'featuredContent',
  title: 'Featured Content',
  type: 'reference',
  to: [
    { type: 'destination' },
    { type: 'accommodation' },
    { type: 'deal' },
  ],
});
```

### Querying References

```typescript
// GROQ reference queries

// Fetch document with referenced data
export async function getDestinationWithCountry(slug: string) {
  return sanityFetch({
    query: groq`*[
      _type == "destination" &&
      slug.current == $slug
    ][0]{
      _id,
      title,
      "country": country->{
        _id,
        name,
        "flagUrl": flag.asset->url
      },
      "accommodations": *[
        _type == "accommodation" &&
        ^.slug.current == $slug
      ]{
        _id,
        name,
        slug,
        "imageUrl": images[0].asset->url
      }
    }`,
    params: { slug },
  });
}

// Fetch documents that reference this one
export async function getAccommodationsForDestination(
  destinationSlug: string
) {
  return sanityFetch({
    query: groq`*[
      _type == "accommodation" &&
      destination->slug.current == $slug
    ]|order(name asc){
      _id,
      name,
      slug,
      "destination": destination->title,
    }`,
    params: { slug: destinationSlug },
  });
}
```

---

## Localization

### I18n Field Strategy

```typescript
// Localization approaches

interface LocalizationStrategy {
  // Option 1: Separate language documents
  separateDocuments: {
    pros: ['Clean separation', 'Independent publishing'];
    cons: ['More documents', 'Complex queries'];
  };

  // Option 2: Language prefix fields (RECOMMENDED)
  prefixFields: {
    pros: ['Single document', 'Easy comparison'];
    cons: ['More fields in schema'];
  };

  // Option 3: Sanity i18n plugin
  plugin: {
    pros: ['Automated', 'Studio integration'];
    cons: ['External dependency'];
  };
}

// Selected: Prefix fields for core content
export const localizedDestination = defineType({
  name: 'destination',
  title: 'Destination',
  type: 'document',
  fields: [
    // Non-localized fields
    defineField({
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: { source: 'title' },
    }),
    defineField({
      name: 'country',
      title: 'Country',
      type: 'reference',
      to: [{ type: 'country' }],
    }),

    // Localized fields
    defineField({
      name: 'title',
      title: 'Title',
      type: 'object',
      fieldsets: [
        { name: 'en', title: 'English' },
        { name: 'es', title: 'Spanish' },
        { name: 'fr', title: 'French' },
      ],
      fields: [
        defineField({
          name: 'en',
          title: 'English',
          type: 'string',
        }),
        defineField({
          name: 'es',
          title: 'Spanish',
          type: 'string',
        }),
        defineField({
          name: 'fr',
          title: 'French',
          type: 'string',
        }),
      ],
    }),

    // Or use Sanity i18n for simpler setup
    defineField({
      name: 'title',
      title: 'Title',
      type: 'localeString',
      options: { locales: ['en', 'es', 'fr'] },
    }),
  ],
});
```

### Querying Localized Content

```typescript
// Language-aware queries

import { groq } from 'next-sanity';

export async function getLocalizedDestination(
  slug: string,
  locale = 'en'
) {
  return sanityFetch({
    query: groq`*[
      _type == "destination" &&
      slug.current == $slug
    ][0]{
      _id,
      "title": title.${locale},
      "description": description.${locale},
      country,
      // Always use image (not localized)
      heroImage,
    }`,
    params: { slug, locale },
    tags: ['destination'],
  });
}

// Fallback to English if translation missing
export async function getDestinationWithFallback(
  slug: string,
  locale = 'en'
) {
  return sanityFetch({
    query: groq`*[
      _type == "destination" &&
      slug.current == $slug
    ][0]{
      _id,
      "title": coalesce(title.${locale}, title.en),
      "description": coalesce(description.${locale}, description.en),
      country,
      heroImage,
    }`,
    params: { slug, locale },
  });
}
```

---

## Rich Text and Blocks

### Portable Text Configuration

```typescript
// Portable text (rich text) configuration

import { defineArrayMember } from 'sanity';

export const blockContent = defineType({
  name: 'blockContent',
  title: 'Block Content',
  type: 'array',
  of: [
    // Standard blocks
    defineArrayMember({
      type: 'block',
      // Styles
      styles: [
        { title: 'Normal', value: 'normal' },
        { title: 'Heading 1', value: 'h1' },
        { title: 'Heading 2', value: 'h2' },
        { title: 'Heading 3', value: 'h3' },
        { title: 'Quote', value: 'blockquote' },
      ],
      // Lists
      lists: [
        { title: 'Bullet', value: 'bullet' },
        { title: 'Numbered', value: 'number' },
      ],
      // Marks
      marks: {
        decorators: [
          { title: 'Strong', value: 'strong' },
          { title: 'Emphasis', value: 'em' },
          { title: 'Code', value: 'code' },
          { title: 'Underline', value: 'underline' },
          { title: 'Strike', value: 'strikethrough' },
        ],
        annotations: [
          {
            name: 'link',
            type: 'object',
            fields: [
              defineField({
                name: 'href',
                title: 'URL',
                type: 'url',
              }),
            ],
          },
          {
            name: 'internalLink',
            type: 'object',
            fields: [
              defineField({
                name: 'reference',
                title: 'Reference',
                type: 'reference',
                to: [{ type: 'destination' }, { type: 'accommodation' }],
              }),
            ],
          },
        ],
      },
    }),

    // Custom blocks
    defineArrayMember({
      type: 'image',
      options: { hotspot: true },
    }),
    defineArrayMember({
      type: 'callToAction',
    }),
    defineArrayMember({
      type: 'destinationEmbed',
    }),
  ],
});
```

### Custom Block Types

```typescript
// Custom Portable Text blocks

// CTA Block
export const callToAction = defineType({
  name: 'callToAction',
  title: 'Call to Action',
  type: 'object',
  fields: [
    defineField({ name: 'title', type: 'string' }),
    defineField({ name: 'body', type: 'text' }),
    defineField({
      name: 'button',
      type: 'ctaButton',
    }),
    defineField({
      name: 'background',
      type: 'string',
      options: {
        list: ['light', 'dark', 'primary', 'secondary'],
      },
      initialValue: 'light',
    }),
  ],
  preview: {
    select: {
      title: 'title',
    },
    prepare({ title }) {
      return {
        title: 'CTA',
        subtitle: title,
      };
    },
  },
});

// Destination Embed Block
export const destinationEmbed = defineType({
  name: 'destinationEmbed',
  title: 'Destination Embed',
  type: 'object',
  fields: [
    defineField({
      name: 'destination',
      title: 'Destination',
      type: 'reference',
      to: [{ type: 'destination' }],
    }),
    defineField({
      name: 'layout',
      title: 'Layout',
      type: 'string',
      options: {
        list: [
          { title: 'Card', value: 'card' },
          { title: 'Compact', value: 'compact' },
          { title: 'Featured', value: 'featured' },
        ],
      },
      initialValue: 'card',
    }),
  ],
  preview: {
    select: {
      destinationTitle: 'destination.title',
      destinationImage: 'destination.heroImage',
    },
    prepare({ destinationTitle, destinationImage }) {
      return {
        title: 'Destination Embed',
        subtitle: destinationTitle,
        media: destinationImage,
      };
    },
  },
});
```

---

## Summary

Content modeling for the travel agency platform:

- **Schemas**: Destination, Accommodation, Deal, Blog, Page
- **Field Types**: String, text, number, reference, image, etc.
- **Relationships**: References between documents
- **Localization**: Prefix fields or i18n plugin
- **Rich Text**: Portable Text with custom blocks

**Key Modeling Decisions:**
- Reusable field groups (SEO, Image with Alt)
- References for relationships
- Portable Text for rich content
- Custom blocks for embeds

---

**Next:** [Part 3: Content Delivery](./CONTENT_MANAGEMENT_03_DELIVERY.md) — CDN, caching, and edge delivery
