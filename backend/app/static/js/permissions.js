export const PERMISSION_MATRIX_VERSION = "rbac-v1";
export const ROLE_LEVEL = { VIEWER: 10, RESEARCHER: 20, ADMIN: 30, OWNER: 40 };
export function canRoleWrite(role) {
    return (ROLE_LEVEL[role] || 0) >= ROLE_LEVEL.RESEARCHER;
}
export function isAdminRole(role) {
    return (ROLE_LEVEL[role] || 0) >= ROLE_LEVEL.ADMIN;
}
export function isOwnerRole(role) {
    return role === "OWNER";
}
