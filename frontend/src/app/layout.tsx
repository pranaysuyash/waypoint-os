import type { Metadata } from 'next';
import { Sora, Rubik, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ErrorBoundary } from '@/components/error-boundary';
import { AuthProvider } from '@/components/auth/AuthProvider';
import { Providers } from '@/components/providers';

const sora = Sora({
  variable: '--font-sora',
  subsets: ['latin'],
});

const rubik = Rubik({
  variable: '--font-rubik',
  subsets: ['latin'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Waypoint OS',
  description: 'AI operating workspace for boutique travel agencies',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang='en'
      className={`${sora.variable} ${rubik.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body>
        <ErrorBoundary>
          <AuthProvider>
            <Providers>{children}</Providers>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
