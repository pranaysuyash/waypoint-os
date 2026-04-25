# Con Spec: Hyper-Local Language-Bridge (CON-REAL-007)

**Status**: Research/Draft
**Area**: Cultural Nuance & Interaction Safety

---

## 1. The Problem: "The Tone-Deaf Translation"
Standard translation apps provide literal meaning but fail at "Contextual-Etiquette." For example, using "Du" instead of "Sie" in a formal German setting, or failing to use the correct honorifics in Japan, can lead to social friction. Travelers need more than a dictionary; they need a "Cultural-Prompt" that matches their exact physical location and social context.

## 2. The Solution: 'Contextual-Linguistic-Bridge-Protocol' (CLBP)

The CLBP allows the agent to act as a "Cultural-Interpreter."

### Interaction Actions:

1.  **Just-in-Time-Norm-Sync**:
    *   **Action**: When the traveler's GPS enters a specific "Micro-Zone" (e.g., a traditional temple, a high-end sushi bar, a local market), the agent pushes a "Social-Norm-Brief" (e.g., "Remove shoes here," "Don't tip in this establishment").
2.  **Dialect-Nuance-Injection**:
    *   **Action**: Providing local slang or phrases that build rapport (e.g., using "Servus" in Bavaria vs "Moin" in Hamburg).
3.  **Interaction-Blueprint**:
    *   **Action**: Providing a "Scripted-Interaction" for high-friction tasks (e.g., "How to haggle in the souk without offending the merchant").
4.  **Phonetic-Confidence-Guide**:
    *   **Action**: Providing high-fidelity audio snippets of local pronunciation for "Survival-Phrases" (Medical needs, allergy warnings, police help).

## 3. Data Schema: `Cultural_Context_Payload`

```json
{
  "payload_id": "CLBP-11221",
  "traveler_id": "GUID_9911",
  "location_context": "RYOKAN_KYOTO_HIIRAGIYA",
  "detected_activity": "CHECK_IN",
  "social_norms": [
    { "behavior": "SHOE_REMOVAL", "severity": "CRITICAL", "description": "Remove shoes at the genkan before stepping on tatami." },
    { "behavior": "HONORIFICS", "severity": "HIGH", "description": "Address the Okami-san with formal -sama suffix." }
  ],
  "phrases": [
    { "phrase": "O-sewa ni narimasu", "usage": "Standard greeting for long-term care/hospitality", "phonetic": "Oh-seh-wah nee nah-ree-mass" }
  ],
  "status": "PUSHED_TO_DEVICE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Silent-Briefing' Rule**: Briefs should be "Micro-Readable" (under 100 characters) to avoid distracting the traveler from the actual experience.
- **Rule 2: Emergency-Linguistic-Override**: In medical or security situations, the agent MUST prioritize "Binary-Communication-Tools" (e.g., visual cards with localized text for "Allergy," "Pain," "Exit") over complex phrases.
- **Rule 3: Etiquette-Confidence-Score**: The agent monitors the traveler's "Cultural-Comfort-Level" (via chat sentiment) and scales the intensity of social-norm pings up or down accordingly.

## 5. Success Metrics (Cultural)

- **Interaction-Smoothness-Score**: Traveler's self-reported comfort during local interactions.
- **Gaffe-Prevention-Rate**: % of critical norms briefed before the traveler enters the zone.
- **Rapport-Efficiency**: Time taken to successfully complete a complex local transaction (e.g., hotel check-in, market purchase).
