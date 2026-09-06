'use client';

import React, { useState } from 'react';
import { History, Undo2, Redo2, Check, Clock, User, ArrowRight } from 'lucide-react';

interface Checkpoint {
  id: string;
  timestamp: string;
  author: string;
  description: string;
  summaryDelta: string;
}

const SAMPLE_CHECKPOINTS: Checkpoint[] = [
  { id: 'chk_1', timestamp: '10:14 AM', author: 'Marcus Chen (Associate)', description: 'Initial Ingestion & Date Extraction', summaryDelta: 'Set destination Tokyo/Kyoto, Dates: Apr 10-20, 2027, Party: 3' },
  { id: 'chk_2', timestamp: '10:18 AM', author: 'Lars Lindqvist (DMC Lead)', description: 'Supplier Rate Bargaining Concession', summaryDelta: 'Secured -$700 concession from Bali DMC (Net: $7,420)' },
  { id: 'chk_3', timestamp: '10:25 AM', author: 'Elena Rostova (Agency Owner)', description: 'Dynamic Margin Curve Optimization', summaryDelta: 'Adjusted take-rate to 16.1% (+$862.25 gross margin)' },
  { id: 'chk_4', timestamp: '10:32 AM', author: 'Clara Sterling (Compliance)', description: 'Infant Bassinet & Layover Filter Lock', summaryDelta: 'Locked requires_infant_bassinet and 90m connection buffer' },
  { id: 'chk_5', timestamp: '10:45 AM', author: 'Marcus Chen (Associate)', description: 'VIP Proposal Final Compilation', summaryDelta: 'Generated 3-tier proposal with Aman Tokyo & Private Ryokan' },
];

export function TimeTravelScrubber() {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(SAMPLE_CHECKPOINTS.length - 1);

  const canUndo = currentStepIndex > 0;
  const canRedo = currentStepIndex < SAMPLE_CHECKPOINTS.length - 1;

  const handleUndo = () => {
    if (canUndo) setCurrentStepIndex(currentStepIndex - 1);
  };

  const handleRedo = () => {
    if (canRedo) setCurrentStepIndex(currentStepIndex + 1);
  };

  const activeCheckpoint = SAMPLE_CHECKPOINTS[currentStepIndex];

  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
        <div>
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Invertible Time-Travel & State Rollback Stack
          </h3>
          <p className="text-ui-xs text-muted-foreground">
            Lossless audit ledger. Test counterfactual changes and revert to any historical snapshot without data loss.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleUndo}
            disabled={!canUndo}
            className={`px-3 py-1.5 rounded-lg border text-ui-xs font-semibold flex items-center gap-1.5 transition-colors ${
              canUndo ? 'border-border text-foreground hover:bg-muted bg-background' : 'border-border/40 text-muted-foreground/40 cursor-not-allowed bg-background/50'
            }`}
          >
            <Undo2 className="h-3.5 w-3.5" />
            Undo
          </button>
          <button
            onClick={handleRedo}
            disabled={!canRedo}
            className={`px-3 py-1.5 rounded-lg border text-ui-xs font-semibold flex items-center gap-1.5 transition-colors ${
              canRedo ? 'border-border text-foreground hover:bg-muted bg-background' : 'border-border/40 text-muted-foreground/40 cursor-not-allowed bg-background/50'
            }`}
          >
            <Redo2 className="h-3.5 w-3.5" />
            Redo
          </button>
        </div>
      </div>

      {/* Scrubber Timeline */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-ui-xs text-muted-foreground">
          <span>Checkpoint Timeline ({currentStepIndex + 1} of {SAMPLE_CHECKPOINTS.length})</span>
          <span className="font-mono text-ui-2xs text-primary">Active: {activeCheckpoint.id}</span>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {SAMPLE_CHECKPOINTS.map((chk, idx) => {
            const isCurrent = idx === currentStepIndex;
            const isPast = idx < currentStepIndex;
            return (
              <button
                key={chk.id}
                onClick={() => setCurrentStepIndex(idx)}
                className={`p-2.5 rounded-lg border text-left transition-all ${
                  isCurrent ? 'bg-primary/10 border-primary ring-1 ring-primary' : isPast ? 'bg-background border-border hover:border-border/80' : 'bg-background/40 border-border/40 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between text-ui-2xs font-mono text-muted-foreground mb-1">
                  <span>{chk.timestamp}</span>
                  {isCurrent && <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />}
                </div>
                <div className="text-ui-xs font-semibold text-foreground truncate">
                  {chk.description}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active State Inspector Card */}
      <div className="p-4 rounded-xl bg-background border border-border space-y-2">
        <div className="flex items-center justify-between text-ui-xs">
          <div className="flex items-center gap-2 text-foreground font-semibold">
            <Check className="h-4 w-4 text-emerald-400" />
            <span>Active Checkpoint: {activeCheckpoint.description}</span>
          </div>
          <span className="text-ui-2xs text-muted-foreground flex items-center gap-1 font-mono">
            <User className="h-3 w-3" />
            {activeCheckpoint.author}
          </span>
        </div>
        <p className="text-ui-xs text-muted-foreground pl-6">
          <span className="text-foreground font-medium">State Mutation Delta: </span>
          {activeCheckpoint.summaryDelta}
        </p>
      </div>
    </div>
  );
}
