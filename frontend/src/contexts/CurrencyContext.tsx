'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import type { SupportedCurrency } from '@/lib/currency';
import { formatMoney } from '@/lib/currency';

interface CurrencyContextValue {
  preferredCurrency: SupportedCurrency;
  setPreferredCurrency: (currency: SupportedCurrency) => void;
  formatAsPreferred: (amount: number, fromCurrency: SupportedCurrency) => string;
}

const CurrencyContext = createContext<CurrencyContextValue | undefined>(undefined);

const STORAGE_KEY = 'preferred_currency';

interface CurrencyProviderProps {
  children: ReactNode;
  defaultCurrency?: SupportedCurrency;
}

export function CurrencyProvider({ children, defaultCurrency = 'INR' }: CurrencyProviderProps) {
  const [preferredCurrency, setPreferredCurrencyState] = useState<SupportedCurrency>(defaultCurrency);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as SupportedCurrency;
      if (stored && ['INR', 'USD', 'EUR', 'GBP', 'AED', 'SGD', 'THB', 'AUD', 'CAD', 'JPY'].includes(stored)) {
        setPreferredCurrencyState(stored);
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const setPreferredCurrency = useCallback((currency: SupportedCurrency) => {
    setPreferredCurrencyState(currency);
    try {
      localStorage.setItem(STORAGE_KEY, currency);
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const formatAsPreferred = useCallback((amount: number, fromCurrency: SupportedCurrency): string => {
    return formatMoney(amount, fromCurrency);
  }, []);

  return (
    <CurrencyContext.Provider value={{ preferredCurrency, setPreferredCurrency, formatAsPreferred }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency(): CurrencyContextValue {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
}
