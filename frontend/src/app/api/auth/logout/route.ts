import { NextResponse } from 'next/server';

const SPINE_API_URL = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  try {
    // Forward logout to backend to clear refresh_token cookie
    await fetch(`${SPINE_API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('Backend logout error:', error);
    // Continue to clear cookies even if backend call fails
  }

  // Clear both cookies on the frontend response
  const nextResponse = NextResponse.json({ ok: true });
  nextResponse.cookies.set('access_token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 0,
  });
  nextResponse.cookies.set('refresh_token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/api/auth',
    maxAge: 0,
  });

  return nextResponse;
}
