import type { Metadata } from 'next';
import './auth.css';

export const metadata: Metadata = {
  title: 'Waypoint OS — Sign In',
  description: 'Sign in to your Waypoint workspace',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className='auth-layout'>
      <div className='auth-bg' />
      <div className='auth-container'>
        <div className='auth-brand'>
          <div className='auth-brand-icon'>W</div>
          <span className='auth-brand-text'>Waypoint</span>
        </div>
        {children}
      </div>
    </div>
  );
}
