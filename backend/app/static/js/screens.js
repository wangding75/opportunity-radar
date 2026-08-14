import { api, ApiError } from "./client.js";
import { routeFor, navigate } from "./router.js";
import { appendActionRow, badge, button, capabilityUnavailableNotice, card, input, linkTo, modal, readOnlyNotice, select, settingsFrame, statePanel, table } from "./ui.js";
export async function renderScreen(route, session, context) {
    installScreenStyles();
    switch (route.screen) {
        case "P02": return renderDashboard(context);
        case "P03": return renderSearch(context);
        case "P04": return renderForbidden(route, session);
        case "P05": return renderNotFound(route);
        case "P26A": return renderLoginHelp();
        case "P06": return renderObservations(context);
        case "P07": return renderObservationDetail(route, context);
        case "P08": return renderKeywords(route, context);
        case "P09": return renderWatchKeywords(route, context);
        case "P10": return renderTrend(route, context);
        case "P11": return renderGraph(route, context);
        case "P12": return renderOpportunities(context);
        case "P13": return renderOpportunityDetail(route, context, "detail");
        case "P14": return route.params.get("id") ? renderOpportunityDetail(route, context, "analysis") : renderStructuredAnalysisList(route, context);
        case "P15": return renderResearch(route, context);
        case "P16": return renderOpportunityDetail(route, context, "research");
        case "P17": return route.params.get("id") ? renderResearchResultDetail(route, context) : renderResearchResultList(route, context);
        case "P18": return renderSources(context);
        case "P19": return renderSourceHealth(route, context);
        case "P20": return renderMonitoring(context);
        case "P21": return renderRuns(context);
        case "P22": return renderRunDetail(route, context);
        case "P23": return renderAnalysisQueue(context);
        case "P24": return renderAlerts(context);
        case "P25": return renderAlertRules(context);
        case "P26": return renderAudit(context);
        case "P27": return renderUsers(context);
        case "P28": return renderAccount(context);
        case "P29-A": return renderSettings(route, "P29-A", "General", "The backend has no general preference schema yet.");
        case "P29-B": return renderSettings(route, "P29-B", "Security", "Security controls are owned by the existing auth configuration and are not editable from this UI yet.");
        case "P29-C": return renderSettings(route, "P29-C", "Notifications", "Notification preferences are not exposed by the current backend contract.");
        case "P29-D": return renderSettings(route, "P29-D", "Integrations", "Integration credentials and endpoints remain backend-managed in this release.");
        case "P29-E": return renderSourcePreferenceSettings(route, context);
        case "P30": return renderDiagnostics(context);
        default: return renderNotFound(route);
    }
}
function content(title, subtitle) {
    const host = document.createElement("div");
    host.className = "r02-screen-content";
    const intro = document.createElement("div");
    intro.className = "r02-screen-intro";
    const heading = document.createElement("h2");
    heading.textContent = title;
    const copy = document.createElement("p");
    copy.textContent = subtitle;
    intro.append(heading, copy);
    host.append(intro);
    return host;
}
function append(host, ...children) { host.append(...children); }
function errorState(error, context, retry) {
    if (error instanceof ApiError && error.status === 401) {
        context.onSessionExpired();
        return statePanel("permission", "Your session has expired. Please sign in again.");
    }
    if (error instanceof ApiError && error.status === 403) {
        context.onForbidden?.();
        return statePanel("permission", "Your role does not have access to this screen.");
    }
    if (error instanceof ApiError && error.status === 429)
        return statePanel("rate-limit", error.message);
    return statePanel("error", error instanceof Error ? error.message : String(error), retry);
}
function formatDate(value) {
    if (!value)
        return "—";
    const date = new Date(String(value));
    return Number.isNaN(date.valueOf()) ? String(value) : date.toLocaleString();
}
function text(value, fallback = "—") {
    if (value === null || value === undefined || value === "")
        return fallback;
    return String(value);
}
function number(value, digits = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed.toFixed(digits) : "—";
}
function kpi(label, value, href) {
    const host = document.createElement(href ? "a" : "section");
    host.className = "r02-kpi r02-card";
    if (href)
        host.href = href;
    const valueEl = document.createElement("strong");
    valueEl.className = "r02-kpi-value";
    valueEl.textContent = number(value);
    const labelEl = document.createElement("span");
    labelEl.className = "r02-kpi-label";
    labelEl.textContent = label;
    host.append(valueEl, labelEl);
    return host;
}
async function renderDashboard(context) {
    const host = document.createElement("div");
    host.className = "r04-workbench";
    const heading = document.createElement("div");
    heading.className = "r04-workbench-heading";
    const title = document.createElement("h1");
    title.textContent = "工作台";
    const subtitle = document.createElement("p");
    subtitle.textContent = "快速判断今天最值得关注的机会、情报变化与运行异常";
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.className = "r04-workbench-refresh";
    refresh.textContent = "↻ 刷新视图";
    refresh.addEventListener("click", () => window.location.reload());
    heading.append(document.createElement("div"), refresh);
    heading.firstElementChild?.append(title, subtitle);
    host.append(heading);
    const [dashboardResult, alertResult, observationsResult] = await Promise.allSettled([
        api("/api/v1/dashboard"),
        api("/api/v1/alerts/events?status=NEW&limit=8"),
        api("/api/v1/observations?limit=5"),
    ]);
    if (dashboardResult.status === "rejected") {
        host.append(statePanel("error", "工作台数据暂时不可用，请稍后重试。", () => void renderDashboard(context)));
        if (dashboardResult.reason instanceof ApiError && dashboardResult.reason.status === 401)
            context.onSessionExpired();
        return host;
    }
    const data = dashboardResult.value;
    const totals = data.totals ?? {};
    const summary = document.createElement("div");
    summary.className = "r04-workbench-summary";
    summary.append(workbenchSummary("重点机会", totals.starred_opportunities ?? totals.opportunities, "真实研究状态中标记的机会", "P12"), workbenchSummary("近 7 日情报", totals.observations_7d, "最近一周已采集证据", "P06"), workbenchSummary("运行异常", Number(totals.failed_collection_runs_24h ?? 0) + Number(totals.open_source_circuits ?? 0), "失败运行与熔断数据源", "P21", "danger"));
    host.append(summary);
    const columns = document.createElement("div");
    columns.className = "r04-workbench-columns";
    const left = document.createElement("div");
    left.className = "r04-workbench-primary";
    const right = document.createElement("div");
    right.className = "r04-workbench-secondary";
    const opportunities = (Array.isArray(data.top_opportunities) ? data.top_opportunities : []).slice(0, 8);
    const opportunityRows = opportunities.map((row) => [
        linkTo("P13", text(row.title), { id: row.id }),
        text(row.id),
        number(row.score, 1),
        text(row.evidence_count, "0"),
        stageLabel(row.stage),
        formatDate(row.last_seen_at),
    ]);
    const opportunityBody = opportunityRows.length ? table(["机会", "ID", "评分", "证据", "阶段", "更新时间"], opportunityRows) : statePanel("empty", "当前没有可分诊的机会记录。");
    left.append(workbenchSection("重点机会", linkTo("P12", "查看全部"), opportunityBody));
    const alertBody = document.createElement("div");
    alertBody.className = "r04-workbench-alerts";
    if (alertResult.status === "fulfilled") {
        const alerts = Array.isArray(alertResult.value) ? alertResult.value : [];
        if (alerts.length)
            for (const row of alerts.slice(0, 5)) {
                const item = document.createElement("article");
                item.className = "r04-workbench-alert";
                const titleRow = document.createElement("div");
                titleRow.className = "r04-workbench-alert-title";
                titleRow.append(badge(alertType(row), row.priority === "CRITICAL" ? "danger" : "warning"));
                const when = document.createElement("time");
                when.textContent = formatDate(row.created_at);
                titleRow.append(when);
                const name = document.createElement("strong");
                name.textContent = text(row.title, "未命名告警");
                const message = document.createElement("p");
                message.textContent = text(row.message, "该告警未提供补充说明。");
                const target = alertTarget(row);
                const link = document.createElement("a");
                link.href = target.href;
                link.textContent = target.label;
                item.append(titleRow, name, message, link);
                alertBody.append(item);
            }
        else
            alertBody.append(statePanel("empty", "当前没有待处理告警。"));
    }
    else
        alertBody.append(statePanel("partial", "告警接口暂时不可用；其余工作台数据仍可查看。"));
    right.append(workbenchSection("需要关注", linkTo("P24", "查看全部"), alertBody));
    const researchBody = document.createElement("div");
    researchBody.className = "r04-workbench-research";
    researchBody.append(capabilityUnavailableNotice("当前后端未暴露独立研究结果资源；工作台不从机会摘要拼装研究结果。", "研究结果暂不可用"));
    researchBody.append(linkTo("P15", "进入研究任务列表"));
    right.append(workbenchSection("最近研究结果", linkTo("P15", "查看研究"), researchBody));
    columns.append(left, right);
    host.append(columns);
    const latestBody = document.createElement("div");
    latestBody.className = "r04-workbench-latest";
    if (observationsResult.status === "fulfilled") {
        const rows = (observationsResult.value?.items ?? []);
        if (rows.length)
            for (const row of rows.slice(0, 5)) {
                const item = document.createElement("article");
                const meta = document.createElement("div");
                meta.className = "r04-workbench-latest-meta";
                meta.textContent = formatDate(row.observed_at);
                const link = linkTo("P07", text(row.title), { id: row.id });
                link.className = "r04-workbench-latest-title";
                const copy = document.createElement("p");
                copy.textContent = text(row.text, "该情报未提供摘要。");
                const source = document.createElement("span");
                source.textContent = `来源：${text(row.source_id)}`;
                item.append(meta, link, copy, source);
                latestBody.append(item);
            }
        else
            latestBody.append(statePanel("empty", "当前没有已采集的最新情报。"));
    }
    else
        latestBody.append(statePanel("partial", "情报接口暂时不可用；请从情报工作台重试。"));
    host.append(workbenchSection("最新情报变化", linkTo("P06", "进入情报工作台"), latestBody, "r04-workbench-latest-section"));
    return host;
}
function workbenchSummary(labelValue, value, meta, screen, tone = "normal") {
    const link = linkTo(screen, "", {});
    link.className = `r04-workbench-summary-card r04-workbench-summary-${tone}`;
    const label = document.createElement("span");
    label.textContent = labelValue;
    const numberValue = document.createElement("strong");
    numberValue.textContent = number(value);
    const copy = document.createElement("small");
    copy.textContent = meta;
    link.append(label, numberValue, copy);
    return link;
}
function workbenchSection(titleValue, action, body, className = "") {
    const section = document.createElement("section");
    section.className = `r04-workbench-section ${className}`.trim();
    const header = document.createElement("header");
    header.className = "r04-workbench-section-header";
    const title = document.createElement("h2");
    title.textContent = titleValue;
    header.append(title, action);
    section.append(header, body);
    return section;
}
function stageLabel(value) { return { DISCOVERY: "发现", EARLY_GROWTH: "早期增长", PRODUCTIZING: "产品化", COMMERCIALIZING: "商业化", DORMANT: "休眠" }[String(value)] ?? text(value); }
async function renderSearch(context) {
    const host = document.createElement("div");
    host.className = "r04-search-page";
    const heading = document.createElement("div");
    heading.className = "r04-search-heading";
    const title = document.createElement("h1");
    title.textContent = "全局搜索";
    const subtitle = document.createElement("p");
    subtitle.textContent = "在已确认可搜索的机会、情报和关键词中查找真实记录。";
    heading.append(title, subtitle);
    const form = document.createElement("form");
    form.className = "r04-search-form";
    const query = document.createElement("input");
    query.type = "search";
    query.name = "q";
    query.placeholder = "输入关键词、标题或实体 ID";
    query.setAttribute("aria-label", "搜索关键词、标题或实体 ID");
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "r04-search-submit";
    submit.textContent = "搜索";
    form.append(query, submit);
    const body = document.createElement("div");
    body.className = "r04-search-layout";
    const main = document.createElement("section");
    main.className = "r04-search-main";
    const tabsHost = document.createElement("nav");
    tabsHost.className = "r04-search-tabs";
    tabsHost.setAttribute("aria-label", "搜索对象类型");
    const results = document.createElement("div");
    results.className = "r04-search-results";
    const filter = document.createElement("aside");
    filter.className = "r04-search-filter";
    const filterTitle = document.createElement("h2");
    filterTitle.textContent = "筛选条件";
    const filterCopy = document.createElement("p");
    filterCopy.textContent = "搜索范围由当前后端资源决定。研究和运行暂未提供统一搜索资源，因此不展示未验证的结果。";
    filter.append(filterTitle, filterCopy, capabilityUnavailableNotice("研究与运行没有统一搜索接口；可从帮助入口进入对应列表。", "搜索范围说明"));
    let activeCategory = "all";
    const categories = [["all", "全部"], ["opportunities", "机会"], ["observations", "情报"], ["keywords", "关键词"]];
    const renderTabs = () => {
        tabsHost.replaceChildren();
        for (const [key, label] of categories) {
            const tab = document.createElement("button");
            tab.type = "button";
            tab.className = `r04-search-tab${activeCategory === key ? " is-active" : ""}`;
            tab.textContent = label;
            tab.setAttribute("aria-selected", String(activeCategory === key));
            tab.addEventListener("click", () => { activeCategory = key; renderTabs(); void runSearch(text(query.value).trim(), activeCategory, results, context); });
            tabsHost.append(tab);
        }
    };
    form.addEventListener("submit", (event) => { event.preventDefault(); void runSearch(text(query.value).trim(), activeCategory, results, context); });
    const initial = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("q") ?? "";
    query.value = initial;
    renderTabs();
    main.append(tabsHost, results);
    body.append(main, filter);
    host.append(heading, form, body);
    if (initial)
        void runSearch(initial, activeCategory, results, context);
    else
        results.append(statePanel("ready", "输入查询词后搜索真实业务记录。"));
    return host;
}
async function runSearch(query, category, results, context) {
    results.replaceChildren(statePanel("loading", "正在搜索真实记录…"));
    if (!query) {
        results.replaceChildren(statePanel("empty", "请输入查询词后再搜索。"));
        return;
    }
    const jobs = [];
    if (category === "all" || category === "opportunities")
        jobs.push(api(`/api/v1/opportunities/page?q=${encodeURIComponent(query)}&limit=50`));
    if (category === "all" || category === "observations")
        jobs.push(api(`/api/v1/observations?q=${encodeURIComponent(query)}&limit=50`));
    if (category === "all" || category === "keywords")
        jobs.push(api("/api/v1/keywords?limit=500"));
    const settled = await Promise.allSettled(jobs);
    const failed = settled.find((item) => item.status === "rejected");
    if (settled.length > 0 && settled.every((item) => item.status === "rejected")) {
        results.replaceChildren(statePanel("error", "搜索接口暂时不可用，请稍后重试。", () => void runSearch(query, category, results, context)));
        if (failed && failed.status === "rejected" && failed.reason instanceof ApiError && failed.reason.status === 401)
            context.onSessionExpired();
        return;
    }
    const records = [];
    let index = 0;
    if (category === "all" || category === "opportunities") {
        const value = settled[index++];
        if (value.status === "fulfilled")
            for (const row of value.value?.items ?? [])
                records.push(searchResultCard("机会", "success", text(row.opportunity_key ?? row.id), text(row.title), text(row.summary), `评分 ${number(row.score, 1)} · ${text(row.stage)}`, routeFor("P13", { id: row.id })));
    }
    if (category === "all" || category === "observations") {
        const value = settled[index++];
        if (value.status === "fulfilled")
            for (const row of value.value?.items ?? [])
                records.push(searchResultCard("情报", "info", text(row.source_id), text(row.title), text(row.text), `观察时间 ${formatDate(row.observed_at)}`, routeFor("P07", { id: row.id })));
    }
    if (category === "all" || category === "keywords") {
        const value = settled[index++];
        if (value.status === "fulfilled")
            for (const row of (value.value ?? []).filter((item) => `${item.keyword ?? item.display_name ?? ""} ${item.canonical ?? ""}`.toLowerCase().includes(query.toLowerCase())))
                records.push(searchResultCard("关键词", "warning", text(row.id), text(row.keyword ?? row.display_name), `状态：${text(row.status)}`, `得分 ${number(row.score, 1)} · 观察数 ${text(row.observation_count)}`, routeFor("P10", { keyword_id: row.id })));
    }
    const summary = document.createElement("p");
    summary.className = "r04-search-summary";
    summary.textContent = `找到 ${records.length} 个相关结果`;
    results.replaceChildren(summary);
    if (!records.length)
        results.append(statePanel("empty", `没有找到与“${query}”匹配的真实记录。`));
    else {
        const list = document.createElement("div");
        list.className = "r04-search-list";
        list.append(...records);
        results.append(list);
    }
    if (failed)
        results.prepend(statePanel("partial", "部分搜索分类暂时不可用；当前结果仍来自真实接口。"));
}
function searchResultCard(type, tone, id, titleValue, description, meta, href) {
    const card = document.createElement("article");
    card.className = "r04-search-result";
    const top = document.createElement("div");
    top.className = "r04-search-result-top";
    top.append(badge(type, tone));
    const idEl = document.createElement("code");
    idEl.textContent = id;
    top.append(idEl);
    const title = document.createElement("a");
    title.href = href;
    title.textContent = titleValue;
    title.className = "r04-search-result-title";
    const copy = document.createElement("p");
    copy.textContent = description;
    const footer = document.createElement("div");
    footer.className = "r04-search-result-footer";
    const metaEl = document.createElement("span");
    metaEl.textContent = meta;
    const open = document.createElement("a");
    open.href = href;
    open.textContent = "查看详情";
    footer.append(metaEl, open);
    card.append(top, title, copy, footer);
    return card;
}
function renderLoginHelp() {
    const page = document.createElement("main");
    page.className = "r04-auth-page";
    const card = document.createElement("section");
    card.className = "r04-help-card";
    const brand = document.createElement("div");
    brand.className = "r04-help-brand-mark";
    brand.textContent = "@";
    const title = document.createElement("h1");
    title.textContent = "无法登录？";
    const subtitle = document.createElement("p");
    subtitle.className = "r04-help-subtitle";
    subtitle.textContent = "Opportunity Radar  |  R04 机会情报平台";
    const notice = document.createElement("div");
    notice.className = "r04-help-notice";
    notice.textContent = "当前平台尚未开放已验证的自助密码重置流程。请联系系统管理员确认账户状态或执行密码恢复。";
    const sections = document.createElement("div");
    sections.className = "r04-help-sections";
    sections.append(helpSection("账户恢复方式", ["管理员协助处理。"]), helpSection("可能原因", ["密码错误", "账户锁定", "MFA 问题", "认证服务不可用"]));
    const info = document.createElement("section");
    info.className = "r04-help-info";
    const infoTitle = document.createElement("h2");
    infoTitle.textContent = "需要提供给管理员的信息";
    const infoList = document.createElement("ul");
    for (const value of ["用户名/邮箱", "发生时间", "错误提示"]) {
        const item = document.createElement("li");
        item.textContent = value;
        infoList.append(item);
    }
    const safety = document.createElement("p");
    safety.className = "r04-help-safety";
    safety.textContent = "安全提示：系统管理员不会要求您提供密码或 MFA 密钥。请勿在任何通信中包含此类敏感凭证。";
    info.append(infoTitle, infoList, safety);
    const footer = document.createElement("footer");
    footer.className = "r04-help-footer";
    const login = document.createElement("a");
    login.className = "r04-auth-submit";
    login.href = routeFor("P01");
    login.textContent = "返回登录";
    const status = document.createElement("a");
    status.className = "r04-help-status-link";
    status.href = routeFor("P30");
    status.textContent = "查看系统状态";
    footer.append(login, status);
    card.append(brand, title, subtitle, notice, sections, info, footer);
    page.append(card);
    return page;
}
function helpSection(titleValue, values) {
    const section = document.createElement("section");
    section.className = "r04-help-section";
    const title = document.createElement("h2");
    title.textContent = titleValue;
    const list = document.createElement("ul");
    for (const value of values) {
        const item = document.createElement("li");
        item.textContent = value;
        list.append(item);
    }
    section.append(title, list);
    return section;
}
export function renderNotificationDrawer(context) {
    const utility = createUtilityDrawer("通知", "最近需要关注的系统与业务变化");
    const loading = statePanel("loading", "正在读取告警事件…");
    utility.body.append(loading);
    const allAlerts = linkTo("P24", "查看全部告警");
    const runs = linkTo("P21", "查看运行记录");
    utility.footer.append(allAlerts, runs);
    void loadNotificationEvents(utility.body, context);
    return utility.overlay;
}
async function loadNotificationEvents(body, context) {
    try {
        const rows = await api("/api/v1/alerts/events?limit=20");
        body.replaceChildren();
        if (!Array.isArray(rows) || !rows.length) {
            body.append(statePanel("empty", "当前没有可读取的告警事件。"));
            return;
        }
        const list = document.createElement("div");
        list.className = "r04-notification-list";
        for (const row of rows) {
            const item = document.createElement("article");
            item.className = `r04-notification-item r04-notification-${String(row.priority ?? "NORMAL").toLowerCase()}`;
            const top = document.createElement("div");
            top.className = "r04-notification-top";
            top.append(badge(alertType(row), row.priority === "CRITICAL" ? "danger" : row.status === "NEW" ? "warning" : "neutral"));
            const time = document.createElement("time");
            time.dateTime = String(row.created_at ?? "");
            time.textContent = formatDate(row.created_at);
            top.append(time);
            const title = document.createElement("h3");
            title.textContent = text(row.title, "未命名告警");
            const message = document.createElement("p");
            message.textContent = text(row.message, "该告警未提供补充说明。");
            const meta = document.createElement("span");
            meta.className = "r04-notification-meta";
            meta.textContent = `ID：${text(row.event_key ?? row.id)} · 状态：${alertStatusLabel(row.status)}`;
            const target = alertTarget(row);
            const link = document.createElement("a");
            link.href = target.href;
            link.textContent = target.label;
            const footer = document.createElement("div");
            footer.className = "r04-notification-footer";
            footer.append(meta, link);
            item.append(top, title, message, footer);
            list.append(item);
        }
        body.append(list);
    }
    catch (error) {
        body.replaceChildren();
        if (error instanceof ApiError && error.status === 401)
            context.onSessionExpired();
        body.append(statePanel("error", "通知数据暂时不可用。", () => void loadNotificationEvents(body, context)));
    }
}
function alertType(row) {
    if (row.priority === "CRITICAL")
        return "关键告警";
    if (row.opportunity_id)
        return "机会变化";
    if (row.keyword_id)
        return "关键词告警";
    return "系统告警";
}
function alertStatusLabel(value) {
    return { NEW: "新建", ACKNOWLEDGED: "已确认", DISMISSED: "已忽略", RESOLVED: "已解决" }[String(value)] ?? text(value);
}
function alertTarget(row) {
    if (row.opportunity_id)
        return { href: routeFor("P13", { id: row.opportunity_id }), label: "查看机会" };
    if (row.keyword_id)
        return { href: routeFor("P10", { keyword_id: row.keyword_id }), label: "查看关键词" };
    return { href: routeFor("P24"), label: "查看告警详情" };
}
export function renderHelpDrawer(route) {
    const utility = createUtilityDrawer("帮助", "当前页面说明与常用排查入口");
    const current = document.createElement("section");
    current.className = "r04-help-drawer-section";
    const currentTitle = document.createElement("h3");
    currentTitle.textContent = "当前页面说明";
    const currentCopy = document.createElement("p");
    currentCopy.textContent = `当前位于${pageLabel(route.screen)}。这里的内容来自真实接口或明确的只读降级状态。`;
    current.append(currentTitle, currentCopy);
    const path = document.createElement("section");
    path.className = "r04-help-drawer-section";
    const pathTitle = document.createElement("h3");
    pathTitle.textContent = "常用使用路径";
    const opportunityPath = document.createElement("div");
    opportunityPath.className = "r04-help-path";
    opportunityPath.append(linkTo("P02", "工作台"), arrow(), linkTo("P12", "机会"), arrow(), linkTo("P06", "证据"), arrow(), linkTo("P18", "数据源"));
    const operationsPath = document.createElement("div");
    operationsPath.className = "r04-help-path";
    operationsPath.append(linkTo("P18", "数据源"), arrow(), linkTo("P21", "运行记录"), arrow(), linkTo("P22", "运行详情"), arrow(), linkTo("P23", "分析队列"));
    path.append(pathTitle, pathLabel("机会溯源链路"), opportunityPath, pathLabel("故障排查链路"), operationsPath);
    const glossary = document.createElement("section");
    glossary.className = "r04-help-drawer-section";
    const glossaryTitle = document.createElement("h3");
    glossaryTitle.textContent = "术语说明";
    glossary.append(glossaryTitle, glossaryItem("机会分数", "系统基于已确认维度计算的机会潜在价值评分。"), glossaryItem("置信度", "情报来源和分析逻辑的可靠性评级。"), glossaryItem("证据覆盖", "研究结果由有效证据支持的比例；未有后端字段时不推算。"), glossaryItem("数据新鲜度", "距离底层数据源最后一次成功同步的时间间隔。"));
    utility.body.append(current, path, glossary);
    utility.footer.append(linkTo("P30", "查看系统诊断"), linkTo("P28", "查看账户与安全"), linkTo("P04", "403 权限说明", { requested: window.location.pathname }));
    return utility.overlay;
}
function createUtilityDrawer(titleValue, subtitleValue) {
    const overlay = document.createElement("div");
    overlay.className = "r04-utility-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    const scrim = document.createElement("button");
    scrim.type = "button";
    scrim.className = "r04-utility-scrim";
    scrim.setAttribute("aria-label", "关闭抽屉");
    const panel = document.createElement("aside");
    panel.className = "r04-utility-drawer";
    const header = document.createElement("header");
    header.className = "r04-utility-header";
    const heading = document.createElement("div");
    const title = document.createElement("h2");
    title.textContent = titleValue;
    const subtitle = document.createElement("p");
    subtitle.textContent = subtitleValue;
    heading.append(title, subtitle);
    const close = document.createElement("button");
    close.type = "button";
    close.className = "r04-utility-close";
    close.setAttribute("aria-label", "关闭抽屉");
    close.textContent = "×";
    header.append(heading, close);
    const body = document.createElement("div");
    body.className = "r04-utility-body";
    const footer = document.createElement("footer");
    footer.className = "r04-utility-footer";
    const dismiss = () => overlay.remove();
    close.addEventListener("click", dismiss);
    scrim.addEventListener("click", dismiss);
    overlay.addEventListener("keydown", (event) => { if (event.key === "Escape")
        dismiss(); });
    panel.append(header, body, footer);
    overlay.append(scrim, panel);
    return { overlay, body, footer };
}
function arrow() { const span = document.createElement("span"); span.className = "r04-help-arrow"; span.textContent = "→"; return span; }
function pathLabel(value) { const span = document.createElement("strong"); span.className = "r04-help-path-label"; span.textContent = `${value}：`; return span; }
function glossaryItem(titleValue, copyValue) { const item = document.createElement("div"); item.className = "r04-help-glossary-item"; const title = document.createElement("strong"); title.textContent = titleValue; const copy = document.createElement("p"); copy.textContent = copyValue; item.append(title, copy); return item; }
function pageLabel(screen) { return { P02: "工作台", P03: "全局搜索", P06: "最新情报", P12: "机会", P13: "机会详情", P18: "数据源", P21: "运行记录", P24: "告警" }[screen] ?? "当前页面"; }
function renderForbidden(route, session) {
    const host = document.createElement("main");
    host.className = "r04-error-page";
    const card = document.createElement("section");
    card.className = "r04-error-card";
    const icon = document.createElement("div");
    icon.className = "r04-error-icon r04-error-icon-danger";
    icon.textContent = "▣";
    const code = document.createElement("strong");
    code.className = "r04-error-code r04-error-code-danger";
    code.textContent = "403";
    const title = document.createElement("h1");
    title.textContent = "无权访问";
    const copy = document.createElement("p");
    copy.textContent = "当前账户没有访问此资源所需的权限。如认为这是错误，请联系管理员。";
    const meta = document.createElement("dl");
    meta.className = "r04-error-meta";
    const requestPath = route.params.get("requested") ?? "当前页面";
    appendMeta(meta, "请求路径", requestPath);
    appendMeta(meta, "当前角色", roleLabel(session.role));
    const primaryActions = document.createElement("div");
    primaryActions.className = "r04-error-actions r04-error-actions-dual";
    primaryActions.append(button("返回上一页", { variant: "primary", onClick: () => goBackOr("P02") }), button("返回工作台", { variant: "secondary", onClick: () => navigate("P02") }));
    const account = linkTo("P28", "查看个人账户与安全");
    account.className = "r04-error-link";
    card.append(icon, code, title, copy, meta, primaryActions, account);
    host.append(card);
    return host;
}
function renderNotFound(route) {
    const page = document.createElement("main");
    page.className = "r04-not-found-page";
    const card = document.createElement("section");
    card.className = "r04-not-found-card";
    const code = document.createElement("span");
    code.className = "r04-error-code-chip";
    code.textContent = "404";
    const title = document.createElement("h1");
    title.textContent = "对象不存在";
    const copy = document.createElement("p");
    copy.textContent = "请求的对象可能已删除、已移动，或当前暂不可用。";
    const meta = document.createElement("dl");
    meta.className = "r04-error-meta r04-error-meta-wide";
    const requested = route.params.get("requested") ?? "/unknown";
    appendMeta(meta, "对象 ID", objectIdFromPath(requested));
    appendMeta(meta, "请求路径", requested);
    const actions = document.createElement("div");
    actions.className = "r04-error-actions";
    actions.append(button("返回上一页", { variant: "primary", onClick: () => goBackOr("P02") }), button("全局搜索", { variant: "secondary", onClick: () => navigate("P03") }), button("返回工作台", { variant: "secondary", onClick: () => navigate("P02") }));
    const opportunities = linkTo("P12", "查看机会列表");
    opportunities.className = "r04-error-link";
    card.append(code, title, copy, meta, actions, opportunities);
    page.append(card);
    return page;
}
function appendMeta(parent, labelValue, value) {
    const dt = document.createElement("dt");
    dt.textContent = labelValue;
    const dd = document.createElement("dd");
    dd.textContent = value;
    parent.append(dt, dd);
}
function objectIdFromPath(path) {
    const value = path.split("/").filter(Boolean).pop();
    return value || "—";
}
function roleLabel(role) {
    return { VIEWER: "查看者", OPERATOR: "操作员", ADMIN: "管理员", OWNER: "所有者" }[role] ?? role;
}
function goBackOr(fallback) {
    if (window.history.length > 1)
        window.history.back();
    else
        navigate(fallback);
}
async function renderIntelligenceList(context) {
    const host = document.createElement("div");
    host.className = "r04-intelligence-list";
    host.append(readOnlyNotice("关联关系由当前后端结果展示，本页不提供人工修改。 observations API 未返回机会关联或处理状态字段，因此不拼装这些筛选项。", "情报关联只读"));
    const heading = document.createElement("div");
    heading.className = "r04-intelligence-heading";
    const headingText = document.createElement("div");
    const title = document.createElement("h1");
    title.textContent = "最新情报";
    const subtitle = document.createElement("p");
    subtitle.textContent = "查看系统采集并入库的最新信号与观察";
    headingText.append(title, subtitle);
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.className = "r04-intelligence-refresh";
    refresh.textContent = "↻ 刷新列表";
    refresh.addEventListener("click", () => window.location.reload());
    heading.append(headingText, refresh);
    host.append(heading);
    const filters = document.createElement("form");
    filters.className = "r04-intelligence-filters";
    const q = document.createElement("input");
    q.type = "search";
    q.name = "q";
    q.placeholder = "搜索关键词或标题";
    q.setAttribute("aria-label", "搜索关键词或标题");
    const source = document.createElement("input");
    source.name = "source_id";
    source.placeholder = "来源 ID";
    source.setAttribute("aria-label", "来源 ID");
    const type = document.createElement("select");
    type.setAttribute("aria-label", "情报类型");
    addOption(type, "", "类型：全部");
    for (const value of ["NEWS", "JOB", "PRODUCT", "REPOSITORY", "TREND"])
        addOption(type, value, observationTypeLabel(value));
    const quality = document.createElement("select");
    quality.setAttribute("aria-label", "证据质量");
    addOption(quality, "", "质量：全部");
    for (const value of ["A", "B", "C"])
        addOption(quality, value, `质量：${qualityLabel(value)}`);
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "r04-intelligence-submit";
    submit.textContent = "筛选";
    filters.append(q, source, type, quality, submit);
    host.append(filters);
    const results = document.createElement("div");
    results.className = "r04-intelligence-results";
    host.append(results);
    const load = async (offset) => {
        results.replaceChildren(statePanel("loading", "正在读取最新情报…"));
        const params = new URLSearchParams({ limit: "50", offset: String(offset) });
        if (q.value.trim())
            params.set("q", q.value.trim());
        if (source.value.trim())
            params.set("source_id", source.value.trim());
        if (type.value)
            params.set("item_type", type.value);
        try {
            const data = await api(`/api/v1/observations?${params.toString()}`);
            const items = (data.items ?? []).filter((row) => !quality.value || String(row.evidence_quality) === quality.value);
            const rows = items.map((row) => [formatDate(row.observed_at), linkTo("P07", text(row.title), { id: row.id, q: q.value, source_id: source.value }), text(row.source_id), observationTypeLabel(row.item_type), badge(qualityLabel(row.evidence_quality), row.evidence_quality === "A" ? "success" : row.evidence_quality === "B" ? "info" : "neutral"), badge("已采集", "neutral")]);
            results.replaceChildren(rows.length ? table(["时间 / 数据新鲜度", "情报摘要", "来源", "类型", "质量", "处理状态"], rows) : statePanel("empty", q.value ? "没有匹配当前筛选条件的情报。" : "当前没有已采集的情报记录。"));
            const pager = document.createElement("div");
            pager.className = "r04-intelligence-pager";
            const previous = document.createElement("button");
            previous.type = "button";
            previous.textContent = "上一页";
            previous.disabled = offset <= 0;
            previous.addEventListener("click", () => void load(Math.max(0, offset - 50)));
            const pageText = document.createElement("span");
            pageText.textContent = `显示 ${offset + (items.length ? 1 : 0)} - ${offset + items.length} 条，共 ${text(data.total, "未知")} 条记录`;
            const next = document.createElement("button");
            next.type = "button";
            next.textContent = "下一页";
            next.disabled = !data.has_more;
            next.addEventListener("click", () => void load(offset + 50));
            pager.append(previous, pageText, next);
            results.append(pager);
        }
        catch (error) {
            results.replaceChildren(errorState(error, context, () => void load(offset)));
        }
    };
    filters.addEventListener("submit", (event) => { event.preventDefault(); void load(0); });
    await load(0);
    return host;
}
async function renderIntelligenceSummary(route, context) {
    const id = route.params.get("id");
    const host = document.createElement("div");
    host.className = "r04-intelligence-detail";
    if (!id) {
        host.append(statePanel("error", "情报 ID 缺失。"));
        return host;
    }
    try {
        const params = new URLSearchParams({ limit: "500" });
        if (route.params.get("q"))
            params.set("q", route.params.get("q"));
        if (route.params.get("source_id"))
            params.set("source_id", route.params.get("source_id"));
        const data = await api(`/api/v1/observations?${params.toString()}`);
        const row = (data.items ?? []).find((item) => String(item.id) === id);
        if (!row) {
            host.append(objectNotFound("情报", id));
            return host;
        }
        const requestedTab = route.params.get("tab") ?? "summary";
        const activeTab = ["summary", "raw", "relations", "process"].includes(requestedTab) ? requestedTab : "summary";
        const header = document.createElement("header");
        header.className = "r04-intelligence-entity";
        const crumb = document.createElement("div");
        crumb.className = "r04-entity-crumb";
        crumb.append(linkTo("P06", "情报"), document.createTextNode(" / "), document.createTextNode("最新情报"), document.createTextNode(" / "), document.createTextNode(id));
        const title = document.createElement("h1");
        title.textContent = `“${text(row.title, "未命名情报")}”`;
        const meta = document.createElement("p");
        meta.className = "r04-intelligence-meta";
        meta.textContent = `来源：${text(row.source_id)} · 采集时间：${formatDate(row.observed_at)} · 质量：${qualityLabel(row.evidence_quality)} · 类型：${observationTypeLabel(row.item_type)}`;
        const tabs = document.createElement("nav");
        tabs.className = "r04-intelligence-tabs";
        for (const [tab, label] of [["summary", "摘要"], ["raw", "原始证据"], ["relations", "关系"], ["process", "处理过程"]]) {
            const link = linkTo("P07", label, { id, tab, q: route.params.get("q") ?? "", source_id: route.params.get("source_id") ?? "" });
            link.className = activeTab === tab ? "is-active" : "";
            link.setAttribute("aria-current", activeTab === tab ? "page" : "false");
            tabs.append(link);
        }
        header.append(crumb, title, badge("已采集记录", "neutral"), meta, tabs);
        const body = document.createElement("div");
        body.className = "r04-intelligence-detail-grid";
        if (activeTab === "raw") {
            body.append(renderIntelligenceRaw(row));
        }
        else if (activeTab === "relations") {
            body.append(renderIntelligenceRelations(row));
        }
        else if (activeTab === "process") {
            body.append(await renderIntelligenceProcess(row, context));
        }
        else {
            const main = document.createElement("main");
            main.className = "r04-intelligence-detail-main";
            const summary = document.createElement("p");
            summary.className = "r04-intelligence-summary-copy";
            summary.textContent = text(row.text, "该情报未提供正文摘要。");
            main.append(detailSectionWithBody("归一化摘要", summary));
            const evidence = document.createElement("div");
            evidence.className = "r04-intelligence-evidence";
            const quote = document.createElement("blockquote");
            quote.textContent = text(row.text, "暂无可展示的原始文本。");
            const sourceLink = row.source_url ? externalLink(text(row.source_url)) : linkTo("P18", "查看数据源列表");
            sourceLink.textContent = row.source_url ? "打开原始来源" : "查看数据源列表";
            evidence.append(quote, sourceLink);
            main.append(detailSectionWithBody("证据出处", evidence));
            body.append(main);
            const side = document.createElement("aside");
            side.className = "r04-intelligence-detail-side";
            side.append(detailSectionWithBody("来源信息", detailList([["来源 ID", row.source_id], ["采集方式", row.acquisition_method], ["来源 URL", row.source_url ? "已提供" : "未提供"], ["采集时间", formatDate(row.observed_at)]])));
            side.append(capabilityUnavailableNotice("观察记录没有返回关联机会 ID；关联对象资源尚未暴露，因此不显示固定机会链接。", "关联机会暂不可用"));
            side.append(detailSectionWithBody("产生该情报的运行", capabilityUnavailableNotice("观察记录没有返回 collection run ID；可从运行记录列表查看真实运行摘要。", "运行关联暂不可用")), linkTo("P21", "查看运行记录"));
            body.append(side);
        }
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "r04-intelligence-copy";
        copy.textContent = "复制当前链接";
        copy.addEventListener("click", () => { void navigator.clipboard?.writeText(window.location.href).then(() => { copy.textContent = "链接已复制"; }); });
        host.append(header, copy, body);
    }
    catch (error) {
        host.append(errorState(error, context, () => void renderIntelligenceSummary(route, context)));
    }
    return host;
}
function renderIntelligenceRaw(row) {
    const host = document.createElement("div");
    host.className = "r04-intelligence-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-intelligence-tab-main";
    const rawBody = document.createElement("div");
    rawBody.className = "r04-intelligence-raw-body";
    const pre = document.createElement("pre");
    pre.className = "r04-intelligence-raw-snippet";
    pre.textContent = text(row.text, "该观察记录没有返回正文片段。");
    const rawNote = document.createElement("p");
    rawNote.className = "r04-intelligence-raw-note";
    rawNote.textContent = "正文来自 observations API 返回的 text 字段；接口当前最多返回 2000 个字符，未宣称为完整原始页面。";
    rawBody.append(pre, rawNote);
    main.append(detailSectionWithBody("原始正文 / 抓取片段", rawBody));
    const fieldRows = [
        ["id", text(row.id), "情报记录标识"],
        ["title", text(row.title, "未提供"), "列表标题"],
        ["text", text(row.text, "未提供"), "正文片段"],
        ["source_id", text(row.source_id, "未提供"), "来源归属"],
        ["source_url", row.source_url ? externalLink(String(row.source_url)) : "未提供", "原始来源入口"],
        ["item_type", observationTypeLabel(row.item_type), "观察类型"],
        ["evidence_quality", qualityLabel(row.evidence_quality), "证据质量"],
        ["acquisition_method", text(row.acquisition_method, "未提供"), "采集方式"],
        ["observed_at", formatDate(row.observed_at), "采集时间"],
    ];
    main.append(detailSectionWithBody("已返回字段 / 只读对照", table(["observations 字段", "当前值", "用途"], fieldRows)));
    const side = document.createElement("aside");
    side.className = "r04-intelligence-tab-side";
    side.append(detailSectionWithBody("来源信息", detailList([["来源 ID", row.source_id], ["来源 URL", row.source_url ? "已提供" : "未提供"], ["采集方式", row.acquisition_method], ["采集时间", formatDate(row.observed_at)]])));
    side.append(detailSectionWithBody("技术溯源", capabilityUnavailableNotice("content hash、原始 HTML、collection run ID 和处理日志没有由当前情报接口返回，因此不显示 HTML 中的示例值。", "技术字段暂不可用")));
    side.append(row.source_url ? externalLink(String(row.source_url)) : linkTo("P19", "查看数据源健康"));
    host.append(main, side);
    return host;
}
function renderIntelligenceRelations(row) {
    const host = document.createElement("div");
    host.className = "r04-intelligence-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-intelligence-tab-main";
    const matrix = document.createElement("div");
    matrix.className = "r04-intelligence-relation-panel";
    matrix.append(capabilityUnavailableNotice("当前后端没有按情报 ID 查询关系拓扑、实体、相似情报或关联机会的资源。此处不使用 HTML mock 中的固定对象 ID、推理理由或关系强度。", "关系拓扑暂不可用"));
    const actualRows = [["情报记录", text(row.id), "当前 observations 记录"], ["来源", text(row.source_id, "未提供"), "observations.source_id 字段"]];
    main.append(detailSectionWithBody("关系拓扑与推理矩阵", matrix), detailSectionWithBody("当前可确认的归属", table(["对象", "标识", "证据"], actualRows)));
    const side = document.createElement("aside");
    side.className = "r04-intelligence-tab-side";
    const links = document.createElement("div");
    links.className = "r04-intelligence-drilldown";
    links.append(linkTo("P19", "查看数据源与健康", { id: text(row.source_id) }), linkTo("P12", "查看真实机会列表"), linkTo("P15", "查看研究入口"));
    side.append(detailSectionWithBody("安全下钻入口", links));
    side.append(capabilityUnavailableNotice("没有真实关联对象 ID 时，不提供“关联机会”或“手动触发分析”按钮，避免伪写和固定对象跳转。", "关联操作已隐藏"));
    host.append(main, side);
    return host;
}
async function renderIntelligenceProcess(row, context) {
    const host = document.createElement("div");
    host.className = "r04-intelligence-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-intelligence-tab-main";
    const pipeline = document.createElement("section");
    pipeline.className = "r04-intelligence-process";
    const heading = document.createElement("div");
    heading.className = "r04-intelligence-process-heading";
    const headingTitle = document.createElement("h2");
    headingTitle.textContent = "数据处理流水线";
    const headingNote = document.createElement("span");
    headingNote.textContent = "仅显示当前记录可证实的阶段";
    heading.append(headingTitle, headingNote);
    pipeline.append(heading);
    pipeline.append(intelligenceProcessStage("采集记录", "接口已返回", [["来源", row.source_id], ["采集方式", row.acquisition_method], ["采集时间", formatDate(row.observed_at)], ["输入", row.source_url ? String(row.source_url) : "未提供 URL"]]));
    pipeline.append(intelligenceProcessStage("观察记录入库", "接口已返回", [["记录 ID", row.id], ["类型", observationTypeLabel(row.item_type)], ["标题", row.title], ["正文", row.text ? "已返回正文片段" : "未返回正文"]]));
    const unavailableStage = document.createElement("div");
    unavailableStage.className = "r04-intelligence-process-stage";
    unavailableStage.append(document.createElement("span"), detailSectionWithBody("规范化、关系与机会关联", capabilityUnavailableNotice("当前没有返回该情报对应的 collection run、处理步骤、日志、关系输出或机会关联 ID，因此无法证明这些阶段已执行。", "处理轨迹未暴露")));
    pipeline.append(unavailableStage);
    main.append(pipeline);
    const side = document.createElement("aside");
    side.className = "r04-intelligence-tab-side";
    const health = document.createElement("div");
    health.append(statePanel("loading", "正在读取来源健康状态…"));
    try {
        const rows = await api("/api/v1/sources/health");
        const selected = (Array.isArray(rows) ? rows : []).filter((item) => String(item.source_id) === String(row.source_id));
        health.replaceChildren(selected.length ? table(["来源", "状态", "最近成功", "最近错误"], selected.map((item) => [text(item.source_id), badge(text(item.status ?? item.runtime_status, "未提供"), item.status === "HEALTHY" ? "success" : "warning"), formatDate(item.last_success_at), text(item.last_error, "未返回")])) : statePanel("empty", "没有找到该来源的健康记录。"));
    }
    catch (error) {
        health.replaceChildren(errorState(error, context));
    }
    side.append(detailSectionWithBody("来源健康", health));
    side.append(detailSectionWithBody("运行上下文", capabilityUnavailableNotice("观察记录没有返回可关联的 run ID；运行列表需要管理员权限，无法在此把其它运行归因给当前情报。", "运行关联暂不可用")), linkTo("P21", "查看运行记录（管理员）"));
    host.append(main, side);
    return host;
}
function intelligenceProcessStage(titleValue, statusValue, entries) {
    const stage = document.createElement("div");
    stage.className = "r04-intelligence-process-stage";
    const marker = document.createElement("span");
    marker.className = "r04-intelligence-process-marker";
    marker.textContent = "·";
    const content = document.createElement("div");
    content.className = "r04-intelligence-process-stage-content";
    const title = document.createElement("h3");
    title.textContent = titleValue;
    title.append(badge(statusValue, "info"));
    content.append(title, detailList(entries));
    stage.append(marker, content);
    return stage;
}
function observationTypeLabel(value) { return { NEWS: "新闻", JOB: "职位", PRODUCT: "产品", REPOSITORY: "代码仓库", TREND: "趋势" }[String(value)] ?? text(value, "未分类"); }
async function renderObservations(context) {
    return renderIntelligenceList(context);
    const host = content("Observations", "Raw evidence collected from registered sources, with provenance and acquisition metadata.");
    const filters = document.createElement("form");
    filters.className = "r02-inline-form";
    const qWrap = input("Content keyword", { placeholder: "title, text, or query" });
    const sourceWrap = input("Source id", { placeholder: "optional" });
    const typeWrap = select("Item type", ["", "NEWS", "JOB", "PRODUCT", "REPOSITORY", "TREND"], "");
    const q = qWrap.querySelector("input");
    const source = sourceWrap.querySelector("input");
    const type = typeWrap.querySelector("select");
    const submit = button("Apply filters", { variant: "primary", type: "submit" });
    appendActionRow(filters, submit);
    filters.prepend(qWrap, sourceWrap, typeWrap);
    const results = document.createElement("div");
    const load = async (offset) => {
        results.replaceChildren(statePanel("loading", "Loading observations…"));
        const params = new URLSearchParams({ limit: "50", offset: String(offset) });
        if (q?.value.trim())
            params.set("q", q.value.trim());
        if (source?.value.trim())
            params.set("source_id", source.value.trim());
        if (type?.value)
            params.set("item_type", type.value);
        try {
            const data = await api(`/api/v1/observations?${params.toString()}`);
            const rows = (data.items ?? []).map((row) => [linkTo("P07", text(row.title), { id: row.id, q: row.title, source_id: row.source_id }), text(row.source_id), text(row.item_type), badge(text(row.evidence_quality), row.evidence_quality === "A" ? "success" : "neutral"), formatDate(row.observed_at)]);
            const body = rows.length ? table(["Observation", "Source", "Type", "Quality", "Observed"], rows) : statePanel("empty", q?.value ? "No observations match the current filters." : "No observations have been collected yet.");
            results.replaceChildren(body);
            const pager = document.createElement("div");
            pager.className = "r02-pagination";
            pager.append(button("Previous", { disabled: offset <= 0, onClick: () => void load(Math.max(0, offset - 50)) }), document.createTextNode(`Offset ${offset}`), button("Next", { disabled: !data.has_more, onClick: () => void load(offset + 50) }));
            results.append(pager);
        }
        catch (error) {
            results.replaceChildren(errorState(error, context, () => void load(offset)));
        }
    };
    filters.addEventListener("submit", (event) => { event.preventDefault(); void load(0); });
    append(host, filters, results);
    await load(0);
    return host;
}
async function renderObservationDetail(route, context) {
    return renderIntelligenceSummary(route, context);
    const id = route.params.get("id");
    const host = content("Observation detail", "A source observation with its evidence text and provenance.");
    if (!id) {
        append(host, statePanel("error", "Observation id is missing."));
        return host;
    }
    try {
        const detailParams = new URLSearchParams({ limit: "500" });
        if (route.params.get("q"))
            detailParams.set("q", route.params.get("q"));
        if (route.params.get("source_id"))
            detailParams.set("source_id", route.params.get("source_id"));
        const data = await api(`/api/v1/observations?${detailParams.toString()}`);
        const row = (data.items ?? []).find((item) => String(item.id) === id);
        if (!row) {
            append(host, objectNotFound("Observation", id ?? ""));
            return host;
        }
        const details = document.createElement("dl");
        details.className = "r02-detail-grid";
        for (const [label, value] of [["Title", row.title], ["Source", row.source_id], ["Type", row.item_type], ["Query", row.query], ["Quality", row.evidence_quality], ["Acquisition", row.acquisition_method], ["Observed", formatDate(row.observed_at)]]) {
            const dt = document.createElement("dt");
            dt.textContent = label;
            const dd = document.createElement("dd");
            dd.textContent = text(value);
            details.append(dt, dd);
        }
        const evidence = card("Evidence text", document.createElement("p"));
        evidence.querySelector("p").textContent = text(row.text);
        const actions = document.createElement("div");
        appendActionRow(actions, button("Back to observations", { onClick: () => navigate("P06") }));
        append(host, card("Observation metadata", details), evidence, actions);
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderKeywords(route, context) {
    const host = document.createElement("div");
    host.className = "r04-keyword-page";
    const heading = r04PageHeading("关键词发现", "识别新出现的术语、概念与语义变化", "刷新关键词");
    host.append(readOnlyNotice("关键词统计来自真实关键词与观察接口；当前页面不直接修改关键词，关注关系请进入关注关键词。", "关键词发现只读"), heading);
    const filter = document.createElement("form");
    filter.className = "r04-keyword-filter";
    const query = document.createElement("input");
    query.type = "search";
    query.placeholder = "关键词搜索…";
    query.setAttribute("aria-label", "关键词搜索");
    const windowSelect = document.createElement("select");
    addOption(windowSelect, "0", "时间范围：全部");
    addOption(windowSelect, "30", "最近 30 天");
    addOption(windowSelect, "90", "最近 90 天");
    const sourceSelect = document.createElement("select");
    addOption(sourceSelect, "0", "来源多样性：全部");
    addOption(sourceSelect, "3", "来源数 ≥ 3");
    addOption(sourceSelect, "5", "来源数 ≥ 5");
    const scoreSelect = document.createElement("select");
    addOption(scoreSelect, "0", "最低信号强度：全部");
    addOption(scoreSelect, "50", "最低信号强度：50+");
    addOption(scoreSelect, "80", "最低信号强度：80+");
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.textContent = "筛选";
    submit.className = "r04-keyword-submit";
    filter.append(query, windowSelect, sourceSelect, scoreSelect, submit);
    const layout = document.createElement("div");
    layout.className = "r04-keyword-layout";
    const results = document.createElement("section");
    results.className = "r04-keyword-results";
    const inspector = document.createElement("aside");
    inspector.className = "r04-keyword-inspector";
    layout.append(results, inspector);
    host.append(filter, layout);
    try {
        const [keywordResult, watchResult] = await Promise.allSettled([api("/api/v1/keywords?limit=500"), api("/api/v1/watch-keywords")]);
        if (keywordResult.status === "rejected")
            throw keywordResult.reason;
        const rows = Array.isArray(keywordResult.value) ? keywordResult.value : [];
        const watchRows = watchResult.status === "fulfilled" && Array.isArray(watchResult.value) ? watchResult.value : [];
        const watched = new Set(watchRows.filter((row) => row.enabled).map((row) => String(row.canonical ?? row.keyword).toLowerCase()));
        let selectedId = route.params.get("keyword_id") ?? (rows[0] ? String(rows[0].id) : "");
        const draw = async () => {
            const filtered = rows.filter((row) => {
                const matchesQuery = !query.value.trim() || `${row.keyword ?? ""} ${row.canonical ?? ""}`.toLowerCase().includes(query.value.trim().toLowerCase());
                const matchesWindow = !Number(windowSelect.value) || keywordWithinDays(row.last_seen_at, Number(windowSelect.value));
                const matchesSource = Number(row.source_count ?? 0) >= Number(sourceSelect.value);
                const matchesScore = Number(row.score ?? 0) >= Number(scoreSelect.value);
                return matchesQuery && matchesWindow && matchesSource && matchesScore;
            });
            const pageRows = filtered.slice(0, 50);
            const tableRows = pageRows.map((row) => {
                const key = String(row.canonical ?? row.keyword ?? "").toLowerCase();
                return [linkTo("P08", text(row.keyword, "未命名关键词"), { keyword_id: row.id }), watched.has(key) ? badge("已关注", "success") : badge("未关注", "neutral"), scoreBadge(row.score), text(row.source_count, "0"), text(row.observation_count, "0"), formatDate(row.first_seen_at), formatDate(row.last_seen_at)];
            });
            const pager = document.createElement("div");
            pager.className = "r04-keyword-pager";
            pager.textContent = `显示 1-${pageRows.length} 条，共 ${filtered.length} 个真实关键词${filtered.length > 50 ? "（仅显示前 50 条）" : ""}`;
            results.replaceChildren(table(["关键词", "关注状态", "信号强度", "来源数", "证据数", "首次出现", "最近采集"], tableRows), pager);
            if (!tableRows.length)
                results.replaceChildren(statePanel("empty", query.value ? "没有匹配当前筛选条件的关键词。" : "当前没有可展示的关键词。"));
            const selected = rows.find((row) => String(row.id) === selectedId) ?? pageRows[0];
            if (selected) {
                selectedId = String(selected.id);
                inspector.replaceChildren(await renderKeywordInspector(selected, watched.has(String(selected.canonical ?? selected.keyword).toLowerCase()), context));
            }
            else
                inspector.replaceChildren(statePanel("ready", "选择真实关键词后查看趋势摘要与证据入口。"));
        };
        if (watchResult.status === "rejected")
            host.append(capabilityUnavailableNotice("关注状态读取暂时不可用，关键词统计仍来自真实接口。", "关注状态部分不可用"));
        filter.addEventListener("submit", (event) => { event.preventDefault(); void draw(); });
        await draw();
    }
    catch (error) {
        layout.replaceChildren(errorState(error, context, () => navigate("P08")));
    }
    return host;
}
async function renderKeywordInspector(row, watched, context) {
    const host = document.createElement("div");
    host.className = "r04-keyword-inspector-inner";
    const title = document.createElement("h2");
    title.textContent = text(row.keyword, "未命名关键词");
    const meta = document.createElement("p");
    meta.textContent = `关键词 ID：${text(row.id)} · 最近采集：${formatDate(row.last_seen_at)}`;
    host.append(title, watched ? badge("已关注", "success") : badge("未关注", "neutral"), meta, detailList([["信号强度", number(row.score, 1)], ["证据数", text(row.observation_count, "0")], ["来源数", text(row.source_count, "0")], ["关键词状态", keywordStatusLabel(row.status)]]));
    const trend = document.createElement("section");
    trend.className = "r04-keyword-inspector-section";
    trend.append(Object.assign(document.createElement("h3"), { textContent: "趋势摘要" }), statePanel("loading", "正在读取趋势…"));
    const evidence = document.createElement("section");
    evidence.className = "r04-keyword-inspector-section";
    evidence.append(Object.assign(document.createElement("h3"), { textContent: "关键词检索结果" }), statePanel("loading", "正在读取真实情报…"));
    const settled = await Promise.allSettled([api(`/api/v1/keywords/${encodeURIComponent(String(row.id))}/trend`), api(`/api/v1/observations?q=${encodeURIComponent(String(row.keyword ?? ""))}&limit=3`)]);
    const trendResult = settled[0];
    const evidenceResult = settled[1];
    trend.replaceChildren(document.createElement("h3"));
    trend.querySelector("h3").textContent = "趋势摘要";
    if (trendResult.status === "fulfilled") {
        trend.append(renderMiniTrend(trendResult.value.points ?? []), linkTo("P10", "查看趋势分析", { keyword_id: row.id }));
    }
    else
        trend.append(statePanel("error", "趋势暂时不可用。"));
    evidence.replaceChildren(document.createElement("h3"));
    evidence.querySelector("h3").textContent = "关键词检索结果";
    if (evidenceResult.status === "fulfilled") {
        const items = (evidenceResult.value.items ?? []);
        const list = document.createElement("div");
        list.className = "r04-keyword-evidence-list";
        for (const item of items) {
            const link = linkTo("P07", text(item.title, "未命名情报"), { id: item.id, q: row.keyword });
            const line = document.createElement("div");
            line.append(link, document.createTextNode(`${text(item.source_id)} · ${formatDate(item.observed_at)}`));
            list.append(line);
        }
        evidence.append(items.length ? list : statePanel("empty", "没有找到包含该关键词的情报记录。"), linkTo("P06", "查看全部情报", { q: row.keyword }));
    }
    else
        evidence.append(statePanel("error", "情报检索暂时不可用。"));
    const related = document.createElement("section");
    related.className = "r04-keyword-inspector-section";
    const relatedTitle = document.createElement("h3");
    relatedTitle.textContent = "相关词与关联机会";
    related.append(relatedTitle, linkTo("P11", "查看真实关系图谱", { keyword_id: row.id }), capabilityUnavailableNotice("关键词列表接口没有返回关联机会 ID，侧栏不显示固定机会对象。", "关联机会暂不可用"), linkTo("P12", "查看机会列表"));
    host.append(trend, evidence, related);
    return host;
}
async function renderWatchKeywords(route, context) {
    const host = document.createElement("div");
    host.className = "r04-watch-keyword-page";
    host.append(r04PageHeading("关注关键词", "查看已关注关键词的信号变化、证据与关联机会", ""));
    host.append(readOnlyNotice("新增、启用和停用会调用真实 watch-keywords 接口；若当前账号没有写权限，接口错误会直接显示，不会伪造成功。", "关注关系按真实接口执行"));
    const form = document.createElement("form");
    form.className = "r04-watch-add-form";
    const keyword = document.createElement("input");
    keyword.name = "keyword";
    keyword.required = true;
    keyword.minLength = 2;
    keyword.placeholder = "新增关键词（至少 2 个字符）";
    const notes = document.createElement("input");
    notes.name = "notes";
    notes.placeholder = "备注（可选）";
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "r04-keyword-submit";
    submit.textContent = "添加关注";
    form.append(keyword, notes, submit);
    const filters = document.createElement("form");
    filters.className = "r04-watch-filters";
    const search = document.createElement("input");
    search.type = "search";
    search.placeholder = "搜索已关注关键词…";
    const status = document.createElement("select");
    addOption(status, "", "状态：全部");
    addOption(status, "true", "状态：已启用");
    addOption(status, "false", "状态：已停用");
    filters.append(search, status);
    const layout = document.createElement("div");
    layout.className = "r04-watch-layout";
    const results = document.createElement("section");
    results.className = "r04-watch-results";
    const inspector = document.createElement("aside");
    inspector.className = "r04-watch-inspector";
    layout.append(results, inspector);
    host.append(form, filters, layout);
    let rows = [];
    let keywordStats = [];
    const draw = async () => {
        const filtered = rows.filter((row) => (!search.value.trim() || String(row.keyword).toLowerCase().includes(search.value.trim().toLowerCase())) && (!status.value || String(Boolean(row.enabled)) === status.value));
        const tableRows = filtered.map((row) => {
            const stats = keywordStats.find((item) => String(item.canonical ?? item.keyword).toLowerCase() === String(row.canonical ?? row.keyword).toLowerCase());
            const toggle = button(row.enabled ? "停用" : "启用", { onClick: async () => { toggle.disabled = true; try {
                    await api(`/api/v1/watch-keywords/${row.id}`, { method: "PATCH", body: JSON.stringify({ enabled: !row.enabled }) });
                    await load();
                }
                catch (error) {
                    results.replaceChildren(errorState(error, context));
                }
                finally {
                    toggle.disabled = false;
                } } });
            return [linkTo("P09", text(row.keyword, "未命名关键词"), { keyword_id: row.id }), row.enabled ? badge("已启用", "success") : badge("已停用", "neutral"), scoreBadge(stats?.score), text(stats?.observation_count, "未知"), text(row.priority, "未设置"), text(row.notes, ""), toggle];
        });
        const pager = document.createElement("div");
        pager.className = "r04-keyword-pager";
        pager.textContent = `共 ${filtered.length} 条关注记录`;
        results.replaceChildren(table(["关键词", "关注状态", "信号强度", "证据数", "优先级", "备注", "操作"], tableRows), pager);
        if (!tableRows.length)
            results.replaceChildren(statePanel("empty", "当前没有匹配的关注关键词。"));
        const selected = rows.find((row) => String(row.id) === route.params.get("keyword_id")) ?? filtered[0];
        inspector.replaceChildren(selected ? await renderWatchKeywordInspector(selected, keywordStats, context) : statePanel("ready", "选择真实关注关键词后查看趋势与证据。"));
    };
    const load = async () => { results.replaceChildren(statePanel("loading", "正在读取关注关键词…")); try {
        const settled = await Promise.allSettled([api("/api/v1/watch-keywords"), api("/api/v1/keywords?limit=500")]);
        if (settled[0].status === "rejected")
            throw settled[0].reason;
        rows = Array.isArray(settled[0].value) ? settled[0].value : [];
        keywordStats = settled[1].status === "fulfilled" && Array.isArray(settled[1].value) ? settled[1].value : [];
        await draw();
    }
    catch (error) {
        results.replaceChildren(errorState(error, context, () => void load()));
        inspector.replaceChildren();
    } };
    form.addEventListener("submit", async (event) => { event.preventDefault(); submit.disabled = true; try {
        await api("/api/v1/watch-keywords", { method: "POST", body: JSON.stringify({ keyword: keyword.value.trim(), notes: notes.value.trim(), priority: 3 }) });
        form.reset();
        await load();
    }
    catch (error) {
        results.replaceChildren(errorState(error, context));
    }
    finally {
        submit.disabled = false;
    } });
    filters.addEventListener("input", () => void draw());
    filters.addEventListener("change", () => void draw());
    await load();
    return host;
}
async function renderWatchKeywordInspector(row, keywordStats, context) {
    const host = document.createElement("div");
    host.className = "r04-watch-inspector-inner";
    const stats = keywordStats.find((item) => String(item.canonical ?? item.keyword).toLowerCase() === String(row.canonical ?? row.keyword).toLowerCase());
    const title = document.createElement("h2");
    title.textContent = text(row.keyword, "未命名关键词");
    const meta = document.createElement("p");
    meta.textContent = `关注记录 ID：${text(row.id)} · 更新：${formatDate(row.updated_at)}`;
    host.append(title, row.enabled ? badge("已启用", "success") : badge("已停用", "neutral"), meta, detailList([["优先级", row.priority], ["备注", row.notes], ["信号强度", stats?.score], ["证据数", stats?.observation_count], ["来源数", stats?.source_count]]));
    const trend = document.createElement("section");
    trend.className = "r04-watch-inspector-section";
    const trendTitle = document.createElement("h3");
    trendTitle.textContent = "7 天信号趋势";
    trend.append(trendTitle, statePanel("loading", "正在读取趋势…"));
    const evidence = document.createElement("section");
    evidence.className = "r04-watch-inspector-section";
    const evidenceTitle = document.createElement("h3");
    evidenceTitle.textContent = "关键词证据";
    evidence.append(evidenceTitle, statePanel("loading", "正在读取情报…"));
    const settled = await Promise.allSettled([stats ? api(`/api/v1/keywords/${encodeURIComponent(String(stats.id))}/trend`) : Promise.reject(new Error("keyword statistics unavailable")), api(`/api/v1/observations?q=${encodeURIComponent(String(row.keyword ?? ""))}&limit=3`)]);
    trend.replaceChildren(trendTitle);
    if (settled[0].status === "fulfilled")
        trend.append(renderMiniTrend(settled[0].value.points ?? []), stats ? linkTo("P10", "查看趋势分析", { keyword_id: stats.id }) : statePanel("partial", "该关注词尚未匹配到关键词统计记录。"));
    else
        trend.append(statePanel("partial", "当前关注记录没有可展示的趋势数据。"));
    evidence.replaceChildren(evidenceTitle);
    if (settled[1].status === "fulfilled") {
        const items = (settled[1].value.items ?? []);
        evidence.append(items.length ? table(["情报", "来源", "采集时间"], items.map((item) => [linkTo("P07", text(item.title, "未命名情报"), { id: item.id, q: row.keyword }), text(item.source_id), formatDate(item.observed_at)])) : statePanel("empty", "没有找到关键词检索结果。"), linkTo("P06", "查看全部情报", { q: row.keyword }));
    }
    else
        evidence.append(statePanel("error", "情报检索暂时不可用。"));
    host.append(trend, evidence, stats ? linkTo("P11", "查看真实关系图谱", { keyword_id: stats.id }) : linkTo("P08", "回到关键词发现"), capabilityUnavailableNotice("当前后端没有按关注关键词返回固定关联机会或运行队列对象，因此不展示 HTML 中的示例 ID。", "关联机会与运行状态暂不可用"));
    return host;
}
async function renderTrend(route, context) {
    const host = document.createElement("div");
    host.className = "r04-trend-page";
    host.append(r04PageHeading("趋势分析", "分析关键词的时间变化与关键拐点", ""));
    try {
        const keywords = await api("/api/v1/keywords?limit=500");
        const rows = Array.isArray(keywords) ? keywords : [];
        if (!rows.length) {
            host.append(statePanel("empty", "当前没有可分析的关键词。"));
            return host;
        }
        const selectedId = route.params.get("keyword_id") ?? String(rows[0].id);
        const selected = rows.find((row) => String(row.id) === selectedId) ?? rows[0];
        const controls = document.createElement("form");
        controls.className = "r04-trend-controls";
        const target = document.createElement("select");
        rows.forEach((row) => addOption(target, String(row.id), text(row.keyword, `关键词 ${row.id}`)));
        target.value = String(selected.id);
        const range = document.createElement("select");
        addOption(range, "90", "时间范围：近 90 天");
        addOption(range, "30", "时间范围：近 30 天");
        addOption(range, "7", "时间范围：近 7 天");
        range.value = route.params.get("since_days") ?? "90";
        const apply = document.createElement("button");
        apply.type = "submit";
        apply.className = "r04-keyword-submit";
        apply.textContent = "更新分析";
        controls.append(document.createTextNode("分析对象"), target, document.createTextNode("时间范围"), range, apply);
        controls.addEventListener("submit", (event) => { event.preventDefault(); navigate("P10", { keyword_id: target.value, since_days: range.value }); });
        host.append(controls);
        const data = await api(`/api/v1/keywords/${encodeURIComponent(String(selected.id))}/trend`);
        const allPoints = (data.points ?? []);
        const sinceDays = Number(range.value);
        const points = allPoints.filter((row) => keywordWithinDays(row.day, sinceDays));
        const layout = document.createElement("div");
        layout.className = "r04-trend-layout";
        const main = document.createElement("main");
        main.className = "r04-trend-main";
        const side = document.createElement("aside");
        side.className = "r04-trend-side";
        main.append(detailSectionWithBody("信号强度趋势", renderTrendChart(points)), detailSectionWithBody("关键时间点", renderTrendPointsTable(points)), capabilityUnavailableNotice("趋势接口只返回按日观察数和来源数，没有返回事件类型、影响等级或人工研判，因此不从 mock 补齐“关键拐点”语义。", "事件研判字段暂不可用"));
        const selectedWindow = sinceDays === 7 ? "7d" : sinceDays === 30 ? "30d" : "90d";
        const sourcePeak = points.reduce((max, row) => Math.max(max, Number(row.sources ?? 0)), 0);
        side.append(detailSectionWithBody("趋势研判概览", detailList([["关键词", data.keyword], ["当前窗口", `近 ${sinceDays} 天`], ["窗口增长", formatGrowth(data.growth?.[selectedWindow === "7d" ? "7d" : "30d"])], ["窗口观察数", data.windows?.[selectedWindow]], ["单日最高来源数", sourcePeak]])));
        const evidence = document.createElement("div");
        evidence.append(statePanel("loading", "正在读取核心情报…"));
        side.append(detailSectionWithBody("核心证据", evidence));
        const opportunities = capabilityUnavailableNotice("趋势接口没有返回关联机会 ID，不能展示固定机会卡片。", "关联机会暂不可用");
        side.append(opportunities, linkTo("P12", "查看机会列表"), linkTo("P11", "打开真实关系图谱", { keyword_id: selected.id, since_days: range.value }));
        layout.append(main, side);
        host.append(layout);
        try {
            const evidenceData = await api(`/api/v1/observations?q=${encodeURIComponent(String(data.keyword ?? selected.keyword ?? ""))}&limit=3`);
            const items = (evidenceData.items ?? []);
            evidence.replaceChildren(items.length ? table(["情报", "来源", "采集时间"], items.map((row) => [linkTo("P07", text(row.title, "未命名情报"), { id: row.id, q: data.keyword }), text(row.source_id), formatDate(row.observed_at)])) : statePanel("empty", "没有找到与该关键词匹配的情报。"), linkTo("P06", "查看全部情报", { q: data.keyword }));
        }
        catch (error) {
            evidence.replaceChildren(errorState(error, context));
        }
    }
    catch (error) {
        host.append(errorState(error, context, () => navigate("P10")));
    }
    return host;
}
function formatGrowth(value) { const n = Number(value); return Number.isFinite(n) ? `${n >= 0 ? "+" : ""}${(n * 100).toFixed(1)}%` : "未提供"; }
function renderTrendChart(points) {
    if (!points.length)
        return statePanel("empty", "当前没有按日趋势点。");
    const wrapper = document.createElement("div");
    wrapper.className = "r04-trend-chart-wrap";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("r04-trend-chart");
    svg.setAttribute("viewBox", "0 0 760 280");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "真实关键词按日观察数趋势");
    const max = Math.max(1, ...points.map((row) => Number(row.observations ?? 0)));
    const left = 42;
    const right = 740;
    const top = 24;
    const bottom = 235;
    const width = Math.max(1, points.length - 1);
    for (let i = 0; i < 5; i++) {
        const y = top + ((bottom - top) * i) / 4;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", String(left));
        line.setAttribute("x2", String(right));
        line.setAttribute("y1", String(y));
        line.setAttribute("y2", String(y));
        line.setAttribute("class", "r04-trend-grid-line");
        svg.append(line);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", "4");
        label.setAttribute("y", String(y + 4));
        label.textContent = String(Math.round(max * (4 - i) / 4));
        label.classList.add("r04-trend-axis-label");
        svg.append(label);
    }
    const pointsPath = points.map((row, index) => { const x = left + ((right - left) * index) / width; const y = bottom - ((bottom - top) * Number(row.observations ?? 0)) / max; return `${index ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`; }).join(" ");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pointsPath);
    path.classList.add("r04-trend-line");
    svg.append(path);
    for (const index of [0, Math.floor(points.length / 2), points.length - 1]) {
        const row = points[index];
        if (!row)
            continue;
        const x = left + ((right - left) * index) / width;
        const y = bottom - ((bottom - top) * Number(row.observations ?? 0)) / max;
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", String(x));
        circle.setAttribute("cy", String(y));
        circle.setAttribute("r", "4");
        circle.classList.add("r04-trend-point");
        svg.append(circle);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(x));
        label.setAttribute("y", "262");
        label.setAttribute("text-anchor", index === 0 ? "start" : index === points.length - 1 ? "end" : "middle");
        label.textContent = text(row.day);
        label.classList.add("r04-trend-axis-label");
        svg.append(label);
    }
    wrapper.append(svg);
    return wrapper;
}
function renderTrendPointsTable(points) {
    if (!points.length)
        return statePanel("empty", "当前没有按日趋势点。");
    const recent = points.slice(-12);
    return table(["日期", "观察数", "来源数", "较前一日变化"], recent.map((row, index) => { const previous = index > 0 ? recent[index - 1] : undefined; const delta = previous ? Number(row.observations ?? 0) - Number(previous.observations ?? 0) : undefined; return [text(row.day), text(row.observations, "0"), text(row.sources, "0"), delta === undefined ? "—" : `${delta >= 0 ? "+" : ""}${delta}`]; }));
}
async function renderGraph(route, context) {
    const host = document.createElement("div");
    host.className = "r04-graph-page";
    host.append(r04PageHeading("关系图谱", "探索关键词之间的真实证据关系", ""), readOnlyNotice("图谱节点和边来自 keyword-graph 接口；当前只展示关键词关系，不虚构实体、来源或关联机会边。", "关系图谱只读"));
    try {
        const keywords = await api("/api/v1/keywords?limit=500");
        const rows = Array.isArray(keywords) ? keywords : [];
        if (!rows.length) {
            host.append(statePanel("empty", "当前没有可用于构建图谱的关键词。"));
            return host;
        }
        const selectedId = route.params.get("keyword_id") ?? String(rows[0].id);
        const selected = rows.find((row) => String(row.id) === selectedId) ?? rows[0];
        const controls = document.createElement("form");
        controls.className = "r04-graph-controls";
        const target = document.createElement("select");
        rows.forEach((row) => addOption(target, String(row.id), text(row.keyword, `关键词 ${row.id}`)));
        target.value = String(selected.id);
        const sinceDays = document.createElement("select");
        addOption(sinceDays, "30", "时间范围：过去 30 天");
        addOption(sinceDays, "90", "时间范围：过去 90 天");
        addOption(sinceDays, "365", "时间范围：过去 1 年");
        sinceDays.value = route.params.get("since_days") ?? "90";
        const apply = document.createElement("button");
        apply.type = "submit";
        apply.className = "r04-keyword-submit";
        apply.textContent = "更新图谱";
        controls.append(document.createTextNode("中心节点"), target, document.createTextNode("时间范围"), sinceDays, apply);
        controls.addEventListener("submit", (event) => { event.preventDefault(); navigate("P11", { keyword_id: target.value, since_days: sinceDays.value }); });
        host.append(controls);
        const data = await api(`/api/v1/keyword-graph?keyword_id=${encodeURIComponent(String(selected.id))}&limit=200&since_days=${encodeURIComponent(sinceDays.value)}`);
        const nodes = (data.nodes ?? []);
        if (!nodes.some((row) => String(row.id) === String(selected.id)))
            nodes.unshift({ id: selected.id, keyword: selected.keyword });
        const edges = (data.edges ?? []);
        const layout = document.createElement("div");
        layout.className = "r04-graph-layout";
        const canvas = document.createElement("section");
        canvas.className = "r04-graph-canvas";
        canvas.append(renderKeywordGraphSvg(nodes, edges, String(selected.id)), detailSectionWithBody("图谱说明", capabilityUnavailableNotice("当前接口没有探索深度或最低关联强度参数；页面仅使用真实 keyword_id、limit 和 since_days 查询。", "部分图谱筛选暂不可用")));
        const side = document.createElement("aside");
        side.className = "r04-graph-inspector";
        const relatedEdges = edges.filter((edge) => String(edge.source) === String(selected.id) || String(edge.target) === String(selected.id));
        const relatedRows = relatedEdges.map((edge) => { const otherId = String(edge.source) === String(selected.id) ? edge.target : edge.source; const other = nodes.find((row) => String(row.id) === String(otherId)); return [text(other?.keyword, `关键词 ${otherId}`), text(edge.type, "未提供"), number(edge.weight, 1), text(edge.cooccurrences, "0"), text(edge.sources, "0"), formatDate(edge.last_seen_at)]; });
        side.append(detailSectionWithBody("核心关联关键词", relatedRows.length ? table(["关键词", "关系类型", "权重", "共现", "来源数", "最近出现"], relatedRows) : statePanel("empty", "当前时间范围没有真实关系边。")), linkTo("P10", "查看该关键词趋势", { keyword_id: selected.id, since_days: sinceDays.value }), linkTo("P08", "回到关键词发现", { keyword_id: selected.id }));
        const evidence = document.createElement("div");
        evidence.append(statePanel("loading", "正在读取关键词证据…"));
        side.append(detailSectionWithBody("关键词证据摘录", evidence));
        side.append(capabilityUnavailableNotice("keyword-graph 接口没有返回机会关联或实体/来源节点，相关对象入口不在此伪造。", "机会与实体关系暂不可用"), linkTo("P12", "查看机会列表"));
        layout.append(canvas, side);
        host.append(layout);
        try {
            const evidenceData = await api(`/api/v1/observations?q=${encodeURIComponent(String(selected.keyword ?? ""))}&limit=2`);
            const items = (evidenceData.items ?? []);
            evidence.replaceChildren(items.length ? table(["情报", "来源", "采集时间"], items.map((row) => [linkTo("P07", text(row.title, "未命名情报"), { id: row.id, q: selected.keyword }), text(row.source_id), formatDate(row.observed_at)])) : statePanel("empty", "没有找到该关键词的真实情报记录。"), linkTo("P06", "查看全部情报", { q: selected.keyword }));
        }
        catch (error) {
            evidence.replaceChildren(errorState(error, context));
        }
    }
    catch (error) {
        host.append(errorState(error, context, () => navigate("P11")));
    }
    return host;
}
function renderKeywordGraphSvg(nodes, edges, centerId) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("r04-graph-svg");
    svg.setAttribute("viewBox", "0 0 800 560");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "真实关键词关系图谱");
    const center = { x: 400, y: 280 };
    const others = nodes.filter((row) => String(row.id) !== centerId);
    const positions = new Map();
    positions.set(centerId, center);
    others.forEach((row, index) => { const angle = -Math.PI / 2 + (Math.PI * 2 * index) / Math.max(1, others.length); positions.set(String(row.id), { x: 400 + Math.cos(angle) * 205, y: 280 + Math.sin(angle) * 185 }); });
    for (const edge of edges) {
        const source = positions.get(String(edge.source));
        const target = positions.get(String(edge.target));
        if (!source || !target)
            continue;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", String(source.x));
        line.setAttribute("y1", String(source.y));
        line.setAttribute("x2", String(target.x));
        line.setAttribute("y2", String(target.y));
        line.classList.add("r04-graph-edge");
        svg.append(line);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String((source.x + target.x) / 2));
        label.setAttribute("y", String((source.y + target.y) / 2 - 6));
        label.textContent = `${text(edge.type, "关系")} · ${number(edge.weight, 1)}`;
        label.classList.add("r04-graph-edge-label");
        svg.append(label);
    }
    for (const node of nodes) {
        const position = positions.get(String(node.id));
        if (!position)
            continue;
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", String(position.x));
        circle.setAttribute("cy", String(position.y));
        circle.setAttribute("r", String(String(node.id) === centerId ? 30 : 22));
        circle.classList.add(String(node.id) === centerId ? "r04-graph-center" : "r04-graph-node");
        svg.append(circle);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(position.x));
        label.setAttribute("y", String(position.y + (String(node.id) === centerId ? 52 : 40)));
        label.setAttribute("text-anchor", "middle");
        label.textContent = text(node.keyword, `关键词 ${node.id}`);
        label.classList.add("r04-graph-node-label");
        svg.append(label);
    }
    return svg;
}
function keywordStatusLabel(value) { return { TRENDING: "趋势中", ACTIVE: "活跃", DORMANT: "休眠", NEW: "新发现" }[String(value)] ?? text(value, "未提供"); }
function keywordWithinDays(value, days) { const timestamp = Date.parse(String(value ?? "")); return !days || !Number.isFinite(timestamp) || (Date.now() - timestamp) <= days * 86_400_000; }
function renderMiniTrend(points) { if (!points.length)
    return statePanel("empty", "没有可展示的趋势点。"); const host = document.createElement("div"); host.className = "r04-mini-trend"; const max = Math.max(1, ...points.slice(-7).map((row) => Number(row.observations ?? 0))); for (const row of points.slice(-7)) {
    const bar = document.createElement("span");
    bar.title = `${text(row.day)} · ${text(row.observations, "0")} 条观察`;
    bar.style.height = `${Math.max(8, (Number(row.observations ?? 0) / max) * 100)}%`;
    host.append(bar);
} return host; }
function r04PageHeading(titleValue, subtitleValue, actionLabel) { const heading = document.createElement("div"); heading.className = "r04-page-heading"; const copy = document.createElement("div"); const title = document.createElement("h1"); title.textContent = titleValue; const subtitle = document.createElement("p"); subtitle.textContent = subtitleValue; copy.append(title, subtitle); heading.append(copy); if (actionLabel) {
    const action = document.createElement("button");
    action.type = "button";
    action.className = "r04-page-action";
    action.textContent = `↻ ${actionLabel}`;
    action.addEventListener("click", () => window.location.reload());
    heading.append(action);
} return heading; }
async function renderOpportunities(context) {
    const host = document.createElement("div");
    host.className = "r04-opportunity-list";
    const heading = document.createElement("div");
    heading.className = "r04-opportunity-heading";
    const title = document.createElement("h1");
    title.textContent = "机会";
    const subtitle = document.createElement("p");
    subtitle.textContent = "按价值、证据与时效性查看系统识别出的机会";
    heading.append(title, subtitle);
    host.append(heading);
    const filters = document.createElement("form");
    filters.className = "r04-opportunity-filters";
    const query = document.createElement("input");
    query.type = "search";
    query.name = "q";
    query.placeholder = "搜索机会";
    query.setAttribute("aria-label", "搜索机会");
    const stage = document.createElement("select");
    stage.setAttribute("aria-label", "机会阶段");
    addOption(stage, "", "阶段：所有");
    addOption(stage, "DISCOVERY", "发现");
    addOption(stage, "EARLY_GROWTH", "早期增长");
    addOption(stage, "PRODUCTIZING", "产品化");
    addOption(stage, "COMMERCIALIZING", "商业化");
    addOption(stage, "DORMANT", "休眠");
    const minScore = document.createElement("select");
    minScore.setAttribute("aria-label", "最低评分");
    addOption(minScore, "0", "评分：所有");
    addOption(minScore, "70", "70 分以上");
    addOption(minScore, "90", "90 分以上");
    const research = document.createElement("select");
    research.setAttribute("aria-label", "研究状态");
    addOption(research, "", "研究：所有");
    addOption(research, "NEW", "未处理");
    addOption(research, "TRIAGED", "已分诊");
    addOption(research, "TRACKING", "跟踪中");
    addOption(research, "DONE", "已完成");
    addOption(research, "DISMISSED", "已忽略");
    const starred = document.createElement("label");
    starred.className = "r04-opportunity-checkbox";
    const starredInput = document.createElement("input");
    starredInput.type = "checkbox";
    starredInput.name = "starred";
    starred.append(starredInput, document.createTextNode("仅重点"));
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "r04-opportunity-submit";
    submit.textContent = "筛选";
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "r04-opportunity-clear";
    clear.textContent = "清除";
    filters.append(query, stage, minScore, research, starred, submit, clear);
    const scopeNotice = readOnlyNotice("阶段写入接口未向用户安全暴露；列表中的阶段和研究状态均来自真实后端，只读展示。", "机会列表读取与权限说明");
    const results = document.createElement("div");
    results.className = "r04-opportunity-results";
    let cursorStack = [];
    const load = async (cursor) => {
        results.replaceChildren(statePanel("loading", "正在读取机会…"));
        const params = new URLSearchParams({ limit: "50", include_dormant: stage.value === "DORMANT" ? "true" : "false" });
        if (cursor)
            params.set("cursor", cursor);
        if (query.value.trim())
            params.set("q", query.value.trim());
        if (stage.value && stage.value !== "DORMANT")
            params.set("stage", stage.value);
        if (minScore.value !== "0")
            params.set("min_score", minScore.value);
        if (research.value)
            params.set("research_status", research.value);
        if (starredInput.checked)
            params.set("starred", "true");
        try {
            const data = await api(`/api/v1/opportunities/page?${params.toString()}`);
            const rows = (data.items ?? []).map((row) => [linkTo("P13", text(row.title), { id: row.id }), text(row.opportunity_key ?? row.id), scoreBadge(row.score), number(row.risk_score, 1), stageLabel(row.stage), text(row.evidence_count, "0"), badge(researchLabel(row.research?.status), row.research?.status === "TRACKING" || row.research?.status === "DONE" ? "success" : "neutral"), formatDate(row.last_seen_at)]);
            results.replaceChildren(rows.length ? table(["机会", "ID", "评分", "风险", "阶段", "证据数", "研究状态", "更新时间"], rows) : statePanel("empty", query.value ? "没有匹配当前筛选条件的机会。" : "当前没有可显示的机会。"));
            const pager = document.createElement("div");
            pager.className = "r04-opportunity-pager";
            const previous = document.createElement("button");
            previous.type = "button";
            previous.textContent = "上一页";
            previous.disabled = !cursorStack.length;
            previous.addEventListener("click", () => { const previousCursor = cursorStack.pop(); void load(previousCursor); });
            const pageText = document.createElement("span");
            pageText.textContent = `${rows.length} 条记录${data.has_more ? " · 还有更多" : ""}`;
            const next = document.createElement("button");
            next.type = "button";
            next.textContent = "下一页";
            next.disabled = !data.next_cursor;
            next.addEventListener("click", () => { if (data.next_cursor) {
                cursorStack.push(cursor ?? "");
                void load(data.next_cursor);
            } });
            pager.append(previous, pageText, next);
            results.append(pager);
        }
        catch (error) {
            results.replaceChildren(errorState(error, context, () => void load(cursor)));
        }
    };
    filters.addEventListener("submit", (event) => { event.preventDefault(); cursorStack = []; void load(); });
    clear.addEventListener("click", () => { filters.reset(); cursorStack = []; void load(); });
    host.append(filters, scopeNotice, results);
    await load();
    return host;
}
async function renderOpportunityOverview(route, context, id) {
    const host = document.createElement("div");
    host.className = "r04-opportunity-detail";
    try {
        const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}`);
        const activeTab = route.params.get("tab") ?? "overview";
        const header = opportunityEntityHeader(data, id);
        const tabs = opportunityTabs(id, activeTab);
        if (activeTab !== "overview") {
            host.append(readOnlyNotice("当前后端未开放安全的机会阶段状态变更接口，本页状态仅供查看。", "机会状态只读"), header, tabs, renderOpportunityTabContent(data, id, activeTab, context));
            return host;
        }
        const grid = document.createElement("div");
        grid.className = "r04-detail-grid-r04";
        const main = document.createElement("main");
        main.className = "r04-detail-main";
        const summary = document.createElement("p");
        summary.className = "r04-detail-summary-copy";
        summary.textContent = text(data.analysis?.summary, "当前后端尚未返回可展示的机会摘要。");
        main.append(detailSectionWithBody("机会摘要", summary));
        const scoreRows = Object.entries(data.scores ?? {}).map(([key, value]) => [scoreLabel(key), number(value, 1)]);
        main.append(detailSectionWithBody("评分构成", scoreRows.length ? table(["维度", "分值"], scoreRows) : statePanel("empty", "暂无评分构成数据。")));
        const keywordRows = (data.keywords ?? []).map((row) => [linkTo("P10", text(row.keyword), { keyword_id: row.id }), text(row.role), number(row.weight, 1)]);
        main.append(detailSectionWithBody("关联关键词", keywordRows.length ? table(["关键词", "角色", "权重"], keywordRows) : statePanel("empty", "暂无关联关键词。")));
        const side = document.createElement("aside");
        side.className = "r04-detail-side";
        side.append(detailSectionWithBody("关键来源", sourceList(data.evidence ?? [])));
        side.append(detailSectionWithBody("已有研究", detailList([["状态", researchLabel(data.research?.status)], ["优先级", data.research?.priority], ["更新时间", formatDate(data.research?.updated_at)]])));
        side.append(capabilityUnavailableNotice("后端未暴露机会生命周期历史接口；这里只读展示首次发现和最近更新时间，不拼装虚假的变更时间线。", "历史记录暂不可用"));
        grid.append(main, side);
        host.append(readOnlyNotice("当前后端未开放安全的机会阶段状态变更接口，本页状态仅供查看。", "机会状态只读"), header, tabs, grid);
    }
    catch (error) {
        host.append(error instanceof ApiError && error.status === 404 ? objectNotFound("机会", id) : errorState(error, context));
    }
    return host;
}
function opportunityEntityHeader(data, id) {
    const header = document.createElement("header");
    header.className = "r04-entity-header";
    const crumb = document.createElement("div");
    crumb.className = "r04-entity-crumb";
    crumb.append(linkTo("P12", "机会"), document.createTextNode(" / "), document.createTextNode(text(data.opportunity_key ?? id)));
    const title = document.createElement("h1");
    title.textContent = text(data.title, "未命名机会");
    const chips = document.createElement("div");
    chips.className = "r04-entity-chips";
    chips.append(scoreBadge(data.score), badge(`阶段：${stageLabel(data.stage)}`, "info"), badge(`风险：${number(data.risk_score, 1)}`, "neutral"), badge(`研究：${researchLabel(data.research?.status)}`, "neutral"));
    const dates = document.createElement("p");
    dates.className = "r04-entity-dates";
    dates.textContent = `首次发现：${formatDate(data.first_seen_at)} · 最近更新：${formatDate(data.last_seen_at)}`;
    header.append(crumb, title, chips, dates);
    return header;
}
function opportunityTabs(id, activeTab) {
    const tabs = document.createElement("nav");
    tabs.className = "r04-entity-tabs";
    tabs.setAttribute("aria-label", "机会详情导航");
    for (const [tab, label] of [["overview", "概览"], ["evidence", "证据"], ["analysis", "分析与研究"], ["history", "历史"]]) {
        const link = linkTo("P13", label, { id, tab });
        link.className = activeTab === tab ? "is-active" : "";
        link.setAttribute("aria-current", activeTab === tab ? "page" : "false");
        tabs.append(link);
    }
    return tabs;
}
function renderOpportunityTabContent(data, id, tab, context) {
    const host = document.createElement("div");
    host.className = "r04-opportunity-tab-content";
    if (tab === "evidence") {
        const note = readOnlyNotice("证据仅用于支持或反对机会判断，不代表机会状态的直接变更。", "证据可追溯性");
        const search = document.createElement("input");
        search.type = "search";
        search.placeholder = "搜索证据内容";
        search.setAttribute("aria-label", "搜索证据内容");
        const quality = document.createElement("select");
        quality.setAttribute("aria-label", "证据质量");
        addOption(quality, "", "质量：全部");
        addOption(quality, "A", "高");
        addOption(quality, "B", "中");
        addOption(quality, "C", "低");
        const filter = document.createElement("div");
        filter.className = "r04-evidence-filter";
        filter.append(quality, search);
        const results = document.createElement("div");
        results.className = "r04-evidence-results";
        const draw = () => { const q = search.value.trim().toLowerCase(); const selected = quality.value; const rows = (data.evidence ?? []).filter((row) => (!selected || String(row.quality) === selected) && (!q || `${row.title ?? ""} ${row.text ?? ""} ${row.source ?? ""}`.toLowerCase().includes(q))).map((row) => [text(row.evidence_id ?? row.id), text(row.title), text(row.source), formatDate(row.observed_at), badge(qualityLabel(row.quality), row.quality === "A" ? "success" : row.quality === "B" ? "info" : "neutral"), weightLabel(row.weight), row.url ? externalLink(text(row.url)) : "—"]); results.replaceChildren(rows.length ? table(["证据编号", "证据摘要", "来源", "捕获时间", "质量", "支持/反对", "原始来源"], rows) : statePanel("empty", "没有匹配的证据记录。")); };
        search.addEventListener("input", draw);
        quality.addEventListener("change", draw);
        draw();
        host.append(note, filter, results);
        return host;
    }
    if (tab === "analysis") {
        host.append(detailSectionWithBody("结构化分析摘要", detailList([["状态", analysisLabel(data.analysis?.status)], ["提供方", text(data.analysis?.provider, "未指定")], ["分析时间", formatDate(data.analysis?.analyzed_at)], ["摘要", data.analysis?.summary], ["目标用户", data.analysis?.target_user], ["商业模式", data.analysis?.business_model], ["变现方式", data.analysis?.monetization], ["风险说明", data.analysis?.risk_notes]])));
        const citations = (data.analysis?.citations ?? []).map((row) => [linkTo("P13", text(row.evidence_id), { id, tab: "evidence", evidence_id: row.evidence_id }), text(row.source), text(row.title), qualityLabel(row.quality)]);
        host.append(detailSectionWithBody("分析引用", citations.length ? table(["证据编号", "来源", "标题", "质量"], citations) : statePanel("empty", "当前分析没有返回已绑定的证据引用。")));
        host.append(detailSectionWithBody("研究状态", detailList([["状态", researchLabel(data.research?.status)], ["重点机会", data.research?.starred ? "是" : "否"], ["优先级", data.research?.priority], ["更新时间", formatDate(data.research?.updated_at)]])));
        host.append(capabilityUnavailableNotice("后端未暴露研究任务、研究结果和生成/重生成接口；本页只展示已有分析与研究状态，不提供伪造操作。", "研究工作流只读"), linkTo("P15", "查看研究任务列表"));
        return host;
    }
    if (tab === "history") {
        const loading = statePanel("loading", "正在读取评分历史…");
        host.append(loading);
        void loadOpportunityHistory(host, id, context);
        return host;
    }
    host.append(statePanel("error", "未知的机会详情 Tab。", () => navigate("P13", { id, tab: "overview" })));
    return host;
}
async function loadOpportunityHistory(host, id, context) {
    try {
        const rows = await api(`/api/v1/scoring/opportunities/${encodeURIComponent(id)}/history?limit=200`);
        host.replaceChildren();
        const records = Array.isArray(rows) ? rows : [];
        if (!records.length) {
            host.append(statePanel("empty", "后端暂无已持久化的评分历史。"), capabilityUnavailableNotice("机会生命周期事件历史未向 UI 暴露；这里只展示可验证的评分快照。", "历史范围说明"));
            return;
        }
        const tableRows = records.map((row) => [formatDate(row.calculated_at), number(row.score, 1), number(row.risk_score, 1), stageLabel(row.stage), text(row.evidence_count, "0"), text(row.model_version)]);
        host.append(detailSectionWithBody("评分历史", table(["计算时间", "评分", "风险", "阶段", "证据数", "模型版本"], tableRows)), capabilityUnavailableNotice("后端未暴露完整机会生命周期事件历史；评分快照不等同于状态变更时间线。", "历史范围说明"));
    }
    catch (error) {
        host.replaceChildren(errorState(error, context, () => void loadOpportunityHistory(host, id, context)));
    }
}
function qualityLabel(value) { return { A: "高", B: "中", C: "低" }[String(value)] ?? text(value, "未标注"); }
function weightLabel(value) { const weight = Number(value); return Number.isFinite(weight) && weight < 0 ? "反对" : "支持"; }
function analysisLabel(value) { return { READY: "已完成", PENDING: "待处理", DEGRADED: "部分可用", FAILED: "失败" }[String(value)] ?? text(value, "未分析"); }
async function renderOpportunityDetail(route, context, mode) {
    const id = route.params.get("id");
    if (!id) {
        const missing = document.createElement("div");
        missing.className = "r04-opportunity-detail";
        missing.append(statePanel("error", "机会 ID 缺失。"));
        return missing;
    }
    if (mode === "detail")
        return renderOpportunityOverview(route, context, id);
    const title = mode === "analysis" ? "Structured analysis" : mode === "research" ? "Research workflow" : mode === "result" ? "Research result" : "Opportunity detail";
    const host = content(title, "Live opportunity detail, score breakdown, evidence citations, and research state.");
    if (!id) {
        append(host, statePanel("error", "Opportunity id is missing."));
        return host;
    }
    try {
        const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}`);
        const summary = document.createElement("div");
        summary.className = "r02-detail-summary";
        append(summary, card("Opportunity", detailList([["Title", data.title], ["Stage", data.stage], ["Score", number(data.score, 1)], ["Risk", number(data.risk_score, 1)], ["Analysis", data.analysis?.status], ["Research", data.research?.status]])), card("Scores", detailList(Object.entries(data.scores ?? {}).map(([key, value]) => [key, number(value, 1)]))));
        const actions = document.createElement("div");
        if (mode === "research" || mode === "result")
            appendActionRow(actions, button("Open analysis", { onClick: () => navigate("P14", { id }) }), button("Open research", { onClick: () => navigate("P16", { id }) }), button("Open research result", { onClick: () => navigate("P17", { id }) }));
        if (mode !== "analysis")
            appendActionRow(actions, button("Back to opportunities", { onClick: () => navigate("P12") }));
        const researchForm = document.createElement("form");
        researchForm.className = "r02-inline-form";
        const statusWrap = select("Research status", ["NEW", "TRIAGED", "TRACKING", "DONE", "DISMISSED"], text(data.research?.status, "NEW"));
        const priorityWrap = input("Priority", { type: "number", value: text(data.research?.priority, "0") });
        const notesWrap = input("Notes", { value: text(data.research?.notes, "") });
        const save = button("Save research state", { variant: "primary", type: "submit" });
        appendActionRow(researchForm, save);
        researchForm.prepend(statusWrap, priorityWrap, notesWrap);
        researchForm.addEventListener("submit", async (event) => { event.preventDefault(); save.disabled = true; try {
            await api(`/api/v1/opportunities/${id}/research`, { method: "PATCH", body: JSON.stringify({ status: statusWrap.querySelector("select")?.value, priority: Number(priorityWrap.querySelector("input")?.value ?? 0), notes: notesWrap.querySelector("input")?.value ?? "" }) });
            save.textContent = "Saved";
        }
        catch (error) {
            researchForm.append(errorState(error, context));
        }
        finally {
            save.disabled = false;
        } });
        const evidenceRows = (data.evidence ?? []).map((row) => [badge(text(row.type), "info"), text(row.source), text(row.title), text(row.quality), formatDate(row.observed_at), row.url ? externalLink(row.url) : "—"]);
        const citationRows = (data.analysis?.citations ?? []).map((row) => [text(row.evidence_id), text(row.source), text(row.title), text(row.type)]);
        append(host, summary, actions, mode === "analysis" ? card("Analysis", detailList(Object.entries(data.analysis ?? {}).filter(([key]) => !["citations", "conflict"].includes(key)).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : text(value)]))) : card("Analysis summary", detailList([["Summary", data.analysis?.summary], ["Target user", data.analysis?.target_user], ["Business model", data.analysis?.business_model], ["Monetization", data.analysis?.monetization], ["Risk notes", data.analysis?.risk_notes]])), mode === "result" ? card("Research result trace", citationRows.length ? table(["Evidence id", "Source", "Title", "Type"], citationRows) : statePanel("empty", "No persisted analysis citations are available.")) : card("Related keywords", table(["Keyword", "Role", "Weight"], (data.keywords ?? []).map((row) => [text(row.keyword), text(row.role), number(row.weight, 1)]))), card("Evidence", evidenceRows.length ? table(["Type", "Source", "Title", "Quality", "Observed", "URL"], evidenceRows) : statePanel("empty", "No evidence citations are available.")), researchForm);
    }
    catch (error) {
        append(host, error instanceof ApiError && error.status === 404 ? objectNotFound("Opportunity", id) : errorState(error, context));
    }
    return host;
}
function addOption(selectEl, value, label) { const option = document.createElement("option"); option.value = value; option.textContent = label; selectEl.append(option); }
function scoreBadge(value) { return badge(`评分 ${number(value, 1)}`, Number(value) >= 80 ? "success" : Number(value) >= 60 ? "info" : "neutral"); }
function researchLabel(value) { return { NEW: "未处理", TRIAGED: "已分诊", TRACKING: "跟踪中", DONE: "已完成", DISMISSED: "已忽略" }[String(value)] ?? text(value, "未处理"); }
function scoreLabel(value) { return { demand: "需求", supply: "供给", execution: "执行", cross_source: "跨来源", saturation: "饱和度" }[value] ?? value; }
function detailSection(title, body) { const section = document.createElement("section"); section.className = "r04-detail-section"; section.append(title, body); return section; }
function detailSectionWithBody(titleValue, body) { const title = document.createElement("h2"); title.textContent = titleValue; return detailSection(title, body); }
function sourceList(rows) { const list = document.createElement("div"); list.className = "r04-source-list"; for (const row of rows.slice(0, 5)) {
    const item = document.createElement("div");
    item.className = "r04-source-item";
    let title;
    if (row.url) {
        const link = externalLink(text(row.url));
        link.textContent = text(row.title, "打开来源");
        title = link;
    }
    else {
        const span = document.createElement("span");
        span.textContent = text(row.title, "未命名来源");
        title = span;
    }
    const meta = document.createElement("small");
    meta.textContent = `${text(row.source)} · ${formatDate(row.observed_at)}`;
    item.append(title, meta);
    list.append(item);
} return list.childElementCount ? list : statePanel("empty", "暂无关键来源。"); }
function detailList(entries) { const dl = document.createElement("dl"); dl.className = "r02-detail-grid"; for (const [key, value] of entries) {
    const dt = document.createElement("dt");
    dt.textContent = key;
    const dd = document.createElement("dd");
    dd.textContent = text(value);
    dl.append(dt, dd);
} return dl; }
function objectNotFound(kind, id) { const panel = document.createElement("div"); panel.className = "r02-object-not-found"; const heading = document.createElement("h2"); heading.textContent = `${kind}不存在`; const copy = document.createElement("p"); copy.textContent = `未找到 ID 为 ${id} 的真实${kind}记录。`; const actions = document.createElement("div"); appendActionRow(actions, button("返回工作台", { variant: "primary", onClick: () => navigate("P02") }), button("返回上一页", { onClick: () => history.back() })); panel.append(heading, copy, actions); return panel; }
function externalLink(url) { const link = document.createElement("a"); link.href = url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = "Open"; return link; }
async function renderStructuredAnalysisList(route, context) {
    const host = document.createElement("div");
    host.className = "r04-research-list";
    host.append(r04PageHeading("结构化分析", "查看机会已经持久化的结构化分析状态与摘要", "刷新分析列表"));
    host.append(readOnlyNotice("当前后端没有独立 StructuredAnalysis 资源；列表使用机会接口返回的 analysis_* 字段，只展示已有记录，不提供生成或重生成操作。", "结构化分析只读"));
    try {
        const data = await api("/api/v1/opportunities?include_dormant=true&limit=200");
        const records = Array.isArray(data) ? data : [];
        if (!records.length) {
            host.append(statePanel("empty", "当前没有可展示的机会分析记录。"));
            return host;
        }
        const controls = document.createElement("form");
        controls.className = "r04-research-filters";
        const search = document.createElement("input");
        search.type = "search";
        search.placeholder = "搜索机会标题或摘要";
        search.setAttribute("aria-label", "搜索机会标题或摘要");
        const status = document.createElement("select");
        status.setAttribute("aria-label", "分析状态");
        addOption(status, "", "分析状态：全部");
        ["READY", "PENDING", "DEGRADED", "FAILED"].forEach((value) => addOption(status, value, analysisLabel(value)));
        const period = document.createElement("select");
        period.setAttribute("aria-label", "最近更新时间");
        addOption(period, "", "时间：全部");
        addOption(period, "7", "最近 7 天");
        addOption(period, "30", "最近 30 天");
        addOption(period, "90", "最近 90 天");
        const submit = document.createElement("button");
        submit.type = "submit";
        submit.className = "r04-keyword-submit";
        submit.textContent = "筛选";
        controls.append(search, status, period, submit);
        host.append(controls);
        const layout = document.createElement("div");
        layout.className = "r04-research-list-layout";
        const results = document.createElement("section");
        results.className = "r04-research-results";
        const inspector = document.createElement("aside");
        inspector.className = "r04-research-inspector";
        const draw = () => {
            const query = search.value.trim().toLowerCase();
            const selectedStatus = status.value;
            const days = Number(period.value || 0);
            const filtered = records.filter((row) => {
                const haystack = `${row.title ?? ""} ${row.summary ?? ""} ${row.id ?? ""}`.toLowerCase();
                const timestamp = Date.parse(String(row.last_seen_at ?? row.first_seen_at ?? ""));
                const inPeriod = !days || (Number.isFinite(timestamp) && Date.now() - timestamp <= days * 86_400_000);
                return (!query || haystack.includes(query)) && (!selectedStatus || String(row.analysis_status ?? "") === selectedStatus) && inPeriod;
            });
            const tableRows = filtered.map((row) => [linkTo("P14", text(row.title, `机会 ${row.id}`), { id: row.id }), text(row.id), badge(analysisLabel(row.analysis_status), analysisTone(row.analysis_status)), text(row.analysis_provider, "未返回"), text(row.analysis_attempt_count, "0"), text(row.evidence_count, "0"), formatDate(row.last_seen_at)]);
            results.replaceChildren(tableRows.length ? table(["机会", "机会 ID", "分析状态", "提供方", "尝试次数", "证据数", "最近出现"], tableRows) : statePanel("empty", "没有符合当前筛选条件的真实分析记录。"));
            renderStructuredAnalysisInspector(inspector, filtered[0]);
        };
        controls.addEventListener("submit", (event) => { event.preventDefault(); draw(); });
        search.addEventListener("input", draw);
        status.addEventListener("change", draw);
        period.addEventListener("change", draw);
        draw();
        layout.append(results, inspector);
        host.append(layout);
        const selectedId = route.params.get("selected_id");
        if (selectedId) {
            const selected = records.find((row) => String(row.id) === selectedId);
            if (selected)
                renderStructuredAnalysisInspector(inspector, selected);
        }
    }
    catch (error) {
        host.append(errorState(error, context, () => void renderStructuredAnalysisList(route, context)));
    }
    return host;
}
function renderStructuredAnalysisInspector(host, row) {
    if (!row) {
        host.replaceChildren(statePanel("empty", "从列表选择一条真实分析记录查看摘要。"));
        return;
    }
    const body = document.createElement("div");
    body.className = "r04-research-inspector-inner";
    const title = document.createElement("h2");
    title.textContent = text(row.title, `机会 ${row.id}`);
    body.append(title, detailList([["分析状态", analysisLabel(row.analysis_status)], ["提供方", text(row.analysis_provider, "未返回")], ["尝试次数", text(row.analysis_attempt_count, "0")], ["证据数", text(row.evidence_count, "0")], ["最近出现", formatDate(row.last_seen_at)], ["摘要", text(row.summary, "机会接口未返回摘要。")]]));
    const actions = document.createElement("div");
    actions.className = "r04-research-inspector-actions";
    actions.append(linkTo("P14", "打开分析详情", { id: row.id }), linkTo("P13", "查看机会", { id: row.id }), linkTo("P13", "查看机会证据", { id: row.id, tab: "evidence" }));
    body.append(actions, capabilityUnavailableNotice("分析详情中的引用与结构化字段需要进入机会详情读取；后端没有独立分析记录 ID 或处理轨迹。", "分析记录范围"));
    host.replaceChildren(body);
}
async function renderResearch(route, context) {
    const host = document.createElement("div");
    host.className = "r04-research-list";
    host.append(r04PageHeading("研究任务", "按机会研究状态查看需要跟进的对象", "刷新研究任务"));
    host.append(readOnlyNotice("当前后端未暴露 ResearchTask 资源、负责人、任务目标或状态推进接口；下表仅映射真实机会的 OpportunityResearch 状态，所有任务写操作均隐藏。", "研究任务只读降级"));
    try {
        const data = await api("/api/v1/opportunities/page?include_dormant=true&limit=200");
        const records = Array.isArray(data?.items) ? data.items : [];
        if (!records.length) {
            host.append(statePanel("empty", "当前没有可展示的机会研究状态。"));
            return host;
        }
        const controls = document.createElement("form");
        controls.className = "r04-research-filters";
        const search = document.createElement("input");
        search.type = "search";
        search.placeholder = "搜索机会标题或 ID";
        search.setAttribute("aria-label", "搜索机会标题或 ID");
        const taskStatus = document.createElement("select");
        taskStatus.setAttribute("aria-label", "研究状态");
        addOption(taskStatus, "", "研究状态：全部");
        ["NEW", "REVIEWING", "TRACKING", "DISMISSED", "ARCHIVED"].forEach((value) => addOption(taskStatus, value, researchLabel(value)));
        const priority = document.createElement("select");
        priority.setAttribute("aria-label", "优先级");
        addOption(priority, "", "优先级：全部");
        ["5", "4", "3", "2", "1", "0"].forEach((value) => addOption(priority, value, `${value} 级`));
        const submit = document.createElement("button");
        submit.type = "submit";
        submit.className = "r04-keyword-submit";
        submit.textContent = "筛选";
        controls.append(search, taskStatus, priority, submit);
        host.append(controls);
        const layout = document.createElement("div");
        layout.className = "r04-research-list-layout";
        const results = document.createElement("section");
        results.className = "r04-research-results";
        const inspector = document.createElement("aside");
        inspector.className = "r04-research-inspector";
        const draw = () => {
            const query = search.value.trim().toLowerCase();
            const selectedStatus = taskStatus.value;
            const selectedPriority = priority.value;
            const filtered = records.filter((row) => { const research = row.research ?? {}; const haystack = `${row.title ?? ""} ${row.id ?? ""}`.toLowerCase(); return (!query || haystack.includes(query)) && (!selectedStatus || String(research.status ?? "NEW") === selectedStatus) && (!selectedPriority || String(research.priority ?? 0) === selectedPriority); });
            const tableRows = filtered.map((row) => { const research = row.research ?? {}; return [linkTo("P16", text(row.title, `机会 ${row.id}`), { id: row.id }), text(row.id), badge(researchLabel(research.status), researchTone(research.status)), text(research.priority, "0"), research.starred ? badge("重点", "warning") : text("普通"), formatDate(research.updated_at), linkTo("P13", "查看机会", { id: row.id })]; });
            results.replaceChildren(tableRows.length ? table(["机会", "机会 ID", "研究状态", "优先级", "标记", "更新时间", "关联机会"], tableRows) : statePanel("empty", "没有符合当前筛选条件的真实研究状态。"));
            renderResearchTaskInspector(inspector, filtered[0]);
        };
        controls.addEventListener("submit", (event) => { event.preventDefault(); draw(); });
        search.addEventListener("input", draw);
        taskStatus.addEventListener("change", draw);
        priority.addEventListener("change", draw);
        draw();
        layout.append(results, inspector);
        host.append(layout);
        const selectedId = route.params.get("selected_id");
        if (selectedId) {
            const selected = records.find((row) => String(row.id) === selectedId);
            if (selected)
                renderResearchTaskInspector(inspector, selected);
        }
    }
    catch (error) {
        host.append(errorState(error, context, () => void renderResearch(route, context)));
    }
    return host;
}
function renderResearchTaskInspector(host, row) {
    if (!row) {
        host.replaceChildren(statePanel("empty", "从列表选择一条真实研究状态查看详情。"));
        return;
    }
    const research = row.research ?? {};
    const body = document.createElement("div");
    body.className = "r04-research-inspector-inner";
    const title = document.createElement("h2");
    title.textContent = text(row.title, `机会 ${row.id}`);
    body.append(title, detailList([["机会 ID", row.id], ["研究状态", researchLabel(research.status)], ["优先级", research.priority], ["重点机会", research.starred ? "是" : "否"], ["标签", (research.tags ?? []).join("、") || "未返回"], ["备注", text(research.notes, "未返回")], ["更新时间", formatDate(research.updated_at)]]));
    const actions = document.createElement("div");
    actions.className = "r04-research-inspector-actions";
    actions.append(linkTo("P16", "打开研究详情", { id: row.id }), linkTo("P13", "查看机会", { id: row.id }), linkTo("P13", "查看机会证据", { id: row.id, tab: "evidence" }));
    body.append(actions, capabilityUnavailableNotice("研究任务的任务 ID、负责人、目标、证据覆盖率和完成结果没有后端资源；这里不显示 HTML mock 字段。", "任务字段范围"));
    host.replaceChildren(body);
}
async function renderResearchResultList(_route, context) {
    const host = document.createElement("div");
    host.className = "r04-research-list";
    host.append(r04PageHeading("研究结果", "查看已经持久化的机会分析快照", "刷新研究结果"));
    host.append(readOnlyNotice("当前后端没有 ResearchResult 资源；下表仅展示机会接口可确认的 READY 分析快照，不把机会摘要冒充独立研究结果，也不提供生成或重试按钮。", "研究结果只读降级"));
    try {
        const data = await api("/api/v1/opportunities?include_dormant=true&limit=200");
        const records = (Array.isArray(data) ? data : []).filter((row) => String(row.analysis_status ?? "") === "READY");
        const results = document.createElement("section");
        results.className = "r04-research-results";
        const rows = records.map((row) => [linkTo("P17", text(row.title, `机会 ${row.id}`), { id: row.id }), badge("已完成", "success"), text(row.analysis_provider, "未返回"), text(row.evidence_count, "0"), text(row.summary, "机会接口未返回分析摘要。"), formatDate(row.last_seen_at)]);
        results.append(rows.length ? table(["机会", "分析状态", "提供方", "证据数", "结果摘要", "最近出现"], rows) : statePanel("empty", "当前没有后端可确认的 READY 分析快照。"));
        const note = capabilityUnavailableNotice("研究结果详情会读取对应机会详情中的 analysis 字段；因为没有独立结果 ID、来源任务或完成事件，列表不展示这些未暴露的字段。", "研究结果资源范围");
        host.append(results, note, linkTo("P14", "查看结构化分析列表"), linkTo("P15", "查看研究任务列表"));
    }
    catch (error) {
        host.append(errorState(error, context, () => void renderResearchResultList(_route, context)));
    }
    return host;
}
async function renderResearchResultDetail(route, context) {
    const id = route.params.get("id");
    const host = document.createElement("div");
    host.className = "r04-research-result-detail";
    if (!id) {
        host.append(objectNotFound("研究结果", "缺失"));
        return host;
    }
    try {
        const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}?evidence_limit=100`);
        const requestedTab = route.params.get("tab") ?? "conclusion";
        const activeTab = ["conclusion", "evidence", "method", "activity"].includes(requestedTab) ? requestedTab : "conclusion";
        const header = document.createElement("header");
        header.className = "r04-research-result-header";
        const breadcrumb = document.createElement("nav");
        breadcrumb.className = "r04-result-breadcrumb";
        breadcrumb.append(linkTo("P15", "研究"), document.createTextNode(" / "), linkTo("P17", "研究结果"), document.createTextNode(" / "), document.createTextNode(text(data.title, `机会 ${id}`)));
        const title = document.createElement("h1");
        title.textContent = text(data.title, `机会 ${id}`);
        const meta = document.createElement("div");
        meta.className = "r04-result-meta";
        meta.append(badge(analysisLabel(data.analysis?.status), analysisTone(data.analysis?.status)), document.createTextNode(" · "), linkTo("P13", "关联机会", { id }), document.createTextNode(` · 证据返回覆盖 ${resultEvidenceCoverage(data)} · 分析时间 ${formatDate(data.analysis?.analyzed_at)}`));
        const actions = document.createElement("div");
        actions.className = "r04-result-actions";
        const copy = button("复制链接", { onClick: () => { void navigator.clipboard?.writeText(window.location.href).then(() => { copy.textContent = "链接已复制"; }); } });
        actions.append(copy);
        const heading = document.createElement("div");
        heading.className = "r04-result-heading-row";
        const headingCopy = document.createElement("div");
        headingCopy.append(title, meta);
        heading.append(headingCopy, actions);
        header.append(breadcrumb, heading);
        host.append(header, readOnlyNotice("本页只展示机会详情接口已经返回的分析与证据字段，不提供重新生成、修改研究状态或伪造活动记录。", "研究结果只读"), researchResultTabs(id, activeTab), renderResearchResultTab(data, id, activeTab));
    }
    catch (error) {
        host.append(errorState(error, context, () => void renderResearchResultDetail(route, context)));
    }
    return host;
}
function researchResultTabs(id, active) {
    const nav = document.createElement("nav");
    nav.className = "r04-result-tabs";
    nav.setAttribute("aria-label", "研究结果详情导航");
    for (const [tab, label] of [["conclusion", "结论"], ["evidence", "证据"], ["method", "方法"], ["activity", "活动记录"]]) {
        const link = linkTo("P17", label, { id, tab });
        link.className = active === tab ? "is-active" : "";
        link.setAttribute("aria-current", active === tab ? "page" : "false");
        nav.append(link);
    }
    return nav;
}
function renderResearchResultTab(data, id, active) {
    if (active === "evidence")
        return renderResearchResultEvidence(data, id);
    if (active === "method")
        return renderResearchResultMethod(data);
    if (active === "activity")
        return renderResearchResultActivity(data, id);
    return renderResearchResultConclusion(data, id);
}
function renderResearchResultConclusion(data, id) {
    const layout = document.createElement("div");
    layout.className = "r04-result-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-result-tab-main";
    const side = document.createElement("aside");
    side.className = "r04-result-tab-side";
    main.append(detailSectionWithBody("执行结论", data.analysis?.summary ? paragraph(text(data.analysis.summary)) : statePanel("empty", "机会详情未返回分析摘要。")));
    main.append(detailSectionWithBody("分析字段", detailList([["目标用户", data.analysis?.target_user], ["商业模式", data.analysis?.business_model], ["变现方式", data.analysis?.monetization], ["风险说明", data.analysis?.risk_notes]])));
    side.append(detailSectionWithBody("关键来源", researchCitationList(data.analysis?.citations ?? [], id)), linkTo("P13", "查看关联机会", { id }), capabilityUnavailableNotice("后端没有独立研究结果的结论实体、源任务或研究完成事件；本页只读取 opportunity.analysis。", "结果资源范围"));
    layout.append(main, side);
    return layout;
}
function researchCitationList(rows, opportunityId) {
    if (!rows.length)
        return statePanel("empty", "当前分析没有返回已绑定的引用来源。");
    const items = document.createElement("div");
    items.className = "r04-result-citation-list";
    rows.slice(0, 8).forEach((row, index) => { const item = document.createElement("div"); const link = linkTo("P13", text(row.title, `引用 ${index + 1}`), { id: opportunityId, tab: "evidence", evidence_id: text(row.evidence_id) }); const meta = document.createElement("small"); meta.textContent = `${text(row.source, "未返回来源")} · ${qualityLabel(row.quality)}`; item.append(link, meta); items.append(item); });
    return items;
}
function renderResearchResultEvidence(data, id) {
    const host = document.createElement("div");
    host.className = "r04-result-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-result-tab-main";
    const side = document.createElement("aside");
    side.className = "r04-result-tab-side";
    const evidence = (data.evidence ?? []);
    const filters = document.createElement("div");
    filters.className = "r04-result-evidence-filters";
    const quality = document.createElement("select");
    quality.setAttribute("aria-label", "证据质量");
    addOption(quality, "", "质量：全部");
    ["A", "B", "C"].forEach((value) => addOption(quality, value, qualityLabel(value)));
    const type = document.createElement("select");
    type.setAttribute("aria-label", "证据类型");
    addOption(type, "", "类型：全部");
    Array.from(new Set(evidence.map((row) => text(row.type, "未标注")))).forEach((value) => addOption(type, value, value));
    const count = document.createElement("span");
    count.className = "r04-result-evidence-count";
    filters.append(quality, type, count);
    const results = document.createElement("div");
    results.className = "r04-result-evidence-results";
    const draw = () => { const rows = evidence.filter((row) => (!quality.value || String(row.quality) === quality.value) && (!type.value || text(row.type, "未标注") === type.value)); count.textContent = `显示 ${rows.length} / ${evidence.length} 条真实证据`; const tableRows = rows.map((row) => [linkTo("P13", text(row.evidence_id ?? row.id), { id, tab: "evidence", evidence_id: text(row.evidence_id ?? row.id) }), text(row.title, "未返回标题"), evidenceSourceCell(row), weightLabel(row.weight), badge(qualityLabel(row.quality), qualityTone(row.quality)), formatDate(row.observed_at)]); results.replaceChildren(tableRows.length ? table(["证据 ID", "证据摘要", "来源", "极性", "置信度", "观察时间"], tableRows) : statePanel("empty", "没有符合当前筛选条件的真实证据。")); };
    quality.addEventListener("change", draw);
    type.addEventListener("change", draw);
    draw();
    main.append(detailSectionWithBody("证据清单", filters), results);
    side.append(detailSectionWithBody("证据统计", detailList([["已存证据", data.evidence_summary?.stored ?? data.evidence_count], ["本次返回", data.evidence_summary?.returned ?? evidence.length], ["近 7 日", data.evidence_summary?.recent_7d], ["近 30 日", data.evidence_summary?.recent_30d], ["平均质量权重", number(data.evidence_summary?.average_quality_weight, 2)]])), capabilityUnavailableNotice("证据来自机会详情的 evidence binding；后端没有独立 ResearchResultEvidence 资源，关联结论和来源只使用接口返回的 ID、URL 与字段。", "证据契约范围"));
    host.append(main, side);
    return host;
}
function evidenceSourceCell(row) { if (row.url) {
    const link = externalLink(text(row.url));
    link.textContent = text(row.source, "打开原始来源");
    return link;
} return text(row.source, "未返回来源"); }
function qualityTone(value) { return { A: "success", B: "warning", C: "danger" }[String(value)] ?? "neutral"; }
function paragraph(value) { const p = document.createElement("p"); p.className = "r04-result-paragraph"; p.textContent = value; return p; }
function renderResearchResultMethod(data) {
    const layout = document.createElement("div");
    layout.className = "r04-result-tab-layout";
    const main = document.createElement("main");
    main.className = "r04-result-tab-main";
    const side = document.createElement("aside");
    side.className = "r04-result-tab-side";
    main.append(detailSectionWithBody("已确认的分析上下文", detailList([["分析提供方", data.analysis?.provider], ["分析状态", analysisLabel(data.analysis?.status)], ["分析时间", formatDate(data.analysis?.analyzed_at)], ["引用契约版本", data.analysis?.citation_contract_version], ["冲突报告", data.analysis?.conflict && Object.keys(data.analysis.conflict).length ? JSON.stringify(data.analysis.conflict) : "未返回"]])));
    main.append(capabilityUnavailableNotice("后端没有返回研究范围、研究问题、纳入/排除规则、分析模型或结果限制的独立字段；不使用 HTML mock 文案补齐方法说明。", "方法字段暂不可用"));
    side.append(detailSectionWithBody("可验证的证据统计", detailList([["已存证据", data.evidence_summary?.stored ?? data.evidence_count], ["来源数量", data.evidence_summary?.sources ? Object.keys(data.evidence_summary.sources).length : "未返回"], ["质量分布", data.evidence_summary?.qualities ? JSON.stringify(data.evidence_summary.qualities) : "未返回"]])), linkTo("P17", "返回研究结果结论", { id: data.id, tab: "conclusion" }));
    layout.append(main, side);
    return layout;
}
function renderResearchResultActivity(data, id) {
    const layout = document.createElement("div");
    layout.className = "r04-result-activity-layout";
    const events = [];
    if (data.analysis?.analyzed_at)
        events.push([data.analysis.analyzed_at, "分析时间", `由 ${text(data.analysis.provider, "未指定提供方")} 写入的 opportunity.analysis 时间字段。`]);
    if (data.analysis?.last_attempt_at)
        events.push([data.analysis.last_attempt_at, "最近尝试时间", "机会分析记录返回的最近尝试时间字段。"]);
    if (data.analysis?.next_retry_at)
        events.push([data.analysis.next_retry_at, "下一次重试时间", "机会分析记录返回的下一次重试时间字段。"]);
    if (data.analysis?.error)
        events.push([data.analysis.last_attempt_at ?? data.analysis.analyzed_at, "分析错误", text(data.analysis.error)]);
    const timeline = document.createElement("div");
    timeline.className = "r04-result-timeline";
    timeline.append(events.length ? table(["时间", "字段", "已确认内容"], events.map(([when, label, detail]) => [formatDate(when), badge(label, label === "分析错误" ? "danger" : "info"), detail])) : statePanel("empty", "机会详情未返回可展示的分析时间字段。"));
    layout.append(detailSectionWithBody("可确认的系统时间字段", timeline), capabilityUnavailableNotice("后端没有研究结果活动事件、操作人或导出记录资源；此处只展示 opportunity.analysis 返回的真实时间与错误字段，不拼装完整时间线。", "活动记录暂不可用"), linkTo("P13", "返回关联机会", { id }));
    return layout;
}
function resultEvidenceCoverage(data) { const stored = Number(data.evidence_summary?.stored ?? data.evidence_count ?? 0); const returned = Number(data.evidence_summary?.returned ?? (data.evidence ?? []).length); return stored > 0 ? `${Math.round((returned / stored) * 100)}%（返回 ${returned}/${stored}）` : "未返回"; }
function analysisTone(value) {
    return { READY: "success", PENDING: "info", DEGRADED: "warning", FAILED: "danger" }[String(value)] ?? "neutral";
}
function researchTone(value) {
    return { TRACKING: "success", REVIEWING: "info", DISMISSED: "danger", ARCHIVED: "neutral" }[String(value)] ?? "neutral";
}
async function renderSources(context) {
    const host = content("Sources", "Registered connectors and their runtime availability.");
    try {
        const rows = await api("/api/v1/sources");
        const tableRows = (rows ?? []).map((row) => [text(row.display_name ?? row.source_id), text(row.source_id), row.runtime_enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.kind ?? row.type), linkTo("P19", "Health", { id: row.source_id })]);
        append(host, tableRows.length ? table(["Source", "Id", "Runtime", "Kind", "Detail"], tableRows) : statePanel("empty", "No source connectors are registered."));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderSourceHealth(route, context) {
    const sourceId = route.params.get("id");
    const host = content("Source health", "Connector health and persisted circuit state.");
    try {
        const rows = await api("/api/v1/sources/health");
        const selected = sourceId ? rows.filter((row) => String(row.source_id) === sourceId) : rows;
        append(host, selected.length ? table(["Source", "Status", "Latency", "Last success", "Last error"], selected.map((row) => [text(row.source_id), badge(text(row.status ?? row.runtime_status ?? "UNKNOWN"), row.status === "HEALTHY" ? "success" : "warning"), text(row.latency_ms ?? row.duration_ms), formatDate(row.last_success_at), text(row.last_error)])) : statePanel("empty", "No health record matches this source."));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderMonitoring(context) {
    const host = content("Monitoring plan", "Probe planning is read-only here; execution remains an admin backend operation.");
    try {
        const data = await api("/api/v1/probes/plan");
        const rows = Array.isArray(data) ? data : (data.tasks ?? data.queries ?? []);
        append(host, rows.length ? table(["Query", "Source", "Intent", "Reason"], rows.slice(0, 100).map((row) => [text(row.query), text(row.source_id), text(row.intent), text(row.reason ?? row.priority)])) : card("Plan snapshot", table(["Field", "Value"], Object.entries(data ?? {}).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : text(value)]))));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderRuns(context) {
    const host = content("Collection runs", "Recent connector runs and their persisted outcomes.");
    try {
        const rows = await api("/api/v1/collection-runs?limit=100");
        const tableRows = (rows ?? []).map((row) => [linkTo("P22", `Run ${row.id}`, { id: row.id }), text(row.source_id), text(row.query), badge(text(row.status), row.status === "SUCCEEDED" ? "success" : row.status === "FAILED" ? "danger" : "warning"), text(row.fetched), text(row.inserted), formatDate(row.started_at)]);
        append(host, tableRows.length ? table(["Run", "Source", "Query", "Status", "Fetched", "Inserted", "Started"], tableRows) : statePanel("empty", "No collection runs are recorded."));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderRunDetail(route, context) {
    const id = route.params.get("id");
    const host = content("Collection run detail", "The run record is loaded from the existing collection-runs endpoint.");
    try {
        const rows = await api("/api/v1/collection-runs?limit=500");
        const row = (rows ?? []).find((item) => String(item.id) === id);
        append(host, row ? card(`Run ${id}`, detailList(Object.entries(row).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value]))) : statePanel("empty", "Run not found."), linkTo("P21", "Back to collection runs"));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderAnalysisQueue(context) {
    const host = content("Analysis queue", "Opportunities waiting for or retrying structured analysis.");
    try {
        const data = await api("/api/v1/opportunities?include_dormant=true&limit=200");
        const rows = (data ?? []).filter((row) => ["PENDING", "DEGRADED", "FAILED"].includes(String(row.analysis_status))).map((row) => [linkTo("P14", text(row.title), { id: row.id }), badge(text(row.analysis_status), row.analysis_status === "DEGRADED" ? "warning" : "info"), text(row.analysis_provider), text(row.analysis_attempt_count), formatDate(row.analysis_next_retry_at)]);
        append(host, rows.length ? table(["Opportunity", "State", "Provider", "Attempts", "Next retry"], rows) : statePanel("empty", "The analysis queue is empty."));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function renderAlerts(context) {
    const host = content("Alert inbox", "Alert lifecycle state is updated through the existing alert event API.");
    try {
        const data = await api("/api/v1/alerts/events?limit=100");
        const rows = (data ?? []).map((row) => { const action = row.status === "NEW" ? button("Acknowledge", { onClick: () => updateAlert(row.id, "ACKNOWLEDGED", host, context) }) : button("Resolve", { onClick: () => updateAlert(row.id, "RESOLVED", host, context) }); return [text(row.title), badge(text(row.status), row.status === "NEW" ? "warning" : "neutral"), text(row.priority), number(row.score, 1), formatDate(row.created_at), action]; });
        append(host, rows.length ? table(["Alert", "Status", "Priority", "Score", "Created", "Action"], rows) : statePanel("empty", "No alert events are available."));
    }
    catch (error) {
        append(host, errorState(error, context));
    }
    return host;
}
async function updateAlert(id, status, host, context) { try {
    await api(`/api/v1/alerts/events/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
    const next = await renderAlerts(context);
    host.replaceChildren(...Array.from(next.childNodes));
}
catch (error) {
    host.append(errorState(error, context));
} }
async function renderAlertRules(context) {
    const host = content("Alert rules", "Rules are persisted by the existing alert-rule endpoints.");
    const form = document.createElement("form");
    form.className = "r02-inline-form";
    const nameWrap = input("Rule name", { placeholder: "e.g. high signal" });
    const name = nameWrap.querySelector("input");
    const save = button("Create rule", { variant: "primary", type: "submit" });
    appendActionRow(form, save);
    form.prepend(nameWrap);
    const list = document.createElement("div");
    form.addEventListener("submit", async (event) => { event.preventDefault(); save.disabled = true; try {
        await api("/api/v1/alerts/rules", { method: "POST", body: JSON.stringify({ name: name?.value ?? "" }) });
        form.reset();
        await loadAlertRules(list, context);
    }
    catch (error) {
        list.replaceChildren(errorState(error, context));
    }
    finally {
        save.disabled = false;
    } });
    append(host, form, list);
    await loadAlertRules(list, context);
    return host;
}
async function loadAlertRules(list, context) { try {
    const rows = await api("/api/v1/alerts/rules");
    list.replaceChildren(rows.length ? table(["Name", "Enabled", "Min score", "Stages", "Updated"], rows.map((row) => { const toggle = button(row.enabled ? "Disable" : "Enable", { onClick: async () => { toggle.disabled = true; try {
            await api(`/api/v1/alerts/rules/${row.id}`, { method: "PATCH", body: JSON.stringify({ enabled: !row.enabled }) });
            await loadAlertRules(list, context);
        }
        catch (error) {
            list.replaceChildren(errorState(error, context));
        } } }); return [text(row.name), row.enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), number(row.min_score, 1), text((row.stages ?? []).join(", ")), formatDate(row.updated_at), toggle]; })) : statePanel("empty", "No alert rules are configured."));
}
catch (error) {
    list.replaceChildren(errorState(error, context));
} }
async function renderAudit(context) { const host = content("Audit log", "Administrative request and mutation records from the backend audit stream."); try {
    const rows = await api("/api/v1/audit?limit=200");
    append(host, rows.length ? table(["Created", "Actor", "Action", "Resource", "Status", "Request"], rows.map((row) => [formatDate(row.created_at), text(row.actor), text(row.action), text(row.resource), text(row.status_code), text(row.request_id)])) : statePanel("empty", "No audit events are recorded."));
}
catch (error) {
    append(host, errorState(error, context));
} return host; }
async function renderUsers(context) {
    const host = content("Users and roles", "Administrative identities from the existing RBAC user API. The server remains authoritative for OWNER invariants.");
    const form = document.createElement("form");
    form.className = "r02-inline-form";
    const usernameWrap = input("Username", { placeholder: "new user" });
    const passwordWrap = input("Initial password", { type: "password", placeholder: "at least 12 characters" });
    const roleWrap = select("Role", ["VIEWER", "OPERATOR", "ADMIN", "OWNER"], "VIEWER");
    const username = usernameWrap.querySelector("input");
    const password = passwordWrap.querySelector("input");
    const role = roleWrap.querySelector("select");
    const create = button("Create user", { variant: "primary", type: "submit" });
    appendActionRow(form, create);
    form.prepend(usernameWrap, passwordWrap, roleWrap);
    const list = document.createElement("div");
    form.addEventListener("submit", async (event) => { event.preventDefault(); create.disabled = true; try {
        await api("/api/v1/admin/users", { method: "POST", body: JSON.stringify({ username: username?.value ?? "", password: password?.value ?? "", role: role?.value ?? "VIEWER", enabled: true }) });
        form.reset();
        await loadUsers(list, context);
    }
    catch (error) {
        list.replaceChildren(errorState(error, context));
    }
    finally {
        create.disabled = false;
    } });
    append(host, form, list);
    await loadUsers(list, context);
    return host;
}
async function loadUsers(list, context) { try {
    const rows = await api("/api/v1/admin/users");
    const tableRows = (rows ?? []).map((row) => { const controls = document.createElement("div"); controls.className = "r02-action-row"; const toggle = button(row.enabled ? "Disable" : "Enable", { variant: row.enabled ? "danger" : "secondary", onClick: async () => { toggle.disabled = true; try {
            await api(`/api/v1/admin/users/${row.id}`, { method: "PATCH", body: JSON.stringify({ enabled: !row.enabled }) });
            await loadUsers(list, context);
        }
        catch (error) {
            controls.append(errorState(error, context));
            toggle.disabled = false;
        } } }); const role = select("Role", ["VIEWER", "OPERATOR", "ADMIN", "OWNER"], text(row.role, "VIEWER")); const roleSelect = role.querySelector("select"); const saveRole = button("Save role", { variant: "ghost", onClick: async () => { saveRole.disabled = true; try {
            await api(`/api/v1/admin/users/${row.id}`, { method: "PATCH", body: JSON.stringify({ role: roleSelect?.value }) });
            await loadUsers(list, context);
        }
        catch (error) {
            controls.append(errorState(error, context));
            saveRole.disabled = false;
        } } }); controls.append(role, saveRole, toggle); return [text(row.username), badge(text(row.role), row.role === "OWNER" ? "success" : "info"), row.enabled ? "Yes" : "No", formatDate(row.last_login_at), text(row.failed_login_count), controls]; });
    list.replaceChildren(tableRows.length ? table(["Username", "Role", "Enabled", "Last login", "Failures", "Server-authorized actions"], tableRows) : statePanel("empty", "No users are configured."));
}
catch (error) {
    list.replaceChildren(errorState(error, context));
} }
async function renderAccount(context) {
    const host = content("Account and security", "Personal API tokens are managed through the existing authenticated token API. Token plaintext is shown once after creation.");
    const form = document.createElement("form");
    form.className = "r02-inline-form";
    const nameWrap = input("Token name", { placeholder: "local integration" });
    const expiresWrap = input("Expires in days", { type: "number", placeholder: "optional" });
    const name = nameWrap.querySelector("input");
    const expires = expiresWrap.querySelector("input");
    const issue = button("Issue API token", { variant: "primary", type: "submit" });
    appendActionRow(form, issue);
    form.prepend(nameWrap, expiresWrap);
    const list = document.createElement("div");
    form.addEventListener("submit", async (event) => { event.preventDefault(); issue.disabled = true; try {
        const payload = { name: name?.value ?? "", scopes: ["read"] };
        if (expires?.value)
            payload.expires_in_days = Number(expires.value);
        const result = await api("/api/v1/auth/tokens", { method: "POST", body: JSON.stringify(payload) });
        const secret = document.createElement("div");
        const copy = document.createElement("p");
        copy.textContent = "This token will not be shown again after closing this dialog.";
        const value = document.createElement("code");
        value.className = "r02-secret-value";
        value.textContent = text(result.token);
        const copyButton = button("Copy token", { variant: "secondary", onClick: () => { void navigator.clipboard?.writeText(text(result.token)); copyButton.textContent = "Copied"; } });
        append(secret, copy, value, copyButton);
        host.append(modal("New API token", secret));
        form.reset();
        await loadTokens(list, context);
    }
    catch (error) {
        list.replaceChildren(errorState(error, context));
    }
    finally {
        issue.disabled = false;
    } });
    append(host, form, list);
    await loadTokens(list, context);
    return host;
}
async function loadTokens(list, context) { try {
    const rows = await api("/api/v1/auth/tokens");
    const tokenRows = (rows ?? []).map((row) => { const revoke = button("Revoke", { variant: "danger", onClick: async () => { revoke.disabled = true; try {
            await api(`/api/v1/auth/tokens/${row.id}`, { method: "DELETE" });
            await loadTokens(list, context);
        }
        catch (error) {
            list.replaceChildren(errorState(error, context));
        } } }); return [text(row.name), text((row.scopes ?? []).join(", ")), formatDate(row.created_at), formatDate(row.expires_at), row.revoked_at ? badge("Revoked", "danger") : badge("Active", "success"), revoke]; });
    list.replaceChildren(tokenRows.length ? table(["Name", "Scopes", "Created", "Expires", "State", "Action"], tokenRows) : statePanel("empty", "No personal API tokens are issued."));
}
catch (error) {
    list.replaceChildren(errorState(error, context));
} }
function renderSettings(_route, active, title, message) { const child = document.createElement("div"); append(child, card(title, statePanel("permission", message))); return settingsFrame(active, child); }
async function renderSourcePreferenceSettings(_route, context) { const frame = document.createElement("div"); const inner = content("Source preference", "Runtime enablement and notes use the existing admin source-preference endpoint."); try {
    const rows = await api("/api/v1/sources");
    const tableRows = (rows ?? []).map((row) => { const toggle = button(row.runtime_enabled ? "Disable" : "Enable", { onClick: async () => { toggle.disabled = true; try {
            await api(`/api/v1/sources/${encodeURIComponent(row.source_id)}/preference`, { method: "PATCH", body: JSON.stringify({ enabled: !row.runtime_enabled, note: row.preference_note ?? "" }) });
            const next = await renderSourcePreferenceSettings(_route, context);
            frame.replaceChildren(...Array.from(next.childNodes));
        }
        catch (error) {
            frame.append(errorState(error, context));
        } } }); return [text(row.source_id), row.runtime_enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.preference_note), toggle]; });
    append(inner, tableRows.length ? table(["Source", "Runtime", "Note", "Action"], tableRows) : statePanel("empty", "No source preference records exist."));
}
catch (error) {
    append(inner, errorState(error, context));
} frame.append(settingsFrame("P29-E", inner)); return frame; }
async function renderDiagnostics(context) { const host = content("System diagnostics", "Read-only runtime health checks from the application and provider registries."); const endpoints = [["Health", "/health"], ["Ready", "/ready"], ["Sources", "/api/v1/sources/health"], ["Analysis providers", "/api/v1/analysis/providers"], ["Provider route", "/api/v1/analysis/providers/route"]]; const results = await Promise.allSettled(endpoints.map(([, url]) => api(url))); const rows = results.map((result, index) => [endpoints[index][0], result.status === "fulfilled" ? badge("OK", "success") : badge("Failed", "danger"), result.status === "fulfilled" ? JSON.stringify(result.value) : text(result.reason)]); append(host, table(["Check", "Status", "Response"], rows)); const failed = results.find((result) => result.status === "rejected"); if (failed && failed.status === "rejected")
    host.append(errorState(failed.reason, context)); return host; }
function installScreenStyles() {
    if (document.getElementById("r02-screen-styles"))
        return;
    const style = document.createElement("style");
    style.id = "r02-screen-styles";
    style.textContent = `
    .r04-opportunity-list, .r04-opportunity-detail { display: grid; gap: 18px; min-width: 0; }
    .r04-opportunity-heading { display: grid; gap: 5px; }
    .r04-opportunity-heading h1 { margin: 0; font-size: 24px; line-height: 1.25; }
    .r04-opportunity-heading p { margin: 0; color: var(--or-text-muted); font-size: 13px; }
    .r04-opportunity-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 10px; overflow-x: auto; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-opportunity-filters input[type=search], .r04-opportunity-filters select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-opportunity-filters input[type=search] { flex: 1 1 180px; min-width: 180px; }
    .r04-opportunity-filters select { flex: 0 0 auto; max-width: 155px; }
    .r04-opportunity-filters input:focus, .r04-opportunity-filters select:focus { border-color: var(--or-primary); outline: 0; }
    .r04-opportunity-checkbox { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 8px; color: var(--or-text-muted); font-size: 12px; white-space: nowrap; }
    .r04-opportunity-submit, .r04-opportunity-clear { min-height: 36px; padding: 7px 12px; border-radius: 6px; cursor: pointer; }
    .r04-opportunity-submit { border: 1px solid var(--or-primary); background: var(--or-primary); color: #fff; font-weight: 700; }
    .r04-opportunity-clear { border: 1px solid var(--or-outline-strong); background: var(--or-surface); color: var(--or-text-muted); }
    .r04-opportunity-results { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-opportunity-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-opportunity-pager { display: flex; justify-content: flex-end; align-items: center; gap: 12px; padding: 12px 16px; border-top: 1px solid var(--or-outline); color: var(--or-text-muted); font-size: 12px; }
    .r04-opportunity-pager button { min-height: 32px; padding: 6px 10px; border: 1px solid var(--or-outline-strong); border-radius: 5px; background: var(--or-surface); color: var(--or-text); }
    .r04-opportunity-pager button:disabled { cursor: not-allowed; opacity: .45; }
    .r04-entity-header { display: grid; gap: 12px; }
    .r04-entity-crumb { display: flex; gap: 6px; color: var(--or-text-muted); font-size: 12px; }
    .r04-entity-crumb a { color: var(--or-primary-dark); text-decoration: none; }
    .r04-entity-header h1 { max-width: 900px; margin: 0; color: var(--or-text); font-size: 28px; line-height: 1.25; }
    .r04-entity-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .r04-entity-dates { margin: 0; color: var(--or-text-muted); font-size: 12px; }
    .r04-entity-tabs { display: flex; flex-wrap: wrap; gap: 4px; border-bottom: 1px solid var(--or-outline); }
    .r04-entity-tabs a { padding: 10px 14px; border-bottom: 2px solid transparent; color: var(--or-text-muted); font-size: 13px; text-decoration: none; }
    .r04-entity-tabs a:hover { color: var(--or-text); background: var(--or-surface-muted); }
    .r04-entity-tabs a.is-active { border-bottom-color: var(--or-primary); color: var(--or-primary-dark); font-weight: 700; }
    .r04-detail-grid-r04 { display: grid; grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr); gap: 28px; align-items: start; }
    .r04-detail-main, .r04-detail-side { display: grid; gap: 24px; min-width: 0; }
    .r04-detail-section { display: grid; gap: 12px; min-width: 0; }
    .r04-detail-section h2 { margin: 0; color: var(--or-text); font-size: 18px; }
    .r04-detail-summary-copy { margin: 0; padding-left: 16px; border-left: 2px solid var(--or-primary); color: var(--or-text); line-height: 1.8; white-space: pre-wrap; }
    .r04-detail-section > .r02-table-wrap { border-radius: 6px; }
    .r04-source-list { display: grid; gap: 12px; }
    .r04-source-item { display: grid; gap: 4px; padding: 10px 0; border-bottom: 1px solid var(--or-outline); }
    .r04-source-item:last-child { border-bottom: 0; }
    .r04-source-item a { color: var(--or-primary-dark); text-decoration: none; }
    .r04-source-item a:hover { text-decoration: underline; }
    .r04-source-item span { color: var(--or-text); }
    .r04-source-item small { color: var(--or-text-muted); font-size: 11px; }
    .r04-opportunity-tab-content { display: grid; gap: 20px; min-width: 0; }
    .r04-evidence-filter { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 8px; }
    .r04-evidence-filter input, .r04-evidence-filter select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-evidence-filter input { width: min(280px, 100%); }
    .r04-evidence-filter input:focus, .r04-evidence-filter select:focus { border-color: var(--or-primary); outline: 0; }
    .r04-evidence-results { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-evidence-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-intelligence-list, .r04-intelligence-detail { display: grid; gap: 18px; min-width: 0; }
    .r04-intelligence-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .r04-intelligence-heading h1 { margin: 0; font-size: 24px; line-height: 1.25; }
    .r04-intelligence-heading p { margin: 6px 0 0; color: var(--or-text-muted); font-size: 13px; }
    .r04-intelligence-refresh, .r04-intelligence-copy { min-height: 36px; padding: 8px 12px; border: 1px solid var(--or-outline-strong); border-radius: 6px; background: var(--or-surface); color: var(--or-text); cursor: pointer; }
    .r04-intelligence-refresh:hover, .r04-intelligence-copy:hover { border-color: var(--or-primary); color: var(--or-primary-dark); }
    .r04-intelligence-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 12px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-intelligence-filters input, .r04-intelligence-filters select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-intelligence-filters input[type=search] { flex: 1 1 200px; min-width: 180px; }
    .r04-intelligence-filters input[name=source_id] { width: 130px; }
    .r04-intelligence-submit { min-height: 36px; padding: 7px 12px; border: 1px solid var(--or-primary); border-radius: 6px; background: var(--or-primary); color: #fff; font-weight: 700; }
    .r04-intelligence-results { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-intelligence-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-intelligence-pager { display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 12px 16px; border-top: 1px solid var(--or-outline); color: var(--or-text-muted); font-size: 12px; }
    .r04-intelligence-pager button { min-height: 32px; padding: 6px 10px; border: 1px solid var(--or-outline-strong); border-radius: 5px; background: var(--or-surface); color: var(--or-text); }
    .r04-intelligence-pager button:disabled { cursor: not-allowed; opacity: .45; }
    .r04-intelligence-entity { display: grid; gap: 12px; padding: 20px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-intelligence-entity h1 { max-width: 1000px; margin: 0; font-size: 24px; line-height: 1.35; }
    .r04-intelligence-meta { margin: 0; color: var(--or-text-muted); font-size: 12px; }
    .r04-intelligence-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 4px -20px -20px; padding: 0 20px; border-top: 1px solid var(--or-outline); }
    .r04-intelligence-tabs a { padding: 11px 14px; border-bottom: 2px solid transparent; color: var(--or-text-muted); font-size: 13px; text-decoration: none; }
    .r04-intelligence-tabs a.is-active { border-bottom-color: var(--or-primary); color: var(--or-primary-dark); font-weight: 700; }
    .r04-intelligence-detail-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr); gap: 20px; align-items: start; }
    .r04-intelligence-detail-main, .r04-intelligence-detail-side { display: grid; gap: 20px; min-width: 0; }
    .r04-intelligence-summary-copy { margin: 0; line-height: 1.8; white-space: pre-wrap; }
    .r04-intelligence-evidence { display: grid; gap: 12px; }
    .r04-intelligence-evidence blockquote { margin: 0; padding: 14px; border-left: 2px solid var(--or-primary); border-radius: 0 6px 6px 0; background: var(--or-surface-muted); color: var(--or-text); line-height: 1.7; white-space: pre-wrap; }
    .r04-intelligence-evidence a, .r04-intelligence-detail-side > a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-intelligence-evidence a:hover, .r04-intelligence-detail-side > a:hover { text-decoration: underline; }
    .r04-intelligence-tab-layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr); gap: 20px; align-items: start; }
    .r04-intelligence-tab-main, .r04-intelligence-tab-side { display: grid; gap: 20px; min-width: 0; }
    .r04-intelligence-raw-body { display: grid; gap: 10px; }
    .r04-intelligence-raw-snippet { max-height: 420px; margin: 0; overflow: auto; padding: 16px; border-radius: 6px; background: #22272b; color: #f1f5f9; font: 12px/1.7 ui-monospace, SFMono-Regular, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
    .r04-intelligence-raw-note { margin: 0; color: var(--or-text-muted); font-size: 12px; line-height: 1.6; }
    .r04-intelligence-tab-side > a, .r04-intelligence-drilldown a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-intelligence-tab-side > a:hover, .r04-intelligence-drilldown a:hover { text-decoration: underline; }
    .r04-intelligence-relation-panel { display: grid; gap: 16px; min-height: 220px; align-content: start; }
    .r04-intelligence-drilldown { display: grid; gap: 10px; }
    .r04-intelligence-process { display: grid; gap: 18px; padding: 20px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-intelligence-process-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding-bottom: 14px; border-bottom: 1px solid var(--or-outline); }
    .r04-intelligence-process-heading h2 { margin: 0; font-size: 18px; }
    .r04-intelligence-process-heading span { color: var(--or-text-muted); font-size: 11px; }
    .r04-intelligence-process-stage { display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 12px; position: relative; }
    .r04-intelligence-process-stage:not(:last-child)::after { position: absolute; top: 22px; bottom: -18px; left: 10px; width: 1px; background: var(--or-outline); content: ""; }
    .r04-intelligence-process-marker { z-index: 1; display: grid; width: 22px; height: 22px; place-items: center; border: 2px solid var(--or-primary); border-radius: 50%; background: var(--or-surface); color: var(--or-primary); font-weight: 700; }
    .r04-intelligence-process-stage-content { display: grid; gap: 10px; min-width: 0; padding: 14px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface-muted); }
    .r04-intelligence-process-stage-content h3 { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 14px; }
    .r04-intelligence-process-stage-content h3 .r02-badge { font-size: 10px; }
    @media (max-width: 900px) { .r04-intelligence-tab-layout { grid-template-columns: 1fr; } }
    @media (max-width: 900px) { .r04-intelligence-detail-grid { grid-template-columns: 1fr; } }
    @media (max-width: 640px) { .r04-intelligence-heading { flex-direction: column; } .r04-intelligence-filters input[name=source_id] { width: auto; flex: 1 1 120px; } }
    @media (max-width: 900px) { .r04-detail-grid-r04 { grid-template-columns: 1fr; } }
    @media (max-width: 640px) { .r04-entity-header h1 { font-size: 22px; } .r04-opportunity-filters input[type=search] { min-width: 140px; } }
    .r04-page-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--or-outline); }
    .r04-page-heading h1 { margin: 0; font-size: 24px; line-height: 1.25; }
    .r04-page-heading p { margin: 6px 0 0; color: var(--or-text-muted); font-size: 13px; }
    .r04-page-action { min-height: 36px; padding: 8px 12px; border: 1px solid var(--or-outline-strong); border-radius: 6px; background: var(--or-surface); color: var(--or-text); cursor: pointer; }
    .r04-page-action:hover { border-color: var(--or-primary); color: var(--or-primary-dark); }
    .r04-research-list { display: grid; gap: 18px; min-width: 0; }
    .r04-research-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 12px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-research-filters input, .r04-research-filters select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-research-filters input { flex: 1 1 220px; min-width: 180px; }
    .r04-research-filters select { max-width: 180px; }
    .r04-research-filters input:focus, .r04-research-filters select:focus { border-color: var(--or-primary); outline: 0; }
    .r04-research-list-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 360px); gap: 18px; align-items: start; min-width: 0; }
    .r04-research-results { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-research-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-research-inspector { display: grid; gap: 14px; min-width: 0; padding: 18px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-research-inspector-inner { display: grid; gap: 14px; min-width: 0; }
    .r04-research-inspector-inner h2 { margin: 0; font-size: 18px; line-height: 1.35; }
    .r04-research-inspector-actions { display: grid; gap: 8px; }
    .r04-research-inspector-actions a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-research-inspector-actions a:hover { text-decoration: underline; }
    .r04-research-result-detail { display: grid; gap: 18px; min-width: 0; }
    .r04-research-result-header { display: grid; gap: 12px; }
    .r04-result-breadcrumb { display: flex; flex-wrap: wrap; gap: 6px; color: var(--or-text-muted); font-size: 12px; }
    .r04-result-breadcrumb a, .r04-result-meta a, .r04-result-tab-side > a, .r04-result-activity-layout > a { color: var(--or-primary-dark); text-decoration: none; }
    .r04-result-breadcrumb a:hover, .r04-result-meta a:hover, .r04-result-tab-side > a:hover, .r04-result-activity-layout > a:hover { text-decoration: underline; }
    .r04-result-heading-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .r04-result-heading-row h1 { margin: 0; color: var(--or-text); font-size: 28px; line-height: 1.3; }
    .r04-result-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; margin-top: 10px; color: var(--or-text-muted); font-size: 12px; }
    .r04-result-actions { display: flex; gap: 8px; flex: 0 0 auto; }
    .r04-result-tabs { display: flex; flex-wrap: wrap; gap: 4px; border-bottom: 1px solid var(--or-outline); }
    .r04-result-tabs a { padding: 11px 14px; border-bottom: 2px solid transparent; color: var(--or-text-muted); font-size: 13px; text-decoration: none; }
    .r04-result-tabs a:hover { background: var(--or-surface-muted); color: var(--or-text); }
    .r04-result-tabs a.is-active { border-bottom-color: var(--or-primary); color: var(--or-primary-dark); font-weight: 700; }
    .r04-result-tab-layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr); gap: 20px; align-items: start; min-width: 0; }
    .r04-result-tab-main, .r04-result-tab-side, .r04-result-activity-layout { display: grid; gap: 20px; min-width: 0; }
    .r04-result-paragraph { margin: 0; color: var(--or-text); line-height: 1.85; white-space: pre-wrap; }
    .r04-result-tab-main > .r04-detail-section, .r04-result-tab-side > .r04-detail-section { min-width: 0; }
    .r04-result-citation-list { display: grid; gap: 10px; }
    .r04-result-citation-list > div { display: grid; gap: 3px; padding-bottom: 10px; border-bottom: 1px solid var(--or-outline); }
    .r04-result-citation-list > div:last-child { border-bottom: 0; }
    .r04-result-citation-list a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-result-citation-list a:hover { text-decoration: underline; }
    .r04-result-citation-list small { color: var(--or-text-muted); font-size: 11px; }
    .r04-result-evidence-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
    .r04-result-evidence-filters select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-result-evidence-count { margin-left: auto; color: var(--or-text-muted); font-size: 12px; }
    .r04-result-evidence-results { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-result-evidence-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-result-evidence-results a { color: var(--or-primary-dark); text-decoration: none; }
    .r04-result-evidence-results a:hover { text-decoration: underline; }
    .r04-result-activity-layout { max-width: 1000px; }
    .r04-result-timeline { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-result-timeline > .r02-table-wrap { border: 0; border-radius: 0; }
    @media (max-width: 1000px) { .r04-result-tab-layout { grid-template-columns: 1fr; } }
    @media (max-width: 700px) { .r04-result-heading-row { flex-direction: column; } .r04-result-heading-row h1 { font-size: 22px; } .r04-result-evidence-count { margin-left: 0; width: 100%; } }
    .r04-keyword-page, .r04-watch-keyword-page, .r04-trend-page, .r04-graph-page { display: grid; gap: 18px; min-width: 0; }
    .r04-keyword-filter, .r04-watch-add-form, .r04-watch-filters, .r04-trend-controls, .r04-graph-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 12px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-keyword-filter input, .r04-keyword-filter select, .r04-watch-add-form input, .r04-watch-filters input, .r04-watch-filters select, .r04-trend-controls select, .r04-graph-controls select { min-height: 36px; border: 1px solid var(--or-outline-strong); border-radius: 6px; padding: 7px 10px; background: var(--or-surface); color: var(--or-text); }
    .r04-keyword-filter input, .r04-watch-filters input { flex: 1 1 200px; min-width: 160px; }
    .r04-watch-add-form input[name=keyword] { flex: 1 1 220px; min-width: 180px; }
    .r04-watch-add-form input[name=notes] { flex: 1 1 240px; min-width: 180px; }
    .r04-keyword-submit { min-height: 36px; padding: 7px 12px; border: 1px solid var(--or-primary); border-radius: 6px; background: var(--or-primary); color: #fff; font-weight: 700; cursor: pointer; }
    .r04-keyword-submit:hover { background: var(--or-primary-dark); }
    .r04-keyword-layout, .r04-watch-layout, .r04-trend-layout, .r04-graph-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 360px); gap: 18px; align-items: start; min-width: 0; }
    .r04-keyword-results, .r04-watch-results, .r04-keyword-inspector, .r04-watch-inspector, .r04-trend-main, .r04-trend-side, .r04-graph-canvas, .r04-graph-inspector { min-width: 0; display: grid; gap: 16px; }
    .r04-keyword-results, .r04-watch-results, .r04-keyword-inspector, .r04-watch-inspector, .r04-graph-canvas, .r04-graph-inspector { overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-keyword-results > .r02-table-wrap, .r04-watch-results > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-keyword-pager { padding: 12px 16px; border-top: 1px solid var(--or-outline); color: var(--or-text-muted); font-size: 12px; }
    .r04-keyword-inspector, .r04-watch-inspector { padding: 18px; }
    .r04-keyword-inspector-inner, .r04-watch-inspector-inner { display: grid; gap: 12px; min-width: 0; }
    .r04-keyword-inspector h2, .r04-watch-inspector h2 { margin: 0; font-size: 20px; }
    .r04-keyword-inspector p, .r04-watch-inspector p { margin: 0; color: var(--or-text-muted); font-size: 12px; }
    .r04-keyword-inspector-section, .r04-watch-inspector-section { display: grid; gap: 10px; padding-top: 14px; border-top: 1px solid var(--or-outline); }
    .r04-keyword-inspector-section h3, .r04-watch-inspector-section h3 { margin: 0; font-size: 14px; }
    .r04-keyword-inspector-section > a, .r04-watch-inspector-inner > a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-keyword-evidence-list { display: grid; gap: 9px; }
    .r04-keyword-evidence-list > div { display: grid; gap: 3px; padding-bottom: 9px; border-bottom: 1px solid var(--or-outline); }
    .r04-keyword-evidence-list a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-keyword-evidence-list div div, .r04-keyword-evidence-list > div > :not(a) { color: var(--or-text-muted); font-size: 11px; }
    .r04-mini-trend { display: flex; align-items: end; gap: 5px; height: 88px; padding: 8px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface-muted); }
    .r04-mini-trend span { flex: 1; min-height: 8px; border-radius: 3px 3px 0 0; background: var(--or-primary); opacity: .82; }
    .r04-trend-controls, .r04-graph-controls { justify-content: flex-start; }
    .r04-trend-controls > select:first-of-type, .r04-graph-controls > select:first-of-type { min-width: 220px; }
    .r04-trend-main > .r04-detail-section, .r04-trend-side > .r04-detail-section { min-width: 0; }
    .r04-trend-chart { display: block; width: 100%; min-height: 280px; padding: 8px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface-muted); }
    .r04-trend-grid-line { stroke: var(--or-outline); stroke-width: 1; opacity: .45; }
    .r04-trend-axis-label { fill: var(--or-text-muted); font-size: 10px; }
    .r04-trend-line { fill: none; stroke: var(--or-primary); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
    .r04-trend-point { fill: var(--or-surface); stroke: var(--or-primary); stroke-width: 3; }
    .r04-graph-controls { box-shadow: var(--or-shadow-1); }
    .r04-graph-canvas { padding: 14px; }
    .r04-graph-svg { display: block; width: 100%; min-height: 520px; border-radius: 6px; background: var(--or-surface-muted); }
    .r04-graph-edge { stroke: var(--or-outline-strong); stroke-width: 1.5; }
    .r04-graph-edge-label { fill: var(--or-text-muted); font-size: 10px; text-anchor: middle; }
    .r04-graph-center { fill: var(--or-primary); stroke: var(--or-primary-dark); stroke-width: 2; }
    .r04-graph-node { fill: var(--or-surface); stroke: var(--or-outline-strong); stroke-width: 2; }
    .r04-graph-node-label { fill: var(--or-text); font-size: 11px; }
    .r04-graph-inspector { padding: 18px; }
    .r04-graph-inspector > .r04-detail-section { min-width: 0; }
    @media (max-width: 1000px) { .r04-keyword-layout, .r04-watch-layout, .r04-trend-layout, .r04-graph-layout, .r04-research-list-layout { grid-template-columns: 1fr; } }
    @media (max-width: 700px) { .r04-page-heading { flex-direction: column; } .r04-keyword-filter, .r04-watch-add-form, .r04-watch-filters, .r04-trend-controls, .r04-graph-controls { align-items: stretch; } .r04-keyword-filter input, .r04-watch-filters input { min-width: 100%; } .r04-graph-svg { min-height: 360px; } }
    .r04-workbench { display: grid; gap: 20px; min-width: 0; }
    .r04-workbench-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .r04-workbench-heading h1 { margin: 0; font-size: 24px; line-height: 1.25; }
    .r04-workbench-heading p { margin: 6px 0 0; color: var(--or-text-muted); font-size: 13px; }
    .r04-workbench-refresh { min-height: 36px; padding: 8px 12px; border: 1px solid var(--or-outline-strong); border-radius: 6px; background: var(--or-surface); color: var(--or-text); }
    .r04-workbench-refresh:hover { border-color: var(--or-primary); color: var(--or-primary-dark); }
    .r04-workbench-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
    .r04-workbench-summary-card { display: grid; gap: 4px; padding: 16px 20px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); color: var(--or-text); text-decoration: none; }
    .r04-workbench-summary-card:hover { border-color: var(--or-primary); }
    .r04-workbench-summary-card > span { color: var(--or-text-muted); font-size: 12px; font-weight: 700; }
    .r04-workbench-summary-card > strong { font-size: 24px; line-height: 1; }
    .r04-workbench-summary-card > small { color: var(--or-text-muted); font-size: 12px; }
    .r04-workbench-summary-danger { border-color: var(--or-danger); }
    .r04-workbench-summary-danger > strong { color: var(--or-danger); }
    .r04-workbench-columns { display: grid; grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr); gap: 20px; align-items: start; }
    .r04-workbench-primary, .r04-workbench-secondary { display: grid; gap: 20px; min-width: 0; }
    .r04-workbench-section { min-width: 0; overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .r04-workbench-section-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 20px; border-bottom: 1px solid var(--or-outline); }
    .r04-workbench-section-header h2 { margin: 0; font-size: 16px; }
    .r04-workbench-section-header a { color: var(--or-primary-dark); font-size: 12px; text-decoration: none; }
    .r04-workbench-section-header a:hover { text-decoration: underline; }
    .r04-workbench-section > .r02-table-wrap { border: 0; border-radius: 0; }
    .r04-workbench-alerts, .r04-workbench-research { display: grid; gap: 12px; padding: 16px; }
    .r04-workbench-alert { display: grid; gap: 6px; padding: 12px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface-muted); }
    .r04-workbench-alert-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .r04-workbench-alert-title time { color: var(--or-text-muted); font-size: 11px; }
    .r04-workbench-alert strong { font-size: 13px; }
    .r04-workbench-alert p { margin: 0; color: var(--or-text-muted); font-size: 12px; line-height: 1.5; }
    .r04-workbench-alert a, .r04-workbench-research > a { color: var(--or-primary-dark); font-size: 12px; text-decoration: none; }
    .r04-workbench-alert a:hover, .r04-workbench-research > a:hover { text-decoration: underline; }
    .r04-workbench-latest-section { margin-bottom: 8px; }
    .r04-workbench-latest { display: grid; }
    .r04-workbench-latest article { display: grid; grid-template-columns: 112px minmax(0, 1fr) auto; gap: 12px; align-items: start; padding: 16px 20px; border-bottom: 1px solid var(--or-outline); }
    .r04-workbench-latest article:last-child { border-bottom: 0; }
    .r04-workbench-latest-meta, .r04-workbench-latest article > span { color: var(--or-text-muted); font-size: 11px; }
    .r04-workbench-latest-title { min-width: 0; overflow: hidden; color: var(--or-primary-dark); font-size: 13px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; text-decoration: none; }
    .r04-workbench-latest-title:hover { text-decoration: underline; }
    .r04-workbench-latest article p { grid-column: 2 / 3; margin: -4px 0 0; overflow: hidden; color: var(--or-text-muted); font-size: 12px; line-height: 1.5; text-overflow: ellipsis; white-space: nowrap; }
    @media (max-width: 1000px) { .r04-workbench-columns { grid-template-columns: 1fr; } }
    @media (max-width: 720px) { .r04-workbench-summary { grid-template-columns: 1fr; } .r04-workbench-heading { flex-direction: column; } .r04-workbench-latest article { grid-template-columns: 1fr; gap: 6px; } .r04-workbench-latest article p { grid-column: auto; white-space: normal; } }
    .r02-screen-content { display: grid; gap: 20px; }
    .r02-screen-intro h2 { margin: 0 0 5px; font-size: 21px; }
    .r02-screen-intro p { margin: 0; color: var(--r02-text-muted); }
    .r02-kpi-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; }
    .r02-kpi { display: grid; gap: 4px; text-decoration: none; color: inherit; }
    .r02-kpi:hover { border-color: var(--r02-primary); }
    .r02-kpi-value { font-size: 26px; letter-spacing: -.03em; }
    .r02-kpi-label { color: var(--r02-text-muted); font-size: 12px; font-weight: 700; }
    .r02-two-column, .r02-detail-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .r02-search-form, .r02-inline-form { display: flex; align-items: end; flex-wrap: wrap; gap: 12px; }
    .r02-search-form .r02-field-wrap { flex: 1 1 260px; }
    .r02-inline-form .r02-field-wrap { min-width: 180px; }
    .r02-detail-grid { display: grid; grid-template-columns: minmax(120px, .4fr) 1fr; gap: 8px 16px; margin: 0; }
    .r02-detail-grid dt { color: var(--r02-text-muted); font-size: 12px; font-weight: 700; }
    .r02-detail-grid dd { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    .r02-detail-summary .r02-card { min-width: 0; }
    @media (max-width: 1100px) { .r02-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
    @media (max-width: 720px) { .r02-kpi-grid, .r02-two-column, .r02-detail-summary { grid-template-columns: 1fr; } }
  `;
    document.head.appendChild(style);
}
