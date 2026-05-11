import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Quote Assessment",
  description: "Assess whether the selected trip is ready for quote preparation.",
};

export default function Page() {
  return <PageClient />;
}
