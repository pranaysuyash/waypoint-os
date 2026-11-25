import { getItineraryFeasibilityEvidence, getItineraryFeasibilityFindings } from '@/lib/itinerary-feasibility';

export function ItineraryFeasibilityFindings({ packet, headingId }: { packet: unknown; headingId?: string }) {
  const findings = getItineraryFeasibilityFindings(packet);
  const { context, question, source, ask, returnDatePending } = getItineraryFeasibilityEvidence(packet);
  if (findings.length === 0 && !question && !returnDatePending) return null;

  return (
    <section aria-label="Itinerary feasibility" className="space-y-3 rounded-xl border border-[var(--border-default)] bg-surface p-4">
      <h2 id={headingId} tabIndex={headingId ? -1 : undefined} className="text-ui-lg font-semibold text-text-primary">Itinerary feasibility</h2>
      {returnDatePending && <p className="text-ui-sm text-text-primary">Confirm the return date with the traveler.</p>}
      {context && <p className="text-ui-sm text-text-muted">{context}</p>}
      {question && <p className="text-ui-sm font-medium text-text-primary">{question}</p>}
      {question && ask && <p className="text-ui-sm text-text-muted">Ask {ask}</p>}
      {question && source && <a className="text-ui-sm text-accent-blue underline" href={source.url}>{source.label}</a>}
      {findings.map(({ id, title, message, context, source, ask }) => (
        <article key={id} className="rounded-lg border border-[rgba(var(--accent-amber-rgb)/0.3)] bg-[rgba(var(--accent-amber-rgb)/0.06)] p-4">
          <h3 className="font-semibold text-accent-amber">{title}</h3>
          {context && <p className="mt-1 text-ui-xs text-text-muted">{context}</p>}
          <p className="mt-2 text-ui-sm leading-relaxed text-text-primary">{message}</p>
          {ask && <p className="mt-2 text-ui-sm text-text-muted">Ask {ask}</p>}
          {source && <a className="mt-2 inline-block text-ui-sm text-accent-blue underline" href={source.url}>{source.label}</a>}
        </article>
      ))}
    </section>
  );
}
