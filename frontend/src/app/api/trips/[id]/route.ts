import { NextRequest, NextResponse } from "next/server";

const MOCK_TRIPS: Record<string, Record<string, unknown>> = {
  "TRP-2026-SGP-0315": {
    id: "TRP-2026-SGP-0315",
    destination: "Singapore",
    type: "Family",
    state: "green",
    age: "2h ago",
    createdAt: "2026-04-16T08:00:00Z",
    updatedAt: "2026-04-16T10:00:00Z",
    party: 4,
    dateWindow: "Aug 1–10",
    action: "Ready to proceed",
    overdue: false,
    origin: "Mumbai",
    budget: "$4,500",
    customerMessage: "Hi, we're a family of 4 (2 adults, 2 kids aged 8 and 12) planning a trip to Singapore in early August. We'd like to visit Universal Studios, Gardens by the Bay, and maybe Sentosa. Budget is around $4,000-$5,000 for the whole trip including flights. We're flexible on exact dates within the first two weeks of August.",
    agentNotes: "Family has traveled internationally before. Kids are excited about Universal Studios. Parents interested in cultural experiences too. Prefers 4-star hotels near MRT for easy transport.",
    packet: {
      facts: {
        destination_candidates: { value: "Singapore", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Mumbai", confidence: 0.9, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Aug 1–10, 2026", confidence: 0.85, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$4,000-$5,000 total", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "4 (2 adults, 2 children)", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        hotel_preference: { value: "4-star near MRT", confidence: 0.8, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "leisure_family", confidence: 0.9 },
        visa_required: { value: "no (Indian passport, e-visa available)", confidence: 0.7 },
        peak_season: { value: "yes (school holidays)", confidence: 0.85 },
      },
      ambiguities: [
        { field_name: "exact_dates", ambiguity_type: "range", raw_value: "first two weeks of August" },
      ],
      unknowns: [
        { field_name: "flight_class", reason: "not mentioned", notes: "assumed economy" },
        { field_name: "meal_preferences", reason: "not mentioned", notes: null },
      ],
      contradictions: [],
    },
    validation: {
      is_valid: true,
      errors: [],
      warnings: [{ severity: "warning", code: "W001", message: "Peak season — prices may be higher", field: "date_window" }],
    },
    decision: {
      decision_state: "PROCEED_TRAVELER_SAFE",
      hard_blockers: [],
      soft_blockers: ["Peak season pricing may stretch budget"],
      contradictions: [],
      risk_flags: ["peak_season"],
      follow_up_questions: [
        { field_name: "exact_dates", question: "Can you confirm your preferred exact travel dates?", priority: "high", suggested_values: ["Aug 1-10", "Aug 3-12", "Aug 5-14"] },
      ],
      rationale: { hard_blockers: [], soft_blockers: ["Peak season pricing"], contradictions: [], confidence: 0.88, feasibility: "realistic" },
      confidence_score: 0.88,
      branch_options: ["Standard family package", "Premium with Sentosa resort stay"],
      commercial_decision: "Ready to quote — family trip with clear requirements",
      budget_breakdown: {
        verdict: "realistic",
        currency: "INR",
        budget_stated: 450000,
        total_estimated_low: 380000,
        total_estimated_high: 520000,
        buckets: [
          { bucket: "flights", low: 120000, high: 160000, covered: true },
          { bucket: "stay", low: 100000, high: 140000, covered: true },
          { bucket: "food", low: 40000, high: 60000, covered: true },
          { bucket: "local_transport", low: 15000, high: 25000, covered: true },
          { bucket: "activities", low: 60000, high: 80000, covered: true },
          { bucket: "visa_insurance", low: 10000, high: 15000, covered: true },
          { bucket: "shopping", low: 20000, high: 30000, covered: true },
          { bucket: "buffer", low: 10000, high: 15000, covered: true },
        ],
        missing_buckets: [],
        risks: ["peak_season_surcharge"],
        critical_changes: [],
        must_confirm: ["exact_travel_dates"],
        alternative: null,
      },
    },
    strategy: {
      session_goal: "Confirm travel dates and send detailed itinerary quote for Singapore family trip",
      priority_sequence: ["Confirm exact dates", "Send hotel options near MRT", "Quote Universal Studios + Gardens by the Bay package", "Confirm flight preference"],
      tonal_guardrails: ["Family-friendly language", "Highlight kid-friendly activities", "Be transparent about peak season pricing"],
      risk_flags: ["peak_season"],
      suggested_opening: "Thank you for choosing Singapore for your family vacation! I've put together some wonderful options that I think your family will love, especially the kids.",
      exit_criteria: ["Dates confirmed", "Hotel selected", "Activity package approved"],
      next_action: "Send date confirmation request with 3 itinerary options",
      assumptions: ["Economy flights from Mumbai", "Indian passport holders", "Budget includes all expenses"],
      suggested_tone: "warm_professional",
    },
    safety: {
      leakage_passed: true,
      strict_leakage: false,
      leakage_errors: [],
    },
    internal_bundle: {
      system_context: "Family of 4 traveling Mumbai → Singapore Aug 1-10. Budget ~$4,500. Interested in Universal Studios, Gardens by the Bay, Sentosa. Need 4-star hotel near MRT.",
      user_message: "Family vacation package — Singapore August 2026. 4 pax (2A, 2C). Universal Studios + Gardens by the Bay + Sentosa. 4-star near MRT.",
      follow_up_sequence: [{ field_name: "exact_dates", question: "Confirm preferred travel dates", priority: "high" }],
      branch_prompts: [],
      internal_notes: "Budget is realistic. Peak season may push to upper range. Recommend booking flights early.",
      constraints: ["Budget cap $5,000", "Family-friendly activities only", "Near MRT for easy transport"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a friendly travel advisor helping a family plan their Singapore vacation.",
      user_message: "Hi! We'd love to help plan your family trip to Singapore. Could you confirm your preferred dates in August? We have some great options for Universal Studios and Gardens by the Bay that the kids will absolutely love!",
      follow_up_sequence: [{ field_name: "exact_dates", question: "What dates in August work best for your family?", priority: "high" }],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-DXB-0418": {
    id: "TRP-2026-DXB-0418",
    destination: "Dubai",
    type: "Corporate",
    state: "blue",
    age: "5h ago",
    createdAt: "2026-04-16T05:00:00Z",
    updatedAt: "2026-04-16T07:00:00Z",
    party: 8,
    dateWindow: "Jul 3–7",
    action: "Clarification requested from client",
    overdue: false,
    origin: "Delhi",
    budget: "$15,000",
    customerMessage: "We need to organize a corporate retreat for 8 people in Dubai, July 3-7. Need meeting facilities for 2 days, team building activities, and some leisure time. Budget is approximately $15,000 total. We need visa assistance for 3 team members.",
    agentNotes: "Corporate client — TechCorp Solutions. CFO approved budget. 3 team members need visa assistance (first-time travelers). Previous corporate trips were to Bangkok and Kuala Lumpur.",
    packet: {
      facts: {
        destination_candidates: { value: "Dubai, UAE", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Delhi", confidence: 0.85, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Jul 3–7, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$15,000 total", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "8 (corporate group)", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "corporate_retreat", confidence: 0.95 },
        visa_required: { value: "yes (3 of 8 travelers)", confidence: 0.9 },
      },
      ambiguities: [
        { field_name: "meeting_format", ambiguity_type: "vague", raw_value: "meeting facilities for 2 days" },
      ],
      unknowns: [
        { field_name: "accommodation_tier", reason: "not specified", notes: "corporate standard assumed" },
      ],
      contradictions: [],
    },
    validation: {
      is_valid: true,
      errors: [],
      warnings: [
        { severity: "warning", code: "W002", message: "July is extremely hot in Dubai — confirm indoor activities", field: "destination" },
        { severity: "warning", code: "W003", message: "Visa processing for 3 travelers needs 5-7 business days", field: "visa" },
      ],
    },
    decision: {
      decision_state: "ASK_FOLLOWUP",
      hard_blockers: [],
      soft_blockers: ["Extreme heat in July", "Visa processing timeline tight"],
      contradictions: [],
      risk_flags: ["extreme_weather", "visa_timeline"],
      follow_up_questions: [
        { field_name: "meeting_format", question: "What type of meeting setup do you need? (conference room, boardroom, workshop space)", priority: "high", suggested_values: ["Conference room", "Boardroom", "Workshop space"] },
        { field_name: "visa_travelers", question: "Can you share passport details for the 3 team members who need visa assistance?", priority: "critical", suggested_values: [] },
      ],
      rationale: { hard_blockers: [], soft_blockers: ["Weather", "Visa timeline"], contradictions: [], confidence: 0.72, feasibility: "borderline" },
      confidence_score: 0.72,
      branch_options: ["Proceed with indoor-focused itinerary", "Suggest alternative dates (November)"],
      commercial_decision: "High-value corporate booking — gather missing info before quoting",
      budget_breakdown: {
        verdict: "realistic",
        currency: "INR",
        budget_stated: 1500000,
        total_estimated_low: 1200000,
        total_estimated_high: 1650000,
        buckets: [
          { bucket: "flights", low: 320000, high: 400000, covered: true },
          { bucket: "stay", low: 300000, high: 400000, covered: true },
          { bucket: "food", low: 160000, high: 200000, covered: true },
          { bucket: "local_transport", low: 60000, high: 80000, covered: true },
          { bucket: "activities", low: 200000, high: 300000, covered: true },
          { bucket: "visa_insurance", low: 40000, high: 60000, covered: true },
          { bucket: "shopping", low: 80000, high: 120000, covered: true },
          { bucket: "buffer", low: 40000, high: 90000, covered: true },
        ],
        missing_buckets: [],
        risks: ["extreme_heat_july", "visa_processing_delay"],
        critical_changes: [],
        must_confirm: ["meeting_room_requirements", "visa_traveler_details"],
        alternative: "Consider moving to November for better weather",
      },
    },
    strategy: {
      session_goal: "Collect missing meeting format and visa details, then send corporate retreat quote",
      priority_sequence: ["Get visa details for 3 travelers", "Confirm meeting room requirements", "Propose indoor-focused itinerary", "Handle visa processing"],
      tonal_guardrails: ["Professional corporate tone", "Proactive about weather warning", "Clear timeline communication"],
      risk_flags: ["extreme_weather", "visa_timeline"],
      suggested_opening: "Thank you for choosing Dubai for your corporate retreat. To prepare the best proposal, I have a few quick questions about your meeting setup and visa requirements.",
      exit_criteria: ["Meeting format confirmed", "Visa documents collected", "Itinerary approved"],
      next_action: "Send clarification request for meeting format and visa details",
      assumptions: ["Corporate tier accommodation", "Group visa processing available", "Indoor activities preferred due to heat"],
      suggested_tone: "professional_efficient",
    },
    safety: {
      leakage_passed: true,
      strict_leakage: false,
      leakage_errors: [],
    },
    internal_bundle: {
      system_context: "Corporate retreat for 8, Dubai Jul 3-7. $15K budget. Need meeting facilities + team building. 3 visas required. High-value corporate client.",
      user_message: "Corporate retreat — Dubai July 3-7. 8 pax. Meeting facilities 2 days + team building. 3 visa assistance needed. Budget $15K.",
      follow_up_sequence: [{ field_name: "meeting_format", question: "Meeting room setup?", priority: "high" }, { field_name: "visa_travelers", question: "Passport details for visa?", priority: "critical" }],
      branch_prompts: [],
      internal_notes: "TechCorp Solutions — CFO approved. Previous trips: BKK, KUL. Consider indoor focus due to July heat.",
      constraints: ["Budget cap $15,000", "Visa for 3 travelers", "Indoor activities preferred"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a professional travel advisor helping plan a corporate retreat to Dubai.",
      user_message: "Hello! We're excited to help organize your team's Dubai retreat. To put together the perfect proposal, could you let us know what type of meeting setup you'd prefer and share details for the team members who need visa assistance?",
      follow_up_sequence: [{ field_name: "meeting_format", question: "What meeting room setup works best for your team?", priority: "high" }],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-AND-0420": {
    id: "TRP-2026-AND-0420",
    destination: "Andaman",
    type: "Honeymoon",
    state: "amber",
    age: "1d ago",
    createdAt: "2026-04-15T12:00:00Z",
    updatedAt: "2026-04-15T14:00:00Z",
    party: 2,
    dateWindow: "May 15–22",
    action: "Draft itinerary branch pending",
    overdue: false,
    origin: "Chennai",
    budget: "$3,000",
    customerMessage: "Planning our honeymoon in the Andaman Islands, May 15-22. We want a mix of relaxation and adventure — beach time, snorkeling, maybe scuba. Looking for a romantic beachfront resort. Budget around $3,000.",
    agentNotes: "Couple in late 20s. First big trip together. Want it to be special. Beachfront is non-negotiable. Open to island hopping.",
    packet: {
      facts: {
        destination_candidates: { value: "Andaman Islands", confidence: 0.97, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Chennai", confidence: 0.75, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "May 15–22, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$3,000", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "2 (couple)", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        hotel_preference: { value: "beachfront resort", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "honeymoon_romantic", confidence: 0.95 },
        activities: { value: "snorkeling, scuba, beach", confidence: 0.9 },
      },
      ambiguities: [],
      unknowns: [
        { field_name: "scuba_certification", reason: "not mentioned", notes: "need to check if certified" },
      ],
      contradictions: [],
    },
    validation: {
      is_valid: true,
      errors: [],
      warnings: [{ severity: "warning", code: "W004", message: "May is start of monsoon season in Andaman", field: "date_window" }],
    },
    decision: {
      decision_state: "BRANCH_OPTIONS",
      hard_blockers: [],
      soft_blockers: ["Early monsoon may affect water activities"],
      contradictions: [],
      risk_flags: ["monsoon_season"],
      follow_up_questions: [
        { field_name: "scuba_certification", question: "Are you both certified for scuba diving?", priority: "medium", suggested_values: ["Yes, both certified", "No, interested in beginner course"] },
      ],
      rationale: { hard_blockers: [], soft_blockers: ["Monsoon season"], contradictions: [], confidence: 0.78, feasibility: "borderline" },
      confidence_score: 0.78,
      branch_options: ["Havelock Island focused stay", "Island hopping (Havelock + Neil Island)"],
      commercial_decision: "Draft two itinerary options — monsoon contingency needed",
      budget_breakdown: null,
    },
    strategy: {
      session_goal: "Present honeymoon itinerary options with monsoon contingency",
      priority_sequence: ["Confirm scuba certification", "Present beachfront resort options", "Quote snorkeling + island hopping package", "Add monsoon backup plan"],
      tonal_guardrails: ["Romantic and warm tone", "Be transparent about weather", "Emphasize special moments"],
      risk_flags: ["monsoon_season"],
      suggested_opening: "Congratulations on your upcoming honeymoon! The Andaman Islands are absolutely magical — let me share some beautiful options for your special trip.",
      exit_criteria: ["Resort selected", "Activity package confirmed", "Monsoon backup agreed"],
      next_action: "Send 2 honeymoon itinerary options with different island combinations",
      assumptions: ["Flying from Chennai", "No advance scuba certification", "Beachfront non-negotiable"],
      suggested_tone: "warm_romantic",
    },
    safety: {
      leakage_passed: true,
      strict_leakage: false,
      leakage_errors: [],
    },
    internal_bundle: {
      system_context: "Honeymoon couple, Andaman May 15-22, $3K budget. Beachfront resort required. Snorkeling + scuba interest. Monsoon season — need backup plan.",
      user_message: "Honeymoon package — Andaman Islands May 15-22. 2 pax. Beachfront resort + snorkeling/scuba. $3K budget.",
      follow_up_sequence: [{ field_name: "scuba_certification", question: "Scuba certification status?", priority: "medium" }],
      branch_prompts: [],
      internal_notes: "First big trip together. Make it special. Beachfront is non-negotiable. May is monsoon start — have indoor backup.",
      constraints: ["Beachfront required", "Budget $3,000", "Romantic experiences priority"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a warm travel advisor helping plan a honeymoon.",
      user_message: "Congratulations on your honeymoon! The Andaman Islands will be absolutely perfect for you. We have some stunning beachfront resorts that I know you'll fall in love with. Let me share our top picks!",
      follow_up_sequence: [],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-MSC-0422": {
    id: "TRP-2026-MSC-0422",
    destination: "Moscow",
    type: "Solo",
    state: "red",
    age: "2d ago",
    createdAt: "2026-04-14T10:00:00Z",
    updatedAt: "2026-04-14T12:00:00Z",
    party: 1,
    dateWindow: "Jun 10–20",
    action: "Requires owner review",
    overdue: true,
    origin: "Mumbai",
    budget: "$12,400",
    customerMessage: "I want to travel to Moscow for a solo adventure, June 10-20. I'm interested in history, architecture, and local culture. Budget is around $12,000. I have some concerns about the visa process and current travel advisories.",
    agentNotes: "Experienced solo traveler. Has been to 30+ countries. Aware of geopolitical situation but still wants to proceed. Needs visa guidance. High-value trip requiring owner review.",
    packet: {
      facts: {
        destination_candidates: { value: "Moscow, Russia", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Mumbai", confidence: 0.8, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Jun 10–20, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$12,000", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "1 (solo)", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "solo_adventure_cultural", confidence: 0.9 },
        visa_complexity: { value: "high — Russian visa for Indian passport", confidence: 0.95 },
        geopolitical_risk: { value: "high — active travel advisories", confidence: 0.95 },
      },
      ambiguities: [],
      unknowns: [],
      contradictions: [],
    },
    validation: {
      is_valid: true,
      errors: [],
      warnings: [
        { severity: "warning", code: "W005", message: "Active travel advisory for Russia", field: "destination" },
        { severity: "warning", code: "W006", message: "Visa processing may take 10-15 business days", field: "visa" },
      ],
    },
    decision: {
      decision_state: "STOP_NEEDS_REVIEW",
      hard_blockers: ["Active travel advisory for destination", "Geopolitical risk requires owner approval"],
      soft_blockers: ["Complex visa process"],
      contradictions: [],
      risk_flags: ["travel_advisory", "geopolitical_risk", "unusual_destination", "high_value"],
      follow_up_questions: [],
      rationale: { hard_blockers: ["Travel advisory", "Geopolitical risk"], soft_blockers: ["Visa complexity"], contradictions: [], confidence: 0.45, feasibility: "not_realistic_without_approval" },
      confidence_score: 0.45,
      branch_options: [],
      commercial_decision: "STOP — requires owner review before proceeding",
      budget_breakdown: null,
    },
    strategy: {
      session_goal: "Escalate to owner for review — high-risk destination with active travel advisory",
      priority_sequence: ["Flag for owner review", "Prepare risk assessment", "If approved: handle visa process", "If rejected: suggest alternatives"],
      tonal_guardrails: ["Be honest about risks", "Don't discourage but be transparent", "Present facts objectively"],
      risk_flags: ["travel_advisory", "geopolitical_risk", "high_value"],
      suggested_opening: "Thank you for your interest in Moscow. I want to be transparent — there are some important considerations about this destination that we need to review carefully before proceeding.",
      exit_criteria: ["Owner review complete", "Risk assessment signed off", "Client informed of decision"],
      next_action: "Escalate to owner for risk review and approval",
      assumptions: ["Client aware of geopolitical situation", "Indian passport holder"],
      suggested_tone: "honest_professional",
    },
    safety: {
      leakage_passed: true,
      strict_leakage: false,
      leakage_errors: [],
    },
    internal_bundle: {
      system_context: "SOLO TRIP TO MOSCOW — REQUIRES OWNER REVIEW. Active travel advisory. $12K budget. Experienced traveler. Geopolitical risk HIGH.",
      user_message: "ESCALATION: Solo Moscow trip Jun 10-20. $12K. Travel advisory active. Needs owner sign-off before quoting.",
      follow_up_sequence: [],
      branch_prompts: [],
      internal_notes: "Client is experienced (30+ countries). Still wants to proceed despite advisories. High-value booking. Owner MUST review before any customer communication.",
      constraints: ["Owner approval required", "Travel advisory disclosure required", "Insurance must cover geopolitical risk"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a travel advisor. A trip request is under review.",
      user_message: "Thank you for your interest in Moscow. We're currently reviewing the details of your request to ensure we can provide the best possible experience. We'll get back to you within 24 hours with next steps.",
      follow_up_sequence: [],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-BKK-0401": {
    id: "TRP-2026-BKK-0401",
    destination: "Bangkok",
    type: "Group",
    state: "green",
    age: "3d ago",
    createdAt: "2026-04-13T08:00:00Z",
    updatedAt: "2026-04-13T10:00:00Z",
    party: 12,
    dateWindow: "Sep 5–12",
    action: "Booking confirmation pending",
    overdue: false,
    origin: "Mumbai",
    budget: "$8,500",
    customerMessage: "We are a group of 12 friends planning a trip to Bangkok and Pattaya, September 5-12. Mix of sightseeing, street food tours, and nightlife. Some want to visit temples, others want shopping. Budget around $8,500 total for everyone.",
    agentNotes: "Large group — need group booking discounts. Mix of interests so need flexible itinerary. 4 vegetarians in the group. Previous group trip to Goa was successful.",
    packet: {
      facts: {
        destination_candidates: { value: "Bangkok + Pattaya", confidence: 0.92, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Mumbai", confidence: 0.8, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Sep 5–12, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$8,500 total (group)", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "12 (group of friends)", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "group_friends_mixed", confidence: 0.9 },
        dietary_needs: { value: "4 vegetarians", confidence: 0.85 },
        best_value_month: { value: "September (low season)", confidence: 0.9 },
      },
      ambiguities: [
        { field_name: "bangkok_pattaya_split", ambiguity_type: "unspecified_split", raw_value: "Bangkok and Pattaya" },
      ],
      unknowns: [
        { field_name: "room_sharing", reason: "not discussed", notes: "need room allocation" },
      ],
      contradictions: [],
    },
    validation: { is_valid: true, errors: [], warnings: [{ severity: "warning", code: "W007", message: "Large group — book early for availability", field: "party_size" }] },
    decision: {
      decision_state: "PROCEED_TRAVELER_SAFE",
      hard_blockers: [],
      soft_blockers: ["Coordinating 12 people is complex"],
      contradictions: [],
      risk_flags: ["large_group"],
      follow_up_questions: [
        { field_name: "room_allocation", question: "How would you like to split rooms? (twin share, triples, etc.)", priority: "medium", suggested_values: ["6 twin rooms", "4 triple rooms"] },
      ],
      rationale: { hard_blockers: [], soft_blockers: ["Group coordination"], contradictions: [], confidence: 0.82, feasibility: "realistic" },
      confidence_score: 0.82,
      branch_options: ["Bangkok-focused with day trip to Pattaya", "Split stay: 4 nights Bangkok + 3 nights Pattaya"],
      commercial_decision: "Ready to quote — group discount available for 12+",
      budget_breakdown: null,
    },
    strategy: {
      session_goal: "Confirm room allocation and send group quote with itinerary",
      priority_sequence: ["Confirm room split", "Send group hotel options", "Quote street food tour + temple visits", "Arrange group airport transfer"],
      tonal_guardrails: ["Fun and casual tone", "Highlight group deals", "Mention vegetarian options"],
      risk_flags: ["large_group"],
      suggested_opening: "Bangkok with 12 friends is going to be an amazing trip! Let me put together a great group deal for you — we can get some excellent discounts for a party this size.",
      exit_criteria: ["Room allocation confirmed", "Itinerary approved", "Group booking deposit paid"],
      next_action: "Send group booking quote with room options",
      assumptions: ["Twin sharing rooms", "Economy flights", "Group visa on arrival available"],
      suggested_tone: "fun_enthusiastic",
    },
    safety: { leakage_passed: true, strict_leakage: false, leakage_errors: [] },
    internal_bundle: {
      system_context: "Group of 12 friends, Bangkok+Pattaya Sep 5-12. $8.5K group budget. 4 vegetarians. Mixed interests. Group discounts possible.",
      user_message: "Group trip — Bangkok+Pattaya Sep 5-12. 12 pax. Street food + temples + shopping. 4 vegetarians. $8.5K group budget.",
      follow_up_sequence: [{ field_name: "room_allocation", question: "Room sharing preference?", priority: "medium" }],
      branch_prompts: [],
      internal_notes: "Previous Goa trip went well. Consider group booking for better rates. Vegetarian food is easy in Bangkok.",
      constraints: ["Budget $8,500 group total", "4 vegetarians", "Flexible itinerary for mixed interests"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a fun travel advisor helping plan a group trip.",
      user_message: "Bangkok with your friends is going to be epic! We've got some amazing group deals lined up. Let me share the options — there's something for everyone, from temples to street food markets!",
      follow_up_sequence: [{ field_name: "room_allocation", question: "How would you like to split the rooms?", priority: "medium" }],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-PAR-0430": {
    id: "TRP-2026-PAR-0430",
    destination: "Paris",
    type: "Anniversary",
    state: "amber",
    age: "4d ago",
    createdAt: "2026-04-12T08:00:00Z",
    updatedAt: "2026-04-12T10:00:00Z",
    party: 2,
    dateWindow: "Oct 14–21",
    action: "Visa docs incomplete",
    overdue: false,
    origin: "Delhi",
    budget: "$9,500",
    customerMessage: "Planning our 10th wedding anniversary trip to Paris, October 14-21. We want luxury — 5-star hotel near the Seine, Michelin-star dining, and a day trip to Champagne region. Budget is around $9,500.",
    agentNotes: "Repeat luxury clients. Previous trip: Maldives anniversary (rated 5 stars by them). Want the full Parisian luxury experience. Wife loves art — must include Louvre private tour.",
    packet: {
      facts: {
        destination_candidates: { value: "Paris, France", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Delhi", confidence: 0.8, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Oct 14–21, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$9,500", confidence: 0.9, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "2 (couple)", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        hotel_preference: { value: "5-star near Seine", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "luxury_anniversary", confidence: 0.95 },
        schengen_visa: { value: "required — documents incomplete", confidence: 0.9 },
      },
      ambiguities: [],
      unknowns: [],
      contradictions: [],
    },
    validation: { is_valid: true, errors: [], warnings: [{ severity: "warning", code: "W008", message: "Schengen visa docs incomplete — appointment needed ASAP", field: "visa" }] },
    decision: {
      decision_state: "ASK_FOLLOWUP",
      hard_blockers: ["Schengen visa documents incomplete"],
      soft_blockers: [],
      contradictions: [],
      risk_flags: ["visa_incomplete", "high_value"],
      follow_up_questions: [
        { field_name: "visa_documents", question: "Can you share the pending visa documents? The Schengen appointment needs to be booked within the next 2 weeks.", priority: "critical", suggested_values: [] },
      ],
      rationale: { hard_blockers: ["Visa incomplete"], soft_blockers: [], contradictions: [], confidence: 0.65, feasibility: "realistic_if_visa_cleared" },
      confidence_score: 0.65,
      branch_options: ["Proceed with booking (refundable rates)", "Wait for visa confirmation"],
      commercial_decision: "High-value luxury booking — collect visa docs urgently",
      budget_breakdown: null,
    },
    strategy: {
      session_goal: "Urgently collect visa documents and confirm luxury Paris itinerary",
      priority_sequence: ["Get visa documents TODAY", "Book Schengen appointment", "Confirm 5-star hotel (refundable rate)", "Plan Michelin + Champagne experiences"],
      tonal_guardrails: ["Luxury concierge tone", "Create excitement about the experience", "Be urgent but not panicked about visa"],
      risk_flags: ["visa_incomplete", "high_value"],
      suggested_opening: "Happy almost-anniversary! Paris in October is absolutely magical — the autumn colors along the Seine are breathtaking. Let me help make this your most memorable celebration yet.",
      exit_criteria: ["Visa documents complete", "Hotel confirmed", "Dining reservations made"],
      next_action: "Send urgent visa document checklist",
      assumptions: ["Schengen visa eligible", "Budget flexible for luxury experiences"],
      suggested_tone: "luxury_concierge",
    },
    safety: { leakage_passed: true, strict_leakage: false, leakage_errors: [] },
    internal_bundle: {
      system_context: "LUXURY ANNIVERSARY — Paris Oct 14-21. $9.5K. 5-star Seine hotel + Michelin + Champagne. URGENT: Schengen visa docs incomplete. Repeat luxury clients.",
      user_message: "ANNIVERSARY LUXURY — Paris Oct 14-21. 2 pax. 5-star Seine + Michelin dining + Champagne day trip. $9.5K. VISA DOCS INCOMPLETE — urgent collection needed.",
      follow_up_sequence: [{ field_name: "visa_documents", question: "Pending visa docs?", priority: "critical" }],
      branch_prompts: [],
      internal_notes: "Repeat luxury clients (Maldives was 5-star rated). Wife loves art — add Louvre private tour. Book refundable rates until visa clears.",
      constraints: ["Budget $9,500", "5-star only", "Refundable bookings until visa confirmed"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a luxury travel concierge planning an anniversary celebration.",
      user_message: "Paris in October for your 10th anniversary — what a beautiful choice! The city will be dressed in autumn gold, and we have some truly special experiences lined up for you. First, let's get those travel documents sorted so we can lock in the perfect celebration.",
      follow_up_sequence: [{ field_name: "visa_documents", question: "Could you share the outstanding visa documents at your earliest convenience? We want to secure your appointments.", priority: "critical" }],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
  "TRP-2026-NYC-0512": {
    id: "TRP-2026-NYC-0512",
    destination: "New York",
    type: "Family",
    state: "blue",
    age: "6h ago",
    createdAt: "2026-04-16T06:00:00Z",
    updatedAt: "2026-04-16T08:00:00Z",
    party: 5,
    dateWindow: "Dec 20–28",
    action: "Budget clarification needed",
    overdue: false,
    origin: "Mumbai",
    budget: "$18,700",
    customerMessage: "Family of 5 planning a Christmas trip to New York City, Dec 20-28. Want to see the Christmas tree at Rockefeller Center, a Broadway show, and do some shopping. Kids are 14, 11, and 7. We need a budget-friendly place to stay — is $18,700 realistic for everything?",
    agentNotes: "First international trip for the family. Very excited but cost-conscious. Need to manage expectations about NYC Christmas pricing. Kids have varied interests — teen wants Broadway, younger ones want toys and Central Park.",
    packet: {
      facts: {
        destination_candidates: { value: "New York City, USA", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
        origin_city: { value: "Mumbai", confidence: 0.8, authority_level: "inferred", extraction_mode: "derived" },
        date_window: { value: "Dec 20–28, 2026", confidence: 0.95, authority_level: "explicit", extraction_mode: "direct" },
        budget_raw_text: { value: "$18,700 (asking if realistic)", confidence: 0.85, authority_level: "explicit", extraction_mode: "direct" },
        party_size: { value: "5 (2 adults, 3 kids 14/11/7)", confidence: 0.98, authority_level: "explicit", extraction_mode: "direct" },
      },
      derived_signals: {
        trip_style: { value: "family_christmas", confidence: 0.95 },
        peak_pricing: { value: "extreme — Christmas week NYC", confidence: 0.98 },
        first_international: { value: "yes — needs extra hand-holding", confidence: 0.7 },
      },
      ambiguities: [
        { field_name: "budget", ambiguity_type: "uncertain", raw_value: "is $18,700 realistic?" },
      ],
      unknowns: [
        { field_name: "us_visa_status", reason: "not mentioned", notes: "B1/B2 visa needed for Indian passport" },
      ],
      contradictions: [],
    },
    validation: { is_valid: true, errors: [], warnings: [{ severity: "warning", code: "W009", message: "Christmas week is the most expensive time in NYC — budget may be tight", field: "budget" }] },
    decision: {
      decision_state: "ASK_FOLLOWUP",
      hard_blockers: [],
      soft_blockers: ["Christmas week premium pricing", "Budget may be tight for 5 people", "US visa required"],
      contradictions: [],
      risk_flags: ["peak_pricing", "visa_required", "budget_tight"],
      follow_up_questions: [
        { field_name: "budget_flexibility", question: "Is the $18,700 budget firm, or is there flexibility? Christmas week in NYC is the most expensive time of year.", priority: "high", suggested_values: ["Firm at $18,700", "Can go up to $22,000", "Flexible — show options"] },
        { field_name: "us_visa", question: "Do all 5 family members have valid US visas?", priority: "critical", suggested_values: ["Yes, all have visas", "No, need to apply"] },
      ],
      rationale: { hard_blockers: [], soft_blockers: ["Peak pricing", "Budget tight", "Visa unknown"], contradictions: [], confidence: 0.55, feasibility: "borderline" },
      confidence_score: 0.55,
      branch_options: ["Manhattan hotel (premium, tight budget)", "Stay in NJ/Brooklyn (more budget-friendly, commute in)"],
      commercial_decision: "Clarify budget flexibility and visa status before quoting",
      budget_breakdown: null,
    },
    strategy: {
      session_goal: "Clarify budget and visa status, then present Christmas NYC family options",
      priority_sequence: ["Confirm US visa status", "Clarify budget flexibility", "Present hotel options (Manhattan vs outer)", "Plan Broadway + Christmas activities"],
      tonal_guardrails: ["Warm family tone", "Be honest about costs", "Build excitement while managing expectations"],
      risk_flags: ["peak_pricing", "visa_required"],
      suggested_opening: "A Christmas trip to New York with the family — what an incredible experience! The city is absolutely magical during the holidays. Let me help you plan something special while being mindful of your budget.",
      exit_criteria: ["Budget confirmed", "Visa status verified", "Hotel location decided"],
      next_action: "Send budget reality check with two options (premium vs value)",
      assumptions: ["Economy flights", "Indian passport (US visa needed)", "Budget-conscious but willing to pay for key experiences"],
      suggested_tone: "warm_helpful",
    },
    safety: { leakage_passed: true, strict_leakage: false, leakage_errors: [] },
    internal_bundle: {
      system_context: "FAMILY CHRISTMAS NYC — Dec 20-28. 5 pax (2A+3C). $18.7K budget (tight for Xmas week). First international trip. US visa status unknown. Peak pricing EXTREME.",
      user_message: "CHRISTMAS FAMILY TRIP — NYC Dec 20-28. 5 pax. Rockefeller + Broadway + shopping. $18.7K budget (need to clarify if flexible). US visa status TBD. First international trip.",
      follow_up_sequence: [{ field_name: "budget_flexibility", question: "Budget firm or flexible?", priority: "high" }, { field_name: "us_visa", question: "US visa status?", priority: "critical" }],
      branch_prompts: [],
      internal_notes: "First-timers — need extra care. Christmas pricing is brutal. Consider NJ/Brooklyn hotel to save $200/night. Broadway tickets book FAST for Xmas week.",
      constraints: ["Budget around $18,700 (clarify flexibility)", "Family-friendly activities", "Must include Rockefeller + Broadway"],
      audience: "agent",
    },
    traveler_bundle: {
      system_context: "You are a warm travel advisor helping a family plan their first international trip — a Christmas NYC vacation.",
      user_message: "A New York Christmas with the family is going to be absolutely unforgettable! The Rockefeller Center tree, the window displays, Broadway — it's truly the most wonderful time of year in the city. Let me help you make it perfect!",
      follow_up_sequence: [{ field_name: "budget_flexibility", question: "Is your budget flexible, or would you like us to work within the $18,700?", priority: "high" }],
      branch_prompts: [],
      internal_notes: "",
      constraints: [],
      audience: "traveler",
    },
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const trip = MOCK_TRIPS[id];

    if (!trip) {
      return NextResponse.json(
        { error: "Trip not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(trip);
  } catch (error) {
    console.error("Error fetching trip:", error);
    return NextResponse.json(
      { error: "Failed to fetch trip" },
      { status: 500 }
    );
  }
}

const PATCHABLE_FIELDS = new Set([
  "customerMessage",
  "agentNotes",
  "budget",
  "party",
  "dateWindow",
  "origin",
  "destination",
  "type",
  "state",
]);

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const trip = MOCK_TRIPS[id];

    if (!trip) {
      return NextResponse.json(
        { error: "Trip not found" },
        { status: 404 }
      );
    }

    const body = await request.json();
    const updates: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(body)) {
      if (PATCHABLE_FIELDS.has(key)) {
        updates[key] = value;
      }
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json(
        { error: "No patchable fields provided" },
        { status: 400 }
      );
    }

    Object.assign(trip, updates, { updatedAt: new Date().toISOString() });

    return NextResponse.json(trip);
  } catch (error) {
    console.error("Error patching trip:", error);
    return NextResponse.json(
      { error: "Failed to update trip" },
      { status: 500 }
    );
  }
}
