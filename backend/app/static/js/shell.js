import { navigate, routeFor, SCREEN_ROUTES } from "./router.js";
import { R02_TOKENS } from "./theme.js";
export const NAV_REGISTRY = [
    { screen: "P02", label: "总览", icon: "⌂", group: "Workspace" },
    { screen: "P06", label: "Observation", icon: "◉", group: "Intelligence" },
    { screen: "P08", label: "关键词发现", icon: "✦", group: "Intelligence" },
    { screen: "P10", label: "趋势分析", icon: "↗", group: "Intelligence" },
    { screen: "P11", label: "关系图谱", icon: "◎", group: "Intelligence" },
    { screen: "P12", label: "Opportunity", icon: "◇", group: "Intelligence" },
    { screen: "P14", label: "结构化分析", icon: "▤", group: "Research" },
    { screen: "P15", label: "Research", icon: "⌁", group: "Research" },
    { screen: "P18", label: "来源管理", icon: "◌", group: "Operations" },
    { screen: "P20", label: "监控计划", icon: "◷", group: "Operations" },
    { screen: "P21", label: "运行记录", icon: "▷", group: "Operations" },
    { screen: "P23", label: "Analysis Queue", icon: "≡", group: "Operations" },
    { screen: "P24", label: "告警收件箱", icon: "!", group: "Governance" },
    { screen: "P26", label: "审计日志", icon: "▥", group: "Governance", adminOnly: true },
    { screen: "P27", label: "用户与角色", icon: "♙", group: "Governance", adminOnly: true },
    { screen: "P30", label: "系统诊断", icon: "⌁", group: "Governance", adminOnly: true },
    { screen: "P29-A", label: "设置", icon: "⚙", group: "System" },
];
const LABELS = {
    P01: "登录", P02: "Dashboard", P03: "全局搜索", P04: "无权限", P05: "未找到", P06: "Observation",
    P07: "Observation 详情", P08: "关键词发现", P09: "关注关键词", P10: "趋势分析", P11: "关系图谱",
    P12: "Opportunity", P13: "Opportunity 详情", P14: "结构化分析", P15: "Research Workflow",
    P16: "Workflow 详情", P17: "Research Result", P18: "来源管理", P19: "Source Health", P20: "监控计划",
    P21: "运行记录", P22: "运行详情", P23: "Analysis Queue", P24: "告警收件箱", P25: "告警规则",
    P26: "审计日志", P27: "用户与角色", P28: "账户与安全", "P29-A": "设置 / 常规", "P29-B": "设置 / 安全",
    "P29-C": "设置 / 通知", "P29-D": "设置 / Integrations", "P29-E": "设置 / Source Preference", P30: "系统诊断",
};
export function screenLabel(screen) { return LABELS[screen]; }
export function createAppShell(route, content, userLabel = "未登录", role = "VIEWER", onLogout) {
    const shell = document.createElement("div");
    shell.className = "r02-app r02-shell";
    shell.dataset.shell = "r02-app-shell";
    shell.append(createSideNav(route, role), createMainFrame(route, content, userLabel, role, onLogout));
    return shell;
}
function createSideNav(route, role) {
    const aside = document.createElement("aside");
    aside.className = "r02-sidebar";
    aside.dataset.component = "SideNav";
    const brand = document.createElement("a");
    brand.className = "r02-brand";
    brand.href = routeFor("P02");
    brand.innerHTML = `<span class="r02-brand-mark">R</span><span class="r02-brand-copy"><strong>Opportunity Radar</strong><span>Decision workspace · R02</span></span>`;
    aside.append(brand);
    const nav = document.createElement("nav");
    nav.className = "r02-nav";
    nav.setAttribute("aria-label", "Primary navigation");
    let group = "";
    for (const item of NAV_REGISTRY) {
        if (item.adminOnly && !["ADMIN", "OWNER"].includes(role))
            continue;
        if (item.group !== group) {
            group = item.group;
            const heading = document.createElement("div");
            heading.className = "r02-nav-group";
            heading.textContent = group;
            nav.append(heading);
        }
        const link = document.createElement("a");
        link.className = `r02-nav-link${isActiveNav(route, item.screen) ? " is-active" : ""}`;
        link.href = routeFor(item.screen);
        link.setAttribute("aria-current", isActiveNav(route, item.screen) ? "page" : "false");
        link.innerHTML = `<span class="r02-nav-icon" aria-hidden="true">${item.icon}</span><span>${item.label}</span>`;
        nav.append(link);
    }
    aside.append(nav);
    const footer = document.createElement("div");
    footer.className = "r02-sidebar-footer";
    footer.textContent = `R02 · ${R02_TOKENS.layout.maxContent} grid`;
    aside.append(footer);
    return aside;
}
function isActiveNav(current, candidate) {
    if (candidate === "P14" && ["P14", "P16", "P17", "P23"].includes(current))
        return true;
    if (candidate === "P15" && ["P15", "P16", "P17"].includes(current))
        return true;
    if (candidate === "P18" && ["P18", "P19"].includes(current))
        return true;
    if (candidate === "P21" && ["P21", "P22"].includes(current))
        return true;
    if (candidate === "P24" && ["P24", "P25"].includes(current))
        return true;
    if (candidate === "P29-A" && current.startsWith("P29-"))
        return true;
    return current === candidate;
}
function createMainFrame(route, content, userLabel, role, onLogout) {
    const main = document.createElement("div");
    main.className = "r02-main";
    main.dataset.component = "GlobalContentArea";
    const topbar = document.createElement("header");
    topbar.className = "r02-topbar";
    topbar.dataset.component = "TopBar";
    topbar.innerHTML = `<div class="r02-topbar-title">${screenLabel(route)}</div><a class="r02-topbar-search" href="${routeFor("P03")}" aria-label="打开全局搜索"><span aria-hidden="true">⌕</span><span>搜索机会、证据、关键词…</span><kbd>/</kbd></a><span class="r02-topbar-spacer"></span><div class="r02-topbar-user"><span class="r02-avatar">${escapeText(userLabel.slice(0, 1).toUpperCase())}</span><span>${escapeText(userLabel)} · ${escapeText(role)}</span>${onLogout ? `<button class="r02-button r02-button-ghost" data-r02-logout type="button">退出</button>` : ""}</div>`;
    main.append(topbar);
    const contentArea = document.createElement("div");
    contentArea.className = "r02-content";
    const frame = document.createElement("section");
    frame.className = "r02-page-frame";
    frame.dataset.component = "PageFrame";
    const header = document.createElement("header");
    header.className = "r02-page-header";
    header.innerHTML = `<div class="r02-page-heading"><div class="r02-breadcrumb"><a href="${routeFor("P02")}">Workspace</a><span aria-hidden="true">/</span><span>${screenLabel(route)}</span></div><h1 class="r02-page-title">${screenLabel(route)}</h1><p class="r02-page-subtitle">R02 dynamic content frame · route ${escapeText(SCREEN_ROUTES[route])}</p></div>`;
    frame.append(header, content);
    contentArea.append(frame);
    main.append(contentArea);
    return main;
}
export function updateAppShell(shell, route, content) {
    const title = shell.querySelector(".r02-topbar-title");
    if (title)
        title.textContent = screenLabel(route);
    shell.querySelectorAll(".r02-nav-link").forEach((link) => {
        const active = link.href.endsWith(routeFor(route));
        link.classList.toggle("is-active", active);
        link.setAttribute("aria-current", active ? "page" : "false");
    });
    const frame = shell.querySelector("[data-component='PageFrame']");
    if (!frame)
        return;
    const header = document.createElement("header");
    header.className = "r02-page-header";
    header.innerHTML = `<div class="r02-page-heading"><div class="r02-breadcrumb"><a href="${routeFor("P02")}">Workspace</a><span aria-hidden="true">/</span><span>${screenLabel(route)}</span></div><h1 class="r02-page-title">${screenLabel(route)}</h1><p class="r02-page-subtitle">R02 dynamic content frame · route ${escapeText(SCREEN_ROUTES[route])}</p></div>`;
    frame.replaceChildren(header, content);
}
function escapeText(value) {
    return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char] ?? char));
}
export function renderFramePlaceholder(route) {
    const placeholder = document.createElement("div");
    placeholder.className = "r02-skeleton";
    placeholder.innerHTML = `<div><strong>${screenLabel(route)}</strong><p>PageFrame 已就绪，业务内容将在对应批次实现。</p></div>`;
    return placeholder;
}
export function bindShellShortcuts() {
    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(event.target?.tagName)) {
            event.preventDefault();
            navigate("P03");
        }
    }, { once: true });
}
