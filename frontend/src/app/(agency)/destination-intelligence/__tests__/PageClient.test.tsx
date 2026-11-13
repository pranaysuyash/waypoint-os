// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import DestinationIntelligencePageClient from '../PageClient';

const mockGetSafetyVerdict = vi.fn();
const mockGetWeatherSuitability = vi.fn();
const mockGetDestinationRatings = vi.fn();
const mockSubmitDestinationRating = vi.fn();

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('@/lib/api-client', () => ({
  getSafetyVerdict: (...args: unknown[]) => mockGetSafetyVerdict(...args),
  getWeatherSuitability: (...args: unknown[]) => mockGetWeatherSuitability(...args),
  getDestinationRatings: (...args: unknown[]) => mockGetDestinationRatings(...args),
  submitDestinationRating: (...args: unknown[]) => mockSubmitDestinationRating(...args),
}));

describe('DestinationIntelligencePageClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSafetyVerdict.mockResolvedValue({
      destination_slug: 'south-africa',
      band: '2',
      label: 'Increased caution',
      components: {},
      coverage: ['fcdo_advisory'],
      coverage_gaps: ['neighborhood_crime'],
      provenance: [{ source_id: 'fcdo-content-api', retrieved_at: '2026-11-12T10:00:00Z' }],
    });
    mockGetDestinationRatings.mockResolvedValue({
      location: 'south-africa',
      total_ratings: 3,
      dimensions: {
        safety: { count: 2, mean: 4.0, min: 3, max: 5 },
        food: { count: 1, mean: 5.0, min: 5, max: 5 },
      },
    });
    mockGetWeatherSuitability.mockResolvedValue({
      mode: 'forecast',
      activity: 'hiking',
      status: 'graded',
      verdict: 'yellow',
      summary: { green: 4, yellow: 1, red: 0, unverifiable: 0 },
      days: [
        { date: '2026-11-26', verdict: 'green', tmax_c: 24.5, precip_mm: 0.0 },
        { date: '2026-11-27', verdict: 'yellow', tmax_c: 21.0, precip_mm: 3.2, uv_note: 'very high UV (9) — sun protection advised' },
      ],
      provenance: [{ source_id: 'open-meteo-forecast', retrieved_at: '2026-11-12T10:00:00Z' }],
      timezone: 'Africa/Johannesburg',
    });
    mockSubmitDestinationRating.mockResolvedValue({
      ok: true,
      record_id: 'rat_123',
      location: 'south-africa',
      dimension: 'connectivity',
      score: 4,
    });
  });

  it('uses backend-valid activity enum (hiking for Cape Town) and renders forecast summary + daily rows', async () => {
    render(<DestinationIntelligencePageClient />);

    const activitySelect = screen.getByLabelText('Activity profile') as HTMLSelectElement;
    const options = Array.from(activitySelect.options).map((o) => o.value);
    expect(options).toEqual(['city', 'beach', 'hiking']);

    fireEvent.click(screen.getByRole('button', { name: 'Cape Town, ZA' }));

    await waitFor(() => {
      expect(mockGetSafetyVerdict).toHaveBeenCalledWith('south-africa');
      expect(screen.getByText('Band 2')).toBeInTheDocument();
      expect(screen.getByText('fcdo-content-api')).toBeInTheDocument();
      expect(screen.getByText(/fetched 2026-11-12T10:00:00Z/)).toBeInTheDocument();
    });
    expect(activitySelect.value).toBe('hiking');

    fireEvent.click(screen.getByRole('button', { name: 'Grade' }));

    await waitFor(() => {
      expect(mockGetWeatherSuitability).toHaveBeenCalledWith(
        expect.objectContaining({ activity: 'hiking' })
      );
      expect(screen.getByText('2026-11-26')).toBeInTheDocument();
      expect(screen.getByText(/very high UV \(9\)/i)).toBeInTheDocument();
    });
  });

  it('renders all 6 canonical RATING_DIMENSIONS and enforces explicit TRV-DP-07 consent before submit', async () => {
    render(<DestinationIntelligencePageClient />);

    fireEvent.click(screen.getByRole('button', { name: 'Cape Town, ZA' }));
    await waitFor(() => {
      expect(screen.getByText(/Anonymized ratings — south-africa/i)).toBeInTheDocument();
    });

    for (const label of [
      'Safety',
      'Value for money',
      'Family fit',
      'Food & dining',
      'Local transport',
      'Connectivity & Wi-Fi',
    ]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }

    const submitBtn = screen.getByRole('button', { name: 'Submit rating' });
    expect(submitBtn).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Dimension'), { target: { value: 'connectivity' } });
    fireEvent.change(screen.getByLabelText('Score'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Trip month (optional)'), { target: { value: '2026-10' } });
    fireEvent.change(screen.getByLabelText(/Note \(optional/i), { target: { value: 'Reliable fiber at hotel' } });
    fireEvent.click(screen.getByLabelText(/Traveler gave explicit consent/i));

    expect(submitBtn).not.toBeDisabled();
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockSubmitDestinationRating).toHaveBeenCalledWith('south-africa', {
        dimension: 'connectivity',
        score: 4,
        consent: true,
        trip_month: '2026-10',
        note: 'Reliable fiber at hotel',
      });
    });
  });

  it('renders climate_baseline normals with years_used and surfaces lookup errors honestly', async () => {
    mockGetSafetyVerdict.mockRejectedValueOnce(new Error('FCDO upstream timeout'));
    mockGetWeatherSuitability.mockResolvedValueOnce({
      mode: 'climate_baseline',
      activity: 'city',
      status: 'graded',
      verdict: 'green',
      normals: { mean_tmax_c: 26.4, mean_precip_mm: 1.2, rain_day_fraction: 0.15 },
      years_used: [2021, 2022, 2023, 2024, 2025],
      years_skipped: [],
      confidence_note: 'historical normal over 5 years — a climate expectation, not a forecast',
      provenance: [{ source_id: 'open-meteo-era5', retrieved_at: '2026-11-12T10:05:00Z' }],
    });

    render(<DestinationIntelligencePageClient />);

    fireEvent.click(screen.getByRole('button', { name: 'Tokyo, JP' }));
    await waitFor(() => {
      expect(screen.getByText('FCDO upstream timeout')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Grade' }));
    await waitFor(() => {
      expect(screen.getByText(/Climate normals \(5 yrs\):/i)).toBeInTheDocument();
      expect(screen.getByText(/mean max 26\.4°C/i)).toBeInTheDocument();
      expect(screen.getByText(/rain-day share 15%/i)).toBeInTheDocument();
      expect(screen.getByText('open-meteo-era5')).toBeInTheDocument();
    });
  });
});
