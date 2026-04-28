# Document Generation — PDF Generation Pipeline

> Research document for converting templates to high-quality PDF documents.

---

## Key Questions

1. **What's the best PDF generation approach for travel documents — HTML-to-PDF, native PDF, or template-based?**
2. **How do we handle complex layouts (multi-column itinerary, tables, images)?**
3. **What's the generation speed target, and how to parallelize bulk generation?**
4. **How do we ensure consistent output across different devices and browsers?**
5. **What about PDF/UA (accessible PDF) and PDF/A (archival) requirements?**

---

## Research Areas

### PDF Generation Approaches

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **HTML → PDF** (Puppeteer/Playwright) | Full CSS support, familiar tech, fast iteration | Large dependency, resource-heavy, server-side only | Complex layouts, web-first documents |
| **HTML → PDF** (wkhtmltopdf) | Lightweight, fast | Limited CSS (no flexbox/grid), outdated WebKit | Simple documents |
| **Native PDF** (PDFKit, jsPDF) | Full control, small output, no headless browser | Manual layout, no CSS, complex code | Structured forms, tickets |
| **Template-based** (Carbone, Docx-templates) | Easy template editing, Office-native | Limited styling, format constraints | Invoices, reports |
| **LaTeX → PDF** | Superior typography, math, tables | Steep learning curve, heavy dependencies | Academic/technical documents |
| **Cloud API** (PDFShift, DocRaptor) | No server load, managed infrastructure | Per-document cost, external dependency | Low-volume, managed service |

```typescript
interface PDFGenerationConfig {
  approach: 'html_to_pdf' | 'native' | 'template' | 'cloud_api';
  engine: string;
  options: PDFGenerationOptions;
}

interface PDFGenerationOptions {
  format: 'A4' | 'Letter' | 'Legal';
  orientation: 'portrait' | 'landscape';
  margin: { top: number; right: number; bottom: number; left: number };
  quality: 'draft' | 'standard' | 'high';
  dpi: number;
  compress: boolean;
  accessibility: boolean;        // PDF/UA tagging
  archival: boolean;             // PDF/A compliance
  watermark?: WatermarkConfig;
  password?: string;             // Password protection
}
```

### Generation Pipeline

```typescript
interface DocumentGenerationRequest {
  requestId: string;
  templateId: string;
  documentType: DocumentType;
  data: Record<string, unknown>;
  brandId: string;
  outputFormat: 'pdf' | 'html' | 'docx';
  options: PDFGenerationOptions;
  callbackUrl?: string;          // For async generation
}

interface DocumentGenerationResult {
  requestId: string;
  status: 'queued' | 'generating' | 'completed' | 'failed';
  documentUrl?: string;          // Signed URL to download
  fileSize?: number;
  pageCount?: number;
  generationTimeMs?: number;
  error?: string;
}
```

### Performance Considerations

**Targets:**
- Single itinerary PDF: < 3 seconds
- Single quote PDF: < 2 seconds
- Bulk generation (100 itineraries): < 60 seconds
- Concurrent requests: 20+ simultaneous generations

**Optimization strategies:**
- Template pre-compilation (compile once, render many)
- Headless browser pool (reuse Chromium instances)
- Asset caching (logo, font files)
- Parallel rendering for multi-page documents
- CDN for generated document storage

---

## Open Problems

1. **HTML/CSS fidelity** — Complex CSS layouts (flexbox, grid) may render differently in headless browsers vs. real browsers. Need visual regression testing for PDFs.

2. **Font embedding** — Custom fonts must be embedded in PDFs. License compliance for font embedding in generated documents.

3. **Image quality vs. file size** — High-res hotel images make itineraries beautiful but create large PDFs. Need intelligent image compression.

4. **Bulk generation** — Sending 500 itinerary PDFs for a conference group requires queue-based generation with progress tracking.

5. **Accessible PDF (PDF/UA)** — Proper tagging, reading order, and alt text for screen readers. Most HTML-to-PDF tools don't generate tagged PDFs. Need specialized tooling.

---

## Next Steps

- [ ] Compare Puppeteer vs. Playwright for HTML-to-PDF quality and performance
- [ ] Benchmark generation speed with sample itinerary templates
- [ ] Research PDF/UA generation tools (pdfua, PANDOC)
- [ ] Design async generation queue for bulk requests
- [ ] Evaluate cloud PDF APIs for cost vs. self-hosted
- [ ] Create visual regression tests for PDF output
