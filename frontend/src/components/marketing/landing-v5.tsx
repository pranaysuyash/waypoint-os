'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, CircleDollarSign, Clock3, FileQuestion, MessageSquareText, Route, ShieldCheck } from 'lucide-react';
import { useEffect, useRef } from 'react';
import styles from './landing-v5.module.css';

const intakeRows = [
  { label: 'WhatsApp thread', value: 'Italy honeymoon, Sept, flexible budget', icon: MessageSquareText },
  { label: 'Missing before quote', value: 'arrival city, passport validity, room type', icon: FileQuestion },
  { label: 'Commercial signal', value: 'high intent, premium hotel tolerance', icon: CircleDollarSign },
];

const proof = [
  { label: 'Time to first usable brief', value: '2m 14s' },
  { label: 'Questions removed from back-and-forth', value: '7' },
  { label: 'Owner reviews routed only when needed', value: '18%' },
];

export function V5LandingPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link href='/' className={styles.brand}>Waypoint OS</Link>
        <nav className={styles.nav} aria-label='Primary'>
          <a href='#workflow'>Workflow</a>
          <a href='#proof'>Proof</a>
          <Link href='/v3'>Experiments</Link>
          <Link href='/signup' className={styles.navCta}>Book demo</Link>
        </nav>
      </header>

      <section className={styles.hero}>
        <Image
          src='/landing/experiments/waypoint-ops-hero-v5.png'
          alt=''
          fill
          priority
          sizes='100vw'
        />
        <WorkflowSketch />
        <div className={styles.heroCopy}>
          <span className={styles.kicker}>Boutique travel ops, without the theater</span>
          <h1>Make every travel request quote-ready before anyone starts quoting.</h1>
          <p>
            Waypoint turns scattered client context into the brief, risk questions,
            commercial signals, and owner checks your agency needs to reply with confidence.
          </p>
          <div className={styles.actions}>
            <Link href='/signup' className={styles.primaryButton}>
              Book a demo <ArrowRight className='size-4' />
            </Link>
            <Link href='/itinerary-checker' className={styles.secondaryButton}>
              Try the public checker
            </Link>
          </div>
        </div>
      </section>

      <section className={styles.workspace} id='workflow'>
        <div className={styles.panelIntro}>
          <span className={styles.kicker}>Live workspace</span>
          <h2>Not a prettier CRM. A judgment surface.</h2>
          <p>
            The page should prove the product’s operating logic immediately: what came in,
            what is missing, what is risky, and what can safely go to the client.
          </p>
        </div>

        <div className={styles.workbench}>
          <div className={styles.inboxPanel}>
            <div className={styles.panelHeader}>
              <span>New inquiry</span>
              <strong>Honeymoon in Italy</strong>
            </div>
            {intakeRows.map((row) => {
              const Icon = row.icon;
              return (
                <article key={row.label} className={styles.intakeRow}>
                  <Icon className='size-5' />
                  <div>
                    <span>{row.label}</span>
                    <strong>{row.value}</strong>
                  </div>
                </article>
              );
            })}
          </div>

          <div className={styles.decisionPanel}>
            <span className={styles.panelLabel}>Decision packet</span>
            <h3>Ask 3 questions before quote build.</h3>
            <ol>
              <li>Confirm arrival city and preferred routing.</li>
              <li>Check passport validity for both travelers.</li>
              <li>Choose between relaxed coast-first or culture-first pacing.</li>
            </ol>
            <div className={styles.safeReply}>
              <ShieldCheck className='size-5' />
              <span>Internal risk stays private. Client reply is ready to draft.</span>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.proof} id='proof'>
        <div className={styles.proofLead}>
          <span className={styles.kicker}>Why this is better</span>
          <h2>Warm first impression, real product proof, fewer empty vibes.</h2>
        </div>
        <div className={styles.proofGrid}>
          {proof.map((item) => (
            <article key={item.label} className={styles.metric}>
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </article>
          ))}
        </div>
        <div className={styles.checks}>
          <p><CheckCircle2 className='size-4' /> Brighter palette avoids the heavy generic SaaS look.</p>
          <p><CheckCircle2 className='size-4' /> The hero is tactile and travel-specific, not abstract dashboard theater.</p>
          <p><CheckCircle2 className='size-4' /> Animation explains transformation instead of merely sparkling.</p>
        </div>
      </section>
    </main>
  );
}

function WorkflowSketch() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let tick = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.floor(rect.width * ratio);
      canvas.height = Math.floor(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      const points = [
        [rect.width * 0.54, rect.height * 0.32],
        [rect.width * 0.66, rect.height * 0.42],
        [rect.width * 0.76, rect.height * 0.31],
        [rect.width * 0.88, rect.height * 0.47],
      ];

      ctx.strokeStyle = 'rgba(17, 83, 92, 0.42)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      points.forEach(([x, y], index) => {
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      points.forEach(([x, y], index) => {
        ctx.fillStyle = index === 1 ? '#e75f3f' : '#11535c';
        ctx.beginPath();
        ctx.arc(x, y, 5 + Math.sin(tick / 22 + index) * 1.5, 0, Math.PI * 2);
        ctx.fill();
      });

      const progress = (tick % 180) / 180;
      const current = Math.min(2, Math.floor(progress * 3));
      const local = progress * 3 - current;
      const [x1, y1] = points[current];
      const [x2, y2] = points[current + 1];
      ctx.fillStyle = '#f2b84b';
      ctx.beginPath();
      ctx.arc(x1 + (x2 - x1) * local, y1 + (y2 - y1) * local, 6, 0, Math.PI * 2);
      ctx.fill();

      tick += 1;
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

  return <canvas ref={canvasRef} className={styles.canvas} aria-hidden='true' />;
}
