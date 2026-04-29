import { Shell } from '@/components/layouts/Shell';

export default function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Shell>{children}</Shell>;
}
