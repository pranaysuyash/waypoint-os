import type { Metadata } from 'next';
import { IBM_Plex_Sans, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Shell } from '@/components/layouts/Shell';
import { ErrorBoundary } from '@/components/error-boundary';

const ibmPlexSans = IBM_Plex_Sans({
  variable: '--font-display',
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Travel Agency Agent',
  description: 'AI-powered travel agency decision support system',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang='en'
      className={`${ibmPlexSans.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <ErrorBoundary>
          <Shell>{children}</Shell>
        </ErrorBoundary>
      </body>
    </html>
  );
}
