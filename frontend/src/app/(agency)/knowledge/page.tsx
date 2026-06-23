import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Knowledge Base',
  description: 'Agency memory, playbooks, and learned preferences.',
};

export default function Page() {
  return <PageClient />;
}
