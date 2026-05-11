import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { Circle } from 'lucide-react';
import { Badge, badgeVariants, type BadgeProps } from '../badge';
import { Button, buttonVariants, type ButtonProps } from '../button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  type CardContentProps,
  type CardDescriptionProps,
  type CardFooterProps,
  type CardHeaderProps,
  type CardProps,
  type CardTitleProps,
} from '../card';
import { EmptyState, type EmptyStateAction } from '../empty-state';
import { IconButton, IconLink, IconWrapper } from '../icon';
import { Input, type InputProps } from '../input';
import { Skeleton, type SkeletonProps } from '../loading';
import { Select, type SelectOption, type SelectProps } from '../select';
import { StatusBadge, type StatusConfig, type StatusMap } from '../status-badge';
import { Textarea, type TextareaProps } from '../textarea';

describe('shared primitive surfaces', () => {
  it('renders Badge as a semantic inline status primitive', () => {
    const props: BadgeProps = { variant: 'manual', children: 'Manual' };
    render(<Badge {...props} />);

    expect(screen.getByText('Manual')).toHaveClass('inline-flex');
    expect(badgeVariants({ variant: 'manual' })).toContain('badge-manual');
  });

  it('renders Button with variant helpers and typed props', () => {
    const props: ButtonProps = { variant: 'secondary', children: 'Continue' };
    render(<Button {...props} />);

    expect(screen.getByRole('button', { name: 'Continue' })).toHaveClass('inline-flex');
    expect(buttonVariants({ variant: 'secondary' })).toContain('bg-elevated');
  });

  it('renders Card slots with typed primitive props', () => {
    const cardProps: CardProps = { variant: 'elevated' };
    const headerProps: CardHeaderProps = {};
    const titleProps: CardTitleProps = { level: 'h2' };
    const descriptionProps: CardDescriptionProps = {};
    const contentProps: CardContentProps = {};
    const footerProps: CardFooterProps = {};

    render(
      <Card {...cardProps}>
        <CardHeader {...headerProps}>
          <CardTitle {...titleProps}>Proposal health</CardTitle>
          <CardDescription {...descriptionProps}>Operator-facing card copy</CardDescription>
        </CardHeader>
        <CardContent {...contentProps}>Body</CardContent>
        <CardFooter {...footerProps}>Footer</CardFooter>
      </Card>
    );

    expect(screen.getByRole('heading', { name: 'Proposal health', level: 2 })).toBeInTheDocument();
    expect(screen.getByText('Operator-facing card copy')).toBeInTheDocument();
    expect(screen.getByText('Body')).toBeInTheDocument();
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });

  it('hides decorative IconWrapper content unless a label is provided', () => {
    const { rerender } = render(<IconWrapper><span>plane</span></IconWrapper>);

    expect(screen.getByText('plane').parentElement).toHaveAttribute('aria-hidden', 'true');

    rerender(<IconWrapper label='Travel mode'><span>plane</span></IconWrapper>);
    expect(screen.getByLabelText('Travel mode')).toHaveAttribute('role', 'img');
  });

  it('renders IconButton with an accessible label and default button type', () => {
    const onClick = vi.fn();
    render(<IconButton icon={<span>+</span>} label='Add traveler' onClick={onClick} />);

    const button = screen.getByRole('button', { name: 'Add traveler' });
    expect(button).toHaveAttribute('type', 'button');

    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders IconLink with visible children and an accessible label', () => {
    render(<IconLink href='/trips' icon={<span>→</span>} label='Open trips'>Trips</IconLink>);

    expect(screen.getByRole('link', { name: 'Open trips' })).toHaveAttribute('href', '/trips');
    expect(screen.getByText('Trips')).toBeInTheDocument();
  });

  it('renders Select with label, placeholder, and options', () => {
    const option: SelectOption = { value: 'beach', label: 'Beach' };
    const props: SelectProps = {
      label: 'Destination type',
      options: [option],
      defaultValue: '',
    };

    render(<Select {...props} />);

    expect(screen.getByLabelText('Destination type')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Select an option…' })).toBeDisabled();
    expect(screen.getByRole('option', { name: 'Beach' })).toHaveValue('beach');
  });

  it('renders Input with descriptions, errors, and typed props', () => {
    const props: InputProps = { label: 'Customer name', description: 'Visible to operators' };
    const { rerender } = render(<Input {...props} />);

    expect(screen.getByLabelText('Customer name')).toHaveAccessibleDescription('Visible to operators');

    rerender(<Input label='Customer name' error='Required' />);
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
    expect(screen.getByLabelText('Customer name')).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders EmptyState link and button action contracts', () => {
    const action: EmptyStateAction = { label: 'Create trip', href: '/trips/new' };
    const secondaryAction: EmptyStateAction = { label: 'Refresh', onClick: vi.fn() };

    render(
      <EmptyState
        title='No trips yet'
        description='Start from a customer brief.'
        action={action}
        secondaryAction={secondaryAction}
      />
    );

    expect(screen.getByRole('link', { name: 'Create trip' })).toHaveAttribute('href', '/trips/new');
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(secondaryAction.onClick).toHaveBeenCalledOnce();
  });

  it('renders Skeleton with typed presentation props', () => {
    const props: SkeletonProps = { variant: 'text', width: 120, height: 16, animation: 'none' };
    render(<Skeleton data-testid='skeleton' {...props} />);

    expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByTestId('skeleton')).toHaveStyle({ width: '120px', height: '16px' });
  });

  it('renders StatusBadge from an explicit status map contract', () => {
    const config: StatusConfig = { label: 'Ready', color: '#22c55e', icon: Circle };
    const map: StatusMap = { ready: config };

    render(<StatusBadge status='ready' map={map} />);

    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  it('renders Textarea with error wiring and resize control', () => {
    const props: TextareaProps = { label: 'Owner notes', error: 'Required', resize: 'none' };
    render(<Textarea {...props} />);

    const textarea = screen.getByLabelText('Owner notes');
    expect(textarea).toHaveAttribute('aria-invalid', 'true');
    expect(textarea).toHaveStyle({ resize: 'none' });
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });
});
