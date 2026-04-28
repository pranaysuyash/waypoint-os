# Customer Identity & Verification — Document Processing & OCR

> Research document for document scanning, OCR extraction, automated verification, and document intelligence.

---

## Key Questions

1. **How do we extract data from travel documents automatically?**
2. **What OCR accuracy is needed for different document types?**
3. **How do we verify extracted data against booking details?**
4. **What's the document quality validation model?**
5. **How do we handle multi-format, multi-language documents?**

---

## Research Areas

### Document Processing Pipeline

```typescript
interface DocumentProcessingPipeline {
  stages: ProcessingStage[];
  supportedFormats: DocumentFormat[];
  supportedLanguages: string[];
}

type ProcessingStage =
  | 'upload'                         // Receive document
  | 'quality_check'                  // Validate image quality
  | 'preprocessing'                  // Enhance, crop, rotate
  | 'ocr_extraction'                 // Extract text and fields
  | 'field_mapping'                  // Map to structured data
  | 'validation'                     // Cross-check extracted data
  | 'verification'                   // Verify authenticity
  | 'storage';                       // Secure encrypted storage

// Pipeline flow:
// 1. Upload: Agent or customer uploads document (image, PDF, scan)
// 2. Quality check:
//    - Resolution: Minimum 300 DPI for passport scans
//    - Completeness: All corners visible, not cropped
//    - Clarity: Not blurry, readable text
//    - Lighting: No glare, shadows, or overexposure
//    - File size: Max 10MB
//    If quality fails → Specific feedback: "Image too blurry. Please retake."
//
// 3. Preprocessing:
//    - Auto-rotate to correct orientation
//    - Crop to document boundaries
//    - Enhance contrast and sharpness
//    - Remove noise and artifacts
//    - Deskew (straighten tilted scans)
//
// 4. OCR extraction: Extract all text from document
//
// 5. Field mapping: Identify and extract specific fields
//
// 6. Validation: Cross-check extracted data
//
// 7. Verification: Verify document authenticity
//
// 8. Storage: Encrypt and store

interface DocumentFormat {
  format: 'jpg' | 'png' | 'pdf' | 'heic' | 'webp';
  maxFileSize: string;
  minResolution: string;
  acceptedSources: 'camera' | 'scanner' | 'file_upload' | 'whatsapp';
}
```

### OCR Field Extraction

```typescript
interface OCRResult {
  documentId: string;
  documentType: DocumentType;
  confidence: number;                // Overall confidence 0-1
  fields: ExtractedField[];
  rawText: string;
  processingTimeMs: number;
}

interface ExtractedField {
  fieldName: string;
  value: string;
  confidence: number;                // Per-field confidence
  source: 'ocr' | 'mrz' | 'barcode' | 'manual';
  boundingBox?: { x: number; y: number; width: number; height: number };
}

// Passport field extraction:
// Fields extracted from Indian passport:
// - Passport Number: "J1234567" (confidence: 0.98)
// - Full Name: "RAJESH KUMAR SHARMA" (confidence: 0.95)
// - Nationality: "INDIAN" (confidence: 0.99)
// - Date of Birth: "15/08/1985" (confidence: 0.97)
// - Gender: "M" (confidence: 0.99)
// - Place of Birth: "MUMBAI" (confidence: 0.92)
// - Date of Issue: "10/01/2016" (confidence: 0.96)
// - Date of Expiry: "09/01/2026" (confidence: 0.96)
// - Place of Issue: "MUMBAI" (confidence: 0.94)
// - MRZ: Full MRZ string (confidence: 0.99)

// MRZ (Machine Readable Zone) extraction:
// MRZ is the two-line code at the bottom of passports
// More reliable than visual OCR — standardized format
// Contains: Document type, country, name, passport number, nationality,
//           date of birth, gender, expiry date, check digits

// Field extraction confidence thresholds:
// > 0.95: Auto-accept (field populated, no review needed)
// 0.80-0.95: Suggest for review (highlight for agent check)
// 0.60-0.80: Require review (agent must verify)
// < 0.60: Manual entry (OCR too unreliable, agent types manually)

// Multi-language support:
// English passports: High accuracy (>95%)
// Hindi documents (Aadhaar, PAN): Medium accuracy (85-90%)
// Regional languages (Tamil, Bengali, etc.): Lower accuracy (70-80%)
// Arabic/Chinese passports: May need specialized OCR
```

### Data Validation

```typescript
interface DocumentValidation {
  documentId: string;
  checks: ValidationCheck[];
  overallResult: 'pass' | 'warning' | 'fail';
}

interface ValidationCheck {
  checkType: ValidationCheckType;
  result: 'pass' | 'warning' | 'fail';
  message: string;
  autoFixed: boolean;
}

type ValidationCheckType =
  | 'name_match'                     // Does passport name match booking?
  | 'expiry_check'                   // Is passport valid for travel dates?
  | 'format_check'                   // Is passport number format correct?
  | 'checksum_validation'            // MRZ check digits valid?
  | 'country_match'                  // Nationality matches expected?
  | 'duplicate_check'                // Same passport already in system?
  | 'age_verification'              // DOB consistent with age-restricted services?
  | 'photo_quality';                 // Photo meets visa application standards?

// Validation examples:
// name_match:
//   Booking: "Rajesh Sharma"
//   Passport: "RAJESH KUMAR SHARMA"
//   Result: WARNING — Middle name in passport not in booking
//   Action: Agent reviews, adds middle name to booking
//
// expiry_check:
//   Travel date: September 15, 2026
//   Passport expiry: October 10, 2026
//   Destination: Singapore (requires 6-month validity)
//   Result: FAIL — Passport must be valid until March 15, 2027
//   Action: Block booking, advise passport renewal
//
// format_check:
//   Indian passport: 1 letter + 7 digits (J1234567)
//   Extracted: "J1234567" → PASS
//   Extracted: "J1234S67" → FAIL (letter in digit position)

// Auto-correction:
// Common OCR errors and corrections:
// O → 0, l → 1, S → 5 (in MRZ, corrected by check digits)
// Common name OCR errors flagged for manual review
// Date format normalization (DD/MM/YYYY vs. YYYY-MM-DD)
```

### Verification Intelligence

```typescript
interface DocumentVerification {
  documentId: string;
  authenticityChecks: AuthenticityCheck[];
  riskScore: number;                 // 0-100, higher = more suspicious
  verifiedBy: 'automated' | 'agent' | 'third_party';
}

interface AuthenticityCheck {
  check: string;
  result: 'pass' | 'fail' | 'unknown';
  details: string;
}

// Authenticity checks:
// 1. MRZ checksum: All check digits in MRZ validate correctly
// 2. Photo consistency: Photo in passport matches face (if selfie provided)
// 3. Document template: Matches known template for the issuing country
// 4. Security features: Holograms, watermarks visible in scan
// 5. Cross-reference: Passport number format valid for issuing country
// 6. Blacklist check: Not on lost/stolen passport database
// 7. Consistency: Issue date < expiry date, DOB < issue date

// Risk scoring:
// 0-20: Low risk (clean document, all checks pass)
// 21-50: Medium risk (some checks unknown, minor discrepancies)
// 51-80: High risk (multiple check failures, significant discrepancies)
// 81-100: Very high risk (likely fraudulent, escalate immediately)

// Handling failed verifications:
// MRZ checksum failure → Retake photo (likely bad scan)
// Name mismatch → Agent reviews and resolves
// Expiry check fail → Block international booking
// High risk score → Escalate to compliance team
```

---

## Open Problems

1. **OCR accuracy for Indian documents** — Aadhaar cards, PAN cards, and voter IDs have varied formats and languages. OCR accuracy is lower than passports.

2. **Mobile capture quality** — Customers take photos of documents with phone cameras. Lighting, angles, and focus vary wildly. Need camera guidance overlay.

3. **Handwritten documents** — Some older passports and documents have handwritten entries. OCR handles these poorly. Need human fallback.

4. **Consent for OCR processing** — Extracting data from documents requires customer consent. The consent flow must be clear and not burdensome.

5. **Processing speed** — OCR processing takes 2-10 seconds per document. For a family of 5 with multiple documents, this adds up. Need parallel processing.

---

## Next Steps

- [ ] Design document processing pipeline with quality validation
- [ ] Build OCR extraction for passports, Aadhaar, and PAN cards
- [ ] Create field validation engine with name matching and expiry checking
- [ ] Design mobile document capture with guidance overlay
- [ ] Study OCR systems (Tesseract, Google Vision, AWS Textract, Azure Document Intelligence)
