import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProtectedSurfaceNotice } from '../ProtectedSurfaceNotice';

describe('ProtectedSurfaceNotice', () => {
  it('shows a clear sign-in path for protected surfaces', () => {
    render(
      <ProtectedSurfaceNotice
        surfaceName='Workbench'
        redirectTarget='/workbench?draft=new'
        description='Sign in to continue.'
      />
    );

    expect(screen.getByRole('heading', { name: /workbench/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /sign in to continue/i })[0]).toHaveAttribute(
      'href',
      '/login?redirect=%2Fworkbench%3Fdraft%3Dnew'
    );
  });
});
