"use client";

import { Trip } from "@/lib/api-client";
import { Star, MessageSquare, Info, CheckCircle2 } from "lucide-react";
import styles from "@/app/workbench/workbench.module.css";

interface FeedbackPanelProps {
  trip: Trip;
}

export function FeedbackPanel({ trip }: FeedbackPanelProps) {
  const feedback = trip.feedback;

  if (!feedback) {
    return (
      <div className={styles.emptyState}>
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <MessageSquare className="h-12 w-12 text-[#30363d] mb-4" />
          <h3 className="text-lg font-medium text-[#c9d1d9] mb-2">Awaiting Feedback</h3>
          <p className="text-sm text-[#8b949e] max-w-xs">
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
        <div className="p-3 bg-[#111b27] border border-[#16335a] rounded-lg flex items-start gap-3">
          <Info className="h-4 w-4 text-[#58a6ff] mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-[#58a6ff]">FALLBACK DATA</p>
            <p className="text-[11px] text-[#8b949e]">
              This feedback is simulated to populate your dashboard. Real data will appear as customers reply.
            </p>
          </div>
        </div>
      )}

      {/* Main Scorecard */}
      <div className="p-8 bg-[#0d1117] border border-[#30363d] rounded-2xl flex flex-col items-center text-center shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-50" />
        
        <div className="mb-6">
          <h3 className="text-sm uppercase tracking-widest text-[#8b949e] mb-4">Customer Satisfaction</h3>
          <div className="flex gap-2">
            {stars.map((s) => (
              <Star
                key={s}
                className={`h-8 w-8 ${
                  s <= rating ? "text-[#f2cc60] fill-[#f2cc60]" : "text-[#30363d]"
                }`}
              />
            ))}
          </div>
        </div>

        <div className="relative">
          <MessageSquare className="h-4 w-4 text-[#30363d] absolute -top-4 -left-4" />
          <p className="text-lg text-[#e6edf3] italic leading-relaxed font-light text-center">
            "{feedback.notes}"
          </p>
          <MessageSquare className="h-4 w-4 text-[#30363d] absolute -bottom-4 -right-4 rotate-180" />
        </div>

        <div className="mt-8 pt-6 border-t border-[#30363d] w-full flex items-center justify-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-[#3fb950] font-medium px-3 py-1 bg-[#0f1d16] rounded-full">
            <CheckCircle2 className="h-3 w-3" />
            Verified Response
          </div>
          <span className="text-[11px] text-[#8b949e]">
            Received via WhatsApp • {new Date().toLocaleDateString()}
          </span>
        </div>
      </div>
      
      {/* Follow-up Opportunities (Mocked for Wave 9) */}
      <div className="space-y-4">
        <h4 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider px-2">Next Conversion Steps</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl hover:bg-[#1c2128] cursor-pointer transition-all">
            <p className="text-xs font-bold text-[#e6edf3] mb-1">Send Referral Link</p>
            <p className="text-[10px] text-[#8b949e]">Leverage high satisfaction for word-of-mouth.</p>
          </div>
          <div className="p-4 bg-[#161b22] border border-[#30363d] rounded-xl hover:bg-[#1c2128] cursor-pointer transition-all">
            <p className="text-xs font-bold text-[#e6edf3] mb-1">Upsell Next Trip</p>
            <p className="text-[10px] text-[#8b949e]">Recommend similar destinations for Q4.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
