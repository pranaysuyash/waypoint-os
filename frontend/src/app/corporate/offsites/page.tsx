'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle2, Clock, Plane, Building, Users, FileText, ArrowRight, DollarSign } from 'lucide-react';

export default function CorporateOffsitesPage() {
  const [dutyOfCare, setDutyOfCare] = useState<any | null>(null);
  const [policyAudit, setPolicyAudit] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      try {
        const [docRes, auditRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/corporate/duty-of-care/cockpit?company_id=comp_techcorp_01`),
          fetch(`${apiUrl}/api/v1/corporate/policy-audit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              trip_id: 'trip_zrh_offsite_01',
              destination: 'Zurich',
              city_code: 'ZRH',
              hotel_rate_per_night: 420.0,
              cabin_class: 'BUSINESS',
              employee_grade: 'JUNIOR',
            }),
          }),
        ]);

        if (docRes.ok) {
          const docData = await docRes.json();
          setDutyOfCare(docData);
        }
        if (auditRes.ok) {
          const auditData = await auditRes.json();
          setPolicyAudit(auditData);
        }
      } catch (err) {
        // Fallback demo data
        setDutyOfCare({
          ok: true,
          company_id: 'comp_techcorp_01',
          group_offsite_title: 'Q3 Zurich Executive Leadership Offsite',
          total_active_travelers: 3,
          disrupted_count: 1,
          travelers: [
            {
              traveler_id: 'exec_01',
              traveler_name: 'Vikram Sethi (VP Eng)',
              origin: 'SFO',
              destination: 'ZRH',
              flight_pnr: 'LX18',
              flight_status: 'ON_SCHEDULE',
              hotel_name: 'The Dolder Grand Zurich',
              risk_level: 'LOW',
            },
            {
              traveler_id: 'exec_02',
              traveler_name: 'Sarah Miller (Dir Product)',
              origin: 'LHR',
              destination: 'ZRH',
              flight_pnr: 'BA710',
              flight_status: 'DELAYED_90M',
              hotel_name: 'The Dolder Grand Zurich',
              risk_level: 'MEDIUM',
              recommended_action: 'Ground Transfer #1 rescheduled to 18:30. Concierge standing by.',
            },
          ],
          duty_of_care_sla_status: 'ACTIVE_PROTECTED',
        });
        setPolicyAudit({
          ok: true,
          is_compliant: false,
          requires_approval: true,
          violations: [
            {
              code: 'PER_DIEM_EXCEEDED',
              severity: 'WARNING',
              description: 'Hotel rate £420.00/night exceeds ZRH policy cap of £400.00/night by £20.00.',
              amount_exceeded: 20.0,
              currency: 'GBP',
            },
            {
              code: 'CABIN_CLASS_DISCREPANCY',
              severity: 'HARD_BLOCK',
              description: 'JUNIOR grade is restricted to ECONOMY cabin. BUSINESS requested.',
              amount_exceeded: 0.0,
              currency: 'GBP',
            },
          ],
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/70 border border-blue-700/60 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <Building className="w-3.5 h-3.5" /> Corporate Travel Cockpit
            </div>
            <h1 className="text-3xl font-extrabold text-white">
              {dutyOfCare?.group_offsite_title || 'Executive Leadership Offsite'}
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Duty-of-Care Flight Tracker & Per-Diem Policy Compliance Engine
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg bg-emerald-950 border border-emerald-700 text-emerald-400 text-xs font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> Duty-of-Care SLA: Active
            </span>
          </div>
        </div>

        {/* Section 1: Executive Flight Duty-of-Care Tracker */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Plane className="w-5 h-5 text-cyan-400" /> Multi-Executive Flight Synchronization
            </h2>
            <span className="text-xs text-slate-400">
              Total Executives: <strong className="text-slate-200">{dutyOfCare?.total_active_travelers || 0}</strong>
            </span>
          </div>

          <div className="space-y-4">
            {dutyOfCare?.travelers?.map((t: any) => (
              <div
                key={t.traveler_id}
                className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="font-semibold text-slate-100 text-sm">{t.traveler_name}</div>
                  <div className="text-xs text-slate-400 flex items-center gap-2">
                    <span>Flight: <strong className="text-slate-300">{t.flight_pnr}</strong> ({t.origin} → {t.destination})</span>
                    <span>•</span>
                    <span>{t.hotel_name}</span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {t.flight_status.includes('DELAYED') ? (
                    <div className="px-3 py-1 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-300 text-xs font-semibold flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Delayed 90m (Shuttle Auto-Rescheduled)
                    </div>
                  ) : (
                    <div className="px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> On Schedule
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 2: Policy Compliance & Override Audit */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" /> Corporate Policy Audit Engine
            </h2>
            <span className="px-2.5 py-1 rounded-md bg-amber-950/80 border border-amber-700 text-amber-300 text-xs font-semibold">
              Approval Required
            </span>
          </div>

          <div className="space-y-3">
            {policyAudit?.violations?.map((v: any, idx: number) => (
              <div
                key={idx}
                className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 flex items-start justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="text-xs font-mono font-bold text-amber-400">{v.code}</div>
                  <div className="text-xs text-slate-300">{v.description}</div>
                </div>
                <button
                  type="button"
                  className="px-3 py-1.5 rounded-lg bg-indigo-950 border border-indigo-700 text-indigo-300 text-xs font-medium hover:bg-indigo-900 transition"
                >
                  Request EA Override
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
