# Feature: Visual Intent Extraction Engine

## POV: User & Agent POV

### 1. Objective
To allow travelers and agents to communicate complex travel preferences via images, automatically extracting "Intent," "Vibe," and "Technical Data" from visual assets.

### 2. Functional Requirements

#### A. "Vibe-to-Source" Parsing
- **Atmosphere Extraction**: Traveler sends a photo of a hotel room from Instagram or Pinterest → AI identifies the aesthetic style (e.g., "Mid-Century Modern," "Wabi-Sabi," "Brutalist Luxury").
- **Asset Identification**: Identifying specific furniture or lighting brands in a photo to find hotels that feature similar design-forward interiors.
- **Geography Detection**: Identifying landmarks or architectural styles in a "I want to go somewhere that looks like this" photo to suggest matching destinations.

#### B. Intelligent Document OCR (Optical Character Recognition)
- **Messy Document Recovery**: Parsing hand-written local transport receipts or blurry passport photos with 99.9% accuracy.
- **Visa/Stamp Analysis**: Scanning a traveler's passport pages to identify existing visas and entry/exit stamps to calculate "Remaining Stay" or "Visa Eligibility" automatically.
- **Medical/Health Certs**: Validating vaccination cards or doctor's notes against local entry requirements.

#### C. Visual "Waitlist" Monitoring
- **Room-Type Verification**: AI compares the traveler's "Live photo" of their hotel room upon check-in against the "Booked room type" (e.g., Sea View vs. Garden View). If a discrepancy is found, it alerts the agent to demand a refund or upgrade immediately.

### 3. Core Engine Logic
- **Multi-Modal Embedding**: Converting images into the same vector space as the "Customer Genome" to find semantic matches between "What they see" and "What they like."
- **Fraud Detection**: Identifying "Photoshopped" or altered documents (e.g., fake insurance certificates) before they are submitted to suppliers.

### 4. Safety & Privacy
- **Auto-Redaction**: Identifying and blurring out sensitive PII (e.g., SSN, CC numbers) in images before they are shared in the agent workspace.
- **Metadata Scrubbing**: Removing EXIF/GPS data from traveler photos to protect their location privacy if they choose.
