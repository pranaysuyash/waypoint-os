import { AuthProvider } from '@/components/auth/AuthProvider';
import { Providers } from '@/components/providers';
import { Shell } from '@/components/layouts/Shell';
import { ToastContainer } from '@/components/ui/toast';

export default function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <AuthProvider>
        <Shell>{children}</Shell>
        <ToastContainer />
      </AuthProvider>
    </Providers>
  );
}
