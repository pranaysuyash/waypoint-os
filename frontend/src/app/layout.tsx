import type { Metadata } from 'next';
import Script from 'next/script';
import './globals.css';

export const metadata: Metadata = {
  title: 'Waypoint OS',
  description: 'AI operating workspace for boutique travel agencies',
};

const enableReactDiagnostics =
  process.env.NODE_ENV === 'development' &&
  process.env.NEXT_PUBLIC_ENABLE_REACT_DIAGNOSTICS === '1';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en' suppressHydrationWarning>
      {enableReactDiagnostics ? (
        <head>
          <Script
            id='react-scan-devtools'
            src='https://unpkg.com/react-scan@0.5.6/dist/auto.global.js'
            crossOrigin='anonymous'
            strategy='beforeInteractive'
          />
          <Script
            id='react-grab-devtools'
            src='https://unpkg.com/react-grab@0.1.33/dist/index.global.js'
            crossOrigin='anonymous'
            strategy='beforeInteractive'
          />
        </head>
      ) : null}
      <body>{children}</body>
    </html>
  );
}
