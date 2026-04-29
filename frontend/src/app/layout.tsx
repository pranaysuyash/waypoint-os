import type { Metadata } from 'next';
import { Sora, Rubik, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Shell } from '@/components/layouts/Shell';
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
      className={`${sora.variable} ${rubik.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body>
        <ErrorBoundary>
          <AuthProvider>
            <Providers>
              <Shell>{children}</Shell>
            </Providers>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
