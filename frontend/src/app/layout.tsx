import type { Metadata } from 'next';
import { IBM_Plex_Sans, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Shell } from '@/components/layouts/Shell';
import { ErrorBoundary } from '@/components/error-boundary';
import { AuthProvider } from '@/components/auth/AuthProvider';

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
  title: 'Waypoint OS',
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
          <AuthProvider>
            <Shell>{children}</Shell>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
