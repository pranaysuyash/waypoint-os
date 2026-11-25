import { NextRequest } from 'next/server';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { proxyRequest } from '@/lib/proxy-core';
import { DELETE, GET, POST } from '../route';

vi.mock('@/lib/proxy-core', () => ({ proxyRequest: vi.fn() }));

const authorization = 'Bearer synthetic-report-capability';

describe('checker report capability forwarding', () => {
  beforeEach(() => vi.clearAllMocks());

  it.each([
    [GET, 'GET', ['public-checker', 'trip', 'fixture']],
    [GET, 'GET', ['public-checker', 'trip', 'fixture', 'export']],
    [DELETE, 'DELETE', ['public-checker', 'trip', 'fixture']],
  ] as const)('forwards the capability for %s %s', async (handler, method, segments) => {
    const request = new NextRequest('http://localhost/api/' + segments.join('/'), {
      method,
      headers: { authorization },
    });
    await handler(request, { params: Promise.resolve({ path: [...segments] }) });
    expect(proxyRequest).toHaveBeenCalledWith(request, expect.objectContaining({
      extraHeaders: { authorization },
    }));
  });

  it('keeps the standard proxy policy for other checker routes', async () => {
    const request = new NextRequest('http://localhost/api/public-checker/run', {
      method: 'POST',
      headers: { authorization },
    });
    await POST(request, { params: Promise.resolve({ path: ['public-checker', 'run'] }) });
    expect(proxyRequest).toHaveBeenCalledWith(request, expect.objectContaining({
      extraHeaders: undefined,
    }));
  });
});
