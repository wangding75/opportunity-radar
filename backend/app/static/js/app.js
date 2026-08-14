import { api, getAuthConfig, loginRequest, logoutRequest, setCsrfCookieName, ApiError } from "./client.js";
import { parseRoute, navigate, routeFor } from "./router.js";
import { createAppShell, updateAppShell } from "./shell.js";
import { installR04Theme } from "./theme.js";
import { installComponentStyles } from "./ui.js";
import { renderScreen } from "./screens.js";
let session = null;
let shell = null;
let rootElement = null;
let renderSequence = 0;
export function renderApp(root) {
    installR04Theme();
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
    if (!session && !["P01", "P26A"].includes(route.screen))
        navigate("P01");
    else
        render();
}
async function renderRoute(route) {
    if (!rootElement)
        return;
    const sequence = ++renderSequence;
    try {
        if (route.screen === "P01" || route.screen === "P26A" || !session) {
            shell = null;
            if (route.screen === "P26A") {
                const publicContext = { onSessionExpired: handleSessionExpired, onForbidden: () => navigate("P01") };
                const help = await renderScreen(route, { label: "未登录", role: "PUBLIC" }, publicContext);
                if (sequence === renderSequence)
                    rootElement.replaceChildren(help);
            }
            else {
                rootElement.replaceChildren(renderLoginPage());
            }
            return;
        }
        const activeSession = session;
        if (!activeSession)
            return;
        const content = await renderScreen(route, activeSession, { onSessionExpired: handleSessionExpired, onForbidden: () => navigate("P04") });
        if (sequence !== renderSequence || !session)
            return;
        if (route.screen === "P05") {
            shell = null;
            rootElement.replaceChildren(content);
            return;
        }
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
    panel.className = "r04-state r04-state-error";
    const title = document.createElement("strong");
    title.textContent = "页面加载失败";
    const message = document.createElement("span");
    message.textContent = error instanceof Error ? error.message : String(error);
    const retryButton = document.createElement("button");
    retryButton.className = "r04-button r04-button-secondary";
    retryButton.type = "button";
    retryButton.textContent = "Retry";
    retryButton.addEventListener("click", retry);
    panel.append(title, message, retryButton);
    return panel;
}
function renderLoginPage() {
    const wrapper = document.createElement("main");
    wrapper.className = "r04-auth-page";
    const card = document.createElement("section");
    card.className = "r04-auth-card";
    card.setAttribute("aria-labelledby", "login-title");
    const brand = document.createElement("div");
    brand.className = "r04-auth-brand";
    const brandTitle = document.createElement("strong");
    brandTitle.textContent = "Opportunity Radar";
    const brandSubtitle = document.createElement("span");
    brandSubtitle.textContent = "R04 机会情报平台";
    brand.append(brandTitle, brandSubtitle);
    const heading = document.createElement("div");
    heading.className = "r04-auth-heading";
    const title = document.createElement("h1");
    title.id = "login-title";
    title.textContent = "登录";
    const subtitle = document.createElement("p");
    subtitle.textContent = "使用平台账户继续访问机会情报工作区";
    heading.append(title, subtitle);
    const form = document.createElement("form");
    form.id = "r04-login-form";
    form.className = "r04-auth-form";
    form.noValidate = true;
    const username = authField("邮箱或用户名", "请输入邮箱或用户名", "text", "username");
    const password = authField("密码", "请输入密码", "password", "password");
    const passwordInput = password.querySelector("input");
    const passwordToggle = document.createElement("button");
    passwordToggle.type = "button";
    passwordToggle.className = "r04-password-toggle";
    passwordToggle.setAttribute("aria-label", "显示密码");
    passwordToggle.textContent = "◉";
    passwordToggle.addEventListener("click", () => {
        if (!passwordInput)
            return;
        const showing = passwordInput.type === "text";
        passwordInput.type = showing ? "password" : "text";
        passwordToggle.setAttribute("aria-label", showing ? "显示密码" : "隐藏密码");
        passwordToggle.textContent = showing ? "◉" : "⊙";
    });
    password.append(passwordToggle);
    const actions = document.createElement("div");
    actions.className = "r04-auth-actions";
    const help = document.createElement("a");
    help.href = routeFor("P26A");
    help.textContent = "忘记密码？";
    actions.append(help);
    const error = document.createElement("div");
    error.id = "r04-login-error";
    error.className = "r04-auth-alert r04-auth-alert-error";
    error.hidden = true;
    const submit = document.createElement("button");
    submit.className = "r04-auth-submit";
    submit.type = "submit";
    submit.textContent = "登录";
    form.append(username, password, actions, error, submit);
    form.addEventListener("submit", (event) => { event.preventDefault(); void submitLogin(wrapper); });
    card.append(brand, heading, form);
    wrapper.append(card, renderLoginStateSpecimens());
    return wrapper;
}
function authField(labelValue, placeholder, type, name) {
    const wrap = document.createElement("label");
    wrap.className = "r04-auth-field";
    const label = document.createElement("span");
    label.textContent = labelValue;
    const input = document.createElement("input");
    input.type = type;
    input.name = name;
    input.placeholder = placeholder;
    input.autocomplete = name === "password" ? "current-password" : "username";
    input.required = true;
    wrap.append(label, input);
    return wrap;
}
function renderLoginStateSpecimens() {
    const host = document.createElement("section");
    host.className = "r04-auth-specimens";
    const heading = document.createElement("h2");
    heading.textContent = "状态示例";
    host.append(heading);
    const states = [
        ["表单校验错误", "请输入邮箱或用户名", "validation"],
        ["认证失败", "账户或密码不正确", "failure"],
        ["请求频繁", "尝试次数过多，请稍后再试", "rate-limit"],
        ["认证服务不可用", "认证服务暂时不可用", "unavailable"],
    ];
    for (const [titleValue, copyValue, tone] of states) {
        const row = document.createElement("div");
        row.className = `r04-auth-state r04-auth-state-${tone}`;
        const icon = document.createElement("span");
        icon.className = "r04-auth-state-icon";
        icon.textContent = tone === "validation" ? "!" : tone === "failure" ? "△" : tone === "rate-limit" ? "⌛" : "⊘";
        const body = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = titleValue;
        const copy = document.createElement("span");
        copy.textContent = copyValue;
        body.append(title, copy);
        row.append(icon, body);
        host.append(row);
    }
    return host;
}
async function submitLogin(wrapper) {
    const form = wrapper.querySelector("#r04-login-form");
    const error = wrapper.querySelector("#r04-login-error");
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
        const username = String(data.get("username") ?? "").trim();
        const password = String(data.get("password") ?? "");
        if (!username || !password) {
            error.textContent = !username ? "请输入邮箱或用户名" : "请输入密码";
            error.hidden = false;
            return;
        }
        await loginRequest(username, password);
        const me = await api("/api/v1/auth/me");
        session = { label: String(me.user?.username ?? me.actor ?? "User"), role: String(me.role ?? "VIEWER") };
        navigate("P02");
    }
    catch (requestError) {
        const status = requestError instanceof ApiError ? requestError.status : 0;
        error.textContent = status === 429 ? "尝试次数过多，请稍后再试" : status === 401 ? "账户或密码不正确" : "认证服务暂时不可用";
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
