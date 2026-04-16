import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardContent, CardFooter } from '../card';

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(
      <Card>
        <span>Test content</span>
      </Card>
    );
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <Card className='custom-class'>
        <span>Content</span>
      </Card>
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders with CardHeader', () => {
    render(
      <Card>
        <CardHeader>
          <h2>Header Title</h2>
        </CardHeader>
      </Card>
    );
    expect(screen.getByText('Header Title')).toBeInTheDocument();
  });

  it('renders with CardContent', () => {
    render(
      <Card>
        <CardContent>
          <p>Card content</p>
        </CardContent>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with CardFooter', () => {
    render(
      <Card>
        <CardFooter>
          <button>Action</button>
        </CardFooter>
      </Card>
    );
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('renders complete card structure', () => {
    render(
      <Card>
        <CardHeader>
          <h2>Title</h2>
        </CardHeader>
        <CardContent>
          <p>Content</p>
        </CardContent>
        <CardFooter>
          <button>Action</button>
        </CardFooter>
      </Card>
    );

    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });
});
