"use client";

import { Trip } from "@/lib/api-client";
import { Star, MessageSquare, Info, CheckCircle2 } from "lucide-react";
import { ClientNow } from "@/hooks/useClientDate";
import styles from "@/components/workbench/workbench.module.css";

interface FeedbackPanelProps {
  trip: Trip;
}

export default function FeedbackPanel({ trip }: FeedbackPanelProps) {
  const feedback = trip.feedback;

  if (!feedback) {
    return (
      <div className={styles.emptyState}>
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <MessageSquare className="size-12 text-border-default mb-4" />
          <h3 className="text-ui-lg font-medium text-text-rationale mb-2">Awaiting Feedback</h3>
          <p className="text-ui-sm text-text-muted max-w-xs">
            We've reached out to the customer for their thoughts. Feedback will appear here once received.
          </p>
        </div>
      </div>
    );
  }

  const rating = feedback.rating;
  const stars = Array.from({ length: 5 }, (_, i) => i + 1);

  return (
    <div className="space-y-6">
      {/* Banner for Simulated Data */}
      {feedback.is_simulated && (
        <div className="p-3 bg-surface border border-border-default rounded-lg flex items-start gap-3">
          <Info className="size-4 text-accent-blue mt-0.5" />
          <div>
            <p className="text-ui-xs font-semibold text-accent-blue">FALLBACK DATA</p>
            <p className="text-[var(--ui-text-xs)] text-text-muted">
              This feedback is simulated to populate your dashboard. Real data will appear as customers reply.
            </p>
          </div>
        </div>
      )}

      {/* Main Scorecard */}
      <div className="p-8 bg-rationale border border-border-default rounded-2xl flex flex-col items-center text-center shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-50" />
        
        <div className="mb-6">
          <h3 className="text-ui-sm uppercase tracking-widest text-text-muted mb-4">Customer Satisfaction</h3>
          <div className="flex gap-2">
            {stars.map((s) => (
              <Star
                key={s}
                className={`size-8 ${
                  s <= rating ? "text-accent-amber fill-accent-amber" : "text-border-default"
                }`}
              />
            ))}
          </div>
        </div>

        <div className="relative">
          <MessageSquare className="size-4 text-border-default absolute -top-4 -left-4" />
          <p className="text-ui-lg text-text-primary italic leading-relaxed font-light text-center">
            "{feedback.notes}"
          </p>
          <MessageSquare className="size-4 text-border-default absolute -bottom-4 -right-4 rotate-180" />
        </div>

        <div className="mt-8 pt-6 border-t border-border-default w-full flex items-center justify-center gap-4">
          <div className="flex items-center gap-1.5 text-ui-xs text-accent-green font-medium px-3 py-1 bg-[#0f1d16] rounded-full">
            <CheckCircle2 className="size-3" />
            Verified Response
          </div>
          <span className="text-[var(--ui-text-xs)] text-text-muted">
            Received via WhatsApp • <ClientNow />
          </span>
        </div>
      </div>
      
      {/* Follow-up Opportunities (Mocked for Wave 9) */}
      <div className="space-y-4">
        <h4 className="text-ui-xs font-semibold text-text-muted uppercase tracking-wider px-2">Next Conversion Steps</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-elevated border border-border-default rounded-xl hover:bg-[#1c2128] cursor-pointer transition-all">
            <p className="text-ui-xs font-bold text-text-primary mb-1">Send Referral Link</p>
            <p className="text-[var(--ui-text-xs)] text-text-muted">Leverage high satisfaction for word-of-mouth.</p>
          </div>
          <div className="p-4 bg-elevated border border-border-default rounded-xl hover:bg-[#1c2128] cursor-pointer transition-all">
            <p className="text-ui-xs font-bold text-text-primary mb-1">Upsell Next Trip</p>
            <p className="text-[var(--ui-text-xs)] text-text-muted">Recommend similar destinations for Q4.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
