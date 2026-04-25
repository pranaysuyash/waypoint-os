# Agency Settings — Branding Deep Dive

> Part 3 of 4 in Agency Settings Exploration Series

---

## Document Overview

**Series:** Agency Settings / Configuration
**Part:** 3 — Branding System
**Status:** Complete
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Branding Overview](#branding-overview)
2. [Logo Management](#logo-management)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Email Branding](#email-branding)
6. [Document Branding](#document-branding)
7. [Custom Domain](#custom-domain)
8. [Brand Guidelines](#brand-guidelines)

---

## Branding Overview

### What is Agency Branding?

Agency Branding enables travel agencies to customize their visual identity across all customer touchpoints. This includes logos, colors, fonts, email templates, document headers/footers, and custom domains for customer portals.

### Brand Touchpoints

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRAND TOUCHPOINTS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CUSTOMER FACING                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Customer     │  │ Quotes &    │  │ Email        │  │ WhatsApp     │  │
│  │ Portal       │  │ Invoices     │  │ Templates    │  │ Messages     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                           │                                               │         │
│                           ▼                                               │         │
│                    ┌────────────────┐                                          │
│                    │ Agency Brand   │                                          │
│                    │ - Logo          │                                          │
│                    │ - Colors        │                                          │
│                    │ - Fonts         │                                          │
│                    │ - Templates     │                                          │
│                    └────────────────┘                                          │
│                                                                             │
│  INTERNAL FACING                                                            │
│  ┌──────────────┐  ┌──────────────┐                                           │
│  │ Agent Portal │  │ Mobile App    │                                           │
│  └──────────────┘  └──────────────┘                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Logo Management

### Logo Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LOGO SPECIFICATIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY LOGO (Light Mode)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Format:       PNG (preferred), SVG (if available)                  │   │
│  │  Dimensions:   Recommended 400px width, height proportional          │   │
│  │  Background:   Transparent                                         │   │
│  │  Max Size:     5MB                                                   │   │
│  │  Usage:        Quotes, invoices, emails, portal                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DARK MODE LOGO                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Format:       PNG with transparent background                       │   │
│  │  Dimensions:   Same as primary logo                                  │   │
│  │  Colors:       Optimized for dark backgrounds                        │   │
│  │  Usage:        Portal dark mode, mobile app dark theme              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  APP ICON / FAVICON                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Format:       PNG or ICO                                            │   │
│  │  Dimensions:   512x512px (recommended)                              │   │
│  │  Background:   Can be solid or transparent                           │   │
│  │  Usage:        Browser tab, app icon, shortcut                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WATERMARK LOGO (Optional)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Format:       PNG with transparency                                 │   │
│  │  Dimensions:   Any, will be scaled to 20% opacity                   │   │
│  │  Usage:        Document previews, itineraries                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Logo Upload Component

```typescript
// components/branding/LogoManager.tsx

interface LogoManagerProps {
  agencyId: string;
  logos: {
    light?: string;
    dark?: string;
    icon?: string;
  };
  onUpload: (variant: 'light' | 'dark' | 'icon', file: File) => Promise<void>;
  onDelete: (variant: 'light' | 'dark' | 'icon') => Promise<void>;
}

export const LogoManager: React.FC<LogoManagerProps> = ({
  agencyId,
  logos,
  onUpload,
  onDelete
}) => {
  const [activeTab, setActiveTab] = useState<'light' | 'dark' | 'icon'>('light');
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      await onUpload(activeTab, file);
      toast.success('Logo uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload logo');
    } finally {
      setIsUploading(false);
    }
  };

  const tabs: Array<{ key: 'light' | 'dark' | 'icon'; label: string; description: string }> = [
    { key: 'light', label: 'Light Mode', description: 'Used on light backgrounds' },
    { key: 'dark', label: 'Dark Mode', description: 'Used on dark backgrounds' },
    { key: 'icon', label: 'App Icon', description: 'Browser tab and mobile app' }
  ];

  return (
    <div className="space-y-6">
      {/* Logo Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {tabs.map((tab) => (
          <div
            key={tab.key}
            className={cn(
              "p-4 border-2 rounded-lg transition-colors",
              activeTab === tab.key
                ? "border-indigo-500 bg-indigo-50"
                : "border-gray-200"
            )}
          >
            <button
              onClick={() => setActiveTab(tab.key)}
              className="w-full text-left"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{tab.label}</h4>
                {activeTab === tab.key && (
                  <Badge variant="info" size="sm">Active</Badge>
                )}
              </div>
              <p className="text-sm text-gray-500">{tab.description}</p>
            </button>

            {/* Preview Area */}
            <div className="mt-4 flex items-center justify-center h-32 bg-white border border-dashed border-gray-300 rounded">
              {logos[tab.key] ? (
                <img
                  src={logos[tab.key]}
                  alt={`${tab.key} logo`}
                  className="max-h-24 max-w-full object-contain"
                />
              ) : (
                <div className="text-center text-gray-400">
                  <ImageIcon size={32} className="mx-auto mb-1" />
                  <span className="text-xs">No logo</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Upload Area for Active Tab */}
      <UploadArea
        onUpload={handleUpload}
        onDelete={() => onDelete(activeTab)}
        currentLogo={logos[activeTab]}
        isUploading={isUploading}
      />

      {/* Logo Guidelines */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-start gap-3">
          <InfoIcon className="text-blue-500 shrink-0" size={20} />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Logo Guidelines</p>
            <ul className="space-y-1 text-blue-600">
              <li>• Use PNG format with transparent background</li>
              <li>• Recommended width: 400px for main logos, 512px for app icon</li>
              <li>• Maximum file size: 5MB</li>
              <li>• For dark mode, ensure logo is visible on dark backgrounds</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

const UploadArea: React.FC<{
  onUpload: (file: File) => void;
  onDelete: () => void;
  currentLogo?: string;
  isUploading: boolean;
}> = ({ onUpload, onDelete, currentLogo, isUploading }) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <div className="flex items-center gap-4">
      {currentLogo ? (
        <>
          <Button
            variant="outline"
            size="sm"
            icon={<UploadIcon />}
            onClick={() => document.getElementById('logo-upload')?.click()}
            disabled={isUploading}
          >
            Replace Logo
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<TrashIcon />}
            onClick={onDelete}
            className="text-red-600"
          >
            Remove
          </Button>
        </>
      ) : (
        <div
          className={cn(
            "flex-1 p-8 border-2 border-dashed rounded-lg text-center transition-colors cursor-pointer",
            isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300 hover:border-gray-400"
          )}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) onUpload(file);
          }}
          onClick={() => document.getElementById('logo-upload')?.click()}
        >
          <input
            id="logo-upload"
            type="file"
            className="hidden"
            accept="image/png,image/svg+xml"
            onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])}
            disabled={isUploading}
          />
          {isUploading ? (
            <Spinner />
          ) : (
            <>
              <ImageIcon className="text-gray-400 mx-auto mb-2" size={32} />
              <p className="text-sm text-gray-600">
                {isDragging ? 'Drop image here' : 'Click to upload or drag and drop'}
              </p>
              <p className="text-xs text-gray-400 mt-1">PNG or SVG, max 5MB</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};
```

### Logo Processing Service

```typescript
// services/branding/logo-processor.service.ts

import sharp from 'sharp';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

export class LogoProcessorService {
  private s3: S3Client;
  private bucketName: string;

  constructor() {
    this.s3 = new S3Client({
      region: process.env.AWS_REGION
    });
    this.bucketName = process.env.S3_BRANDING_BUCKET!;
  }

  /**
   * Process and upload logo
   */
  async processAndUploadLogo(
    agencyId: string,
    file: File,
    variant: 'light' | 'dark' | 'icon'
  ): Promise<{ url: string; width: number; height: number }> {
    // Validate file
    this.validateLogoFile(file);

    // Process image
    const processed = await this.processImage(file, variant);

    // Generate S3 key
    const key = this.generateS3Key(agencyId, variant);

    // Upload to S3
    const url = await this.uploadToS3(key, processed);

    // Get dimensions
    const metadata = await sharp(processed).metadata();

    return {
      url,
      width: metadata.width || 0,
      height: metadata.height || 0
    };
  }

  /**
   * Process image based on variant
   */
  private async processImage(
    file: File,
    variant: 'light' | 'dark' | 'icon'
  ): Promise<Buffer> {
    let image = sharp(await file.arrayBuffer());

    switch (variant) {
      case 'light':
        // Max width 400px, maintain aspect ratio
        image = image.resize(400, null, {
          withoutEnlargement: true,
          fit: 'inside'
        });
        // Convert to PNG with transparency
        return image.png().toBuffer();

      case 'dark':
        // Same as light, but could apply color adjustment if needed
        image = image.resize(400, null, {
          withoutEnlargement: true,
          fit: 'inside'
        });
        return image.png().toBuffer();

      case 'icon':
        // Resize to 512x512, fit within square
        image = image.resize(512, 512, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        });
        // Generate multiple sizes
        return image.png().toBuffer();

      default:
        return image.png().toBuffer();
    }
  }

  /**
   * Validate logo file
   */
  private validateLogoFile(file: File): void {
    // Check file type
    const validTypes = ['image/png', 'image/svg+xml', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
      throw new Error('Invalid file type. Please upload PNG, SVG, or JPEG.');
    }

    // Check file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      throw new Error('File size exceeds 5MB limit.');
    }

    // Check image dimensions
    sharp(await file.arrayBuffer()).metadata().then((metadata) => {
      if (metadata.width && metadata.width > 4000) {
        throw new Error('Image width exceeds 4000px.');
      }
      if (metadata.height && metadata.height > 4000) {
        throw new Error('Image height exceeds 4000px.');
      }
    });
  }

  /**
   * Generate S3 key with agency ID and variant
   */
  private generateS3Key(agencyId: string, variant: string): string {
    const timestamp = Date.now();
    return `branding/${agencyId}/logo-${variant}-${timestamp}.png`;
  }

  /**
   * Upload processed image to S3
   */
  private async uploadToS3(key: string, buffer: Buffer): Promise<string> {
    const command = new PutObjectCommand({
      Bucket: this.bucketName,
      Key: key,
      Body: buffer,
      ContentType: 'image/png',
      CacheControl: 'public, max-age=31536000', // 1 year cache
      Metadata: {
        uploadedAt: new Date().toISOString()
      }
    });

    await this.s3.send(command);

    return `https://${this.bucketName}.s3.${process.env.AWS_REGION}.amazonaws.com/${key}`;
  }

  /**
   * Delete old logo from S3
   */
  async deleteLogo(url: string): Promise<void> {
    const key = this.extractKeyFromUrl(url);

    if (!key) {
      throw new Error('Invalid logo URL');
    }

    // Only delete logos from our bucket
    if (!key.startsWith('branding/')) {
      throw new Error('Cannot delete logo from external source');
    }

    const command = new DeleteObjectCommand({
      Bucket: this.bucketName,
      Key: key
    });

    await this.s3.send(command);
  }

  /**
   * Extract S3 key from URL
   */
  private extractKeyFromUrl(url: string): string | null {
    try {
      const urlObj = new URL(url);
      if (urlObj.hostname === `${this.bucketName}.s3.${process.env.AWS_REGION}.amazonaws.com`) {
        return urlObj.pathname.slice(1); // Remove leading slash
      }
      return null;
    } catch {
      return null;
    }
  }
}
```

---

## Color System

### Color Palette Generator

```typescript
// services/branding/color-palette.service.ts

import { Color, RGB } from 'color';

export class ColorPaletteService {
  /**
   * Generate color palette from primary color
   */
  generatePalette(primaryColor: string): ColorPalette {
    const primary = Color(primaryColor);

    return {
      primary: primary.hex(),
      primaryLight: this.lighten(primary, 20).hex(),
      primaryDark: this.darken(primary, 20).hex(),

      secondary: this.analogous(primary, 30)[0].hex(),
      secondaryLight: this.lighten(this.analogous(primary, 30)[0], 20).hex(),
      secondaryDark: this.darken(this.analogous(primary, 30)[0], 20).hex(),

      accent: this.complementary(primary).hex(),
      accentLight: this.lighten(this.complementary(primary), 20).hex(),
      accentDark: this.darken(this.complementary(primary), 20).hex(),

      neutral: {
        50: '#F9FAFB',
        100: '#F3F4F6',
        200: '#E5E7EB',
        300: '#D1D5DB',
        400: '#9CA3AF',
        500: '#6B7280',
        600: '#4B5563',
        700: '#374151',
        800: '#1F2937',
        900: '#111827'
      },

      semantic: {
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: primary.hex()
      }
    };
  }

  /**
   * Extract dominant colors from image
   */
  async extractColorsFromLogo(imageUrl: string): Promise<ExtractedColors> {
    // Download image
    const response = await fetch(imageUrl);
    const buffer = Buffer.from(await response.arrayBuffer());

    // Use sharp to get palette
    const { dominant } = await sharp(buffer)
      .resize(100, 100, { fit: 'cover' })
      .raw()
      .toBuffer({ resolveWithObject: true })
      .then(({ data }) => this.quantizeColors(data, 5));

    return {
      primary: dominant[0],
      palette: dominant,
      recommended: this.generatePalette(dominant[0])
    };
  }

  /**
   * Generate accessible text colors for background
   */
  getAccessibleTextColor(backgroundColor: string): {
    primary: string;
    secondary: string;
    tertiary: string;
  } {
    const bg = Color(backgroundColor);
    const luminance = this.getLuminance(bg);

    // WCAG contrast requirements
    if (luminance > 0.5) {
      // Dark text on light background
      return {
        primary: '#111827', // Gray 900
        secondary: '#374151', // Gray 700
        tertiary: '#6B7280' // Gray 500
      };
    } else {
      // Light text on dark background
      return {
        primary: '#FFFFFF',
        secondary: '#F3F4F6', // Gray 100
        tertiary: '#D1D5DB' // Gray 300
      };
    }
  }

  /**
   * Check if color meets WCAG AA contrast ratio
   */
  checkContrastRatio(foreground: string, background: string): {
    ratio: number;
    wcagAA: boolean; // 4.5:1 for normal text
    wcagAAA: boolean; // 7:1 for normal text
  } {
    const fg = Color(foreground);
    const bg = Color(background);

    const ratio = this.contrastRatio(fg, bg);

    return {
      ratio: Math.round(ratio * 100) / 100,
      wcagAA: ratio >= 4.5,
      wcagAAA: ratio >= 7
    };
  }

  /**
   * Calculate contrast ratio between two colors
   */
  private contrastRatio(color1: Color, color2: Color): number {
    const l1 = this.getLuminance(color1);
    const l2 = this.getLuminance(color2);

    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Calculate relative luminance
   */
  private getLuminance(color: Color): number {
    const rgb = color.rgb().array();

    const [r, g, b] = rgb.map((v) => {
      v = v / 255;
      return v <= 0.03928
        ? v / 12.92
        : Math.pow((v + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Lighten color by percentage
   */
  private lighten(color: Color, percent: number): Color {
    return color.lighten(percent);
  }

  /**
   * Darken color by percentage
   */
  private darken(color: Color, percent: number): Color {
    return color.darken(percent);
  }

  /**
   * Get analogous colors (same hue, different lightness)
   */
  private analogous(color: Color, degrees: number): Color[] {
    return [
      color.rotate(degrees),
      color.rotate(-degrees)
    ];
  }

  /**
   * Get complementary color (opposite on color wheel)
   */
  private complementary(color: Color): Color {
    const hsl = color.hsl();
    return Color({
      h: (hsl.object().h + 180) % 360,
      s: hsl.object().s,
      l: hsl.object().l
    });
  }

  /**
   * Quantize colors to find dominant ones
   */
  private quantizeColors(data: Buffer, colorCount: number): { dominant: string[] } {
    const colorMap: Map<string, number> = new Map();

    // Sample pixels
    for (let i = 0; i < data.length; i += 40) { // Sample every 10th pixel
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const a = data[i + 3];

      // Skip transparent pixels
      if (a < 128) continue;

      // Round to nearest 10 to group similar colors
      const key = `${Math.round(r / 10) * 10},${Math.round(g / 10) * 10},${Math.round(b / 10) * 10}`;
      colorMap.set(key, (colorMap.get(key) || 0) + 1);
    }

    // Sort by frequency and return top colors
    const sorted = Array.from(colorMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, colorCount)
      .map(([color]) => {
        const [r, g, b] = color.split(',').map(Number);
        return Color({ r, g, b }).hex();
      });

    return { dominant: sorted };
  }
}

interface ColorPalette {
  primary: string;
  primaryLight: string;
  primaryDark: string;
  secondary: string;
  secondaryLight: string;
  secondaryDark: string;
  accent: string;
  accentLight: string;
  accentDark: string;
  neutral: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  semantic: {
    success: string;
    warning: string;
    error: string;
    info: string;
  };
}

interface ExtractedColors {
  primary: string;
  palette: string[];
  recommended: ColorPalette;
}
```

---

## Typography

### Font System

```typescript
// services/branding/typography.service.ts

export const FONT_FAMILIES = [
  {
    id: 'inter',
    name: 'Inter',
    category: 'sans-serif',
    preview: 'Inter',
    variants: ['300', '400', '500', '600', '700'],
    googleFont: 'Inter:wght@300;400;500;600;700&display=swap',
    fallback: 'system-ui, sans-serif'
  },
  {
    id: 'poppins',
    name: 'Poppins',
    category: 'sans-serif',
    preview: 'Poppins',
    variants: ['300', '400', '500', '600', '700'],
    googleFont: 'Poppins:wght@300;400;500;600;700&display=swap',
    fallback: 'system-ui, sans-serif'
  },
  {
    id: 'roboto',
    name: 'Roboto',
    category: 'sans-serif',
    preview: 'Roboto',
    variants: ['300', '400', '500', '700', '900'],
    googleFont: 'Roboto:wght@300;400;500;700;900&display=swap',
    fallback: 'system-ui, sans-serif'
  },
  {
    id: 'open-sans',
    name: 'Open Sans',
    category: 'sans-serif',
    preview: 'Open Sans',
    variants: ['300', '400', '500', '600', '700', '800'],
    googleFont: 'Open+Sans:wght@300;400;500;600;700;800&display=swap',
    fallback: 'system-ui, sans-serif'
  },
  {
    id: 'lato',
    name: 'Lato',
    category: 'sans-serif',
    preview: 'Lato',
    variants: ['300', '400', '700', '900'],
    googleFont: 'Lato:wght@300;400;700;900&display=swap',
    fallback: 'system-ui, sans-serif'
  },
  {
    id: 'merriweather',
    name: 'Merriweather',
    category: 'serif',
    preview: 'Merriweather',
    variants: ['300', '400', '700', '900'],
    googleFont: 'Merriweather:wght@300;400;700;900&display=swap',
    fallback: 'Georgia, serif'
  }
];

export class TypographyService {
  /**
   * Generate CSS with font family
   */
  generateTypographyCSS(settings: {
    fontFamily: string;
    fontHeading?: string;
    fontSize: number;
  }): string {
    const font = FONT_FAMILIES.find(f => f.id === settings.fontFamily);
    const headingFont = settings.fontHeading
      ? FONT_FAMILIES.find(f => f.id === settings.fontHeading)
      : font;

    return `
      :root {
        --font-family: '${font?.name}', ${font?.fallback};
        --font-heading: '${headingFont?.name}', ${headingFont?.fallback};
        --font-size-base: ${settings.fontSize}px;
      }

      body {
        font-family: var(--font-family);
        font-size: var(--font-size-base);
      }

      h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-heading);
      }

      /* Import fonts */
      @import url('${font?.googleFont}');
      ${settings.fontHeading && settings.fontHeading !== settings.fontFamily
        ? `@import url('${headingFont?.googleFont}');`
        : ''}
    `;
  }

  /**
   * Get font scale (type scale) for consistent sizing
   */
  getTypeScale(baseSize: number): TypeScale {
    const ratio = 1.250; // Major third scale

    return {
      xs: baseSize * 0.75,
      sm: baseSize * 0.875,
      base: baseSize,
      lg: baseSize * 1.125,
      xl: baseSize * 1.25,
      '2xl': baseSize * 1.5,
      '3xl': baseSize * 1.875,
      '4xl': baseSize * 2.25,
      '5xl': baseSize * 3
    };
  }
}

interface TypeScale {
  xs: number;
  sm: number;
  base: number;
  lg: number;
  xl: number;
  '2xl': number;
  '3xl': number;
  '4xl': number;
  '5xl': number;
}
```

---

## Email Branding

### Email Template System

```typescript
// services/branding/email-template.service.ts

export class EmailTemplateService {
  /**
   * Render email with agency branding
   */
  async renderBrandedEmail(
    agencyId: string,
    templateType: 'booking_confirmation' | 'payment_receipt' | 'itinerary',
    data: Record<string, unknown>
  ): Promise<{ html: string; text: string }> {
    // Get agency branding
    const branding = await this.getAgencyBranding(agencyId);
    const settings = await this.getAgencySettings(agencyId, 'branding');

    // Load template
    const template = await this.loadTemplate(templateType);

    // Render with branding context
    const context = {
      ...data,
      branding: {
        logoUrl: branding.logo_url || `${process.env.DEFAULT_LOGO_URL}`,
        primaryColor: branding.primary_color,
        secondaryColor: branding.secondary_color,
        agencyName: settings.agencyName,
        agencyEmail: settings.agencyEmail,
        agencyPhone: settings.agencyPhone,
        agencyWebsite: settings.agencyWebsite,
        agencyAddress: this.formatAddress(settings.address)
      }
    };

    const html = template.renderHtml(context);
    const text = template.renderText(context);

    return { html, text };
  }

  /**
   * Preview email template
   */
  async previewEmail(
    agencyId: string,
    templateType: string
  ): Promise<EmailPreview> {
    const sampleData = this.getSampleData(templateType);

    const { html, text } = await this.renderBrandedEmail(
      agencyId,
      templateType as any,
      sampleData
    );

    return {
      html,
      text,
      subject: this.getSubject(templateType, sampleData)
    };
  }

  /**
   * Get sample data for preview
   */
  private getSampleData(templateType: string): Record<string, unknown> {
    const samples: Record<string, Record<string, unknown>> = {
      booking_confirmation: {
        customerName: 'John Doe',
        destination: 'Goa',
        checkIn: '2026-05-01',
        checkOut: '2026-05-05',
        guests: 2,
        totalPrice: '₹45,000',
        bookingReference: 'ABC-2026-001'
      },
      payment_receipt: {
        customerName: 'John Doe',
        amount: '₹45,000',
        paymentDate: '2026-04-25',
        paymentMethod: 'UPI',
        transactionId: 'TXN123456789',
        bookingReference: 'ABC-2026-001'
      },
      itinerary: {
        customerName: 'John Doe',
        destination: 'Goa',
        startDate: '2026-05-01',
        endDate: '2026-05-05',
        activities: [
          { day: 1, activity: 'Arrival and beach visit', time: '10:00 AM' },
          { day: 2, activity: 'South Goa sightseeing', time: '9:00 AM' },
          { day: 3, activity: 'North Goa temples', time: '8:00 AM' },
          { day: 4, activity: 'Dudhsagar Falls', time: '7:00 AM' },
          { day: 5, activity: 'Departure', time: 'As per flight' }
        ]
      }
    };

    return samples[templateType] || {};
  }

  /**
   * Format address for email footer
   */
  private formatAddress(address: Address): string {
    const parts = [
      address.line1,
      address.line2,
      `${address.city}, ${address.state} ${address.postalCode}`,
      address.country
    ].filter(Boolean);

    return parts.join('\n');
  }

  /**
   * Get agency branding
   */
  private async getAgencyBranding(agencyId: string): Promise<AgencyBranding> {
    const result = await db.query(
      'SELECT * FROM agency_branding WHERE agency_id = $1',
      [agencyId]
    );

    return result.rows[0] || this.getDefaultBranding();
  }

  /**
   * Get agency settings
   */
  private async getAgencySettings(agencyId: string, category: string): Promise<Record<string, unknown>> {
    const result = await db.query(
      'SELECT * FROM agency_settings WHERE agency_id = $1 AND category = $2',
      [agencyId, category]
    );

    const settings: Record<string, unknown> = {};
    for (const row of result.rows) {
      settings[row.key] = row.value;
    }

    return settings;
  }

  /**
   * Load email template
   */
  private async loadTemplate(type: string): EmailTemplate {
    // Load from file system or database
    const templatePath = path.join(
      process.cwd(),
      'templates',
      'email',
      `${type}.hbs`
    );

    const content = await fs.readFile(templatePath, 'utf-8');

    return {
      renderHtml: (context: Record<string, unknown>) => {
        // Use Handlebars or similar
        return Handlebars.compile(content)(context);
      },
      renderText: (context: Record<string, unknown>) => {
        // Strip HTML for text version
        return this.htmlToText(Handlebars.compile(content)(context));
      }
    };
  }

  /**
   * Convert HTML to plain text
   */
  private htmlToText(html: string): string {
    return html
      .replace(/<style[^>]*>.*?<\/style>/gi, '')
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<[^>]+>/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Get email subject line
   */
  private getSubject(templateType: string, data: Record<string, unknown>): string {
    const subjects: Record<string, string> = {
      booking_confirmation: `Booking Confirmed: ${data.destination}`,
      payment_receipt: `Payment Receipt: ${data.bookingReference}`,
      itinerary: `Your Itinerary for ${data.destination}`
    };

    return subjects[templateType] || '';
  }

  private getDefaultBranding(): AgencyBranding {
    return {
      id: '',
      agency_id: '',
      logo_url: null,
      primary_color: '#6366F1',
      secondary_color: '#8B5CF6',
      // ... other defaults
    };
  }
}

interface EmailTemplate {
  renderHtml: (context: Record<string, unknown>) => string;
  renderText: (context: Record<string, unknown>) => string;
}

interface EmailPreview {
  html: string;
  text: string;
  subject: string;
}

interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}
```

---

## Document Branding

### PDF Header/Footer Service

```typescript
// services/branding/document-branding.service.ts

import { PDFDocument, StandardFonts } from 'pdf-lib';

export class DocumentBrandingService {
  /**
   * Apply branding to PDF document
   */
  async applyBrandingToPDF(
    pdfBytes: Buffer,
    agencyId: string,
    options: {
      header?: boolean;
      footer?: boolean;
      watermark?: boolean;
    } = {}
  ): Promise<Buffer> {
    const branding = await this.getAgencyBranding(agencyId);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const pages = pdfDoc.getPages();

    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

    for (const page of pages) {
      const { width, height } = page.getSize();

      // Add header
      if (options.header && branding.logo_url) {
        const logoImage = await this.loadLogoImage(branding.logo_url);
        const logoDims = logoImage.scaleToFit(width - 100, 50);

        page.drawImage(logoImage, {
          x: 50,
          y: height - 50 - logoDims.height,
          width: logoDims.width,
          height: logoDims.height
        });
      }

      // Add footer
      if (options.footer) {
        const footerText = this.buildFooterText(branding);
        page.drawText(footerText, {
          x: 50,
          y: 30,
          size: 9,
          font,
          color: rgb(0.5, 0.5, 0.5)
        });
      }

      // Add watermark
      if (options.watermark && branding.document_watermark_enabled) {
        page.drawText(branding.document_watermark_text || 'CONFIDENTIAL', {
          x: width / 2 - 100,
          y: height / 2,
          size: 40,
          font,
          color: rgb(0.9, 0.9, 0.9),
          opacity: 0.3
        });
      }
    }

    return await pdfDoc.save();
  }

  /**
   * Build footer text
   */
  private buildFooterText(branding: AgencyBranding): string {
    const parts: string[] = [];

    if (branding.agency_name) {
      parts.push(branding.agency_name);
    }

    if (branding.agency_email) {
      parts.push(branding.agency_email);
    }

    if (branding.agency_phone) {
      parts.push(branding.agency_phone);
    }

    if (branding.agency_website) {
      parts.push(branding.agency_website);
    }

    return parts.join(' | ');
  }

  /**
   * Load logo image for PDF
   */
  private async loadLogoImage(url: string): Promise<PDFImage> {
    const response = await fetch(url);
    const buffer = Buffer.from(await response.arrayBuffer());

    return await pdfDoc.embedPng(buffer);
  }
}
```

---

## Custom Domain

### Domain Verification Service

```typescript
// services/branding/custom-domain.service.ts

import { DNSResolver } from 'dns-resolver';

export class CustomDomainService {
  /**
   * Set up custom domain for agency
   */
  async setupCustomDomain(
    agencyId: string,
    domain: string,
    userId: string
  ): Promise<CustomDomainSetup> {
    // Validate domain format
    if (!this.isValidDomain(domain)) {
      throw new Error('Invalid domain format');
    }

    // Check if domain is already in use
    const existing = await db.query(
      'SELECT agency_id FROM agency_branding WHERE custom_domain = $1 AND custom_domain_verified = true',
      [domain]
    );

    if (existing.rows.length > 0) {
      throw new Error('Domain is already in use by another agency');
    }

    // Generate verification token
    const verificationToken = this.generateVerificationToken();

    // Save domain
    await db.query(`
      INSERT INTO agency_branding (agency_id, custom_domain, custom_domain_verified)
      VALUES ($1, $2, false)
      ON CONFLICT (agency_id)
      DO UPDATE SET custom_domain = EXCLUDED.custom_domain, custom_domain_verified = false
    `, [agencyId, domain]);

    // Get DNS records to add
    const dnsRecords = this.getDNSRecords(domain, verificationToken);

    return {
      domain,
      verificationToken,
      dnsRecords,
      status: 'pending_verification'
    };
  }

  /**
   * Verify custom domain ownership
   */
  async verifyDomain(agencyId: string): Promise<DomainVerificationResult> {
    const branding = await this.getAgencyBranding(agencyId);

    if (!branding.custom_domain) {
      throw new Error('No custom domain configured');
    }

    const checks = await this.runDomainChecks(branding.custom_domain);

    if (checks.cname && checks.txt) {
      // All checks passed
      await db.query(
        'UPDATE agency_branding SET custom_domain_verified = true WHERE agency_id = $1',
        [agencyId]
      );

      // Provision SSL certificate
      await this.provisionSSLCertificate(agencyId, branding.custom_domain);

      return {
        domain: branding.custom_domain,
        verified: true,
        checks,
        ssl: 'provisioning'
      };
    }

    return {
      domain: branding.custom_domain,
      verified: false,
      checks,
      errors: this.getVerificationErrors(checks)
    };
  }

  /**
   * Run domain verification checks
   */
  private async runDomainChecks(domain: string): Promise<DomainChecks> {
    const resolver = new DNSResolver();

    try {
      // Check CNAME record
      const cnameRecords = await resolver.resolveCNAME(domain);
      const cname = cnameRecords.some(record =>
        record === process.env.CUSTOM_DOMAIN_TARGET
      );

      // Check TXT verification record
      const txtRecords = await resolver.resolveTXT(`_travelagency-verify.${domain}`);
      const txt = txtRecords.some(record =>
        record.includes(process.env.DOMAIN_VERIFICATION_TOKEN || '')
      );

      return { cname, txt };
    } catch (error) {
      return {
        cname: false,
        txt: false,
        error: (error as Error).message
      };
    }
  }

  /**
   * Get DNS records for user to configure
   */
  private getDNSRecords(domain: string, token: string): DNSRecord[] {
    return [
      {
        type: 'CNAME',
        host: domain,
        value: process.env.CUSTOM_DOMAIN_TARGET || 'app.travelagency.com',
        ttl: 3600
      },
      {
        type: 'TXT',
        host: `_travelagency-verify.${domain}`,
        value: token,
        ttl: 3600
      },
      {
        type: 'A',
        host: 'www',
        value: process.env.CUSTOM_DOMAIN_IP || '75.2.70.75',
        ttl: 3600
      }
    ];
  }

  /**
   * Provision SSL certificate using Let's Encrypt
   */
  private async provisionSSLCertificate(agencyId: string, domain: string): Promise<void> {
    // Integrate with Let's Encrypt or AWS Certificate Manager
    // This is a placeholder for the actual implementation

    await db.query(
      'UPDATE agency_branding SET custom_domain_ssl_until = $1 WHERE agency_id = $2',
      [new Date(Date.now() + 90 * 24 * 60 * 60 * 1000), agencyId] // 90 days
    );
  }

  /**
   * Validate domain format
   */
  private isValidDomain(domain: string): boolean {
    const domainRegex = /^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/i;
    return domainRegex.test(domain);
  }

  /**
   * Generate verification token
   */
  private generateVerificationToken(): string {
    return crypto.randomBytes(16).toString('hex');
  }

  /**
   * Get verification errors
   */
  private getVerificationErrors(checks: DomainChecks): string[] {
    const errors: string[] = [];

    if (!checks.cname) {
      errors.push('CNAME record not found or incorrect');
    }

    if (!checks.txt) {
      errors.push('TXT verification record not found or incorrect');
    }

    return errors;
  }
}

interface CustomDomainSetup {
  domain: string;
  verificationToken: string;
  dnsRecords: DNSRecord[];
  status: string;
}

interface DomainVerificationResult {
  domain: string;
  verified: boolean;
  checks: DomainChecks;
  ssl?: string;
  errors?: string[];
}

interface DomainChecks {
  cname: boolean;
  txt: boolean;
  error?: string;
}

interface DNSRecord {
  type: 'CNAME' | 'A' | 'TXT';
  host: string;
  value: string;
  ttl: number;
}
```

---

## Brand Guidelines

### Brand Guidelines Generator

```typescript
// services/branding/brand-guidelines.service.ts

export class BrandGuidelinesService {
  /**
   * Generate brand guidelines PDF
   */
  async generateBrandGuidelines(agencyId: string): Promise<Buffer> {
    const branding = await this.getAgencyBranding(agencyId);
    const settings = await this.getAgencySettings(agencyId, 'general');

    const pdfDoc = await PDFDocument.create();
    let page = pdfDoc.addPage();

    // Add title page
    await this.addTitlePage(page, branding, settings);

    // Add logo usage section
    page = pdfDoc.addPage();
    await this.addLogoUsageSection(page, branding);

    // Add color palette section
    page = pdfDoc.addPage();
    await this.addColorSection(page, branding);

    // Add typography section
    page = pdfDoc.addPage();
    await this.addTypographySection(page, branding);

    return await pdfDoc.save();
  }

  /**
   * Generate brand guidelines as HTML
   */
  async generateBrandGuidelinesHTML(agencyId: string): Promise<string> {
    const branding = await this.getAgencyBranding(agencyId);
    const palette = this.generatePalette(branding.primary_color);

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>${branding.agency_name} Brand Guidelines</title>
        <style>
          :root {
            --primary: ${branding.primary_color};
            --secondary: ${branding.secondary_color};
          }
          body { font-family: ${branding.font_family}; }
          .color-swatch { width: 100px; height: 100px; border-radius: 8px; }
        </style>
      </head>
      <body>
        <h1>${branding.agency_name} Brand Guidelines</h1>

        <section>
          <h2>Logo</h2>
          <img src="${branding.logo_url}" alt="Logo" />
          <p>Use the logo on light backgrounds. Ensure clear space around the logo.</p>
        </section>

        <section>
          <h2>Colors</h2>
          <h3>Primary</h3>
          <div class="color-swatch" style="background: ${palette.primary}"></div>
          <p>${palette.primary}</p>

          <h3>Secondary</h3>
          <div class="color-swatch" style="background: ${palette.secondary}"></div>
          <p>${palette.secondary}</p>
        </section>

        <section>
          <h2>Typography</h2>
          <p style="font-family: ${branding.font_family}; font-size: 24px;">
            Heading in ${branding.font_family}
          </p>
          <p style="font-family: ${branding.font_family}; font-size: 16px;">
            Body text in ${branding.font_family}
          </p>
        </section>
      </body>
      </html>
    `;
  }
}
```

---

## Summary

The Agency Branding system provides:

1. **Logo Management**: Upload, store, and optimize logos for all contexts
2. **Color System**: Generate palettes with WCAG-compliant contrast ratios
3. **Typography**: Google Fonts integration with type scale
4. **Email Branding**: Dynamic template rendering with agency identity
5. **Document Branding**: PDF headers, footers, and watermarks
6. **Custom Domains**: White-label customer portals with SSL
7. **Brand Guidelines**: Auto-generated guidelines for consistency

---

**Next:** Agency Settings Team Management Deep Dive (AGENCY_SETTINGS_04) — roles, permissions, onboarding, and access control
