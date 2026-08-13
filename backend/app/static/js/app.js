import { api, getAuthConfig, loginRequest, logoutRequest, setCsrfCookieName, ApiError } from "./client.js";
import { parseRoute, navigate } from "./router.js";
import { createAppShell, updateAppShell } from "./shell.js";
import { installR02Theme } from "./theme.js";
import { installComponentStyles } from "./ui.js";
import { renderScreen } from "./screens.js";
let session = null;
let shell = null;
let rootElement = null;
let renderSequence = 0;
export function renderApp(root) {
    installR02Theme();
    installComponentStyles();
    rootElement = root;
    const render = () => { void renderRoute(parseRoute()); };
    window.addEventListener("hashchange", render);
    void bootstrap(render);
}
async function bootstrap(render) {
    try {
        const config = await getAuthConfig();
        setCsrfCookieName(config.csrf_cookie_name);
        if (config.auth_mode === "disabled") {
            session = { label: "开发模式", role: "OWNER" };
        }
        else {
            const me = await api("/api/v1/auth/me");
            session = { label: String(me.user?.username ?? me.actor ?? "User"), role: String(me.role ?? "VIEWER") };
        }
    }
    catch (error) {
        if (!(error instanceof ApiError && error.status === 401))
            session = null;
    }
    const route = parseRoute();
    if (!session && route.screen !== "P01")
        navigate("P01");
    else if (session && route.screen === "P01")
        navigate("P02");
    else
        render();
}
async function renderRoute(route) {
    if (!rootElement)
        return;
    const sequence = ++renderSequence;
    try {
        if (route.screen === "P01" || !session) {
            shell = null;
            rootElement.replaceChildren(renderLoginPage());
            return;
        }
        const activeSession = session;
        if (!activeSession)
            return;
        const content = await renderScreen(route, activeSession, { onSessionExpired: handleSessionExpired });
        if (sequence !== renderSequence || !session)
            return;
        if (!shell) {
            shell = createAppShell(route.screen, content, activeSession.label, activeSession.role, handleLogout);
            rootElement.replaceChildren(shell);
        }
        else {
            updateAppShell(shell, route.screen, content);
        }
    }
    catch (error) {
        if (sequence !== renderSequence)
            return;
        const fallback = document.createElement("div");
        fallback.append(statePanelForError(error, () => { void renderRoute(parseRoute()); }));
        if (shell)
            updateAppShell(shell, route.screen, fallback);
        else {
            shell = createAppShell(route.screen, fallback, session?.label, session?.role, handleLogout);
            rootElement.replaceChildren(shell);
        }
    }
}
function statePanelForError(error, retry) {
    const panel = document.createElement("div");
    panel.className = "r02-state r02-state-error";
    const title = document.createElement("strong");
    title.textContent = "Unable to load";
    const message = document.createElement("span");
    message.textContent = error instanceof Error ? error.message : String(error);
    const retryButton = document.createElement("button");
    retryButton.className = "r02-button r02-button-secondary";
    retryButton.type = "button";
    retryButton.textContent = "Retry";
    retryButton.addEventListener("click", retry);
    panel.append(title, message, retryButton);
    return panel;
}
function renderLoginPage(message = "") {
    const wrapper = document.createElement("main");
    wrapper.className = "r02-login";
    wrapper.innerHTML = `<section class="r02-login-card r02-card" aria-labelledby="login-title"><div class="r02-brand"><span class="r02-brand-mark">R</span><span class="r02-brand-copy"><strong>Opportunity Radar</strong><span>Decision workspace · R02</span></span></div><h1 id="login-title" class="r02-page-title">登录工作台</h1><p class="r02-page-subtitle">使用已有账户访问机会情报。</p><form id="r02-login-form" class="r02-form"><label class="r02-field-wrap"><span class="r02-field-label">用户名</span><input class="r02-field" name="username" autocomplete="username" required></label><label class="r02-field-wrap"><span class="r02-field-label">密码</span><input class="r02-field" name="password" type="password" autocomplete="current-password" required></label><div id="r02-login-error" class="r02-inline-alert r02-inline-alert-danger">${escapeHtml(message)}</div><button class="r02-button r02-button-primary" type="submit">登录</button></form></section>`;
    const error = wrapper.querySelector("#r02-login-error");
    if (error && !message)
        error.hidden = true;
    wrapper.querySelector("#r02-login-form")?.addEventListener("submit", (event) => { event.preventDefault(); void submitLogin(wrapper); });
    return wrapper;
}
async function submitLogin(wrapper) {
    const form = wrapper.querySelector("#r02-login-form");
    const error = wrapper.querySelector("#r02-login-error");
    if (!form || !error)
        return;
    const submit = form.querySelector("button[type=submit]");
    if (submit) {
        submit.disabled = true;
        submit.textContent = "登录中…";
    }
    error.hidden = true;
    try {
        const data = new FormData(form);
        await loginRequest(String(data.get("username") ?? ""), String(data.get("password") ?? ""));
        const me = await api("/api/v1/auth/me");
        session = { label: String(me.user?.username ?? me.actor ?? "User"), role: String(me.role ?? "VIEWER") };
        navigate("P02");
    }
    catch (requestError) {
        const status = requestError instanceof ApiError ? requestError.status : 0;
        error.textContent = status === 429 ? "登录请求过于频繁，请稍后重试。" : status === 401 ? "用户名或密码不正确。" : "认证服务暂时不可用，请稍后重试。";
        error.hidden = false;
    }
    finally {
        if (submit) {
            submit.disabled = false;
            submit.textContent = "登录";
        }
    }
}
async function handleLogout() {
    try {
        await logoutRequest();
    }
    finally {
        session = null;
        shell = null;
        navigate("P01");
    }
}
function handleSessionExpired() { session = null; shell = null; navigate("P01"); }
function escapeHtml(value) { return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char] ?? char)); }
