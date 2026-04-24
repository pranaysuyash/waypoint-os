import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SPINE_API_URL = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward the refresh_token cookie to the backend
    const cookie = request.headers.get('cookie') || '';
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (cookie) headers['cookie'] = cookie;

    const response = await fetch(`${SPINE_API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();

    const nextResponse = NextResponse.json(data, { status: response.status });

    // Set new access_token cookie
    if (data.access_token) {
      nextResponse.cookies.set('access_token', data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });
    }

    // Forward new refresh_token cookie from backend
    const backendRefreshToken = response.headers.get('set-cookie');
    if (backendRefreshToken) {
      const match = backendRefreshToken.match(/refresh_token=([^;]+)/);
      if (match) {
        nextResponse.cookies.set('refresh_token', match[1], {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          path: '/api/auth',
          maxAge: 60 * 60 * 24 * 7, // 7 days
        });
      }
    }

    return nextResponse;
  } catch (error) {
    console.error('Refresh proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to refresh token' },
      { status: 500 }
    );
  }
}
