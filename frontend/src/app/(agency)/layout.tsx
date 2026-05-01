import { AuthProvider } from '@/components/auth/AuthProvider';
import { Providers } from '@/components/providers';
import { Shell } from '@/components/layouts/Shell';

export default function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <AuthProvider>
        <Shell>{children}</Shell>
      </AuthProvider>
    </Providers>
  );
}
