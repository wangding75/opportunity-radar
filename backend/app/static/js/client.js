let csrfCookieName = "or_csrf";
export function setCsrfCookieName(value) {
    csrfCookieName = value || "or_csrf";
}
function cookie(name) {
    const prefix = `${encodeURIComponent(name)}=`;
    for (const part of document.cookie.split(";")) {
        const value = part.trim();
        if (value.startsWith(prefix))
            return decodeURIComponent(value.slice(prefix.length));
    }
    return "";
}
function headers(method = "GET") {
    const result = { "Content-Type": "application/json" };
    if (!["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase())) {
        const csrf = cookie(csrfCookieName);
        if (csrf)
            result["X-CSRF-Token"] = csrf;
    }
    return result;
}
export async function api(url, opt = {}) {
    const method = opt.method || "GET";
    const response = await fetch(url, {
        ...opt,
        credentials: "same-origin",
        headers: { ...headers(method), ...(opt.headers || {}) },
    });
    if (!response.ok) {
        let message = `HTTP ${response.status}`;
        try {
            const body = await response.json();
            message += ` ${typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)}`;
        }
        catch { /* non-JSON error */ }
        throw new Error(message);
    }
    const contentType = response.headers.get("content-type") || "";
    return contentType.includes("json") ? response.json() : response.text();
}
export async function getAuthConfig() {
    const response = await fetch("/api/v1/auth/config", { credentials: "same-origin" });
    if (!response.ok)
        throw new Error(`HTTP ${response.status}`);
    return response.json();
}
export async function loginRequest(username, password) {
    return api("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}
export async function logoutRequest() {
    return api("/api/v1/auth/logout", { method: "POST", body: "{}" });
}
export async function downloadExport(url, filename) {
    const response = await fetch(url, { credentials: "same-origin", headers: headers("GET") });
    if (!response.ok)
        throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    try {
        const anchor = document.createElement("a");
        anchor.href = href;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
    }
    finally {
        URL.revokeObjectURL(href);
    }
}
