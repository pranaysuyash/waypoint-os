# Voice Intake & Orchestration Spec

## Interaction Model
- **Agency Side**: Enters initial lead context $\rightarrow$ generates a unique link.
- **Traveler Side**: Joins a voice session via the link $\rightarrow$ sees a live-updating brief panel.

## Orchestration Flow
The system uses a "Question Router" rather than a script:
1. **State Extraction**: Convert voice input to structured fields.
2. **Classification**: Assign traveler to "brackets" (e.g., `family_with_toddler`, `shopping_first`).
3. **Gap Detection**: Identify missing critical information.
4. **Next-Question Policy**: Priority given to blocking unknowns $\rightarrow$ contradictions $\rightarrow$ route-changing fields.

## The "Audit Mode"
When a user uploads an existing itinerary:
- **Extraction**: Parse PDF/URL for hotels, activities, and prices.
- **Suitability Check**: Compare the plan against the specific traveler group.
- **Waste Detection**: Flag activities that are paid for but low-utility for certain group members (e.g., Universal Studios for elderly/toddlers).
- **Alternative Generation**: Suggest a "smarter" version of the existing plan.
