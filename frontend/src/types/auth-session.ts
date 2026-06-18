export interface AuthUser {
  id: string;
  email: string;
  name?: string;
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
