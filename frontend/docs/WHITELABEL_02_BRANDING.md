# Multi-Brand & White Label — Branding & Theming

> Research document for dynamic theming, brand asset management, and per-brand customization.

---

## Key Questions

1. **How do we implement dynamic theming that's per-brand?**
2. **What brand assets need management (logos, images, templates)?**
3. **How do we handle dark mode across multiple brands?**
4. **What's the email and document branding system?**
5. **How do we preview brand changes before publishing?**

---

## Research Areas

### Dynamic Theming

```typescript
interface ThemeConfig {
  colors: ColorPalette;
  typography: TypographyConfig;
  spacing: SpacingConfig;
  components: ComponentThemeOverrides;
  darkMode: ColorPalette;
}

interface ColorPalette {
  primary: string;
  primaryLight: string;
  primaryDark: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

interface TypographyConfig {
  fontFamily: string;                 // Google Font or custom font
  headingFont?: string;              // Separate heading font (optional)
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  fontWeight: {
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
}

// Theme implementation:
// 1. CSS custom properties (--color-primary, --font-family, etc.)
// 2. Theme loaded at runtime based on domain/brand
// 3. Theme cached in localStorage for instant load
// 4. Theme changes applied without page reload
// 5. Dark mode: Brand defines both light and dark palettes
// 6. Fallback: If theme fails to load, use default platform theme

// Theme constraints:
// Accessibility: All color combinations must pass WCAG AA contrast ratio
//   Primary on background: >= 4.5:1 contrast
//   Error on background: >= 4.5:1 contrast
//   Auto-check on theme save, reject non-compliant colors
//
// Font loading: Google Fonts loaded asynchronously, no FOUT
//   Custom fonts: Uploaded as brand assets, served from CDN
//   Max 2 font families per brand (performance)
//
// Component overrides:
//   Agency can customize: Button radius, card shadows, input borders
//   Agency cannot customize: Layout structure, panel positions, core UX
```

### Brand Asset Management

```typescript
interface BrandAssets {
  logos: BrandLogo[];
  images: BrandImage[];
  icons: BrandIcon[];
  templates: BrandTemplate[];
}

interface BrandLogo {
  type: 'primary' | 'light_on_dark' | 'dark_on_light' | 'square' | 'favicon';
  format: 'svg' | 'png';
  url: string;
  altText: string;
  constraints: {
    maxWidth: string;
    maxHeight: string;
    minResolution: string;
  };
}

interface BrandImage {
  imageId: string;
  category: 'login_background' | 'email_header' | 'document_header' | 'marketing_banner' | 'placeholder';
  url: string;
  altText: string;
  dimensions: { width: number; height: number };
}

// Brand asset requirements:
// Primary logo: SVG preferred, PNG fallback. Max 200px height
// Favicon: 32x32 and 180x180 (Apple touch icon)
// Login background: 1920x1080 minimum, compressed
// Email header: 600x200 max (email client constraints)
// Document header: 800x100 (A4 width proportion)

// Asset delivery:
// All assets served from CDN with cache headers
// Assets versioned (brand v15 = cache bust on update)
// SVG logos preferred (scale without quality loss)
// WebP images where supported (with PNG fallback)
```

### Document Branding

```typescript
interface DocumentBranding {
  templates: DocumentTemplate[];
  emailBranding: EmailBranding;
  whatsappBranding: WhatsAppBranding;
}

interface DocumentTemplate {
  documentType: 'itinerary' | 'quote' | 'invoice' | 'voucher' | 'receipt' | 'confirmation';
  header: TemplateSection;
  footer: TemplateSection;
  watermark?: string;
  pageSize: 'A4' | 'Letter';
  orientation: 'portrait' | 'landscape';
  margins: { top: number; right: number; bottom: number; left: number };
  colors: DocumentColors;
  fonts: DocumentFonts;
}

// Document branding layers:
// Layer 1: Platform template (structure, layout, sections)
// Layer 2: Agency brand (colors, logo, fonts)
// Layer 3: Trip-specific (customer name, trip details)
//
// Example: Itinerary PDF
// Header: [Agency Logo] + [Agency Name] + [Contact Info]
// Body: Trip details with agency brand colors
// Footer: [Agency Address] + [License Number] + [Page X of Y]
// Watermark: Optional agency watermark (for draft quotes)
```

### Brand Preview & Publishing

```typescript
interface BrandPreview {
  previewId: string;
  brandId: string;
  pages: PreviewPage[];
  status: 'draft' | 'published';
  lastPublishedAt?: Date;
}

type PreviewPage =
  | 'login'
  | 'dashboard'
  | 'trip_builder'
  | 'customer_portal'
  | 'email_sample'
  | 'document_sample';

// Brand preview workflow:
// 1. Admin edits brand settings (colors, logo, fonts)
// 2. Preview generated instantly (no save needed)
// 3. Admin can preview:
//    - Login page with brand
//    - Workbench with theme applied
//    - Customer portal with brand
//    - Sample email with brand
//    - Sample itinerary PDF with brand
// 4. Admin reviews and approves
// 5. Changes published (takes ~5 minutes to propagate)
// 6. Rollback available within 24 hours

// Publishing safety:
// - Auto-check: Accessibility contrast validation
// - Auto-check: Font loading performance (< 2s)
// - Auto-check: Image size limits
// - Auto-check: All required assets present
// - If any check fails → Block publishing with specific feedback
```

---

## Open Problems

1. **Brand consistency** — An agency changes their logo. Every cached email, PDF, and page needs to update. Cache invalidation across all brand assets is complex.

2. **Dark mode per brand** — Not every brand's color palette works in dark mode. Need automated dark mode generation or per-brand dark mode configuration.

3. **Custom fonts performance** — Custom fonts add 200KB+ to page load. Need font subsetting and lazy loading to maintain performance.

4. **Email client compatibility** — Branded emails render differently across Gmail, Outlook, Apple Mail. Need cross-client testing.

5. **Brand preview accuracy** — Preview may not match production exactly (CDN caching, font rendering differences). Need reliable preview.

---

## Next Steps

- [ ] Design dynamic theming system with CSS custom properties
- [ ] Build brand asset management with CDN delivery
- [ ] Create document branding template system
- [ ] Design brand preview and publishing workflow
- [ ] Study theming systems (Tailwind CSS, Chakra UI, Material Design theming)
