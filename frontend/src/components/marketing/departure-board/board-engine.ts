import type { FlapCellSpec } from "./board-fixtures";

export const SOLARI_DRUM_ALPHABET: readonly string[] = [
  " ",
  "A",
  "B",
  "C",
  "D",
  "E",
  "F",
  "G",
  "H",
  "I",
  "J",
  "K",
  "L",
  "M",
  "N",
  "O",
  "P",
  "Q",
  "R",
  "S",
  "T",
  "U",
  "V",
  "W",
  "X",
  "Y",
  "Z",
  "0",
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "+",
  "-",
  "?",
  ".",
  "/",
];

export interface FlapStepFrame {
  topText: string;
  bottomText?: string;
  variant: FlapCellSpec["variant"];
  subLabel?: string;
}

/**
 * Computes whether two FlapCellSpec descriptors represent the exact same visual tile.
 */
export function isSameFlapCell(a: FlapCellSpec, b: FlapCellSpec): boolean {
  return (
    a.topText === b.topText &&
    (a.bottomText ?? "") === (b.bottomText ?? "") &&
    a.variant === b.variant &&
    (a.subLabel ?? "") === (b.subLabel ?? "")
  );
}

/**
 * Generates a realistic sequence of intermediate drum flaps between `fromCell` and `toCell`.
 * - Unchanged cells return `[toCell]` (zero flips) unless `forceCascade` is true.
 * - Multi-character two-line yellow hazard flaps (`NEED / CONFIRMATION`) cycle through
 *   a brief mechanical drum roll before locking into the signal-yellow hazard plates.
 */
export function computeFlapSequence(
  fromCell: FlapCellSpec,
  toCell: FlapCellSpec,
  options?: {
    maxSteps?: number;
    forceCascade?: boolean;
    seedOffset?: number;
  }
): FlapStepFrame[] {
  const maxSteps = options?.maxSteps ?? 6;
  const forceCascade = options?.forceCascade ?? false;
  const seed = options?.seedOffset ?? 0;

  if (!forceCascade && isSameFlapCell(fromCell, toCell)) {
    return [
      {
        topText: toCell.topText,
        bottomText: toCell.bottomText,
        variant: toCell.variant,
        subLabel: toCell.subLabel,
      },
    ];
  }

  // Determine intermediate step count (between 4 and maxSteps)
  const stepCount = Math.max(4, Math.min(maxSteps, 4 + ((seed * 3 + 1) % 4)));
  const startChar = (fromCell.topText.trim()[0] ?? " ").toUpperCase();
  const targetChar = (toCell.topText.trim()[0] ?? " ").toUpperCase();

  const startIdx = Math.max(0, SOLARI_DRUM_ALPHABET.indexOf(startChar));
  const targetIdx = Math.max(0, SOLARI_DRUM_ALPHABET.indexOf(targetChar));

  const alphabetLen = SOLARI_DRUM_ALPHABET.length;
  const forwardDist =
    (targetIdx - startIdx + alphabetLen) % alphabetLen || alphabetLen;

  const frames: FlapStepFrame[] = [];

  for (let i = 1; i < stepCount; i++) {
    const progress = i / stepCount;
    const charIdx =
      (startIdx + Math.max(1, Math.round(forwardDist * progress))) %
      alphabetLen;
    const ch = SOLARI_DRUM_ALPHABET[charIdx] ?? " ";

    frames.push({
      topText: ch,
      bottomText: undefined,
      // Intermediate drum leaves are cream or dark mechanical plates before settling on final state
      variant:
        toCell.variant === "yellow_two_line" && i === stepCount - 1
          ? "yellow_two_line"
          : "cream",
      subLabel: undefined,
    });
  }

  frames.push({
    topText: toCell.topText,
    bottomText: toCell.bottomText,
    variant: toCell.variant,
    subLabel: toCell.subLabel,
  });

  return frames;
}

/**
 * Computes staggered motor start delay (ms) for a cell at `(rowIdx, colIdx)`.
 */
export function computeCellStartDelayMs(rowIdx: number, colIdx: number): number {
  const rowDelay = rowIdx * 58;
  const colDelay = colIdx * 24;
  const jitter = ((rowIdx * 7 + colIdx * 13) % 5) * 4;
  return rowDelay + colDelay + jitter;
}

/**
 * Procedural Web Audio API Solari split-flap mechanical clack synthesizer.
 * Zero external audio files required; respects browser autoplay rules and mute state.
 */
class SplitFlapAudioController {
  private ctx: AudioContext | null = null;
  private enabled = true;
  private lastClackAt = 0;

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(next: boolean): void {
    this.enabled = next;
  }

  public toggle(): boolean {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.playConfirmationLatch();
    }
    return this.enabled;
  }

  private ensureContext(): AudioContext | null {
    if (typeof window === "undefined") return null;
    if (!this.ctx) {
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext;
      if (!AudioCtx) return null;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {
        // Ignore autoplay restriction until user gesture
      });
    }
    return this.ctx;
  }

  /**
   * Fires a single mechanical flap leaf impact sound with stereo placement.
   */
  public playFlapClack(colIndex = 4, isFinalSettle = false): void {
    if (!this.enabled) return;
    const nowMs = typeof performance !== "undefined" ? performance.now() : Date.now();
    // Rate-limit dense cascades to avoid audio clipping while keeping rich mechanical texture
    if (nowMs - this.lastClackAt < 18 && !isFinalSettle) return;
    this.lastClackAt = nowMs;

    const ctx = this.ensureContext();
    if (!ctx || ctx.state !== "running") return;

    const t = ctx.currentTime;

    // 1. Short noise burst for PVC/aluminum leaf slap
    const bufferSize = Math.floor(ctx.sampleRate * 0.018);
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      const decay = Math.exp(-i / (bufferSize * 0.28));
      data[i] = (Math.random() * 2 - 1) * decay;
    }

    const noise = ctx.createBufferSource();
    noise.buffer = noiseBuffer;

    const filter = ctx.createBiquadFilter();
    filter.type = "bandpass";
    const baseFreq = isFinalSettle ? 1720 : 2150;
    const detune = ((colIndex * 97) % 420) - 210;
    filter.frequency.setValueAtTime(baseFreq + detune, t);
    filter.Q.setValueAtTime(isFinalSettle ? 3.2 : 4.5, t);

    const gain = ctx.createGain();
    const peakGain = isFinalSettle ? 0.055 : 0.032;
    gain.gain.setValueAtTime(peakGain, t);
    gain.gain.exponentialRampToValueAtTime(0.0008, t + 0.017);

    // 2. Low-mid steel chassis resonance thump
    const osc = ctx.createOscillator();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(isFinalSettle ? 195 : 245, t);
    osc.frequency.exponentialRampToValueAtTime(82, t + 0.024);

    const bodyGain = ctx.createGain();
    bodyGain.gain.setValueAtTime(isFinalSettle ? 0.038 : 0.018, t);
    bodyGain.gain.exponentialRampToValueAtTime(0.0005, t + 0.025);

    // Stereo panning (+0.12 to +0.48 since board is on the right half of the stage)
    if (typeof ctx.createStereoPanner === "function") {
      const panner = ctx.createStereoPanner();
      const pan = Math.max(-0.4, Math.min(0.65, 0.12 + (colIndex / 15) * 0.38));
      panner.pan.setValueAtTime(pan, t);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(panner);

      osc.connect(bodyGain);
      bodyGain.connect(panner);

      panner.connect(ctx.destination);
    } else {
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.connect(bodyGain);
      bodyGain.connect(ctx.destination);
    }

    noise.start(t);
    noise.stop(t + 0.018);
    osc.start(t);
    osc.stop(t + 0.026);
  }

  /**
   * Plays a subtle dual-relay confirmation latch when the board resolves.
   */
  public playConfirmationLatch(): void {
    if (!this.enabled) return;
    const ctx = this.ensureContext();
    if (!ctx || ctx.state !== "running") return;

    this.playFlapClack(6, true);
    setTimeout(() => {
      this.playFlapClack(9, true);
    }, 55);
  }
}

export const splitFlapAudio = new SplitFlapAudioController();
