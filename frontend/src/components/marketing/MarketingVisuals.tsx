'use client';

import { useMemo, useState } from 'react';
import type { CSSProperties } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircleDashed,
  FileText,
  Loader2,
  MapPinned,
  NotebookPen,
  Plane,
  Search,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import styles from './marketing.module.css';

type HeroSceneProps = {
  mode: 'agency' | 'checker';
};

export function HeroScene({ mode }: HeroSceneProps) {
  const nodes =
    mode === 'agency'
      ? ['Lead lands', 'Blockers found', 'Options framed', 'Owner review', 'Traveler-safe reply']
      : ['Plan uploaded', 'Transfers checked', 'Pacing reviewed', 'Brief written'];

  return (
    <div className={styles.heroScene} aria-hidden='true'>
      <div className={styles.routeLine} />
      <div className={styles.sceneMap}>
        {nodes.map((node, index) => (
          <div
            key={node}
            className={styles.sceneNode}
            style={{ '--node-index': index } as CSSProperties}
          >
            <span>{String(index + 1).padStart(2, '0')}</span>
            <strong>{node}</strong>
          </div>
        ))}
      </div>
      <div className={styles.sceneArtifact}>
        {mode === 'agency' ? (
          <>
            <MapPinned className='h-5 w-5 text-[#39d0d8]' />
            <strong>Agency command graph</strong>
            <span>Inbox to output, with judgment preserved.</span>
          </>
        ) : (
          <>
            <NotebookPen className='h-5 w-5 text-[#d29922]' />
            <strong>Trip notebook active</strong>
            <span>Findings become questions worth asking.</span>
          </>
        )}
      </div>
    </div>
  );
}

export function LogoShowcase() {
  return (
    <div className={styles.logoShowcase} aria-label='Waypoint logo directions'>
      {[
        ['/brand/waypoint-logo-primary.svg', 'Primary lockup'],
        ['/brand/waypoint-logo-compass.svg', 'Compass mark'],
        ['/brand/waypoint-logo-notebook.svg', 'Notebook wedge mark'],
      ].map(([src, label]) => (
        <div key={src} className={styles.logoTile}>
          <img src={src} alt={`Waypoint ${label}`} />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

const notebookSteps = [
  { icon: UploadCloud, label: 'Reading itinerary', text: 'Pulling out dates, stays, transfers, and rough pacing.' },
  { icon: Search, label: 'Checking weak spots', text: 'Looking for fragile timing, missing docs, and overloaded days.' },
  { icon: NotebookPen, label: 'Writing the notebook', text: 'Turning findings into questions you can take to your planner.' },
  { icon: CheckCircle2, label: 'Brief ready', text: 'A calm summary is ready for the next conversation.' },
];

export function NotebookAnalyzer() {
  const [tripText, setTripText] = useState('');
  const [fileName, setFileName] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [step, setStep] = useState(0);

  const hasInput = tripText.trim().length > 12 || Boolean(fileName);
  const currentStep = notebookSteps[step];
  const Icon = currentStep.icon;

  const findings = useMemo(() => {
    if (!hasInput) {
      return ['Upload or paste a rough plan to start the notebook mode.'];
    }

    return [
      fileName ? `Source noted: ${fileName}` : 'Pasted plan captured',
      'Transfer timing needs a sanity check before payment',
      'One day looks crowded enough to deserve a pacing question',
      'Ask your planner to confirm document and cancellation assumptions',
    ];
  }, [fileName, hasInput]);

  function runNotebook() {
    if (!hasInput || isRunning) return;
    setIsRunning(true);
    setStep(0);
    const timers = [0, 850, 1700, 2550].map((delay, index) =>
      window.setTimeout(() => setStep(index), delay),
    );
    window.setTimeout(() => setIsRunning(false), 3300);
    return () => timers.forEach(window.clearTimeout);
  }

  return (
    <div className={styles.notebookExperience} id='notebook'>
      <section className={styles.notebookPanel}>
        <div className={styles.notebookHeader}>
          <div>
            <span className={styles.notebookLabel}>Minimal notebook mode</span>
            <h2>Give it a trip. Watch it think in a notebook.</h2>
          </div>
          <img src='/brand/waypoint-logo-notebook.svg' alt='Waypoint notebook mark' />
        </div>

        <label className={styles.fileDrop}>
          <input
            type='file'
            accept='.pdf,.txt,.png,.jpg,.jpeg'
            onChange={(event) => setFileName(event.target.files?.[0]?.name ?? '')}
          />
          <FileText className='h-5 w-5' />
          <span>{fileName || 'Upload PDF, screenshot, or notes'}</span>
        </label>

        <textarea
          className={styles.tripTextarea}
          value={tripText}
          onChange={(event) => setTripText(event.target.value)}
          placeholder='Paste a rough itinerary: flights, hotels, cities, dates, activities, transfers, concerns...'
        />

        <button
          type='button'
          className={styles.notebookButton}
          onClick={runNotebook}
          disabled={!hasInput || isRunning}
        >
          {isRunning ? <Loader2 className='h-4 w-4 animate-spin' /> : <Sparkles className='h-4 w-4' />}
          {isRunning ? 'Notebook is working' : 'Start notebook check'}
          <ArrowRight className='h-4 w-4' />
        </button>
      </section>

      <section className={styles.characterPanel} aria-live='polite'>
        <div className={styles.characterStage}>
          <div className={styles.character}>
            <div className={styles.characterHead} />
            <div className={styles.characterBody} />
            <div className={styles.characterArm} />
          </div>
          <div className={styles.openNotebook}>
            <div className={styles.notebookLine} />
            <div className={styles.notebookLine} />
            <div className={styles.notebookLineShort} />
            <div className={styles.pencilTrack} />
          </div>
          <Plane className={styles.planeIcon} />
        </div>

        <div className={styles.notebookStatus}>
          <span>{isRunning ? 'Working' : hasInput ? 'Ready' : 'Waiting'}</span>
          <h3>{currentStep.label}</h3>
          <p>{currentStep.text}</p>
        </div>

        <div className={styles.notebookSteps}>
          {notebookSteps.map((item, index) => (
            <div
              key={item.label}
              className={`${styles.notebookStep} ${index <= step && hasInput ? styles.notebookStepActive : ''}`}
            >
              {index < step && hasInput ? <CheckCircle2 className='h-4 w-4' /> : <CircleDashed className='h-4 w-4' />}
              <span>{item.label}</span>
            </div>
          ))}
        </div>

        <div className={styles.findingList}>
          {findings.map((finding) => (
            <div key={finding}>
              <BookOpen className='h-4 w-4' />
              <span>{finding}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
