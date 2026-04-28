# Voice & Conversational AI — Speech Processing & NLU

> Research document for speech-to-text, natural language understanding, intent mapping, and multi-language speech processing.

---

## Key Questions

1. **How do we convert customer speech to actionable travel data?**
2. **What NLU (Natural Language Understanding) models do we need?**
3. **How do we handle multi-language and code-switching in India?**
4. **What's the intent mapping for travel conversations?**
5. **How do we handle background noise and poor call quality?**

---

## Research Areas

### Speech-to-Text Pipeline

```typescript
interface SpeechPipeline {
  audioInput: AudioInput;
  preprocessing: AudioPreprocessing;
  stt: SpeechToText;
  postprocessing: STTPostProcessing;
  output: ProcessedSpeech;
}

interface AudioInput {
  source: AudioSource;
  format: 'pcm' | 'wav' | 'mp3' | 'opus';
  sampleRate: number;                 // 8000 Hz (telephony) or 16000 Hz (VoIP)
  channels: 1 | 2;
  language: string;
}

type AudioSource =
  | 'phone_call'                      // Traditional telephony (8kHz, low quality)
  | 'voip'                            // VoIP call (16kHz, better quality)
  | 'whatsapp_voice'                  // WhatsApp voice message (Opus codec)
  | 'voice_note';                     // In-app voice note

// Audio preprocessing:
// 1. Noise reduction: Remove background noise (traffic, music, crowd)
// 2. Echo cancellation: Remove echo from speakerphone calls
// 3. Gain normalization: Normalize volume to consistent level
// 4. Voice activity detection: Detect speech segments, remove silence
// 5. Speaker diarization: Identify who is speaking (agent vs. customer)
//
// India-specific challenges:
// - Background noise: Horns, crowds, music (very common)
// - Network quality: Call drops, compression artifacts
// - Multiple speakers: Family members speaking simultaneously
// - Low-bandwidth: 2G/3G connections in rural areas
// - Speakerphone: Common for group travel planning

interface SpeechToText {
  provider: STTProvider;
  model: STTModel;
  language: STTLanguage[];
  features: STTFeature[];
}

type STTProvider =
  | 'google_speech'                   // Best for Indian languages
  | 'azure_speech'                    // Good multi-language, custom models
  | 'aws_transcribe'                  // Good real-time, India region
  | 'deepgram';                       // Fast, accurate, good for telephony

// STT model selection:
// Google Speech-to-Text (recommended for India):
//   - Supports 12+ Indian languages
//   - India-specific English model (en-IN)
//   - Automatic punctuation
//   - Speaker diarization
//   - Streaming recognition (real-time)
//   - Cost: $0.006/15 seconds (standard), $0.009/15 seconds (enhanced)
//
// Azure Speech:
//   - Custom Speech: Train on travel-specific vocabulary
//   - India language support: Hindi, Tamil, Bengali, Telugu, etc.
//   - Real-time + batch transcription
//   - Pronunciation assessment (for agent training)
//   - Cost: $1/hour (standard), $1.50/hour (custom)
//
// For travel vocabulary accuracy:
// - Destination names: "Allepey" → "Alappuzha", "Cochin" → "Kochi"
// - Hotel names: "Taj Lake Palace" not "Taj Lake Palis"
// - Airline names: "IndiGo" not "Indigo", "Vistara" not "Vistaara"
// - Travel terms: "itinerary", "TCS", "GST invoice", "e-visa"

interface STTFeature {
  feature: string;
  enabled: boolean;
}

// Required STT features:
// - Streaming recognition (real-time, not wait until end of speech)
// - Automatic punctuation (insert commas, periods)
// - Speaker diarization (agent vs. customer)
// - Word-level confidence scores
// - Profanity filter (optional, for customer-facing transcripts)
// - Custom vocabulary (travel terms, destination names)
// - Multi-language detection (detect language switches)
// - Number formatting ("two adults" → "2 adults")

interface ProcessedSpeech {
  transcript: string;
  confidence: number;
  segments: SpeechSegment[];
  language: string;
  languageSwitches: LanguageSwitch[];
}

interface SpeechSegment {
  speaker: 'agent' | 'customer' | 'unknown';
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
  words: WordInfo[];
}

interface WordInfo {
  word: string;
  startTime: number;
  endTime: number;
  confidence: number;
}
```

### NLU Intent Mapping

```typescript
interface NLUModel {
  intents: TravelIntent[];
  entities: TravelEntity[];
  dialogs: DialogFlow[];
  fallback: NLUFallback;
}

type TravelIntent =
  // Inquiry intents
  | 'inquire_destination'              // "I want to go to Kerala"
  | 'inquire_trip_type'               // "Looking for honeymoon packages"
  | 'inquire_budget'                  // "What are budget options for Goa?"
  | 'inquire_dates'                   // "Planning to travel in December"
  | 'inquire_group_size'              // "We are 6 adults and 2 children"
  | 'inquire_visa'                    // "Do I need a visa for Thailand?"
  // Booking intents
  | 'book_trip'                       // "I want to book this trip"
  | 'check_availability'             // "Is this available on Dec 15?"
  | 'confirm_booking'                 // "Yes, go ahead and book it"
  | 'cancel_booking'                  // "I need to cancel my booking"
  | 'modify_booking'                  // "Can I change the dates?"
  // Support intents
  | 'check_status'                    // "What's my booking status?"
  | 'request_itinerary'              // "Send me the itinerary"
  | 'report_issue'                    // "The hotel is not what was promised"
  | 'request_refund'                  // "I want a refund"
  | 'escalate'                        // "Let me speak to your manager"
  // Information intents
  | 'ask_weather'                     // "What's the weather in Goa in January?"
  | 'ask_documents'                   // "What documents do I need?"
  | 'ask_payment'                     // "How do I make payment?"
  | 'ask_policy'                      // "What's the cancellation policy?"
  // Emergency intents
  | 'emergency_medical'               // "I need medical help"
  | 'emergency_lost'                  // "I lost my passport"
  | 'emergency_flight'                // "My flight got cancelled";

// Entity extraction:
interface TravelEntity {
  type: TravelEntityType;
  value: string;
  resolved: string;                   // Canonical form
  confidence: number;
  source: 'spoken' | 'keypad' | 'context';
}

type TravelEntityType =
  | 'destination'                     // "Kerala" → destination_id: "KER"
  | 'date'                            // "December 15th" → 2026-12-15
  | 'date_range'                      // "5 days in January" → Jan 1-5
  | 'duration'                        // "5 nights" → nights: 5
  | 'traveler_count'                  // "2 adults, 1 child" → adults: 2, children: 1
  | 'budget'                          // "around 50 thousand" → ₹50,000
  | 'trip_type'                       // "honeymoon" → trip_type: honeymoon
  | 'booking_ref'                     // "booking number TRV12345" → TRV-12345
  | 'hotel_name'                      // "Taj Lake Palace" → hotel_id
  | 'airline'                         // "IndiGo flight" → airline: 6E
  | 'phone_number'                    // "my number is 98765 43210"
  | 'email'                           // "email is john at gmail dot com"
  | 'name'                            // "My name is Pranay" → customer_name
  | 'payment_method'                  // "I'll pay by UPI"
  | 'complaint_type';                 // "hotel was dirty" → complaint: hygiene

// Intent resolution examples:
//
// Customer: "I want to plan a honeymoon trip to Kerala in December,
//           around 50-60 thousand budget, for 5 nights"
//
// Resolved:
// intent: inquire_destination + inquire_trip_type
// entities:
//   destination: "Kerala" (confidence: 0.97)
//   trip_type: "honeymoon" (confidence: 0.95)
//   date: "December 2026" (confidence: 0.92)
//   budget: ₹50,000-60,000 (confidence: 0.94)
//   duration: 5 nights (confidence: 0.98)
//
// System action:
// → Search for honeymoon packages to Kerala
// → Filter by December availability
// → Filter by ₹50-60K budget, 5 nights
// → Prepare results for agent or voice response
```

### Multi-Language & Code-Switching

```typescript
interface MultiLanguageNLU {
  languages: SupportedLanguage[];
  codeSwitching: CodeSwitchConfig;
  translation: TranslationConfig;
  culturalContext: CulturalContext[];
}

interface SupportedLanguage {
  code: string;                       // "en-IN", "hi-IN"
  name: string;                       // "English (India)", "Hindi"
  sttModel: string;
  ttsVoice: string;
  nluCoverage: number;                // % of intents covered
  entityCoverage: number;
}

// Language support strategy:
// Phase 1: English (India) + Hindi
// Phase 2: Tamil, Bengali, Telugu, Kannada
// Phase 3: Marathi, Gujarati, Malayalam, Punjabi
//
// Code-switching (Hinglish) handling:
// "Mujhe December mein Kerala trip chahiye, around 50 thousand budget,
//  2 adults and 1 child, 5 raat ka plan"
//
// Mixed language detection:
// - Hindi words: "mujhe" (I want), "chahiye" (need), "raat" (night), "ka" (of)
// - English words: "December", "Kerala trip", "budget", "adults", "child", "plan"
// - Numbers: "50 thousand", "2", "1", "5"
//
// Processing:
// 1. Detect primary language (Hindi)
// 2. Identify code-switched segments (English)
// 3. Translate Hindi segments to English internally
// 4. Extract entities from combined text
// 5. Respond in customer's preferred language
//
// Challenge: "booking reference dena" = "give me the booking reference"
// "cancel karna hai" = "I want to cancel"
// "bill bhej do" = "send the invoice"
// These are common Hinglish phrases that need training data

interface CodeSwitchConfig {
  enabled: boolean;
  primaryLanguage: string;
  switchDetection: 'automatic' | 'disabled';
  models: CodeSwitchModel[];
}

// Code-switching models:
// Option 1: Use Google's multilingual STT (auto-detects language)
// Option 2: Train custom model on Hinglish travel conversations
// Option 3: Use LLM (GPT-4, Claude) for code-switched intent detection
//
// Recommended: Google multilingual STT + LLM-based intent detection
// Google handles the speech recognition across languages
// LLM handles the semantic understanding (more flexible than rule-based NLU)
```

### Voice Biometrics & Speaker Identification

```typescript
interface VoiceBiometrics {
  enrollment: VoiceEnrollment;
  identification: SpeakerIdentification;
  authentication: VoiceAuthentication;
  privacy: BiometricPrivacy;
}

interface VoiceEnrollment {
  customerId: string;
  voiceprintId: string;
  sampleCount: number;                // Min 3 samples needed
  enrollmentDate: Date;
  quality: number;                    // Voiceprint quality score
}

// Voice biometrics use cases:
// 1. Customer identification: "Welcome back, {Name}. How can I help?"
// 2. Fraud prevention: Verify caller is the booking customer
// 3. Agent authentication: Voice login for agents
// 4. Personalization: Load customer profile based on voice
//
// India considerations:
// - Voice biometrics must comply with DPDP Act (consent required)
// - Must offer alternative authentication (OTP, PIN)
// - Voice data is sensitive biometric data — strict storage requirements
// - Accuracy may vary with background noise (common in India)
// - Language/accent variation within India affects accuracy
//
// Not recommended for Phase 1 — complexity and privacy risk
// Use phone number + OTP as primary authentication instead
```

---

## Open Problems

1. **Hinglish NLU accuracy** — No off-the-shelf model handles Hinglish well. Need custom training on travel-specific Hinglish conversations.

2. **Indian name recognition** — STT frequently misrecognizes Indian names (both customer and destination names). Need custom pronunciation dictionaries.

3. **Real-time latency** — Streaming STT + NLU must complete within 500ms for natural conversation flow. Network latency in India can be unpredictable.

4. **Cost at scale** — Processing 1,000+ calls/day with cloud STT and NLU costs ₹2-5 lakh/month. Need caching and optimization.

5. **Fallback quality** — When speech recognition fails, fallback to keypad IVR is frustrating. Need graceful degradation, not binary success/failure.

---

## Next Steps

- [ ] Design speech-to-text pipeline with noise preprocessing
- [ ] Build NLU intent model with travel-specific intents and entities
- [ ] Create multi-language support with code-switching detection
- [ ] Train custom vocabulary for travel destinations, hotels, and airlines
- [ ] Study speech AI platforms (Google Speech, Azure Speech, Deepgram, AssemblyAI)
