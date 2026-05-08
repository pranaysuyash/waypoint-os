import { describe, expect, it } from "vitest";
import { forwardAuthHeaders } from "../proxy-core";

function mockNextRequest({
  headers = {},
  url = "http://localhost/api/test",
  method = "GET",
}: {
  headers?: Record<string, string>;
  url?: string;
  method?: string;
}) {
  return {
    headers: new Headers(headers),
    url,
    method,
  } as unknown as Request & { url: string; method: string; headers: Headers };
}

describe("forwardAuthHeaders", () => {
  it("forwards only cookie-based auth context and never forwards Authorization", () => {
    const req = mockNextRequest({
      headers: {
        accept: "application/json",
        "content-type": "application/json",
        authorization: "Bearer stale-client-token",
        cookie: "access_token=legacy-token; theme=dark",
        "x-request-id": "request-1",
      },
    });

    const headers = forwardAuthHeaders(req as any);

    expect(headers["authorization"]).toBeUndefined();
    expect(headers["cookie"]).toBe("access_token=legacy-token; theme=dark");
    expect(headers["Accept"]).toBe("application/json");
    expect(headers["content-type"]).toBe("application/json");
    expect(headers["x-request-id"]).toBe("request-1");
  });
});
