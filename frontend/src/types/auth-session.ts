export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  platform_role?: 'none' | 'support' | 'ops_admin' | 'super_admin';
}

export interface AuthAgency {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
}

export interface AuthMembership {
  role: string;
  isPrimary: boolean;
}

export interface AuthSession {
  user: AuthUser;
  agency: AuthAgency;
  membership: AuthMembership;
}
