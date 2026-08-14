import { navigate, routeFor, SCREEN_ROUTES } from "./router.js";
const intelligenceChildren = [
    { screen: "P06", label: "最新情报", icon: "", group: "情报" },
    { screen: "P08", label: "关键词发现", icon: "", group: "情报" },
    { screen: "P09", label: "关注关键词", icon: "", group: "情报" },
    { screen: "P10", label: "趋势分析", icon: "", group: "情报" },
    { screen: "P11", label: "关系图谱", icon: "", group: "情报" },
];
const researchChildren = [
    { screen: "P14", label: "结构化分析", icon: "", group: "研究", target: "P14" },
    { screen: "P15", label: "研究任务", icon: "", group: "研究", target: "P15" },
    { screen: "P17", label: "研究结果", icon: "", group: "研究", target: "P17" },
];
const operationsChildren = [
    { screen: "P18", label: "数据源", icon: "", group: "运行" },
    { screen: "P20", label: "监控计划", icon: "", group: "运行" },
    { screen: "P21", label: "运行记录", icon: "", group: "运行" },
    { screen: "P23", label: "分析队列", icon: "", group: "运行" },
    { screen: "P24", label: "告警", icon: "", group: "运行" },
];
const managementChildren = [
    { screen: "P27", label: "用户与角色", icon: "", group: "管理", adminOnly: true },
    { screen: "P26", label: "审计日志", icon: "", group: "管理", adminOnly: true },
    { screen: "P29-A", label: "系统设置", icon: "", group: "管理", adminOnly: true },
    { screen: "P30", label: "系统诊断", icon: "", group: "管理", adminOnly: true },
];
export const NAV_REGISTRY = [
    { key: "workbench", label: "工作台", icon: "▦", target: "P02" },
    { key: "opportunities", label: "机会", icon: "☆", target: "P12" },
    { key: "intelligence", label: "情报", icon: "⌁", target: "P06", children: intelligenceChildren },
    { key: "research", label: "研究", icon: "⚗", target: "P14", children: researchChildren },
    { key: "operations", label: "运行", icon: "⌘", target: "P18", children: operationsChildren },
    { key: "management", label: "管理", icon: "⚙", target: "P27", children: managementChildren, adminOnly: true },
];
const LABELS = {
    P01: "登录", P02: "工作台", P03: "全局搜索", P04: "403 无权限", P05: "404 对象不存在", P06: "最新情报",
    P07: "情报详情", P08: "关键词发现", P09: "关注关键词", P10: "趋势分析", P11: "关系图谱", P12: "机会",
    P13: "机会详情", P14: "结构化分析", P15: "研究任务", P16: "研究任务详情", P17: "研究结果", P18: "数据源",
    P19: "数据源健康", P20: "监控计划", P21: "运行记录", P22: "运行详情", P23: "分析队列", P24: "告警",
    P25: "告警规则", P26: "审计日志", P27: "用户与角色", P28: "个人账户与安全", "P29-A": "系统设置 / 通用",
    "P29-B": "系统设置 / 安全", "P29-C": "系统设置 / 通知", "P29-D": "系统设置 / 集成", "P29-E": "系统设置 / 来源偏好",
    P30: "系统诊断",
};
export function screenLabel(screen) { return LABELS[screen]; }
export function createAppShell(route, content, userLabel = "未登录", role = "VIEWER", onLogout) {
    const shell = document.createElement("div");
    shell.className = "or-app-shell";
    shell.dataset.shell = "r04-app-shell";
    shell.dataset.role = role;
    shell.append(createSideNav(route, role), createMainFrame(route, content, userLabel, role, onLogout));
    return shell;
}
function createSideNav(route, role) {
    const aside = document.createElement("aside");
    aside.className = "or-sidebar";
    aside.dataset.component = "SidebarNav";
    const brand = document.createElement("a");
    brand.className = "or-brand";
    brand.href = routeFor("P02");
    brand.setAttribute("aria-label", "返回工作台");
    const title = document.createElement("strong");
    title.textContent = "Opportunity Radar";
    const subtitle = document.createElement("span");
    subtitle.textContent = "R04 机会情报平台";
    brand.append(title, subtitle);
    aside.append(brand);
    const nav = document.createElement("nav");
    nav.className = "or-nav";
    nav.setAttribute("aria-label", "一级导航");
    for (const section of NAV_REGISTRY) {
        if (section.adminOnly && !isAdmin(role))
            continue;
        const sectionEl = document.createElement("div");
        sectionEl.className = "or-nav-section";
        const active = isActiveSection(route, section);
        const primary = document.createElement("a");
        primary.className = `or-nav-primary${active ? " is-active" : ""}`;
        primary.href = routeFor(section.target);
        primary.dataset.section = section.key;
        primary.setAttribute("aria-current", active && !section.children ? "page" : "false");
        const icon = document.createElement("span");
        icon.className = "or-nav-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = section.icon;
        const label = document.createElement("span");
        label.textContent = section.label;
        primary.append(icon, label);
        if (section.children) {
            const chevron = document.createElement("span");
            chevron.className = "or-nav-chevron";
            chevron.setAttribute("aria-hidden", "true");
            chevron.textContent = active ? "⌃" : "⌄";
            primary.append(chevron);
        }
        sectionEl.append(primary);
        if (section.children && active) {
            const children = document.createElement("div");
            children.className = "or-nav-children";
            for (const child of section.children) {
                if (child.adminOnly && !isAdmin(role))
                    continue;
                const link = document.createElement("a");
                link.className = `or-nav-child${isActiveNav(route, child.screen) ? " is-active" : ""}`;
                link.href = routeFor(child.target ?? child.screen);
                link.textContent = child.label;
                link.setAttribute("aria-current", isActiveNav(route, child.screen) ? "page" : "false");
                children.append(link);
            }
            sectionEl.append(children);
        }
        nav.append(sectionEl);
    }
    aside.append(nav);
    const footer = document.createElement("div");
    footer.className = "or-sidebar-footer";
    footer.append(sidebarLink("P30", "▣", "系统诊断"), sidebarLink("P26", "◷", "审计日志"));
    aside.append(footer);
    return aside;
}
function sidebarLink(screen, iconValue, labelValue) {
    const link = document.createElement("a");
    link.href = routeFor(screen);
    const icon = document.createElement("span");
    icon.className = "or-nav-icon";
    icon.textContent = iconValue;
    icon.setAttribute("aria-hidden", "true");
    const label = document.createElement("span");
    label.textContent = labelValue;
    link.append(icon, label);
    return link;
}
function isAdmin(role) { return role === "ADMIN" || role === "OWNER"; }
function isActiveSection(current, section) {
    if (current === section.target)
        return true;
    return Boolean(section.children?.some((item) => isActiveNav(current, item.screen)));
}
function isActiveNav(current, candidate) {
    if (candidate === "P14" && ["P14", "P16", "P17", "P23"].includes(current))
        return true;
    if (candidate === "P15" && ["P15", "P16"].includes(current))
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
    main.className = "or-main";
    main.dataset.component = "GlobalContentArea";
    const topbar = createTopBar(userLabel, role, onLogout);
    main.append(topbar);
    const contentArea = document.createElement("div");
    contentArea.className = "or-content";
    const frame = document.createElement("section");
    frame.className = "or-page-frame";
    frame.dataset.component = "PageFrame";
    frame.append(createPageHeader(route), createRouteOutlet(content));
    contentArea.append(frame);
    main.append(contentArea);
    return main;
}
function createTopBar(userLabel, _role, _onLogout) {
    const topbar = document.createElement("header");
    topbar.className = "or-topbar";
    topbar.dataset.component = "TopBar";
    const search = document.createElement("a");
    search.className = "or-topbar-search";
    search.href = routeFor("P03");
    search.setAttribute("aria-label", "打开全局搜索");
    search.innerHTML = `<span class="or-topbar-search-icon" aria-hidden="true">⌕</span><span>搜索机会、情报、研究、运行记录…</span>`;
    topbar.append(search);
    const spacer = document.createElement("span");
    spacer.className = "or-topbar-spacer";
    topbar.append(spacer);
    const actions = document.createElement("div");
    actions.className = "or-topbar-actions";
    actions.append(shellAction("↻", "刷新", () => window.location.reload()));
    const notification = shellAction("♧", "通知", () => { const handled = window.dispatchEvent(new CustomEvent("or-shell-action", { detail: "notifications", cancelable: true })); if (handled)
        navigate("P24"); });
    const dot = document.createElement("span");
    dot.className = "or-notification-dot";
    dot.setAttribute("aria-hidden", "true");
    notification.append(dot);
    actions.append(notification);
    actions.append(shellAction("?", "帮助", () => { const handled = window.dispatchEvent(new CustomEvent("or-shell-action", { detail: "help", cancelable: true })); if (handled)
        navigate("P30"); }));
    const divider = document.createElement("span");
    divider.className = "or-topbar-divider";
    divider.setAttribute("aria-hidden", "true");
    actions.append(divider);
    const avatar = document.createElement("a");
    avatar.className = "or-avatar";
    avatar.href = routeFor("P28");
    avatar.title = "个人账户与安全";
    avatar.textContent = userLabel.trim().slice(0, 1).toUpperCase() || "用";
    actions.append(avatar);
    topbar.append(actions);
    return topbar;
}
function shellAction(iconValue, labelValue, onClick) {
    const button = document.createElement("button");
    button.className = "or-topbar-action";
    button.type = "button";
    button.title = labelValue;
    button.setAttribute("aria-label", labelValue);
    button.textContent = iconValue;
    button.addEventListener("click", onClick);
    return button;
}
function createPageHeader(route) {
    const header = document.createElement("header");
    header.className = "or-page-header";
    header.dataset.component = "PageHeader";
    const heading = document.createElement("div");
    heading.className = "or-page-heading";
    const breadcrumb = document.createElement("div");
    breadcrumb.className = "or-breadcrumb";
    const home = document.createElement("a");
    home.href = routeFor("P02");
    home.textContent = "工作台";
    const separator = document.createElement("span");
    separator.textContent = "/";
    const current = document.createElement("span");
    current.textContent = screenLabel(route);
    breadcrumb.append(home, separator, current);
    const title = document.createElement("h1");
    title.className = "or-page-title";
    title.textContent = screenLabel(route);
    const subtitle = document.createElement("p");
    subtitle.className = "or-page-subtitle";
    subtitle.textContent = "基于真实接口的机会情报工作区";
    heading.append(breadcrumb, title, subtitle);
    header.append(heading);
    return header;
}
function createRouteOutlet(content) {
    const outlet = document.createElement("div");
    outlet.className = "or-route-outlet";
    outlet.dataset.component = "RouteOutlet";
    outlet.append(content);
    return outlet;
}
export function updateAppShell(shell, route, content) {
    const frame = shell.querySelector("[data-component='PageFrame']");
    if (!frame)
        return;
    const role = shell.dataset.role ?? "VIEWER";
    const sidebar = shell.querySelector("[data-component='SidebarNav']");
    if (sidebar)
        sidebar.replaceWith(createSideNav(route, role));
    const outlet = frame.querySelector("[data-component='RouteOutlet']");
    if (outlet)
        outlet.replaceChildren(content);
    else
        frame.append(createRouteOutlet(content));
    const currentHeader = frame.querySelector("[data-component='PageHeader']");
    if (currentHeader)
        currentHeader.replaceWith(createPageHeader(route));
}
export function renderFramePlaceholder(route) {
    const placeholder = document.createElement("div");
    placeholder.className = "or-placeholder";
    const title = document.createElement("strong");
    title.textContent = screenLabel(route);
    const copy = document.createElement("p");
    copy.textContent = "页面外壳已就绪，业务内容将在对应任务中接入。";
    placeholder.append(title, copy);
    return placeholder;
}
export function bindShellShortcuts() {
    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(event.target?.tagName)) {
            event.preventDefault();
            navigate("P03");
        }
    });
}
export function shellRoutePath(route) { return SCREEN_ROUTES[route]; }
