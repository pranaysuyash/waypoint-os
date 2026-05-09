'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, Compass, FileCheck2, MessageSquareText, Plane, ShieldCheck, Sparkles, TimerReset } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import styles from './landing-experiments.module.css';

const HERO_IMAGE = '/landing/experiments/waypoint-ops-hero-v3.png';

const experiments = [
  {
    id: 'cinematic',
    label: 'Cinematic Ops',
    title: 'Make the messy request feel already under control.',
    body: 'A generated editorial hero gives Waypoint a tactile agency world: documents, routes, supplier signals, and a calm operating surface.',
  },
  {
    id: 'console',
    label: 'Live Console',
    title: 'Show the product doing the judgment work.',
    body: 'The hero becomes a working intake console with moving signals, owner checks, and safer client output instead of a static dashboard mock.',
  },
  {
    id: 'traveler',
    label: 'Traveler Bridge',
    title: 'Turn the public checker into the acquisition wedge.',
    body: 'Lead with the free itinerary audit, then show how it becomes a structured agency brief without retyping context.',
  },
];

const flowSteps = [
  { icon: MessageSquareText, label: 'Messy inquiry', value: 'WhatsApp + PDF + notes' },
  { icon: Sparkles, label: 'Structured brief', value: 'Dates, travelers, budget, constraints' },
  { icon: ShieldCheck, label: 'Risk questions', value: 'Visa, pacing, supplier holds' },
  { icon: FileCheck2, label: 'Client-safe reply', value: 'Polished output, private rationale' },
];

export function ExperimentLab() {
  const [active, setActive] = useState(experiments[0].id);
  const selected = experiments.find((item) => item.id === active) ?? experiments[0];

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link href='/' className={styles.brand}>Waypoint OS</Link>
        <nav className={styles.nav} aria-label='Experiment versions'>
          <Link href='/v4'>Open v4</Link>
          <Link href='/signup'>Book demo</Link>
        </nav>
      </header>

      <section className={styles.labHero}>
        <div className={styles.labCopy}>
          <span className={styles.kicker}>Landing experiment v3</span>
          <h1>Three ways to make Waypoint feel alive before the user signs in.</h1>
          <p>
            This route is intentionally a component lab: generated imagery, canvas motion,
            operational proof, and multiple hero treatments side by side.
          </p>
          <div className={styles.segmented} role='tablist' aria-label='Hero experiments'>
            {experiments.map((item) => (
              <button
                key={item.id}
                type='button'
                className={item.id === active ? styles.segmentActive : styles.segment}
                onClick={() => setActive(item.id)}
                role='tab'
                aria-selected={item.id === active}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div className={styles.generatedFrame}>
          <Image src={HERO_IMAGE} alt='' fill priority sizes='(max-width: 900px) 100vw, 48vw' />
          <RouteCanvas className={styles.routeCanvas} />
        </div>
      </section>

      <section className={styles.selectedExperiment}>
        <div>
          <span className={styles.kicker}>Selected variant</span>
          <h2>{selected.title}</h2>
          <p>{selected.body}</p>
        </div>
        <ProductSignalStack mode={selected.id} />
      </section>

      <section className={styles.variantGrid} aria-label='Component variants'>
        <HeroVariantCinematic />
        <HeroVariantConsole />
        <HeroVariantTraveler />
      </section>
    </main>
  );
}

export function V4LandingPage() {
  return (
    <main className={styles.v4Page}>
      <header className={styles.header}>
        <Link href='/' className={styles.brand}>Waypoint OS</Link>
        <nav className={styles.nav} aria-label='Primary'>
          <a href='#system'>System</a>
          <a href='#proof'>Proof</a>
          <Link href='/itinerary-checker'>Checker</Link>
          <Link href='/signup'>Book demo</Link>
        </nav>
      </header>

      <section className={styles.v4Hero}>
        <Image src={HERO_IMAGE} alt='' fill priority sizes='100vw' />
        <RouteCanvas className={styles.v4Canvas} />
        <div className={styles.v4Overlay}>
          <span className={styles.kicker}>Boutique travel operations</span>
          <h1>Turn every messy travel request into a safer trip decision.</h1>
          <p>
            Waypoint structures intake, exposes the few questions that change the quote,
            and keeps private operator rationale out of client-facing replies.
          </p>
          <div className={styles.heroActions}>
            <Link href='/signup' className={styles.primaryCta}>
              Book a demo <ArrowRight className='size-4' />
            </Link>
            <Link href='/itinerary-checker' className={styles.secondaryCta}>
              Try public checker
            </Link>
          </div>
        </div>
        <ProductSignalStack mode='v4' />
      </section>

      <section className={styles.v4Flow} id='system'>
        {flowSteps.map((step) => {
          const Icon = step.icon;
          return (
            <article key={step.label} className={styles.flowCard}>
              <Icon className='size-5' />
              <span>{step.label}</span>
              <strong>{step.value}</strong>
            </article>
          );
        })}
      </section>

      <section className={styles.proofBand} id='proof'>
        <div>
          <span className={styles.kicker}>Why this direction wins</span>
          <h2>It sells the operating judgment, not just the software shell.</h2>
        </div>
        <div className={styles.proofList}>
          <p><CheckCircle2 className='size-4' />The generated image gives brand memory in the first viewport.</p>
          <p><CheckCircle2 className='size-4' />Canvas motion visualizes intake becoming a governed workflow.</p>
          <p><CheckCircle2 className='size-4' />The UI panels are functional proof: risk, revenue, timing, and owner review.</p>
        </div>
      </section>
    </main>
  );
}

function ProductSignalStack({ mode }: { mode: string }) {
  const signals = mode === 'traveler'
    ? ['Pacing risk found', 'Hotel transfer question', 'Public brief ready']
    : ['Owner check needed', 'Budget tension detected', 'Supplier hold expires'];

  return (
    <aside className={styles.signalStack} aria-label='Live product signals'>
      <div className={styles.signalHeader}>
        <Compass className='size-4' />
        <span>Live trip intelligence</span>
      </div>
      {signals.map((signal, index) => (
        <div key={signal} className={styles.signalRow} style={{ '--delay': `${index * 140}ms` } as React.CSSProperties}>
          <span className={styles.signalPulse} />
          <strong>{signal}</strong>
          <small>{index === 0 ? 'Now' : `${index * 7 + 4}m`}</small>
        </div>
      ))}
      <div className={styles.scorePanel}>
        <span>Quote readiness</span>
        <strong>82%</strong>
        <div><span /></div>
      </div>
    </aside>
  );
}

function HeroVariantCinematic() {
  return (
    <article className={styles.variantCard}>
      <Image src={HERO_IMAGE} alt='' fill sizes='(max-width: 900px) 100vw, 33vw' />
      <div>
        <span>Cinematic Ops</span>
        <h3>Best for brand memory.</h3>
        <p>Use the generated world as a first-viewport signal, then overlay real product state.</p>
      </div>
    </article>
  );
}

function HeroVariantConsole() {
  return (
    <article className={styles.variantCardNoImage}>
      <div className={styles.consoleMock}>
        <div><TimerReset className='size-4' /> Intake deadline <strong>18m</strong></div>
        <div><ShieldCheck className='size-4' /> Owner review <strong>Required</strong></div>
        <div><Plane className='size-4' /> Supplier hold <strong>Pending</strong></div>
      </div>
      <h3>Best for product clarity.</h3>
      <p>Lead with product behavior: what gets detected, routed, and protected.</p>
    </article>
  );
}

function HeroVariantTraveler() {
  return (
    <article className={styles.variantCardNoImage}>
      <div className={styles.checkerMock}>
        <span>Paste itinerary</span>
        <strong>Portugal family trip</strong>
        <p>3 timing risks, 2 document questions, 1 simpler day.</p>
      </div>
      <h3>Best for acquisition.</h3>
      <p>Make the free checker the top-of-funnel wedge and handoff into agency workflow.</p>
    </article>
  );
}

function RouteCanvas({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    let frame = 0;
    let raf = 0;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      context.clearRect(0, 0, rect.width, rect.height);
      context.lineWidth = 1.2;
      context.strokeStyle = 'rgba(111, 220, 210, 0.46)';
      context.fillStyle = 'rgba(255, 255, 255, 0.82)';

      const points = [
        [rect.width * 0.1, rect.height * 0.72],
        [rect.width * 0.36, rect.height * 0.44],
        [rect.width * 0.62, rect.height * 0.58],
        [rect.width * 0.88, rect.height * 0.25],
      ];

      context.beginPath();
      points.forEach((point, index) => {
        const [x, y] = point;
        if (index === 0) context.moveTo(x, y);
        else context.lineTo(x, y);
      });
      context.stroke();

      points.forEach(([x, y], index) => {
        const pulse = 3 + Math.sin(frame / 18 + index) * 1.8;
        context.beginPath();
        context.arc(x, y, pulse, 0, Math.PI * 2);
        context.fill();
      });

      const progress = (frame % 220) / 220;
      const segment = Math.min(points.length - 2, Math.floor(progress * (points.length - 1)));
      const local = progress * (points.length - 1) - segment;
      const [x1, y1] = points[segment];
      const [x2, y2] = points[segment + 1];
      context.fillStyle = '#ffd166';
      context.beginPath();
      context.arc(x1 + (x2 - x1) * local, y1 + (y2 - y1) * local, 4.6, 0, Math.PI * 2);
      context.fill();

      frame += 1;
      raf = requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener('resize', resize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} className={className} aria-hidden='true' />;
}
