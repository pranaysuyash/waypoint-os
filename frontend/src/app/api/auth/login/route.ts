import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SPINE_API_URL = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await fetch(`${SPINE_API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // The backend returns access_token in body and sets refresh_token as httpOnly cookie.
    // We forward the refresh_token cookie and also set access_token as a cookie
    // so that Next.js middleware can read it server-side.
    const nextResponse = NextResponse.json(data, { status: response.status });

    // Set access_token as httpOnly cookie for middleware visibility
    if (data.access_token) {
      nextResponse.cookies.set('access_token', data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });
    }

    // Forward the refresh_token cookie from backend response
    const backendRefreshToken = response.headers.get('set-cookie');
    if (backendRefreshToken) {
      // Parse the refresh_token from the backend's Set-Cookie header
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
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to proxy login request' },
      { status: 500 }
    );
  }
}
