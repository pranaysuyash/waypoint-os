'use client';

/**
 * Destination Intelligence — operator workbench surface for the governed
 * external-data stack (2026-10-30 tranche). Two cards:
 *   1. Safety verdict — government advisory band (C1 gate) + optional
 *      national homicide rate; coverage gaps listed honestly.
 *   2. Trip-date weather — forecast within the horizon, ERA5 climate
 *      baseline beyond it (the mode label says which).
 * Plus anonymized traveler ratings from the federated pool.
 * Every value comes from the backend; unavailable data says so — the
 * gate never fabricates (unverifiable is a verdict, not an error).
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, CloudSun, Star } from 'lucide-react';
import {
  getSafetyVerdict,
  getWeatherSuitability,
  getDestinationRatings,
  submitDestinationRating,
} from '@/lib/api-client';

const BAND_STYLE: Record<string, { color: string; emoji: string }> = {
  '1': { color: 'var(--accent-green, #3fb950)', emoji: '🟢' },
  '2': { color: 'var(--accent-yellow, #d29922)', emoji: '🟡' },
  '3': { color: 'var(--accent-orange, #db6d28)', emoji: '🟠' },
  '4': { color: 'var(--accent-red, #f85149)', emoji: '🔴' },
};

const VERDICT_STYLE: Record<string, string> = {
  green: 'var(--accent-green, #3fb950)',
  yellow: 'var(--accent-yellow, #d29922)',
  red: 'var(--accent-red, #f85149)',
};

function Card({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className='relative rounded-xl border p-4 flex flex-col gap-3'>
      <div className='flex items-center justify-between'>
        <span className='text-[12px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
          {title}
        </span>
        {icon}
      </div>
      {children}
    </section>
  );
}

export default function DestinationIntelligencePageClient() {
  const [country, setCountry] = useState('');
  const [submittedCountry, setSubmittedCountry] = useState('');

  const [lat, setLat] = useState('13.7563');
  const [lng, setLng] = useState('100.5018');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [activity, setActivity] = useState('city');
  const [submittedWeather, setSubmittedWeather] = useState<{ lat: number; lng: number; s: string; e: string; activity: string } | null>(null);

  const safety = useQuery({
    queryKey: ['safety-verdict', submittedCountry],
    queryFn: () => getSafetyVerdict(submittedCountry),
    enabled: submittedCountry.length > 0,
    staleTime: 60 * 60 * 1000,
  });

  const weather = useQuery({
    queryKey: ['weather-suitability', submittedWeather],
    queryFn: () =>
      getWeatherSuitability({
        lat: Number(submittedWeather!.lat),
        lng: Number(submittedWeather!.lng),
        start_date: submittedWeather!.s,
        end_date: submittedWeather!.e,
        activity: submittedWeather!.activity,
      }),
    enabled: !!submittedWeather,
    staleTime: 10 * 60 * 1000,
  });

  const ratings = useQuery({
    queryKey: ['destination-ratings', submittedCountry],
    queryFn: () => getDestinationRatings(submittedCountry),
    enabled: submittedCountry.length > 0,
    staleTime: 10 * 60 * 1000,
  });

  // Contribution form (TRV-DP-07: consent is explicit per submission)
  const [ratingDim, setRatingDim] = useState('safety');
  const [ratingScore, setRatingScore] = useState(5);
  const [ratingNote, setRatingNote] = useState('');
  const [ratingConsent, setRatingConsent] = useState(false);
  const queryClient = useQueryClient();
  const contribution = useMutation({
    mutationFn: () =>
      submitDestinationRating(submittedCountry, {
        dimension: ratingDim,
        score: ratingScore,
        consent: ratingConsent,
        note: ratingNote || undefined,
      }),
    onSuccess: () => {
      setRatingNote('');
      setRatingConsent(false);
      queryClient.invalidateQueries({ queryKey: ['destination-ratings', submittedCountry] });
    },
  });

  const bandStyle = safety.data ? BAND_STYLE[safety.data.band] ?? BAND_STYLE['2'] : null;

  return (
    <div className='p-6 flex flex-col gap-6 max-w-3xl'>
      <header>
        <h1 className='text-lg font-semibold' style={{ color: 'var(--text-primary)' }}>
          Destination Intelligence
        </h1>
        <p className='text-[13px]' style={{ color: 'var(--text-tertiary)' }}>
          Governed external data — every value carries its source and fetch time. Missing data is shown as a gap, never guessed.
        </p>
      </header>

      {/* ── Safety verdict ── */}
      <Card title='Safety verdict (government advisories)' icon={<ShieldAlert className='size-4' style={{ color: 'var(--text-tertiary)' }} />}>
        <form
          className='flex gap-2'
          onSubmit={(e) => {
            e.preventDefault();
            setSubmittedCountry(country.trim().toLowerCase());
          }}
        >
          <input
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder='Country (e.g. japan, russia)'
            className='flex-1 rounded-md border bg-transparent px-3 py-2 text-[13px]'
            style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }}
          />
          <button type='submit' className='rounded-md border px-4 py-2 text-[13px] font-medium' style={{ color: 'var(--text-primary)' }}>
            Check
          </button>
        </form>

        {safety.isFetching && <p className='text-[13px]' style={{ color: 'var(--text-tertiary)' }}>Fetching advisory…</p>}
        {safety.isError && (
          <p className='text-[13px]' style={{ color: 'var(--accent-red, #f85149)' }}>
            Advisory source unavailable right now — shown as a gap, not guessed.
          </p>
        )}
        {safety.data && (
          <div className='flex flex-col gap-2'>
            <div className='flex items-center gap-3'>
              <span className='text-2xl'>{bandStyle?.emoji}</span>
              <span className='text-[15px] font-semibold' style={{ color: bandStyle?.color }}>
                {safety.data.label}
              </span>
              <span className='text-[12px]' style={{ color: 'var(--text-tertiary)' }}>
                band {safety.data.band} {safety.data.cached ? '· cached' : ''}
              </span>
            </div>
            <p className='text-[12px]' style={{ color: 'var(--text-tertiary)' }}>
              Covered: {safety.data.coverage.join(', ')}
              {safety.data.coverage_gaps.length > 0 && <> · gaps: {safety.data.coverage_gaps.join(', ')}</>}
            </p>
          </div>
        )}
        {submittedCountry && ratings.data && (
          <p className='text-[12px]' style={{ color: 'var(--text-tertiary)' }}>
            <Star className='inline size-3' /> Traveler ratings:{' '}
            {ratings.data.total_ratings === 0
              ? 'no contributions yet'
              : Object.entries(ratings.data.dimensions)
                  .map(([dim, d]) => `${dim} ${d.mean}/5 (${d.count})`)
                  .join(', ')}
          </p>
        )}
        {submittedCountry && (
          <div className='flex flex-col gap-2 border-t pt-3' style={{ borderColor: 'var(--border-subtle, #30363d)' }}>
            <span className='text-[12px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
              Add a client's rating (anonymized)
            </span>
            <div className='flex flex-wrap gap-2 items-center'>
              <select
                value={ratingDim}
                onChange={(e) => setRatingDim(e.target.value)}
                className='rounded-md border bg-transparent px-2 py-1.5 text-[13px]'
                style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }}
              >
                <option value='safety'>safety</option>
                <option value='value'>value</option>
                <option value='family_fit'>family fit</option>
                <option value='food'>food</option>
                <option value='transport'>transport</option>
                <option value='connectivity'>connectivity</option>
              </select>
              <select
                value={ratingScore}
                onChange={(e) => setRatingScore(Number(e.target.value))}
                className='rounded-md border bg-transparent px-2 py-1.5 text-[13px]'
                style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }}
              >
                {[5, 4, 3, 2, 1].map((s) => (
                  <option key={s} value={s}>{s}/5</option>
                ))}
              </select>
              <input
                value={ratingNote}
                onChange={(e) => setRatingNote(e.target.value)}
                maxLength={280}
                placeholder='Optional note — no personal details (contacts auto-removed)'
                className='flex-1 min-w-[200px] rounded-md border bg-transparent px-3 py-1.5 text-[13px]'
                style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }}
              />
              <button
                type='button'
                disabled={!ratingConsent || contribution.isPending}
                className='rounded-md border px-3 py-1.5 text-[13px] font-medium disabled:opacity-40'
                style={{ color: 'var(--text-primary)' }}
                onClick={() => contribution.mutate()}
              >
                {contribution.isPending ? 'Submitting…' : 'Submit'}
              </button>
            </div>
            <label className='flex items-center gap-2 text-[12px]' style={{ color: 'var(--text-tertiary)' }}>
              <input type='checkbox' checked={ratingConsent} onChange={(e) => setRatingConsent(e.target.checked)} />
              Traveler consented to an anonymous contribution (stored without agency identity; contacts auto-removed).
            </label>
            {contribution.isError && (
              <p className='text-[12px]' style={{ color: 'var(--accent-red, #f85149)' }}>
                {contribution.error instanceof Error ? contribution.error.message : 'Submission failed.'}
              </p>
            )}
            {contribution.isSuccess && (
              <p className='text-[12px]' style={{ color: 'var(--accent-green, #3fb950)' }}>
                Contribution recorded anonymously — thank you.
              </p>
            )}
          </div>
        )}
      </Card>

      {/* ── Trip-date weather ── */}
      <Card title='Trip-date weather' icon={<CloudSun className='size-4' style={{ color: 'var(--text-tertiary)' }} />}>
        <div className='flex flex-wrap gap-2 items-center'>
          <input value={lat} onChange={(e) => setLat(e.target.value)} placeholder='lat' className='w-24 rounded-md border bg-transparent px-2 py-2 text-[13px]' style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }} />
          <input value={lng} onChange={(e) => setLng(e.target.value)} placeholder='lng' className='w-24 rounded-md border bg-transparent px-2 py-2 text-[13px]' style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }} />
          <input type='date' value={startDate} onChange={(e) => setStartDate(e.target.value)} className='rounded-md border bg-transparent px-2 py-2 text-[13px]' style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }} />
          <input type='date' value={endDate} onChange={(e) => setEndDate(e.target.value)} className='rounded-md border bg-transparent px-2 py-2 text-[13px]' style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }} />
          <select value={activity} onChange={(e) => setActivity(e.target.value)} className='rounded-md border bg-transparent px-2 py-2 text-[13px]' style={{ color: 'var(--text-primary)', borderColor: 'var(--border-subtle, #30363d)' }}>
            <option value='city'>city</option>
            <option value='beach'>beach</option>
            <option value='hiking'>hiking</option>
          </select>
          <button
            type='button'
            className='rounded-md border px-4 py-2 text-[13px] font-medium'
            style={{ color: 'var(--text-primary)' }}
            onClick={() => {
              if (startDate && endDate) setSubmittedWeather({ lat: Number(lat), lng: Number(lng), s: startDate, e: endDate, activity });
            }}
          >
            Grade
          </button>
        </div>

        {weather.isFetching && <p className='text-[13px]' style={{ color: 'var(--text-tertiary)' }}>Grading…</p>}
        {weather.data && (
          <div className='flex flex-col gap-2'>
            <p className='text-[13px]'>
              <span className='font-semibold' style={{ color: VERDICT_STYLE[weather.data.verdict ?? 'green'] ?? 'var(--text-primary)' }}>
                {weather.data.verdict === 'red' ? '🔴 Red' : weather.data.verdict === 'yellow' ? '🟡 Yellow' : weather.data.verdict === 'green' ? '🟢 Green' : 'White'}
              </span>{' '}
              <span style={{ color: 'var(--text-tertiary)' }}>
                ({weather.data.mode === 'climate_baseline' ? 'climate baseline' : 'live forecast'} · {weather.data.activity})
              </span>
            </p>
            {weather.data.confidence_note && (
              <p className='text-[12px]' style={{ color: 'var(--text-tertiary)' }}>
                {weather.data.confidence_note}
              </p>
            )}
            {weather.data.days && weather.data.days.length > 0 && (
              <ul className='text-[12px] flex flex-col gap-1' style={{ color: 'var(--text-secondary)' }}>
                {weather.data.days.map((d) => {
                  const day = d as { date: string; verdict: string; tmax_c?: number | null; uv_note?: string };
                  return (
                    <li key={day.date}>
                      {day.date}: {day.verdict === 'unverifiable' ? 'beyond forecast horizon' : `${day.verdict}${day.tmax_c != null ? ` · ${day.tmax_c}°C` : ''}${day.uv_note ? ` · ${day.uv_note}` : ''}`}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
