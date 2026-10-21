'use client';

import { useState, useEffect, FormEvent } from 'react';
import { CheckCircle, MessageCircleQuestion, Send } from 'lucide-react';

// FND-0301: traveler answer surface for the ask loop. Token-gated like the
// public proposal (same signed-token machinery); the backend only accepts
// answers to questions it actually asked, and records them with
// authority=explicit_user for the next decision run.

interface AskQuestion {
  field_name: string;
  question: string;
  priority: string;
}

interface AskData {
  token: string;
  trip_id: string;
  destination?: string;
  status: string;
  questions: AskQuestion[];
  asked_count: number;
}

type SubmitState = 'idle' | 'submitting' | 'done' | 'error';

export default function TravelerAskPage({ params }: { params: { token: string } }) {
  const token = params.token;

  const [ask, setAsk] = useState<AskData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [respondentName, setRespondentName] = useState('');
  const [submitState, setSubmitState] = useState<SubmitState>('idle');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAsk() {
      try {
        const res = await fetch(`/api/public/asks/${token}`);
        if (res.ok) {
          const data = (await res.json()) as AskData;
          setAsk(data);
        } else if (res.status === 410) {
          setLoadError('This question link has expired or was revoked. Please ask your travel advisor for a fresh link.');
        } else {
          setLoadError('We could not load this question link. Please ask your travel advisor for assistance.');
        }
      } catch {
        setLoadError('Something went wrong loading this page. Please try again.');
      } finally {
        setLoading(false);
      }
    }
    loadAsk();
  }, [token]);

  const openQuestions = ask?.questions ?? [];

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!ask) return;
    const payload = openQuestions
      .map((q) => ({ field_name: q.field_name, answer: (answers[q.field_name] ?? '').trim(), question: q.question }))
      .filter((a) => a.answer.length > 0);
    if (payload.length === 0) return;

    setSubmitState('submitting');
    setSubmitError(null);
    try {
      const res = await fetch(`/api/public/asks/${token}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answers: payload,
          respondent_name: respondentName.trim() || undefined,
        }),
      });
      if (res.ok) {
        setSubmitState('done');
      } else {
        const detail = await res.json().catch(() => null);
        setSubmitError(detail?.detail ?? 'Your answers could not be saved. Please try again.');
        setSubmitState('error');
      }
    } catch {
      setSubmitError('Your answers could not be saved. Please try again.');
      setSubmitState('error');
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-6">
        <p className="text-sm text-[#8b949e]">Loading your questions…</p>
      </main>
    );
  }

  if (loadError || !ask) {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <MessageCircleQuestion className="size-10 text-[#8b949e] mx-auto mb-4" />
          <h1 className="text-xl font-bold text-white mb-2">Questions unavailable</h1>
          <p className="text-sm text-[#8b949e]">{loadError}</p>
        </div>
      </main>
    );
  }

  if (submitState === 'done') {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-6">
        <div className="max-w-md text-center" data-testid="ask-thankyou">
          <CheckCircle className="size-12 text-[#3fb950] mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Thank you!</h1>
          <p className="text-sm text-[#8b949e]">
            Your answers are with your travel advisor{ask.destination ? ` — your ${ask.destination} plan will be updated shortly` : ''}.
          </p>
        </div>
      </main>
    );
  }

  if (openQuestions.length === 0) {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <CheckCircle className="size-10 text-[#3fb950] mx-auto mb-4" />
          <h1 className="text-xl font-bold text-white mb-2">All set</h1>
          <p className="text-sm text-[#8b949e]">There are no open questions right now.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0d1117] text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <header className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <MessageCircleQuestion className="size-5 text-[#58a6ff]" />
            <span className="text-xs uppercase tracking-widest text-[#8b949e]">
              {ask.destination ? `Planning your ${ask.destination} trip` : 'Planning your trip'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">
            A few quick questions
          </h1>
          <p className="text-sm text-[#8b949e]">
            Your travel advisor needs these details to finish your plan. Answer what you can —
            nothing here is mandatory.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-5" data-testid="ask-form">
          {openQuestions.map((q, idx) => (
            <div key={q.field_name} className="rounded-xl border border-[#30363d] bg-[#161b22] p-5">
              <label htmlFor={`ask-${idx}`} className="block text-sm font-medium text-white mb-2">
                {q.question}
              </label>
              <textarea
                id={`ask-${idx}`}
                rows={2}
                value={answers[q.field_name] ?? ''}
                onChange={(e) => setAnswers((prev) => ({ ...prev, [q.field_name]: e.target.value }))}
                placeholder="Type your answer…"
                className="w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-sm text-white placeholder:text-[#484f58] focus:border-[#58a6ff] focus:outline-none"
              />
            </div>
          ))}

          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5">
            <label htmlFor="respondent" className="block text-sm font-medium text-white mb-2">
              Your name <span className="text-[#484f58] font-normal">(optional)</span>
            </label>
            <input
              id="respondent"
              value={respondentName}
              onChange={(e) => setRespondentName(e.target.value)}
              placeholder="So your advisor knows who answered"
              className="w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-sm text-white placeholder:text-[#484f58] focus:border-[#58a6ff] focus:outline-none"
            />
          </div>

          {submitError && (
            <div role="alert" data-testid="ask-submit-error" className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
              {submitError}
            </div>
          )}

          <button
            type="submit"
            disabled={submitState === 'submitting'}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#58a6ff] px-6 py-3 text-sm font-semibold text-[#0d1117] transition-colors hover:bg-[#79b8ff] disabled:opacity-60 sm:w-auto"
          >
            <Send className="size-4" />
            {submitState === 'submitting' ? 'Sending…' : 'Send answers'}
          </button>
        </form>
      </div>
    </main>
  );
}
