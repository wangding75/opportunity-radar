export const SCREEN_ROUTES = {
    P01: "/login", P02: "/dashboard", P03: "/search", P04: "/forbidden", P05: "/not-found",
    P06: "/observations", P07: "/observations/:id", P08: "/keywords/discovery", P09: "/keywords/watch",
    P10: "/trends", P11: "/graph", P12: "/opportunities", P13: "/opportunities/:id", P14: "/analysis/:id",
    P15: "/research", P16: "/research/:id", P17: "/research/:id/result", P18: "/sources",
    P19: "/sources/:id/health", P20: "/monitoring", P21: "/runs", P22: "/runs/:id", P23: "/analysis-queue",
    P24: "/alerts", P25: "/alerts/rules", P26: "/audit", P27: "/users", P28: "/account",
    "P29-A": "/settings/general", "P29-B": "/settings/security", "P29-C": "/settings/notifications",
    "P29-D": "/settings/integrations", "P29-E": "/settings/source-preference", P30: "/diagnostics",
};
const LEGACY_ALIASES = {
    dashboard: "P02", opportunities: "P12", alerts: "P24", watch: "P09", sources: "P18",
    observations: "P06", users: "P27", operations: "P21", login: "P01",
};
export function routeFor(screen, params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => query.set(key, String(value)));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return `#${SCREEN_ROUTES[screen]}${suffix}`;
}
export function parseRoute(hash = window.location.hash) {
    const raw = hash.replace(/^#/, "") || "/dashboard";
    const [path, query = ""] = raw.split("?", 2);
    const normalized = path.replace(/\/+$/, "") || "/dashboard";
    const alias = LEGACY_ALIASES[normalized.replace(/^\//, "")];
    if (alias)
        return { screen: alias, params: new URLSearchParams(query) };
    const exact = Object.entries(SCREEN_ROUTES).find(([, value]) => value === normalized);
    if (exact)
        return { screen: exact[0], params: new URLSearchParams(query) };
    if (/^\/observations\/[^/]+$/.test(normalized))
        return { screen: "P07", params: withPathId(normalized, query) };
    if (/^\/opportunities\/[^/]+$/.test(normalized))
        return { screen: "P13", params: withPathId(normalized, query) };
    if (/^\/analysis\/[^/]+$/.test(normalized))
        return { screen: "P14", params: withPathId(normalized, query) };
    if (/^\/research\/[^/]+\/result$/.test(normalized))
        return { screen: "P17", params: withPathId(normalized, query, true) };
    if (/^\/research\/[^/]+$/.test(normalized))
        return { screen: "P16", params: withPathId(normalized, query) };
    if (/^\/sources\/[^/]+\/health$/.test(normalized))
        return { screen: "P19", params: withPathId(normalized, query) };
    if (/^\/runs\/[^/]+$/.test(normalized))
        return { screen: "P22", params: withPathId(normalized, query) };
    return { screen: "P05", params: new URLSearchParams({ requested: normalized }) };
}
function withPathId(path, query, result = false) {
    const parts = path.split("/").filter(Boolean);
    const params = new URLSearchParams(query);
    params.set("id", parts[1]);
    if (result)
        params.set("result", "true");
    return params;
}
export function navigate(screen, params = {}) {
    window.location.hash = routeFor(screen, params).slice(1);
}
