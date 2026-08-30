import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Workbench",
  description: "Run planning workflows, scenario checks, and operator review for selected trips.",
};

export default function Page() {
  return <PageClient />;
}
