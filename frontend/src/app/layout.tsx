import type { Metadata } from 'next';
import './globals.css';

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
    <html lang='en' suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
