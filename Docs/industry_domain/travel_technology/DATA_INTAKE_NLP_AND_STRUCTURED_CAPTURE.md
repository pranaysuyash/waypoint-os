# Domain Knowledge: Data Intake (NLP & Structured Capture)

**Category**: Communication & Data Intake Architecture  
**Focus**: Transforming "Messy" human communication into structured GDS/API data.

---

## 1. Unstructured NLP Extraction
- **The "Messy" Message**: "Hey, I need to get to NYC on Tuesday morning, maybe JFK or EWR. Business class. Need to be there by noon for a meeting. Oh, and I hate the 777."
- **Extracted Data**:
    - **Origin**: Current City (from Profile).
    - **Destination**: JFK/EWR.
    - **Date**: [Next Tuesday].
    - **Arrival Deadline**: 12:00.
    - **Cabin**: J (Business).
    - **Equipment Filter**: `-777`.
- **SOP**: The agent must provide a **"Verification Summary"** back to the client: "Confirming: NYC next Tuesday, arriving by noon, non-777 aircraft. Correct?"

---

## 2. Document OCR (Passport/Visas)
- **Logic**: Clients send "Photos" of documents.
- **SOP**: Automated OCR (Optical Character Recognition) extracts the **Passport Number**, **Expiry**, and **DOB**.
- **Crucial Check**: "Does the name on the Passport EXACTLY match the name in the GDS?" (The "Middle Name" Trap).

---

## 3. The "Preferences" Crawler
- **Logic**: Analyzing past messages to find "Hidden" preferences (e.g., "The hotel last time was too noisy").
- **SOP**: Tagging the profile with: `NOISE_SENSITIVE`, `PREF_HIGH_FLOOR`.

---

## 4. Structured Intake Forms (The "Safety Net")
- **Logic**: For complex trips (Groups/Events), NLP is too risky.
- **SOP**: Use a "Structured Form" for mandatory data (T-minus 72 hour Health declarations, specialized gear requirements).

---

## 5. Proposed Scenarios
- **The "Ambiguous" Date**: A client says "Next Friday." Does that mean this coming Friday or the one after? The agent must **"Always disambiguate"** by stating the exact date (e.g., "Friday, Oct 24th").
- **OCR Error**: The OCR misreads a '0' as an 'O' in a passport number. The client is denied boarding. The agent must have a **"Human-in-the-loop"** check for all passport data entry.
- **The "I Hate..." Filter Failure**: A client said they "Hate the 777" in a chat 6 months ago. The agent books them on a 777. The client is furious. The agent must have a **"Global Preference Sync"** that flags equipment types.
- **Voice to PNR Error**: A voice transcription says "Five people" but the client meant "Flight people." The agent must verify the "Passenger Count" before issuing the ticket.
