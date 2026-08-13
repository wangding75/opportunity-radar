export const PERMISSION_MATRIX_VERSION = "rbac-v1";
export const ROLE_LEVEL: Record<string, number> = { VIEWER: 10, RESEARCHER: 20, ADMIN: 30, OWNER: 40 };

export function canRoleWrite(role: string): boolean {
  return (ROLE_LEVEL[role] || 0) >= ROLE_LEVEL.RESEARCHER;
}

export function isAdminRole(role: string): boolean {
  return (ROLE_LEVEL[role] || 0) >= ROLE_LEVEL.ADMIN;
}

export function isOwnerRole(role: string): boolean {
  return role === "OWNER";
}
