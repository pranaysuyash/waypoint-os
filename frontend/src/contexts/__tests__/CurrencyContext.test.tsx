import { describe, expect, it, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CurrencyProvider, useCurrency } from '../CurrencyContext';

function CurrencyProbe() {
  const { preferredCurrency, setPreferredCurrency, formatAsPreferred } = useCurrency();
  return (
    <div>
      <p>Preferred: {preferredCurrency}</p>
      <p>Formatted: {formatAsPreferred(1200, 'USD')}</p>
      <button onClick={() => setPreferredCurrency('EUR')}>Set EUR</button>
    </div>
  );
}

describe('CurrencyContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('provides a default currency and formatting helper', () => {
    render(
      <CurrencyProvider defaultCurrency='USD'>
        <CurrencyProbe />
      </CurrencyProvider>
    );

    expect(screen.getByText('Preferred: USD')).toBeInTheDocument();
    expect(screen.getByText(/Formatted:/)).toHaveTextContent('$');
  });

  it('persists preferred currency changes in localStorage', () => {
    render(
      <CurrencyProvider defaultCurrency='INR'>
        <CurrencyProbe />
      </CurrencyProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Set EUR' }));

    expect(screen.getByText('Preferred: EUR')).toBeInTheDocument();
    expect(localStorage.getItem('preferred_currency')).toBe('EUR');
  });
});
