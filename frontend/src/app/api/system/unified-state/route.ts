import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * Unified State API - Next.js Fallback/Proxy
 * 
 * Mandate: Provide a Single Source of Truth for the dashboard.
 * If the spine-api (Python) is not available or hasn't reloaded,
 * this route provides the same aggregation logic to ensure system integrity.
 */
export async function GET() {
  try {
    // 1. Attempt to proxy to the canonical Python backend
    try {
      const response = await fetch('http://localhost:8000/api/system/unified-state', {
        next: { revalidate: 0 } // No cache
      });
      
      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (e) {
      console.warn('Spine API (Python) unreachable, falling back to local aggregation.');
    }

    // 2. Fallback: Direct aggregation from data/trips
    // process.cwd() is usually the root of the nextjs app (frontend/)
    const TRIPS_DIR = path.join(process.cwd(), '..', 'data', 'trips');
    const VALID_STAGES = ["new", "assigned", "in_progress", "completed", "cancelled"];
    
    if (!fs.existsSync(TRIPS_DIR)) {
       return NextResponse.json({
         canonical_total: 0,
         stages: VALID_STAGES.reduce((acc, s) => ({ ...acc, [s]: 0 }), {}),
         sla_breached: 0,
         orphans: [],
         meta: { source: 'fallback', error: 'Trips directory not found' }
       });
    }

    const files = fs.readdirSync(TRIPS_DIR).filter(f => f.startsWith('trip_') && f.endsWith('.json'));
    
    let canonical_total = files.length;
    let stages: Record<string, number> = VALID_STAGES.reduce((acc, s) => ({ ...acc, [s]: 0 }), {});
    let orphans: any[] = [];
    let sla_breached = 0;
    const now = new Date();

    files.forEach(file => {
      try {
        const content = fs.readFileSync(path.join(TRIPS_DIR, file), 'utf-8');
        const trip = JSON.parse(content);
        const status = trip.status;
        
        if (VALID_STAGES.includes(status)) {
          stages[status]++;
        } else {
          orphans.push({
            id: trip.id || file,
            destination: trip.extracted?.trip_metadata?.destination || 'Unknown',
            created_at: trip.created_at || 'Unknown'
          });
        }

        // SLA Breach Detection (Fallback)
        if (trip.created_at) {
          const createdAt = new Date(trip.created_at);
          const ageHours = (now.getTime() - createdAt.getTime()) / (1000 * 60 * 60);
          
          if (status === 'new' && ageHours > 4) {
            sla_breached++;
          } else if (status === 'assigned' && ageHours > 24) {
            sla_breached++;
          }
        }
      } catch (e) {
        orphans.push({ id: file, error: 'Parse failure' });
      }
    });

    return NextResponse.json({
      canonical_total,
      stages,
      sla_breached,
      orphans,
      integrity_meta: {
        sum_stages: Object.values(stages).reduce((a, b) => a + b, 0),
        orphan_count: orphans.length,
        consistent: (Object.values(stages).reduce((a, b) => a + b, 0) + orphans.length === canonical_total)
      },
      meta: { source: 'fallback_nextjs' }
    });

  } catch (error) {
    console.error('Unified State Fallback Error:', error);
    return NextResponse.json({ error: 'Integrity Failure' }, { status: 500 });
  }
}
