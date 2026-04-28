'use client';

import { X, Settings, ToggleLeft, ToggleRight, FileCode2, RotateCcw, ShieldAlert, Wrench, CheckCircle2, Ghost, Heart, Network, ShieldCheck } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';
import { useScenarios } from '@/hooks/useScenarios';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { useState } from 'react';

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const {
    strict_leakage,
    setStrictLeakage,
    debug_raw_json,
    setDebugRawJson,
    scenario_id,
    setScenarioId,
    setInputRawNote,
    setInputOwnerNote,
    setInputStructuredJson,
    setInputItineraryText,
    enable_ghost_concierge,
    setEnableGhostConcierge,
    enable_sentiment_analysis,
    setEnableSentimentAnalysis,
    federated_intelligence_opt_in,
    setFederatedIntelligenceOptIn,
    audit_confidence_threshold,
    setAuditConfidenceThreshold,
    enable_auto_negotiation,
    setEnableAutoNegotiation,
    negotiation_margin_threshold,
    setNegotiationMarginThreshold,
  } = useWorkbenchStore();
  const { data: scenarios, isLoading: scenariosLoading, error: scenariosError } = useScenarios();
  const { state: unifiedState, refresh: refreshUnified } = useUnifiedState();
  const [repairingId, setRepairingId] = useState<string | null>(null);
  const [repairStatus, setRepairStatus] = useState<{ id: string, success: boolean } | null>(null);
  const [isGeneratingScenario, setIsGeneratingScenario] = useState(false);
  const [scenarioGenStatus, setScenarioGenStatus] = useState<string | null>(null);
  const [scenarioSourceMode, setScenarioSourceMode] = useState<'docs' | 'fixtures' | 'llm'>('docs');

  const orphans = unifiedState?.orphans || [];

  const handleRepair = async (id: string) => {
    setRepairingId(id);
    try {
      const response = await fetch(`/api/trips/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: "include",
        body: JSON.stringify({ status: 'new' })
      });
      
      if (response.ok) {
        setRepairStatus({ id, success: true });
        refreshUnified();
        setTimeout(() => setRepairStatus(null), 3000);
      } else {
        setRepairStatus({ id, success: false });
      }
    } catch (err) {
      console.error('Repair failed:', err);
      setRepairStatus({ id, success: false });
    } finally {
      setRepairingId(null);
    }
  };

  const handleGenerateDevScenario = async () => {
    setIsGeneratingScenario(true);
    setScenarioGenStatus(null);
    try {
      const response = await fetch('/api/scenarios/dev/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          prompt: 'messy real-world intake scenario',
          source_mode: scenarioSourceMode,
        }),
      });
      if (!response.ok) {
        setScenarioGenStatus('Failed to generate scenario');
        return;
      }
      const payload = await response.json();
      const input = payload?.input;
      if (!input?.raw_note) {
        setScenarioGenStatus('Scenario generator returned invalid payload');
        return;
      }
      setScenarioId('');
      setInputRawNote(input.raw_note ?? '');
      setInputOwnerNote(input.owner_note ?? '');
      setInputStructuredJson(input.structured_json ? JSON.stringify(input.structured_json, null, 2) : '');
      setInputItineraryText(input.itinerary_text ?? '');
      setScenarioGenStatus(
        `Loaded ${payload?.source ?? 'generated'} scenario and saved fixture ${payload?.persisted_fixture?.file_name ?? ''}`.trim()
      );
    } catch (err) {
      console.error('Scenario generation failed:', err);
      setScenarioGenStatus('Failed to generate scenario');
    } finally {
      setIsGeneratingScenario(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div
        className='fixed inset-0 bg-black/50 z-40'
        onClick={onClose}
        aria-hidden='true'
      />
      <aside
        className='fixed right-0 top-0 bottom-0 w-80 bg-[#0f1115] border-l border-[#30363d] z-50 overflow-y-auto'
        role='dialog'
        aria-label='Pipeline settings'
      >
        <div className='flex items-center justify-between p-4 border-b border-[#30363d]'>
          <div className='flex items-center gap-2'>
            <Settings className='w-4 h-4 text-[#8b949e]' />
            <h2 className='text-sm font-semibold text-[#e6edf3]'>Settings</h2>
          </div>
          <button
            type='button'
            onClick={onClose}
            className='p-1 rounded hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] transition-colors'
            aria-label='Close settings'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='p-4 space-y-6'>
          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
              Safety
            </h3>
            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {strict_leakage ? (
                  <ToggleRight className='w-5 h-5 text-[#f85149]' />
                ) : (
                  <ToggleLeft className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Strict Leakage Check</p>
                  <p className='text-xs text-[#8b949e]'>
                    Block sending if any internal jargon is found
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={strict_leakage}
                onChange={(e) => setStrictLeakage(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  strict_leakage ? 'bg-[#f85149]' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    strict_leakage ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>
          </div>

          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide flex items-center gap-2'>
              <Ghost className='w-3 h-3 text-[#bb86fc]' />
              Advanced AI Features
            </h3>
            
            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {enable_ghost_concierge ? (
                  <Ghost className='w-5 h-5 text-[#bb86fc]' />
                ) : (
                  <Ghost className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Ghost Concierge</p>
                  <p className='text-xs text-[#8b949e]'>
                    Enable autonomic recovery workflows
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={enable_ghost_concierge}
                onChange={(e) => setEnableGhostConcierge(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  enable_ghost_concierge ? 'bg-[#bb86fc]' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    enable_ghost_concierge ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>

            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {enable_sentiment_analysis ? (
                  <Heart className='w-5 h-5 text-[#ff79c6]' />
                ) : (
                  <Heart className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Sentiment Detection</p>
                  <p className='text-xs text-[#8b949e]'>
                    Real-time tonal adaptation
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={enable_sentiment_analysis}
                onChange={(e) => setEnableSentimentAnalysis(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  enable_sentiment_analysis ? 'bg-[#ff79c6]' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    enable_sentiment_analysis ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>

            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {federated_intelligence_opt_in ? (
                  <Network className='w-5 h-5 text-[#50fa7b]' />
                ) : (
                  <Network className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Federated Intelligence</p>
                  <p className='text-xs text-[#8b949e]'>
                    Share anonymized risk data
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={federated_intelligence_opt_in}
                onChange={(e) => setFederatedIntelligenceOptIn(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  federated_intelligence_opt_in ? 'bg-[#50fa7b]' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    federated_intelligence_opt_in ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>

            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {enable_auto_negotiation ? (
                  <ToggleRight className='w-5 h-5 text-accent-blue' />
                ) : (
                  <ToggleLeft className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Auto-Negotiation</p>
                  <p className='text-xs text-[#8b949e]'>
                    Autonomous supplier negotiation
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={enable_auto_negotiation}
                onChange={(e) => setEnableAutoNegotiation(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  enable_auto_negotiation ? 'bg-accent-blue' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    enable_auto_negotiation ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>

            <div className='pt-2 space-y-2'>
              <div className='flex justify-between items-center'>
                <p className='text-xs text-[#e6edf3] flex items-center gap-1'>
                  <ShieldCheck className='w-3 h-3 text-accent-green' />
                  Negotiation Margin
                </p>
                <span className='text-[10px] font-mono text-accent-green'>
                  {(negotiation_margin_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type='range'
                min='0.05'
                max='0.5'
                step='0.05'
                value={negotiation_margin_threshold}
                onChange={(e) => setNegotiationMarginThreshold(parseFloat(e.target.value))}
                className='w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer accent-accent-green'
              />
              <p className='text-[10px] text-[#8b949e]'>
                Minimum expected margin before negotiation
              </p>
            </div>

            <div className='pt-2 space-y-2'>
              <div className='flex justify-between items-center'>
                <p className='text-xs text-[#e6edf3] flex items-center gap-1'>
                  <ShieldCheck className='w-3 h-3 text-[#58a6ff]' />
                  Audit Threshold
                </p>
                <span className='text-[10px] font-mono text-[#58a6ff]'>
                  {(audit_confidence_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type='range'
                min='0.5'
                max='1.0'
                step='0.05'
                value={audit_confidence_threshold}
                onChange={(e) => setAuditConfidenceThreshold(parseFloat(e.target.value))}
                className='w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer accent-[#58a6ff]'
              />
              <p className='text-[10px] text-[#8b949e]'>
                Confidence score below which human audit is triggered
              </p>
            </div>
          </div>

          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
              Scenario
            </h3>
            <select
              value={scenario_id}
              onChange={(e) => setScenarioId(e.target.value)}
              className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
            >
              <option value=''>No scenario (live input)</option>
              {scenariosLoading ? (
                <option value='' disabled>Loading scenarios...</option>
              ) : (
                scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))
              )}
            </select>
            <p className='text-xs text-[#8b949e]'>
              Pre-loaded test scenario for processing trips
            </p>
            <button
              type='button'
              onClick={handleGenerateDevScenario}
              disabled={isGeneratingScenario}
              className='w-full px-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-xs text-[#e6edf3] hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
            >
              {isGeneratingScenario ? 'Generating Dev Scenario...' : 'Generate Random Dev Scenario'}
            </button>
            <select
              value={scenarioSourceMode}
              onChange={(e) => setScenarioSourceMode(e.target.value as 'docs' | 'fixtures' | 'llm')}
              className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
            >
              <option value='docs'>Generate from Docs Templates</option>
              <option value='fixtures'>Generate from Fixture Templates</option>
              <option value='llm'>Generate via LLM (.env.local key)</option>
            </select>
            <p className='text-[10px] text-[#8b949e]'>
              Dev-only: explicit source selection. LLM mode reads `OPENAI_API_KEY` from `frontend/.env.local`. All generated scenarios are saved for reuse.
            </p>
            {scenarioGenStatus && (
              <p className='text-[10px] text-[#58a6ff]'>{scenarioGenStatus}</p>
            )}
            {scenariosError && (
              <p className='text-xs text-[#f85149] mt-1'>
                Failed to load scenarios: {scenariosError.message}
              </p>
            )}
          </div>

          <div className='space-y-3 pt-4 border-t border-[#30363d]'>
            <div className='flex items-center justify-between'>
              <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide flex items-center gap-2'>
                <ShieldAlert className='w-3 h-3 text-[#e3b341]' />
                Incomplete Trips
              </h3>
              {orphans.length > 0 && (
                <span className='px-1.5 py-0.5 rounded-full bg-[#e3b341]/20 text-[#e3b341] text-[10px] font-bold animate-pulse'>
                  {orphans.length} ISSUE{orphans.length !== 1 ? 'S' : ''}
                </span>
              )}
            </div>
            
            {orphans.length === 0 ? (
              <div className='p-3 rounded-lg bg-[#161b22] border border-[#30363d] text-center'>
                <p className='text-xs text-[#8b949e] italic'>No incomplete trip records detected.</p>
              </div>
            ) : (
              <div className='space-y-2 max-h-60 overflow-y-auto pr-1'>
                {orphans.map((orphan) => (
                  <div key={orphan.id} className='p-3 rounded-lg bg-[#161b22] border border-[#30363d] space-y-2'>
                    <div className='flex justify-between items-start'>
                      <div>
                        <p className='text-[10px] font-mono text-[#8b949e] truncate w-40'>{orphan.id}</p>
                        <p className='text-xs text-[#e6edf3] font-medium'>{orphan.destination}</p>
                      </div>
                      <button
                        onClick={() => handleRepair(orphan.id)}
                        disabled={repairingId === orphan.id}
                        className={`p-1.5 rounded transition-all ${
                          repairStatus?.id === orphan.id && repairStatus?.success
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-[#21262d] text-[#58a6ff] hover:bg-[#30363d] hover:scale-105'
                        }`}
                        title="Repair Record"
                      >
                        {repairingId === orphan.id ? (
                          <RotateCcw className='w-3 h-3 animate-spin' />
                        ) : repairStatus?.id === orphan.id && repairStatus?.success ? (
                          <CheckCircle2 className='w-3 h-3' />
                        ) : (
                          <Wrench className='w-3 h-3' />
                        )}
                      </button>
                    </div>
                      {repairStatus?.id === orphan.id && !repairStatus?.success && (
                      <p className='text-[10px] text-[#f85149]'>Failed to repair. Try again.</p>
                    )}
                  </div>
                ))}
              </div>
            )}
            <p className='text-[10px] text-[#8b949e] leading-relaxed'>
              Repairing resets an incomplete trip to "New" status so it can be processed again.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
