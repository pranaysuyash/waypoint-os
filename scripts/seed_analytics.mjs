import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRIPS_DIR = path.join(__dirname, '../data/trips');

// Ensure directory exists
if (!fs.existsSync(TRIPS_DIR)) {
  fs.mkdirSync(TRIPS_DIR, { recursive: true });
}

const destinations = ["Maldives", "Paris", "New York", "Dubai", "Swiss Alps", "Tokyo", "Bali", "Safari (Kenya)"];
const tripTypes = ["Honeymoon", "Family", "Corporate", "Solo", "Adventure", "Luxury"];
const statuses = ["new", "assigned", "in_progress", "completed", "cancelled"];

function seedTrips(num = 15) {
  console.log(`Seeding ${num} trips via Node.js fallback...`);

  for (let i = 0; i < num; i++) {
    const tripId = `trip_seed_${crypto.randomBytes(4).toString('hex')}`;
    const destination = destinations[Math.floor(Math.random() * destinations.length)];
    const type = tripTypes[Math.floor(Math.random() * tripTypes.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const value = Math.floor(Math.random() * 750000) + 50000;
    const margin = parseFloat((Math.random() * 20 + 10).toFixed(1)); // 10-30%
    
    const trip = {
      id: tripId,
      run_id: `run_${crypto.randomBytes(4).toString('hex')}`,
      source: "seed_script_node",
      status: status,
      created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      extracted: {
        trip_metadata: { destination, primary_intent: type, date_window: "Sometime next month" },
        party_profile: { size: Math.floor(Math.random() * 6) + 1 },
        budget: { value }
      },
      decision: { action: "PROCEED" },
      analytics: {
        margin_pct: margin,
        quality_score: Math.floor(Math.random() * 40) + 60,
        quality_breakdown: {
          completeness: 80, feasibility: 90, risk: 95, profitability: 70
        },
        requires_review: value > 500000 || margin < 15,
        review_reason: value > 500000 ? "High value" : (margin < 15 ? "Low margin" : null)
      }
    };

    fs.writeFileSync(path.join(TRIPS_DIR, `${tripId}.json`), JSON.stringify(trip, null, 2));
  }

  console.log("Seeding complete.");
}

seedTrips();
