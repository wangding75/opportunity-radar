import { configureApiClient, request } from './client';

export interface AuthConfig {
  auth_mode: 'disabled' | 'rbac';
  csrf_cookie_name: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  role: 'VIEWER' | 'RESEARCHER' | 'ADMIN' | 'OWNER';
  enabled: boolean;
}

export interface AuthSession {
  authenticated: boolean;
  actor: string;
  role: CurrentUser['role'];
  auth_type?: 'session' | 'api_token';
  scopes?: string[];
  user?: CurrentUser | null;
  auth_mode: AuthConfig['auth_mode'];
}

export interface BootstrapPayload {
  session: AuthSession;
  workspace: { id: string; name: string };
  feature_flags: { react_ui: boolean };
  modules: string[];
  server_time: string;
}

interface LoginResponse {
  user: CurrentUser;
  auth_mode: AuthConfig['auth_mode'];
}

export async function getAuthConfig(): Promise<AuthConfig> {
  const config = await request<AuthConfig>('/api/v1/auth/config');
  configureApiClient({ csrfCookieName: config.csrf_cookie_name });
  return config;
}

export const getCurrentUser = (): Promise<AuthSession> => request<AuthSession>('/api/v1/auth/me');

export const getBootstrap = (): Promise<BootstrapPayload> => request<BootstrapPayload>('/api/v1/auth/bootstrap');

export const login = (username: string, password: string): Promise<LoginResponse> =>
  request<LoginResponse>('/api/v1/auth/login', { method: 'POST', body: { username, password } });

export const logout = (): Promise<void> => request<void>('/api/v1/auth/logout', { method: 'POST', body: {} });
