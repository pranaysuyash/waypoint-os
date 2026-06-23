'use client';

import Link from 'next/link';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';

const knowledgeAreas = [
  {
    title: 'Playbooks',
    body: 'Capture agency-specific operating notes, repeatable trip patterns, and what the team has already learned.',
  },
  {
    title: 'Preferences',
    body: 'Store durable customer and agency preferences so operators do not have to rediscover the same context repeatedly.',
  },
  {
    title: 'Memory',
    body: 'Keep the living guidance close to the trip workspace, not in a parallel research lane that the team has to hunt for.',
  },
];

export default function KnowledgePage() {
  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      <div>
        <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Knowledge Base</h1>
        <p className='text-ui-sm text-[#8b949e] mt-1'>
          Canonical agency memory shell. No parallel knowledge workflow.
        </p>
      </div>

      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <p className='text-sm text-[#c9d1d9]'>
          This surface is a truthful placeholder for agency memory and playbooks. The durable source of truth still lives in the trip and operations surfaces.
        </p>
        <div className='text-xs text-[#8b949e]'>
          Need current trip context?{' '}
          <Link className='text-[#58a6ff] hover:text-[#79b8ff]' href='/overview'>
            Go back to the command center
          </Link>
        </div>
      </div>

      <div className='grid gap-4 md:grid-cols-3'>
        {knowledgeAreas.map((area) => (
          <section key={area.title} className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-2'>
            <h2 className='text-sm font-semibold text-[#e6edf3]'>{area.title}</h2>
            <p className='text-sm text-[#8b949e]'>{area.body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
