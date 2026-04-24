import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SPINE_API_URL = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  try {
    // Forward the access_token cookie or Authorization header to the backend
    const cookie = request.headers.get('cookie') || '';
    const authHeader = request.headers.get('authorization') || '';

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (cookie) headers['cookie'] = cookie;
    if (authHeader) headers['authorization'] = authHeader;

    const response = await fetch(`${SPINE_API_URL}/api/auth/me`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Me proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user info' },
      { status: 500 }
    );
  }
}
