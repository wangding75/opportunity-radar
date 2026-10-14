import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { ApiError } from '@/api/client';
import { AuthSession, CurrentUser, getAuthConfig, getBootstrap, login as loginRequest, logout as logoutRequest } from '@/api/auth';

type AuthStatus = 'loading' | 'authenticated' | 'anonymous' | 'prototype';

interface AuthContextValue {
  status: AuthStatus;
  session: AuthSession | null;
  user: CurrentUser | null;
  role: CurrentUser['role'] | null;
  scopes: ReadonlySet<string>;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const useLiveApi = import.meta.env.VITE_ENABLE_API === 'true';

async function loadSession(): Promise<AuthSession | null> {
  await getAuthConfig();
  try {
    return (await getBootstrap()).session;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<AuthStatus>(useLiveApi ? 'loading' : 'prototype');
  const [session, setSession] = useState<AuthSession | null>(null);

  const refresh = async () => {
    if (!useLiveApi) return;
    setStatus('loading');
    const next = await loadSession();
    setSession(next);
    setStatus(next?.authenticated ? 'authenticated' : 'anonymous');
  };

  useEffect(() => {
    if (!useLiveApi) return;
    void refresh().catch(() => setStatus('anonymous'));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    status,
    session,
    user: session?.user || null,
    role: session?.role || null,
    scopes: new Set(session?.scopes || []),
    signIn: async (username, password) => {
      const response = await loginRequest(username, password);
      const next: AuthSession = {
        authenticated: true,
        actor: response.user.username,
        role: response.user.role,
        auth_type: 'session',
        user: response.user,
        auth_mode: response.auth_mode,
      };
      setSession(next);
      setStatus('authenticated');
    },
    signOut: async () => {
      if (useLiveApi) await logoutRequest();
      setSession(null);
      setStatus(useLiveApi ? 'anonymous' : 'prototype');
    },
    refresh,
  }), [session, status]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
