'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { 
  Users, 
  CreditCard, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  Building2, 
  Sparkles,
  ExternalLink,
  Utensils,
  Bed,
  Globe
} from 'lucide-react';

interface PassengerShareData {
  ok: boolean;
  trip_id: string;
  destination: string;
  passenger_id: string;
  passenger_name: string;
  deposit_share_cents: number;
  agency_payment_url?: string;
  payment_instructions?: string;
  status: string;
  collected_preferences?: {
    dietary_requirements?: string;
    room_preference?: string;
    passport_country?: string;
  };
}

export default function PublicGroupSharePage() {
  const params = useParams();
  const token = params?.token as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PassengerShareData | null>(null);

  // Form states
  const [dietary, setDietary] = useState('');
  const [roomPref, setRoomPref] = useState('');
  const [passportCountry, setPassportCountry] = useState('');
  const [paymentRef, setPaymentRef] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submittedSuccess, setSubmittedSuccess] = useState(false);

  useEffect(() => {
    if (!token) return;

    fetch(`/api/v1/group/token/${token}`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error('Invalid or expired group invite link');
        }
        return res.json();
      })
      .then((shareData: PassengerShareData) => {
        setData(shareData);
        if (shareData.collected_preferences) {
          setDietary(shareData.collected_preferences.dietary_requirements || '');
          setRoomPref(shareData.collected_preferences.room_preference || '');
          setPassportCountry(shareData.collected_preferences.passport_country || '');
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load group invite');
        setLoading(false);
      });
  }, [token]);

  const handleSubmitNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setSubmitting(true);
    try {
      const res = await fetch(`/api/v1/group/token/${token}/pay-share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_reference: paymentRef || undefined,
          dietary_requirements: dietary || undefined,
          room_preference: roomPref || undefined,
          passport_country: passportCountry || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to record payment notification');
      }

      setSubmittedSuccess(true);
      if (data) {
        setData({ ...data, status: 'NOTIFIED_PAID' });
      }
    } catch (err: any) {
      alert(err.message || 'Submission error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="flex items-center space-x-3 bg-slate-900/80 border border-slate-800 rounded-xl p-6 backdrop-blur-md">
          <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium text-slate-300">Loading Group Invite...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 border border-red-900/40 rounded-2xl p-8 text-center shadow-xl">
          <div className="w-12 h-12 rounded-full bg-red-950/60 border border-red-800 flex items-center justify-center mx-auto mb-4 text-red-400">
            !
          </div>
          <h2 className="text-xl font-semibold text-slate-100 mb-2">Group Invite Not Found</h2>
          <p className="text-sm text-slate-400 mb-6">{error || 'This group invite link is invalid or has expired.'}</p>
        </div>
      </div>
    );
  }

  const depositAmount = (data.deposit_share_cents / 100).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const isConfirmed = data.status === 'CONFIRMED' || data.status === 'WAIVED';
  const isNotified = data.status === 'NOTIFIED_PAID';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      {/* Header Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Users className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm tracking-wide text-slate-200 uppercase">
              Group Deposit Portal
            </span>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 bg-emerald-950/50 border border-emerald-800/40 px-3 py-1.5 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Secure Agency Link</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Banner Section */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 p-8 shadow-2xl">
          <div className="relative z-10 space-y-4">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 font-mono">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>{data.destination}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Welcome, {data.passenger_name}
            </h1>
            <p className="text-slate-400 max-w-xl text-sm leading-relaxed">
              You are invited to join the group trip to <strong className="text-slate-200">{data.destination}</strong>. 
              Please review your deposit share details below, complete your preferences, and confirm your share.
            </p>
          </div>
        </div>

        {/* Deposit Summary & Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Share Amount Card */}
          <div className="md:col-span-2 bg-slate-900/70 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div className="space-y-1">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                Your Per-Passenger Deposit Share
              </span>
              <div className="text-4xl font-extrabold text-emerald-400 font-mono">
                {depositAmount}
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-4">
              Calculated for individual attendee contribution. External agency payment links or bank transfer instructions provided by your advisor are supported.
            </p>
          </div>

          {/* Status Card */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Payment Status
            </span>
            <div className="my-3">
              {isConfirmed ? (
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-sm font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Confirmed & Received</span>
                </div>
              ) : isNotified ? (
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-950/80 border border-amber-800 text-amber-300 text-sm font-medium">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <span>Pending Advisor Verification</span>
                </div>
              ) : (
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-sm font-medium">
                  <CreditCard className="w-4 h-4 text-slate-400" />
                  <span>Payment Pending</span>
                </div>
              )}
            </div>
            <span className="text-xs text-slate-400">
              Status updates automatically upon advisor confirmation.
            </span>
          </div>
        </div>

        {/* Agency Payment Options */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 space-y-6">
          <div className="flex items-center space-x-3">
            <Building2 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">Agency Payment Instructions</h2>
          </div>

          {data.agency_payment_url && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 space-y-3">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Direct Agency Payment Link
              </div>
              <p className="text-sm text-slate-300">
                Click below to complete your deposit payment via your travel agency’s secure portal:
              </p>
              <a
                href={data.agency_payment_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-colors"
              >
                <span>Pay Deposit Share via External Link</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}

          {data.payment_instructions && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 space-y-2">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Bank / Offline Instructions
              </div>
              <p className="text-sm text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                {data.payment_instructions}
              </p>
            </div>
          )}
        </div>

        {/* Preferences & Completion Form */}
        <form onSubmit={handleSubmitNotification} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-semibold text-white">Passenger Details & Notification</h2>
            <p className="text-xs text-slate-400">
              Provide your travel preferences and let your advisor know once you’ve completed your share.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-2">
                <Utensils className="w-3.5 h-3.5 text-slate-400" />
                <span>Dietary Requirements</span>
              </label>
              <input
                type="text"
                value={dietary}
                onChange={(e) => setDietary(e.target.value)}
                placeholder="e.g. Vegetarian, Gluten-free, Nut allergy"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-2">
                <Bed className="w-3.5 h-3.5 text-slate-400" />
                <span>Room & Bedding Preferences</span>
              </label>
              <input
                type="text"
                value={roomPref}
                onChange={(e) => setRoomPref(e.target.value)}
                placeholder="e.g. King Bed, Quiet room, Ocean view"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-2">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <span>Passport Issuing Country</span>
              </label>
              <input
                type="text"
                value={passportCountry}
                onChange={(e) => setPassportCountry(e.target.value)}
                placeholder="e.g. United States, United Kingdom"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-2">
                <CreditCard className="w-3.5 h-3.5 text-slate-400" />
                <span>Payment Reference / Notes (Optional)</span>
              </label>
              <input
                type="text"
                value={paymentRef}
                onChange={(e) => setPaymentRef(e.target.value)}
                placeholder="e.g. Stripe Receipt #1234 or Wire Ref"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              />
            </div>
          </div>

          <div className="pt-4 flex items-center justify-between border-t border-slate-800">
            {submittedSuccess ? (
              <div className="flex items-center space-x-2 text-emerald-400 text-sm font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Advisor Notified! Your preferences and payment notification were sent.</span>
              </div>
            ) : (
              <button
                type="submit"
                disabled={submitting}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold text-sm transition-colors"
              >
                {submitting ? 'Submitting...' : 'Notify Advisor & Save Preferences'}
              </button>
            )}
          </div>
        </form>
      </main>
    </div>
  );
}
