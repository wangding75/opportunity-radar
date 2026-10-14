import React from 'react';
import { CurrentUser } from '@/api/auth';
import { useAuth } from '@/app/AuthContext';

const rank: Record<CurrentUser['role'], number> = { VIEWER: 1, RESEARCHER: 2, ADMIN: 3, OWNER: 4 };

export const PermissionGate: React.FC<{
  minimumRole?: CurrentUser['role'];
  scope?: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ minimumRole = 'VIEWER', scope, fallback = null, children }) => {
  const { status, role, scopes } = useAuth();
  if (status === 'prototype') return <>{children}</>;
  if (!role || rank[role] < rank[minimumRole] || (scope && !scopes.has(scope))) return <>{fallback}</>;
  return <>{children}</>;
};
