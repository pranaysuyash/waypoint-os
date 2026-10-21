import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms — Waypoint OS',
  description: 'The terms governing use of the Waypoint OS platform.',
};

// T14: terms page stating the platform's real operating boundaries (what is
// AI-generated vs advisor-confirmed, preview vs persisted state). Formal legal
// language awaits owner/DPA review — marked, not impersoned.

const SECTIONS: Array<{ title: string; body: string }> = [
  {
    title: 'What Waypoint OS is',
    body: 'Waypoint OS is software that travel agencies use to capture traveler inquiries, plan trips, and produce proposals. Your contract for travel services is with your travel agency, not with the platform.',
  },
  {
    title: 'AI-generated content',
    body: 'Itineraries, cost estimates, margins, and question suggestions are generated with AI from the information you provide. They are planning aids: your travel advisor reviews them before anything becomes a booking. Estimates are modeled, not vendor quotes, and are labeled as such in the product.',
  },
  {
    title: 'Simulated and preview features',
    body: 'Some capability surfaces are explicitly labeled as simulated or preview. Labeled surfaces are not production features and their content should not be relied on for real travel decisions.',
  },
  {
    title: 'Proposal links and e-signature',
    body: 'Proposals shared with you are accessible via links that expire and can be revoked. Accepting a proposal through e-signature records your consent and identity as entered by you. The travel agency you contract with uses that acceptance to proceed.',
  },
  {
    title: 'Acceptable use',
    body: 'Do not submit another person’s information without their permission, attempt to access other agencies’ workspaces, or use the public checker and proposal surfaces to probe or scrape the service.',
  },
  {
    title: 'Changes',
    body: 'As the product evolves these terms will be updated with the date of the change. Material changes affecting agencies are communicated before they take effect.',
  },
];

export default function TermsPage() {
  return (
    <main className='min-h-screen bg-[#0d1117] text-white'>
      <div className='mx-auto max-w-3xl px-4 py-14'>
        <h1 className='text-3xl font-bold tracking-tight mb-2'>Terms of Service</h1>
        <p className='text-sm text-[#8b949e] mb-8'>Last updated: September 2026.</p>

        <div className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200 mb-8'>
          <p className='font-semibold uppercase tracking-wide'>Review pending</p>
          <p className='mt-1'>
            These terms describe actual product behavior. Formal legal review is completed with each
            agency before production onboarding.
          </p>
        </div>

        <dl className='space-y-6'>
          {SECTIONS.map((s) => (
            <div key={s.title} className='rounded-xl border border-[#30363d] bg-[#161b22] p-5'>
              <dt className='text-base font-semibold text-white mb-1.5'>{s.title}</dt>
              <dd className='text-sm text-[#8b949e] leading-relaxed'>{s.body}</dd>
            </div>
          ))}
        </dl>
      </div>
    </main>
  );
}
