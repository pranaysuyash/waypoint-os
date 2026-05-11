'use client';

import { Suspense, useMemo, useState, useId } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FileCode2, Loader2, Search, Sparkles } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';
import { useScenarios } from '@/hooks/useScenarios';
import { getScenario, type ScenarioListItem } from '@/lib/api-client';

type ScenarioSourceMode = 'docs' | 'fixtures' | 'llm';

function formatScenarioLabel(item: ScenarioListItem) {
  const sourceLabel = item.source === 'doc' ? 'DOC' : 'FIX';
  return `${sourceLabel} · ${item.title}`;
}

function ScenarioLabInner() {
  const { replace } = useRouter();
  const searchParams = useSearchParams();
  const {
    scenario_id,
    setScenarioId,
    setStage,
    setOperatingMode,
    setInputRawNote,
    setInputOwnerNote,
    setInputStructuredJson,
    setInputItineraryText,
  } = useWorkbenchStore();
  const { data: scenarios, isLoading: scenariosLoading, error: scenariosError, refetch } = useScenarios();
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoadingScenario, setIsLoadingScenario] = useState(false);
  const [scenarioSourceMode, setScenarioSourceMode] = useState<ScenarioSourceMode>('docs');
  const [isGeneratingScenario, setIsGeneratingScenario] = useState(false);
  const [scenarioLabStatus, setScenarioLabStatus] = useState<string | null>(null);
  const scenarioCatalogId = useId();
  const generateModeId = useId();
  const [generatedScenario, setGeneratedScenario] = useState<{
    title: string;
    source: string;
    scenarioId: string;
    fileName: string;
    rawNote: string;
    ownerNote: string;
  } | null>(null);

  const filteredScenarios = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return scenarios;
    return scenarios.filter((item) => {
      const haystack = [item.title, item.id, item.description ?? '', item.source ?? ''].join(' ').toLowerCase();
      return haystack.includes(query);
    });
  }, [scenarios, searchTerm]);

  const selectedScenario = useMemo(
    () => scenarios.find((item) => item.id === scenario_id) ?? null,
    [scenario_id, scenarios]
  );

  const docCount = scenarios.filter((item) => item.source === 'doc').length;
  const fixtureCount = scenarios.filter((item) => item.source !== 'doc').length;

  const updateConfigParams = (stage: string, mode: string, scenarioId: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('stage', stage);
    params.set('mode', mode);
    params.set('scenario', scenarioId);
    replace(`?${params.toString()}`, { scroll: false });
    setStage(stage as Parameters<typeof setStage>[0]);
    setOperatingMode(mode as Parameters<typeof setOperatingMode>[0]);
  };

  const applyScenarioDetail = (detail: Awaited<ReturnType<typeof getScenario>>, title?: string) => {
    setInputRawNote(detail.input.raw_note ?? '');
    setInputOwnerNote(detail.input.owner_note ?? '');
    setInputStructuredJson(detail.input.structured_json ? JSON.stringify(detail.input.structured_json, null, 2) : '');
    setInputItineraryText(detail.input.itinerary_text ?? '');
    setScenarioId(detail.id);
    updateConfigParams(detail.input.stage, detail.input.mode, detail.id);
    setScenarioLabStatus(`Loaded ${title ?? detail.id} into intake`);
  };

  const handleLoadScenario = async () => {
    if (!scenario_id) {
      setScenarioLabStatus('Pick a scenario first');
      return;
    }

    setIsLoadingScenario(true);
    setScenarioLabStatus(null);
    try {
      const detail = await getScenario(scenario_id);
      applyScenarioDetail(detail, selectedScenario?.title);
    } catch (error) {
      console.error('Failed to load scenario:', error);
      setScenarioLabStatus('Failed to load selected scenario');
    } finally {
      setIsLoadingScenario(false);
    }
  };

  const handleGenerateDevScenario = async () => {
    setIsGeneratingScenario(true);
    setScenarioLabStatus(null);
    setGeneratedScenario(null);
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
        setScenarioLabStatus('Failed to generate scenario');
        return;
      }

      const payload = await response.json();
      const input = payload?.input;
      const persisted = payload?.persisted_fixture;

      if (!input?.raw_note) {
        setScenarioLabStatus('Scenario generator returned invalid payload');
        return;
      }

      setInputRawNote(input.raw_note ?? '');
      setInputOwnerNote(input.owner_note ?? '');
      setInputStructuredJson(input.structured_json ? JSON.stringify(input.structured_json, null, 2) : '');
      setInputItineraryText(input.itinerary_text ?? '');
      updateConfigParams(input.stage ?? 'discovery', input.operating_mode ?? 'normal_intake', persisted?.scenario_id ?? '');
      setGeneratedScenario({
        title: payload?.title ?? 'Generated scenario',
        source: payload?.source ?? 'generated',
        scenarioId: persisted?.scenario_id ?? '',
        fileName: persisted?.file_name ?? '',
        rawNote: String(input.raw_note ?? ''),
        ownerNote: String(input.owner_note ?? ''),
      });
      setScenarioLabStatus(
        `Loaded ${payload?.source ?? 'generated'} scenario and saved fixture ${persisted?.file_name ?? ''}`.trim()
      );
      await refetch();
      if (persisted?.scenario_id) {
        setScenarioId(persisted.scenario_id);
      }
    } catch (error) {
      console.error('Scenario generation failed:', error);
      setScenarioLabStatus('Failed to generate scenario');
    } finally {
      setIsGeneratingScenario(false);
    }
  };

  return (
    <section className='rounded-xl border border-[#30363d] bg-[#0f1115] overflow-hidden'>
      <div className='flex items-start justify-between gap-4 border-b border-[#30363d] px-4 py-3'>
        <div className='space-y-1'>
          <div className='flex items-center gap-2'>
            <Sparkles className='size-4 text-[var(--accent-blue)]' />
            <h2 className='text-ui-sm font-semibold text-[#e6edf3]'>Scenario Lab</h2>
          </div>
          <p className='text-ui-xs text-[var(--text-muted)]'>
            Browse the full doc-backed catalog, load a scenario into the intake fields, or generate a fresh dev case.
          </p>
        </div>
        <div className='text-right text-[var(--ui-text-xs)] text-[var(--text-muted)]'>
          <div>{docCount} docs</div>
          <div>{fixtureCount} fixtures</div>
        </div>
      </div>

      <div className='grid gap-4 p-4 lg:grid-cols-[1.25fr_0.95fr]'>
        <div className='space-y-3'>
          <div className='flex items-center gap-2 rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2'>
            <Search className='size-4 text-[var(--text-muted)]' />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder='Filter by title, doc id, or source'
              className='w-full bg-transparent text-ui-sm text-[#e6edf3] outline-none placeholder:text-[#484f58]'
            />
          </div>

          <div className='space-y-2'>
            <label htmlFor={scenarioCatalogId} className='text-[var(--ui-text-xs)] font-semibold uppercase tracking-wide text-[var(--text-muted)]'>
              Scenario catalog
            </label>
            <select
              id={scenarioCatalogId}
              value={scenario_id}
              onChange={(e) => setScenarioId(e.target.value)}
              className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-ui-sm text-[#e6edf3] outline-none focus:border-[var(--accent-blue)]'
            >
              <option value=''>Select a scenario</option>
              {scenariosLoading ? (
                <option value='' disabled>Loading scenarios…</option>
              ) : (
                filteredScenarios.map((item) => (
                  <option key={item.id} value={item.id}>
                    {formatScenarioLabel(item)}
                  </option>
                ))
              )}
            </select>
            <div className='flex flex-wrap items-center gap-2'>
              <button
                type='button'
                onClick={handleLoadScenario}
                disabled={isLoadingScenario || !scenario_id}
                className='inline-flex items-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 text-ui-xs font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] disabled:cursor-not-allowed disabled:opacity-50'
              >
                {isLoadingScenario ? <Loader2 className='size-3.5 animate-spin' /> : <FileCode2 className='size-3.5' />}
                Load into intake
              </button>
              <span className='text-[var(--ui-text-xs)] text-[var(--text-muted)]'>
                Selected scenario becomes the working intake payload.
              </span>
            </div>
            {selectedScenario && (
              <p className='text-[var(--ui-text-xs)] text-[var(--text-muted)]'>
                {selectedScenario.source === 'doc' ? 'Doc template' : 'Fixture'}: {selectedScenario.description ?? selectedScenario.title}
              </p>
            )}
            {scenarioLabStatus && (
              <p className='text-[var(--ui-text-xs)] text-[var(--accent-blue)]'>{scenarioLabStatus}</p>
            )}
            {scenariosError && (
              <p className='text-ui-xs text-[#f85149]'>
                Failed to load scenarios: {scenariosError.message}
              </p>
            )}
          </div>
        </div>

        <div className='space-y-3'>
          <div className='space-y-2 rounded-lg border border-[#30363d] bg-[#0d1117] p-3'>
            <div className='flex items-center justify-between gap-2'>
              <label htmlFor={generateModeId} className='text-[var(--ui-text-xs)] font-semibold uppercase tracking-wide text-[var(--text-muted)]'>
                Generate dev scenario
              </label>
              <span className='text-[var(--ui-text-xs)] text-[var(--text-muted)]'>
                Docs first, fixtures second, LLM last
              </span>
            </div>
            <select
              id={generateModeId}
              value={scenarioSourceMode}
              onChange={(e) => setScenarioSourceMode(e.target.value as ScenarioSourceMode)}
              className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-ui-xs text-[#e6edf3] outline-none focus:border-[var(--accent-blue)]'
            >
              <option value='docs'>Generate from Docs Templates</option>
              <option value='fixtures'>Generate from Fixture Templates</option>
              <option value='llm'>Generate via LLM (.env.local key)</option>
            </select>
            <button
              type='button'
              onClick={handleGenerateDevScenario}
              disabled={isGeneratingScenario}
              className='w-full rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 text-ui-xs font-medium text-[#e6edf3] transition-colors hover:bg-[#21262d] disabled:cursor-not-allowed disabled:opacity-50'
            >
              {isGeneratingScenario ? 'Generating Dev Scenario…' : 'Generate Random Dev Scenario'}
            </button>
            <p className='text-[var(--ui-text-xs)] text-[var(--text-muted)]'>
              LLM mode reads `OPENAI_API_KEY` from `frontend/.env.local`. Every generated scenario is saved for reuse.
            </p>
          </div>

          {generatedScenario && (
            <div className='space-y-2 rounded-lg border border-[#30363d] bg-[#161b22] p-3'>
              <div className='flex items-center justify-between gap-2'>
                <p className='text-[var(--ui-text-xs)] font-semibold uppercase tracking-wide text-[var(--accent-blue)]'>
                  Generated scenario
                </p>
                <span className='text-[var(--ui-text-xs)] text-[var(--text-muted)] truncate'>
                  {generatedScenario.source}
                </span>
              </div>
              <div className='space-y-1'>
                <p className='text-ui-xs font-medium text-[#e6edf3] truncate'>{generatedScenario.title}</p>
                <p className='text-[var(--ui-text-xs)] text-[var(--text-muted)] break-all'>
                  {generatedScenario.scenarioId || 'No scenario id'}
                </p>
                <p className='text-[var(--ui-text-xs)] text-[var(--text-muted)] break-all'>
                  {generatedScenario.fileName ? `Saved as ${generatedScenario.fileName}` : 'Not yet saved'}
                </p>
              </div>
              <div className='rounded-md border border-[#30363d] bg-[#0d1117] p-2'>
                <p className='mb-1 text-[var(--ui-text-xs)] uppercase tracking-wide text-[var(--text-muted)]'>Raw note preview</p>
                <p className='whitespace-pre-wrap break-words text-[var(--ui-text-xs)] leading-snug text-[var(--text-secondary)]'>
                  {generatedScenario.rawNote.slice(0, 220)}
                  {generatedScenario.rawNote.length > 220 ? '…' : ''}
                </p>
              </div>
              <div className='rounded-md border border-[#30363d] bg-[#0d1117] p-2'>
                <p className='mb-1 text-[var(--ui-text-xs)] uppercase tracking-wide text-[var(--text-muted)]'>Owner note</p>
                <p className='whitespace-pre-wrap break-words text-[var(--ui-text-xs)] leading-snug text-[var(--text-secondary)]'>
                  {generatedScenario.ownerNote.slice(0, 220)}
                  {generatedScenario.ownerNote.length > 220 ? '…' : ''}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default function ScenarioLab() {
  return (
    <Suspense fallback={<div className="p-4 text-ui-sm text-[#8b949e]">Loading scenario lab…</div>}>
      <ScenarioLabInner />
    </Suspense>
  );
}
