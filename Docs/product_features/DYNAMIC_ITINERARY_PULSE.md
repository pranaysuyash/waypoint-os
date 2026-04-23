# Feature: Dynamic Itinerary Pulse

## POV: Traveler / End-User

### 1. Objective
To provide a living, breathing digital companion for the trip that goes beyond a static PDF, offering real-time situational awareness and frictionless utility.

### 2. Functional Requirements

#### A. The "Pulse" Dashboard
- **Contextual State**: The UI changes based on where the user is.
    - *Pre-Trip*: Focus on Packing, Visas, and Weather.
    - *At Airport*: Focus on Gate, Boarding Time, and Lounge location.
    - *In-Transit*: Focus on Driver name, Hotel check-in time, and local Currency.
- **Micro-Updates**: Real-time push notifications for gate changes, flight delays, or "Driver Arrived."

#### B. Collaborative "Bracket" Management
- **The "Options" Carousel**: When an agent sends 3 hotel choices, they appear as high-fidelity cards with "Accept/Reject/Modify" buttons.
- **Budget Transparency**: A "Cost Meter" showing how much of the trip budget is spent vs. remaining.

#### C. Smart Document Wallet
- **Encrypted Storage**: Offline-first access to Boarding Passes, Visas, and Insurance.
- **Auto-OCR**: If a traveler takes a photo of a local receipt, it auto-attaches to the "Corporate Expense" thread for that trip.

### 3. User Experience Logic
- **"Vibe" Personalization**: If the user's "Genome" indicates they hate early mornings, the system flags any morning flights with a "High Friction Alert."
- **Social Integration**: Ability to share the "Live Itinerary" (without PNR sensitive data) with family or colleagues for tracking.

### 4. Safety & SOS
- **One-Tap SOS**: Connecting directly to the 24/7 Agency Duty Desk via VoA (Voice over App).
- **Safe-Arrival Notification**: Auto-checking the user into their hotel and notifying their emergency contact.
