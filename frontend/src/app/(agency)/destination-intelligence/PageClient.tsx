'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ShieldAlert, Sun, CloudRain, Star, MapPin } from 'lucide-react';
import {
  getSafetyVerdict,
  getWeatherSuitability,
  getDestinationRatings,
  submitDestinationRating,
} from '@/lib/api-client';
import type {
  SafetyVerdict,
  WeatherSuitability,
  DestinationRatings,
} from '@/lib/api-client';

interface DestinationPreset {
  label: string;
  countrySlug: string;
  lat: string;
  lng: string;
  activity: 'beach' | 'city' | 'hiking';
}

const DESTINATION_PRESETS: DestinationPreset[] = [
  { label: 'Bangkok, TH', countrySlug: 'thailand', lat: '13.7563', lng: '100.5018', activity: 'city' },
  { label: 'Tokyo, JP', countrySlug: 'japan', lat: '35.6762', lng: '139.6503', activity: 'city' },
  { label: 'Bali, ID', countrySlug: 'indonesia', lat: '-8.4095', lng: '115.1889', activity: 'beach' },
  { label: 'Paris, FR', countrySlug: 'france', lat: '48.8566', lng: '2.3522', activity: 'city' },
  { label: 'London, UK', countrySlug: 'united-kingdom', lat: '51.5072', lng: '-0.1276', activity: 'city' },
  { label: 'Cape Town, ZA', countrySlug: 'south-africa', lat: '-33.9249', lng: '18.4241', activity: 'hiking' },
  { label: 'Dubai, AE', countrySlug: 'united-arab-emirates', lat: '25.2048', lng: '55.2708', activity: 'beach' },
  { label: 'Malé, MV', countrySlug: 'maldives', lat: '4.1755', lng: '73.5093', activity: 'beach' },
];

function defaultDateOffset(daysFromToday: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysFromToday);
  return d.toISOString().slice(0, 10);
}

const BAND_STYLES: Record<string, string> = {
  '1': 'border-[#3fb950]/40 bg-[#3fb950]/10 text-[#3fb950]',
  '2': 'border-[#d29922]/40 bg-[#d29922]/10 text-[#d29922]',
  '3': 'border-[#f0883e]/40 bg-[#f0883e]/10 text-[#f0883e]',
  '4': 'border-[#f85149]/40 bg-[#f85149]/10 text-[#f85149]',
  unknown: 'border-[#30363d] bg-[#161b22] text-[#8b949e]',
};

const WEATHER_VERDICT_STYLES: Record<string, string> = {
  green: 'text-[#3fb950]',
  yellow: 'text-[#d29922]',
  red: 'text-[#f85149]',
  unverifiable: 'text-[#8b949e]',
  unknown: 'text-[#8b949e]',
};

const WEATHER_BADGE_STYLES: Record<string, string> = {
  green: 'border-[#3fb950]/40 bg-[#3fb950]/10 text-[#3fb950]',
  yellow: 'border-[#d29922]/40 bg-[#d29922]/10 text-[#d29922]',
  red: 'border-[#f85149]/40 bg-[#f85149]/10 text-[#f85149]',
  unverifiable: 'border-[#30363d] bg-[#161b22] text-[#8b949e]',
};

const DIMENSION_LABELS: Record<string, string> = {
  safety: 'Safety',
  value: 'Value for money',
  family_fit: 'Family fit',
  food: 'Food & dining',
  transport: 'Local transport',
  connectivity: 'Connectivity & Wi-Fi',
};

function ProvenanceLine({
  items,
}: {
  items?: Array<{
    source_id?: string;
    retrieved_at?: string;
    source?: string;
    fetched_at?: string;
    url?: string;
  }>;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className='flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-[#8b949e] mt-2'>
      {items.map((it, idx) => {
        const sourceLabel = it.source_id || it.source || 'governed';
        const fetchedLabel = it.retrieved_at || it.fetched_at;
        return (
          <span key={`${sourceLabel}-${idx}`}>
            Source: <span className='text-[#c9d1d9]'>{sourceLabel}</span>
            {fetchedLabel ? ` · fetched ${fetchedLabel}` : ''}
            {it.url ? (
              <>
                {' · '}
                <a
                  href={it.url}
                  target='_blank'
                  rel='noreferrer'
                  className='text-[#58a6ff] hover:underline'
                >
                  reference
                </a>
              </>
            ) : null}
          </span>
        );
      })}
    </div>
  );
}

export default function DestinationIntelligencePageClient() {
  const searchParams = useSearchParams();
  const initialCountry = searchParams.get('country')?.trim() ?? '';
  const initialPreset = DESTINATION_PRESETS.find(
    (p) => p.countrySlug === initialCountry.toLowerCase(),
  );
  const [country, setCountry] = useState(initialCountry);
  const [safety, setSafety] = useState<SafetyVerdict | null>(null);
  const [safetyErr, setSafetyErr] = useState<string | null>(null);
  const [safetyLoading, setSafetyLoading] = useState(false);

  const [lat, setLat] = useState(initialPreset?.lat ?? '13.7563');
  const [lng, setLng] = useState(initialPreset?.lng ?? '100.5018');
  const [start, setStart] = useState(() => defaultDateOffset(14));
  const [end, setEnd] = useState(() => defaultDateOffset(19));
  const [activity, setActivity] = useState(initialPreset?.activity ?? 'city');
  const [weather, setWeather] = useState<WeatherSuitability | null>(null);
  const [weatherErr, setWeatherErr] = useState<string | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

  const [ratings, setRatings] = useState<DestinationRatings | null>(null);
  const [ratingsErr, setRatingsErr] = useState<string | null>(null);
  const [ratingsMsg, setRatingsMsg] = useState<string | null>(null);
  const [ratingDim, setRatingDim] = useState<string>('safety');
  const [ratingScore, setRatingScore] = useState<number>(5);
  const [ratingTripMonth, setRatingTripMonth] = useState<string>('');
  const [ratingNote, setRatingNote] = useState<string>('');
  const [ratingConsent, setRatingConsent] = useState<boolean>(false);
  const [ratingSubmitting, setRatingSubmitting] = useState<boolean>(false);

  const runSafetyCheck = async (targetCountry: string) => {
    const slug = targetCountry.trim().toLowerCase();
    if (!slug) return;
    setSafetyLoading(true);
    setSafetyErr(null);
    setRatingsErr(null);
    setRatingsMsg(null);
    try {
      const [s, r] = await Promise.allSettled([
        getSafetyVerdict(slug),
        getDestinationRatings(slug),
      ]);
      if (s.status === 'fulfilled') setSafety(s.value);
      else setSafetyErr(s.reason instanceof Error ? s.reason.message : 'Safety lookup failed');
      if (r.status === 'fulfilled') setRatings(r.value);
      else setRatingsErr(r.reason instanceof Error ? r.reason.message : 'Ratings lookup failed');
    } finally {
      setSafetyLoading(false);
    }
  };

  useEffect(() => {
    const slug = initialCountry.toLowerCase();
    if (!slug) return;
    let active = true;
    void Promise.allSettled([
      getSafetyVerdict(slug),
      getDestinationRatings(slug),
    ]).then(([s, r]) => {
      if (!active) return;
      if (s.status === 'fulfilled') setSafety(s.value);
      if (r.status === 'fulfilled') setRatings(r.value);
    });
    return () => {
      active = false;
    };
  }, [initialCountry]);

  const applyPreset = (preset: DestinationPreset) => {
    setCountry(preset.countrySlug);
    setLat(preset.lat);
    setLng(preset.lng);
    setActivity(preset.activity);
    void runSafetyCheck(preset.countrySlug);
  };

  const checkSafety = async (e: React.FormEvent) => {
    e.preventDefault();
    await runSafetyCheck(country);
  };

  const checkWeather = async (e: React.FormEvent) => {
    e.preventDefault();
    const la = Number(lat);
    const lo = Number(lng);
    if (!Number.isFinite(la) || !Number.isFinite(lo) || !start || !end) {
      setWeatherErr('Enter lat, lng, start date, and end date.');
      return;
    }
    if (start > end) {
      setWeatherErr('Start date must be on or before end date.');
      return;
    }
    setWeatherLoading(true);
    setWeatherErr(null);
    try {
      const res = await getWeatherSuitability({ lat: la, lng: lo, start_date: start, end_date: end, activity });
      setWeather(res);
    } catch (err) {
      setWeatherErr(err instanceof Error ? err.message : 'Weather lookup failed');
    } finally {
      setWeatherLoading(false);
    }
  };

  const submitRating = async (e: React.FormEvent) => {
    e.preventDefault();
    const slug = country.trim().toLowerCase();
    if (!slug) return;
    if (!ratingConsent) {
      setRatingsErr('Explicit traveler consent is required before submitting a rating (TRV-DP-07).');
      return;
    }
    setRatingSubmitting(true);
    setRatingsMsg(null);
    setRatingsErr(null);
    try {
      await submitDestinationRating(slug, {
        dimension: ratingDim,
        score: ratingScore,
        consent: true,
        ...(ratingTripMonth ? { trip_month: ratingTripMonth } : {}),
        ...(ratingNote.trim() ? { note: ratingNote.trim() } : {}),
      });
      const updated = await getDestinationRatings(slug);
      setRatings(updated);
      setRatingsMsg(`Recorded anonymous ${ratingScore}/5 for ${DIMENSION_LABELS[ratingDim] ?? ratingDim}.`);
      setRatingNote('');
      setRatingConsent(false);
    } catch (err) {
      setRatingsErr(err instanceof Error ? err.message : 'Rating failed');
    } finally {
      setRatingSubmitting(false);
    }
  };

  return (
    <div className='p-6 max-w-5xl mx-auto space-y-6'>
      <header className='space-y-1'>
        <h1 className='text-ui-2xl font-semibold text-[#e6edf3]'>Destination Intelligence</h1>
        <p className='text-ui-sm text-[#8b949e]'>
          Governed external data — every value carries its source and fetch time. Missing data is shown as a gap, never guessed.
        </p>
      </header>

      {/* Quick-pick destination presets */}
      <section aria-label='Quick-pick destinations' className='rounded-xl border border-[#30363d] bg-[#0d1117] p-4 space-y-2.5'>
        <div className='flex items-center gap-2 text-ui-xs uppercase tracking-wider text-[#8b949e]'>
          <MapPin className='size-3.5 text-[#58a6ff]' />
          <span>Quick-Pick Destinations (populates country advisory &amp; coordinates)</span>
        </div>
        <div className='flex flex-wrap gap-2'>
          {DESTINATION_PRESETS.map((preset) => {
            const isSelected = country.trim().toLowerCase() === preset.countrySlug;
            return (
              <button
                key={preset.label}
                type='button'
                onClick={() => applyPreset(preset)}
                className={`px-3 py-1.5 rounded-lg text-ui-xs border transition-colors ${
                  isSelected
                    ? 'bg-[#58a6ff]/15 border-[#58a6ff]/60 text-[#79c0ff]'
                    : 'bg-[#161b22] border-[#30363d] text-[#c9d1d9] hover:border-[#8b949e]'
                }`}
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Safety verdict lookup */}
      <section className='rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-4'>
        <div className='flex items-center justify-between'>
          <h2 className='text-ui-sm uppercase tracking-wider text-[#8b949e]'>Safety verdict (government advisories)</h2>
          <ShieldAlert className='size-4 text-[#8b949e]' />
        </div>
        <form onSubmit={checkSafety} className='flex gap-2'>
          <label htmlFor='di-country-slug' className='sr-only'>
            Country slug
          </label>
          <input
            id='di-country-slug'
            name='country'
            type='text'
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder='Country (e.g. japan, thailand, united-kingdom)'
            aria-label='Country slug'
            className='flex-1 px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm focus:outline-none focus:border-[#58a6ff]'
          />
          <button
            type='submit'
            disabled={safetyLoading || !country.trim()}
            className='px-4 py-2 rounded-lg border border-[#30363d] bg-[#161b22] text-[#e6edf3] text-ui-sm hover:border-[#58a6ff] disabled:opacity-50'
          >
            {safetyLoading ? 'Checking…' : 'Check'}
          </button>
        </form>

        {safetyErr && <p className='text-ui-sm text-[#f85149]'>{safetyErr}</p>}

        {safety && (
          <div className='space-y-3 pt-2 border-t border-[#21262d]'>
            <div className='flex items-center gap-3 flex-wrap'>
              <span className={`px-2.5 py-1 rounded text-ui-xs border ${BAND_STYLES[safety.band] || BAND_STYLES.unknown}`}>
                Band {safety.band}
              </span>
              <span className='text-ui-base text-[#e6edf3] font-medium'>{safety.label}</span>
              {safety.alias_note && (
                <span className='text-ui-xs text-[#8b949e]'>({safety.alias_note})</span>
              )}
            </div>
            <div className='text-ui-xs text-[#8b949e]'>
              Coverage: <span className='text-[#c9d1d9]'>{safety.coverage.join(', ') || 'none'}</span>
              {safety.coverage_gaps.length > 0 && (
                <> · Gaps: <span className='text-[#d29922]'>{safety.coverage_gaps.join(', ')}</span></>
              )}
            </div>
            <ProvenanceLine items={safety.provenance} />
          </div>
        )}
      </section>

      {/* Weather suitability */}
      <section className='rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-4'>
        <div className='flex items-center justify-between'>
          <h2 className='text-ui-sm uppercase tracking-wider text-[#8b949e]'>Trip-date weather</h2>
          <Sun className='size-4 text-[#8b949e]' />
        </div>
        <form onSubmit={checkWeather} className='grid grid-cols-1 sm:grid-cols-6 gap-2'>
          <div>
            <label htmlFor='di-lat' className='block text-[11px] text-[#8b949e] mb-1'>Latitude</label>
            <input
              id='di-lat'
              name='lat'
              type='text'
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              placeholder='Lat'
              aria-label='Latitude'
              className='w-full px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm'
            />
          </div>
          <div>
            <label htmlFor='di-lng' className='block text-[11px] text-[#8b949e] mb-1'>Longitude</label>
            <input
              id='di-lng'
              name='lng'
              type='text'
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              placeholder='Lng'
              aria-label='Longitude'
              className='w-full px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm'
            />
          </div>
          <div>
            <label htmlFor='di-start-date' className='block text-[11px] text-[#8b949e] mb-1'>Start date</label>
            <input
              id='di-start-date'
              name='start'
              type='date'
              value={start}
              onChange={(e) => setStart(e.target.value)}
              aria-label='Trip start date'
              className='w-full px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm'
            />
          </div>
          <div>
            <label htmlFor='di-end-date' className='block text-[11px] text-[#8b949e] mb-1'>End date</label>
            <input
              id='di-end-date'
              name='end'
              type='date'
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              aria-label='Trip end date'
              className='w-full px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm'
            />
          </div>
          <div>
            <label htmlFor='di-activity' className='block text-[11px] text-[#8b949e] mb-1'>Activity</label>
            <select
              id='di-activity'
              name='activity'
              value={activity}
              onChange={(e) => setActivity(e.target.value as DestinationPreset['activity'])}
              aria-label='Activity profile'
              className='w-full px-3 py-2 rounded-lg bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-ui-sm'
            >
              <option value='city'>city</option>
              <option value='beach'>beach</option>
              <option value='hiking'>hiking</option>
            </select>
          </div>
          <div className='flex items-end'>
            <button
              type='submit'
              disabled={weatherLoading}
              className='w-full px-4 py-2 rounded-lg border border-[#30363d] bg-[#161b22] text-[#e6edf3] text-ui-sm hover:border-[#58a6ff] disabled:opacity-50'
            >
              {weatherLoading ? 'Grading…' : 'Grade'}
            </button>
          </div>
        </form>

        {weatherErr && <p className='text-ui-sm text-[#f85149]'>{weatherErr}</p>}

        {weather && (
          <div className='space-y-3 pt-2 border-t border-[#21262d]'>
            <div className='flex items-center gap-3 flex-wrap'>
              <CloudRain className={`size-4 ${WEATHER_VERDICT_STYLES[weather.verdict || 'unknown']}`} />
              <span className={`text-ui-base font-medium ${WEATHER_VERDICT_STYLES[weather.verdict || 'unknown']}`}>
                {weather.verdict || weather.status}
              </span>
              <span className='text-ui-xs text-[#8b949e]'>
                mode: {weather.mode} · activity: {weather.activity}
                {weather.timezone ? ` · ${weather.timezone}` : ''}
              </span>
            </div>
            {weather.confidence_note && (
              <p className='text-ui-xs text-[#c9d1d9]'>{weather.confidence_note}</p>
            )}
            {weather.summary && (
              <div className='text-ui-xs text-[#8b949e] flex flex-wrap gap-3'>
                <span>Green: <strong className='text-[#3fb950]'>{weather.summary.green ?? 0}</strong></span>
                <span>Yellow: <strong className='text-[#d29922]'>{weather.summary.yellow ?? 0}</strong></span>
                <span>Red: <strong className='text-[#f85149]'>{weather.summary.red ?? 0}</strong></span>
                <span>Unverifiable: <strong className='text-[#8b949e]'>{weather.summary.unverifiable ?? 0}</strong></span>
              </div>
            )}
            {weather.days && weather.days.length > 0 && (
              <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-1'>
                {weather.days.map((d, idx) => {
                  const day = d as {
                    date?: string;
                    verdict?: string;
                    tmax_c?: number | null;
                    precip_mm?: number | null;
                    uv_note?: string;
                  };
                  const v = day.verdict || 'unverifiable';
                  return (
                    <div
                      key={day.date || idx}
                      className='rounded-lg border border-[#21262d] bg-[#161b22]/60 px-3 py-2 text-ui-xs space-y-1'
                    >
                      <div className='flex items-center justify-between gap-2'>
                        <span className='text-[#e6edf3] font-medium tabular-nums'>{day.date || '—'}</span>
                        <span className={`px-1.5 py-0.5 rounded border text-[11px] ${WEATHER_BADGE_STYLES[v] || WEATHER_BADGE_STYLES.unverifiable}`}>
                          {v}
                        </span>
                      </div>
                      {(day.tmax_c != null || day.precip_mm != null) && (
                        <div className='text-[#8b949e] tabular-nums'>
                          {day.tmax_c != null ? `Max ${day.tmax_c}°C` : ''}
                          {day.tmax_c != null && day.precip_mm != null ? ' · ' : ''}
                          {day.precip_mm != null ? `${day.precip_mm} mm precip` : ''}
                        </div>
                      )}
                      {day.uv_note && <div className='text-[11px] text-[#d29922]'>{day.uv_note}</div>}
                    </div>
                  );
                })}
              </div>
            )}
            {weather.normals && (
              <div className='text-ui-xs text-[#8b949e]'>
                Climate normals{weather.years_used && weather.years_used.length > 0 ? ` (${weather.years_used.length} yrs)` : ''}:
                {' '}mean max {weather.normals.mean_tmax_c != null ? `${Number(weather.normals.mean_tmax_c).toFixed(1)}°C` : '—'}
                {' · '}mean precip {weather.normals.mean_precip_mm != null ? `${Number(weather.normals.mean_precip_mm).toFixed(1)} mm/day` : '—'}
                {weather.normals.rain_day_fraction != null ? ` · rain-day share ${(Number(weather.normals.rain_day_fraction) * 100).toFixed(0)}%` : ''}
              </div>
            )}
            {weather.coverage_gaps && weather.coverage_gaps.length > 0 && (
              <p className='text-ui-xs text-[#d29922]'>Gap: {weather.coverage_gaps.join(', ')}</p>
            )}
            <ProvenanceLine items={weather.provenance} />
          </div>
        )}
      </section>

      {/* Anonymized ratings */}
      {country.trim() && (
        <section className='rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-4'>
          <div className='flex items-center justify-between'>
            <h2 className='text-ui-sm uppercase tracking-wider text-[#8b949e]'>
              Anonymized ratings — {country.trim().toLowerCase()}
            </h2>
            <Star className='size-4 text-[#8b949e]' />
          </div>
          {ratingsErr && <p className='text-ui-sm text-[#f85149]'>{ratingsErr}</p>}
          {ratingsMsg && <p className='text-ui-xs text-[#3fb950]'>{ratingsMsg}</p>}
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
            {Object.entries(DIMENSION_LABELS).map(([dim, label]) => {
              const info = ratings?.dimensions?.[dim];
              const count = info?.count ?? 0;
              return (
                <div key={dim} className='rounded-lg border border-[#21262d] bg-[#161b22]/50 p-3 flex items-center justify-between gap-2'>
                  <div>
                    <div className='text-ui-sm text-[#e6edf3]'>{label}</div>
                    <div className='text-ui-xs text-[#8b949e]'>
                      {count > 0 && info?.mean != null ? `${info.mean.toFixed(1)} / 5 (${count} ratings)` : 'No ratings yet'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <form onSubmit={submitRating} className='rounded-lg border border-[#21262d] bg-[#161b22]/40 p-4 space-y-3'>
            <div className='text-ui-xs uppercase tracking-wider text-[#8b949e]'>
              Contribute anonymized traveler rating (TRV-DP-07 consented pool)
            </div>
            <div className='grid grid-cols-1 sm:grid-cols-4 gap-2'>
              <div>
                <label htmlFor='di-rating-dim' className='block text-[11px] text-[#8b949e] mb-1'>Dimension</label>
                <select
                  id='di-rating-dim'
                  name='rating_dimension'
                  value={ratingDim}
                  onChange={(e) => setRatingDim(e.target.value)}
                  className='w-full px-3 py-2 rounded-lg bg-[#0d1117] border border-[#30363d] text-[#e6edf3] text-ui-sm'
                >
                  {Object.entries(DIMENSION_LABELS).map(([dim, label]) => (
                    <option key={dim} value={dim}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor='di-rating-score' className='block text-[11px] text-[#8b949e] mb-1'>Score</label>
                <select
                  id='di-rating-score'
                  name='rating_score'
                  value={ratingScore}
                  onChange={(e) => setRatingScore(Number(e.target.value))}
                  className='w-full px-3 py-2 rounded-lg bg-[#0d1117] border border-[#30363d] text-[#e6edf3] text-ui-sm'
                >
                  {[5, 4, 3, 2, 1].map((s) => (
                    <option key={s} value={s}>{s} / 5</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor='di-rating-month' className='block text-[11px] text-[#8b949e] mb-1'>Trip month (optional)</label>
                <input
                  id='di-rating-month'
                  name='rating_trip_month'
                  type='month'
                  value={ratingTripMonth}
                  onChange={(e) => setRatingTripMonth(e.target.value)}
                  className='w-full px-3 py-2 rounded-lg bg-[#0d1117] border border-[#30363d] text-[#e6edf3] text-ui-sm'
                />
              </div>
              <div className='sm:col-span-1'>
                <label htmlFor='di-rating-note' className='block text-[11px] text-[#8b949e] mb-1'>Note (optional, 280 chars max)</label>
                <input
                  id='di-rating-note'
                  name='rating_note'
                  type='text'
                  maxLength={280}
                  value={ratingNote}
                  onChange={(e) => setRatingNote(e.target.value)}
                  placeholder='Contacts auto-scrubbed'
                  className='w-full px-3 py-2 rounded-lg bg-[#0d1117] border border-[#30363d] text-[#e6edf3] text-ui-sm'
                />
              </div>
            </div>
            <div className='flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1'>
              <label htmlFor='di-rating-consent' className='inline-flex items-center gap-2 text-ui-xs text-[#c9d1d9] cursor-pointer'>
                <input
                  id='di-rating-consent'
                  name='rating_consent'
                  type='checkbox'
                  checked={ratingConsent}
                  onChange={(e) => setRatingConsent(e.target.checked)}
                  className='rounded border-[#30363d] bg-[#0d1117]'
                />
                <span>Traveler gave explicit consent to share this anonymized rating (TRV-DP-07)</span>
              </label>
              <button
                type='submit'
                disabled={ratingSubmitting || !ratingConsent}
                className='px-4 py-2 rounded-lg border border-[#30363d] bg-[#0d1117] text-[#e6edf3] text-ui-sm hover:border-[#58a6ff] disabled:opacity-50'
              >
                {ratingSubmitting ? 'Submitting…' : 'Submit rating'}
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
