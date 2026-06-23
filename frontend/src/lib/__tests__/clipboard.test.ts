import { afterEach, describe, expect, it, vi } from 'vitest';
import { safeWriteClipboardText } from '@/lib/clipboard';

describe('safeWriteClipboardText', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('falls back to execCommand when clipboard permission is denied', async () => {
    const writeText = vi.fn();
    const query = vi.fn().mockResolvedValue({ state: 'denied' });
    const execCommand = vi.fn().mockReturnValue(true);

    vi.stubGlobal('navigator', {
      clipboard: { writeText },
      permissions: { query },
    });
    vi.stubGlobal('document', {
      createElement: vi.fn(() => ({
        value: '',
        setAttribute: vi.fn(),
        style: {},
        select: vi.fn(),
        setSelectionRange: vi.fn(),
      })),
      body: {
        appendChild: vi.fn(),
        removeChild: vi.fn(),
      },
      execCommand,
    });

    const result = await safeWriteClipboardText('https://example.com/join/abc');

    expect(result).toBe(true);
    expect(query).toHaveBeenCalledWith({ name: 'clipboard-write' });
    expect(writeText).not.toHaveBeenCalled();
    expect(execCommand).toHaveBeenCalledWith('copy');
  });
});
