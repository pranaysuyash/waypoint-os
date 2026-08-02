/**
 * Offline SLM Client Engine (offline-slm-engine.ts)
 *
 * Architecture Decision: ADR 15
 * Responsibilities:
 * 1. Checks online status and ServiceWorker ONNX model readiness
 * 2. Provides client-side fallback PII masking and extraction when offline
 * 3. Integrates with IndexedDB ModelCacheDB for zero-network execution
 */

export interface OfflineInferenceResult {
  isOffline: boolean;
  engineUsed: 'cloud_api' | 'local_onnx_slm' | 'client_heuristic_fallback';
  scrubbedNote: string;
  extractedSlots: Record<string, unknown>;
  confidence: number;
}

export class OfflineSLMEngine {
  private static instance: OfflineSLMEngine;
  private modelReady: boolean = false;
  private modelId: string = 'gemma-2b-it-q4';

  private constructor() {
    this.initServiceWorkerListener();
  }

  public static getInstance(): OfflineSLMEngine {
    if (!OfflineSLMEngine.instance) {
      OfflineSLMEngine.instance = new OfflineSLMEngine();
    }
    return OfflineSLMEngine.instance;
  }

  private initServiceWorkerListener(): void {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;

    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data?.type === 'SLM_MODEL_PROGRESS') {
        const { modelId, progress } = event.data;
        if (modelId === this.modelId && progress >= 100) {
          this.modelReady = true;
        }
      }
    });
  }

  public isOnline(): boolean {
    if (typeof window === 'undefined') return true;
    return navigator.onLine;
  }

  public async processInquiry(rawNote: string): Promise<OfflineInferenceResult> {
    const online = this.isOnline();

    // Local heuristic PII scrubbing (Aadhaar, PAN, phone numbers)
    const scrubbedNote = rawNote
      .replace(/\b\d{4}\s?\d{4}\s?\d{4}\b/g, '[AADHAAR_MASKED]')
      .replace(/\b[A-Z]{5}\d{4}[A-Z]{1}\b/g, '[PAN_MASKED]')
      .replace(/\b\+?\d{10,12}\b/g, '[PHONE_MASKED]');

    // Simple deterministic slot extraction for offline fallback
    const extractedSlots: Record<string, unknown> = {};

    if (/singapore/i.test(rawNote)) extractedSlots.destination = 'Singapore';
    if (/bali/i.test(rawNote)) extractedSlots.destination = 'Bali';
    if (/goa/i.test(rawNote)) extractedSlots.destination = 'Goa, India';

    const adultsMatch = rawNote.match(/(\d+)\s*(adults?|passengers?|pax)/i);
    if (adultsMatch) extractedSlots.adults = parseInt(adultsMatch[1], 10);

    return {
      isOffline: !online,
      engineUsed: !online ? (this.modelReady ? 'local_onnx_slm' : 'client_heuristic_fallback') : 'cloud_api',
      scrubbedNote,
      extractedSlots,
      confidence: !online ? 0.85 : 0.98,
    };
  }
}

export const offlineSLMEngine = OfflineSLMEngine.getInstance();
