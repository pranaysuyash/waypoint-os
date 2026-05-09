'use client';

import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircleDashed,
  FileText,
  Loader2,
  MessageSquareText,
  NotebookPen,
  Plane,
  Search,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import styles from './marketing-v2.module.css';

type HeroSceneProps = {
  mode: 'checker';
};

export function HeroScene({ mode: _mode }: HeroSceneProps) {
  const nodes = ['Plan uploaded', 'Transfers checked', 'Pacing reviewed', 'Brief written'];

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
        <NotebookPen className='size-5 text-[#39d0d8]' />
        <strong>Trip notebook active</strong>
        <span>Findings become questions worth asking.</span>
      </div>
    </div>
  );
}

export function DataTransformationHero() {
  const [isStructured, setIsStructured] = useState(false);

  // Toggle every 4 seconds to show the transformation
  useEffect(() => {
    const timer = setInterval(() => {
      setIsStructured((prev) => !prev);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className={styles.agencyCockpit} aria-label='Waypoint OS product preview'>
      <div className={styles.cockpitHeader}>
        <div>
          <span>OPERATOR WORKSPACE</span>
          <strong>{isStructured ? 'Structured Brief' : 'Raw Inquiry'}</strong>
        </div>
        <div className={styles.cockpitPill} style={{ background: isStructured ? '#39d0d822' : '#58a6ff22', color: isStructured ? '#39d0d8' : '#58a6ff' }}>
          {isStructured ? 'NORMALIZED' : 'PROCESSING'}
        </div>
      </div>

      <div className={styles.transformationContainer}>
        {isStructured ? (
          <div className={styles.structuredView}>
            <div className={styles.cockpitPanelWide}>
              <div className={styles.panelTitle}>
                <FileText className='size-4' />
                <span>TRIP PACKET v0.2</span>
              </div>
              <div className={styles.packetGrid}>
                <div className={styles.packetItem}>
                  <span>Destination</span>
                  <strong>Amalfi Coast, Italy</strong>
                </div>
                <div className={styles.packetItem}>
                  <span>Travelers</span>
                  <strong>2 Adults, 2 Kids (8, 11)</strong>
                </div>
                <div className={styles.packetItem}>
                  <span>Dates</span>
                  <strong>June 14 - June 28</strong>
                </div>
                <div className={styles.packetItem}>
                  <span>Budget</span>
                  <strong>Premium ($25k - $30k)</strong>
                </div>
              </div>
              <div className={styles.blockerAlert}>
                <CircleDashed className='size-4 text-[#d29922]' />
                <span>Detected: Passport validity under 6 months for 1 passenger</span>
              </div>
            </div>
          </div>
        ) : (
          <div className={styles.rawView}>
            <div className={styles.cockpitPanelWide}>
              <div className={styles.panelTitle}>
                <MessageSquareText className='size-4' />
                <span>UNSTRUCTURED INTAKE</span>
              </div>
              <div className={styles.rawText}>
                "Hey Alex, looking at Italy again for the summer. Maybe Amalfi? 2 weeks in June. 
                Same group as last time. Need big rooms for the kids. One of the passports might be 
                expiring soon though, can we check that? Budget is around what we spent in Japan…"
              </div>
              <div className={styles.scanLine} />
            </div>
          </div>
        )}
      </div>

      <div className={styles.cockpitFooter}>
        <div className={styles.footerStep}>
          <div className={isStructured ? styles.stepActive : styles.stepInactive}>1</div>
          <span>Intake</span>
        </div>
        <div className={styles.footerLine} />
        <div className={styles.footerStep}>
          <div className={isStructured ? styles.stepActive : styles.stepInactive}>2</div>
          <span>Normalize</span>
        </div>
        <div className={styles.footerLine} />
        <div className={styles.footerStep}>
          <div className={isStructured ? styles.stepActive : styles.stepInactive}>3</div>
          <span>Detect Risks</span>
        </div>
      </div>
    </div>
  );
}

export function AgencyHeroCockpit() {
  return (
    <div className={styles.agencyCockpit} aria-label='Waypoint OS product preview'>
      <div className={styles.cockpitHeader}>
        <div>
          <span>Good morning, Alex</span>
          <strong>Here is what is moving today.</strong>
        </div>
        <div className={styles.cockpitCounters}>
          <span>Unread <strong>12</strong></span>
          <span>Action <strong>28</strong></span>
          <span>Trips <strong>74</strong></span>
        </div>
      </div>

      <div className={styles.dashboardGrid}>
        <section className={`${styles.cockpitPanel} ${styles.inboxPanel}`}>
          <div className={styles.panelTitle}>
            <UploadCloud className='size-4' />
            <span>Inbox</span>
          </div>
          {[
            ['New inquiry', 'Honeymoon in Italy', '5m', '#39d0d8'],
            ['Follow up', 'Family trip to Japan', '18m', '#58a6ff'],
            ['Change request', 'Photo safari route', '1h', '#8fb0c9'],
            ['Supplier update', 'DMC response', '2h', '#39d0d8'],
          ].map(([title, body, time, color]) => (
            <div key={title} className={styles.inboxRow}>
              <i style={{ background: color }} />
              <span><strong>{title}</strong>{body}</span>
              <em>{time}</em>
            </div>
          ))}
        </section>

        <section className={`${styles.cockpitPanel} ${styles.workspacePanel}`}>
          <div className={styles.panelTitle}>
            <NotebookPen className='size-4' />
            <span>Workspaces</span>
          </div>
          <div className={styles.stateRows}>
            {[
              ['Intake', '8', '#39d0d8'],
              ['Decision & Clarification', '12', '#58a6ff'],
              ['Quotes & Options', '15', '#39d0d8'],
              ['Booking Readiness', '9', '#8fb0c9'],
            ].map(([label, value, color]) => (
              <div key={label}>
                <span style={{ background: color }} />
                <strong>{label}</strong>
                <em>{value}</em>
              </div>
            ))}
          </div>
        </section>

        <section className={`${styles.cockpitPanel} ${styles.revenuePanel}`}>
          <div className={styles.panelTitle}>
            <Search className='size-4' />
            <span>Revenue MTD</span>
          </div>
          <div className={styles.revenueValue}>$284,600</div>
          <p className={styles.revenueDelta}>+18% vs last month</p>
          <div className={styles.routeMiniChart}>
            <i />
            <i />
            <i />
            <i />
          </div>
        </section>

        <section className={`${styles.cockpitPanel} ${styles.aiPanel}`}>
          <div className={styles.panelTitle}>
            <Sparkles className='size-4' />
            <span>AI Copilot</span>
          </div>
          <p className={styles.outputText}>27 tasks completed. 21 hours saved this week.</p>
        </section>
      </div>
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
          <FileText className='size-5' />
          <span>{fileName || 'Upload PDF, screenshot, or notes'}</span>
        </label>

        <textarea
          className={styles.tripTextarea}
          value={tripText}
          onChange={(event) => setTripText(event.target.value)}
          placeholder='Paste a rough itinerary: flights, hotels, cities, dates, activities, transfers, concerns…'
        />

        <button
          type='button'
          className={styles.notebookButton}
          onClick={runNotebook}
          disabled={!hasInput || isRunning}
        >
          {isRunning ? <Loader2 className='size-4 animate-spin' /> : <Sparkles className='size-4' />}
          {isRunning ? 'Notebook is working' : 'Start notebook check'}
          <ArrowRight className='size-4' />
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
              {index < step && hasInput ? <CheckCircle2 className='size-4' /> : <CircleDashed className='size-4' />}
              <span>{item.label}</span>
            </div>
          ))}
        </div>

        <div className={styles.findingList}>
          {findings.map((finding) => (
            <div key={finding}>
              <BookOpen className='size-4' />
              <span>{finding}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
