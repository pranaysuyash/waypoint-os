import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SPINE_API_URL = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await fetch(`${SPINE_API_URL}/api/auth/confirm-password-reset`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(errorData, { status: response.status });
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Confirm password reset error:', error);
    return NextResponse.json(
      { error: 'Failed to confirm password reset' },
      { status: 500 }
    );
  }
}
