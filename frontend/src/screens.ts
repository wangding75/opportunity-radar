import { api, ApiError } from "./client.js";
import { routeFor, navigate, type RouteState, type ScreenId } from "./router.js";
import { appendActionRow, badge, button, capabilityUnavailableNotice, card, drawer, input, linkTo, modal, readOnlyNotice, select, settingsFrame, statePanel, table, tabs } from "./ui.js";

export type AuthSession = {label: string; role: string};
export type ScreenContext = {onSessionExpired: () => void; onForbidden?: () => void};
type Row = Record<string, any>;

export async function renderScreen(route: RouteState, session: AuthSession, context: ScreenContext): Promise<HTMLElement> {
  installScreenStyles();
  switch (route.screen) {
    case "P02": return renderDashboard(context);
    case "P03": return renderSearch(context);
    case "P04": return renderForbidden(route, session);
    case "P05": return renderNotFound(route);
    case "P26A": return renderLoginHelp();
    case "P06": return renderObservations(context);
    case "P07": return renderObservationDetail(route, context);
    case "P08": return renderKeywords(context);
    case "P09": return renderWatchKeywords(context);
    case "P10": return renderTrend(route, context);
    case "P11": return renderGraph(context);
    case "P12": return renderOpportunities(context);
    case "P13": return renderOpportunityDetail(route, context, "detail");
    case "P14": return renderOpportunityDetail(route, context, "analysis");
    case "P15": return renderResearch(context);
    case "P16": return renderOpportunityDetail(route, context, "research");
    case "P17": return renderOpportunityDetail(route, context, "result");
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

function content(title: string, subtitle: string): HTMLElement {
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

function append(host: HTMLElement, ...children: (Node | string)[]): void { host.append(...children); }

function errorState(error: unknown, context: ScreenContext, retry?: () => void): HTMLElement {
  if (error instanceof ApiError && error.status === 401) {
    context.onSessionExpired();
    return statePanel("permission", "Your session has expired. Please sign in again.");
  }
  if (error instanceof ApiError && error.status === 403) { context.onForbidden?.(); return statePanel("permission", "Your role does not have access to this screen."); }
  if (error instanceof ApiError && error.status === 429) return statePanel("rate-limit", error.message);
  return statePanel("error", error instanceof Error ? error.message : String(error), retry);
}

function formatDate(value: unknown): string {
  if (!value) return "—";
  const date = new Date(String(value));
  return Number.isNaN(date.valueOf()) ? String(value) : date.toLocaleString();
}

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function number(value: unknown, digits = 0): string {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : "—";
}

function kpi(label: string, value: unknown, href?: string): HTMLElement {
  const host = document.createElement(href ? "a" : "section");
  host.className = "r02-kpi r02-card";
  if (href) (host as HTMLAnchorElement).href = href;
  const valueEl = document.createElement("strong");
  valueEl.className = "r02-kpi-value";
  valueEl.textContent = number(value);
  const labelEl = document.createElement("span");
  labelEl.className = "r02-kpi-label";
  labelEl.textContent = label;
  host.append(valueEl, labelEl);
  return host;
}

async function renderDashboard(context: ScreenContext): Promise<HTMLElement> {
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
    if (dashboardResult.reason instanceof ApiError && dashboardResult.reason.status === 401) context.onSessionExpired();
    return host;
  }
  const data = dashboardResult.value as Row;
  const totals = data.totals ?? {};
  const summary = document.createElement("div");
  summary.className = "r04-workbench-summary";
  summary.append(
    workbenchSummary("重点机会", totals.starred_opportunities ?? totals.opportunities, "真实研究状态中标记的机会", "P12"),
    workbenchSummary("近 7 日情报", totals.observations_7d, "最近一周已采集证据", "P06"),
    workbenchSummary("运行异常", Number(totals.failed_collection_runs_24h ?? 0) + Number(totals.open_source_circuits ?? 0), "失败运行与熔断数据源", "P21", "danger"),
  );
  host.append(summary);

  const columns = document.createElement("div");
  columns.className = "r04-workbench-columns";
  const left = document.createElement("div");
  left.className = "r04-workbench-primary";
  const right = document.createElement("div");
  right.className = "r04-workbench-secondary";
  const opportunities = (Array.isArray(data.top_opportunities) ? data.top_opportunities : []).slice(0, 8);
  const opportunityRows = opportunities.map((row: Row) => [
    linkTo("P13", text(row.title), {id: row.id}),
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
    const alerts = Array.isArray(alertResult.value) ? alertResult.value as Row[] : [];
    if (alerts.length) for (const row of alerts.slice(0, 5)) {
      const item = document.createElement("article");
      item.className = "r04-workbench-alert";
      const titleRow = document.createElement("div");
      titleRow.className = "r04-workbench-alert-title";
      titleRow.append(badge(alertType(row), row.priority === "CRITICAL" ? "danger" : "warning"));
      const when = document.createElement("time"); when.textContent = formatDate(row.created_at); titleRow.append(when);
      const name = document.createElement("strong"); name.textContent = text(row.title, "未命名告警");
      const message = document.createElement("p"); message.textContent = text(row.message, "该告警未提供补充说明。");
      const target = alertTarget(row); const link = document.createElement("a"); link.href = target.href; link.textContent = target.label;
      item.append(titleRow, name, message, link); alertBody.append(item);
    } else alertBody.append(statePanel("empty", "当前没有待处理告警。"));
  } else alertBody.append(statePanel("partial", "告警接口暂时不可用；其余工作台数据仍可查看。"));
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
    const rows = ((observationsResult.value as Row)?.items ?? []) as Row[];
    if (rows.length) for (const row of rows.slice(0, 5)) {
      const item = document.createElement("article");
      const meta = document.createElement("div"); meta.className = "r04-workbench-latest-meta"; meta.textContent = formatDate(row.observed_at);
      const link = linkTo("P07", text(row.title), {id: row.id}); link.className = "r04-workbench-latest-title";
      const copy = document.createElement("p"); copy.textContent = text(row.text, "该情报未提供摘要。");
      const source = document.createElement("span"); source.textContent = `来源：${text(row.source_id)}`;
      item.append(meta, link, copy, source); latestBody.append(item);
    } else latestBody.append(statePanel("empty", "当前没有已采集的最新情报。"));
  } else latestBody.append(statePanel("partial", "情报接口暂时不可用；请从情报工作台重试。"));
  host.append(workbenchSection("最新情报变化", linkTo("P06", "进入情报工作台"), latestBody, "r04-workbench-latest-section"));
  return host;
}

function workbenchSummary(labelValue: string, value: unknown, meta: string, screen: ScreenId, tone: "normal" | "danger" = "normal"): HTMLElement {
  const link = linkTo(screen, "", {}); link.className = `r04-workbench-summary-card r04-workbench-summary-${tone}`;
  const label = document.createElement("span"); label.textContent = labelValue;
  const numberValue = document.createElement("strong"); numberValue.textContent = number(value);
  const copy = document.createElement("small"); copy.textContent = meta;
  link.append(label, numberValue, copy); return link;
}

function workbenchSection(titleValue: string, action: HTMLElement, body: HTMLElement, className = ""): HTMLElement {
  const section = document.createElement("section"); section.className = `r04-workbench-section ${className}`.trim();
  const header = document.createElement("header"); header.className = "r04-workbench-section-header";
  const title = document.createElement("h2"); title.textContent = titleValue; header.append(title, action);
  section.append(header, body); return section;
}

function stageLabel(value: unknown): string { return ({DISCOVERY: "发现", EARLY_GROWTH: "早期增长", PRODUCTIZING: "产品化", COMMERCIALIZING: "商业化", DORMANT: "休眠"} as Record<string, string>)[String(value)] ?? text(value); }

async function renderSearch(context: ScreenContext): Promise<HTMLElement> {
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
  const categories: Array<[string, string]> = [["all", "全部"], ["opportunities", "机会"], ["observations", "情报"], ["keywords", "关键词"]];
  const renderTabs = (): void => {
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
  if (initial) void runSearch(initial, activeCategory, results, context);
  else results.append(statePanel("ready", "输入查询词后搜索真实业务记录。"));
  return host;
}

async function runSearch(query: string, category: string, results: HTMLElement, context: ScreenContext): Promise<void> {
  results.replaceChildren(statePanel("loading", "正在搜索真实记录…"));
  if (!query) { results.replaceChildren(statePanel("empty", "请输入查询词后再搜索。")); return; }
  const jobs: Array<Promise<unknown>> = [];
  if (category === "all" || category === "opportunities") jobs.push(api(`/api/v1/opportunities/page?q=${encodeURIComponent(query)}&limit=50`));
  if (category === "all" || category === "observations") jobs.push(api(`/api/v1/observations?q=${encodeURIComponent(query)}&limit=50`));
  if (category === "all" || category === "keywords") jobs.push(api("/api/v1/keywords?limit=500"));
  const settled = await Promise.allSettled(jobs);
  const failed = settled.find((item) => item.status === "rejected");
  if (settled.length > 0 && settled.every((item) => item.status === "rejected")) {
    results.replaceChildren(statePanel("error", "搜索接口暂时不可用，请稍后重试。", () => void runSearch(query, category, results, context)));
    if (failed && failed.status === "rejected" && failed.reason instanceof ApiError && failed.reason.status === 401) context.onSessionExpired();
    return;
  }
  const records: HTMLElement[] = [];
  let index = 0;
  if (category === "all" || category === "opportunities") {
    const value = settled[index++];
    if (value.status === "fulfilled") for (const row of (value.value as Row)?.items ?? []) records.push(searchResultCard("机会", "success", text(row.opportunity_key ?? row.id), text(row.title), text(row.summary), `评分 ${number(row.score, 1)} · ${text(row.stage)}`, routeFor("P13", {id: row.id})));
  }
  if (category === "all" || category === "observations") {
    const value = settled[index++];
    if (value.status === "fulfilled") for (const row of (value.value as Row)?.items ?? []) records.push(searchResultCard("情报", "info", text(row.source_id), text(row.title), text(row.text), `观察时间 ${formatDate(row.observed_at)}`, routeFor("P07", {id: row.id})));
  }
  if (category === "all" || category === "keywords") {
    const value = settled[index++];
    if (value.status === "fulfilled") for (const row of ((value.value as Row[]) ?? []).filter((item: Row) => `${item.keyword ?? item.display_name ?? ""} ${item.canonical ?? ""}`.toLowerCase().includes(query.toLowerCase()))) records.push(searchResultCard("关键词", "warning", text(row.id), text(row.keyword ?? row.display_name), `状态：${text(row.status)}`, `得分 ${number(row.score, 1)} · 观察数 ${text(row.observation_count)}`, routeFor("P10", {keyword_id: row.id})));
  }
  const summary = document.createElement("p");
  summary.className = "r04-search-summary";
  summary.textContent = `找到 ${records.length} 个相关结果`;
  results.replaceChildren(summary);
  if (!records.length) results.append(statePanel("empty", `没有找到与“${query}”匹配的真实记录。`));
  else { const list = document.createElement("div"); list.className = "r04-search-list"; list.append(...records); results.append(list); }
  if (failed) results.prepend(statePanel("partial", "部分搜索分类暂时不可用；当前结果仍来自真实接口。"));
}

function searchResultCard(type: string, tone: "success" | "info" | "warning", id: string, titleValue: string, description: string, meta: string, href: string): HTMLElement {
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

function renderLoginHelp(): HTMLElement {
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
  sections.append(
    helpSection("账户恢复方式", ["管理员协助处理。"]),
    helpSection("可能原因", ["密码错误", "账户锁定", "MFA 问题", "认证服务不可用"]),
  );
  const info = document.createElement("section");
  info.className = "r04-help-info";
  const infoTitle = document.createElement("h2");
  infoTitle.textContent = "需要提供给管理员的信息";
  const infoList = document.createElement("ul");
  for (const value of ["用户名/邮箱", "发生时间", "错误提示"]) { const item = document.createElement("li"); item.textContent = value; infoList.append(item); }
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

function helpSection(titleValue: string, values: string[]): HTMLElement {
  const section = document.createElement("section");
  section.className = "r04-help-section";
  const title = document.createElement("h2");
  title.textContent = titleValue;
  const list = document.createElement("ul");
  for (const value of values) { const item = document.createElement("li"); item.textContent = value; list.append(item); }
  section.append(title, list);
  return section;
}

export function renderNotificationDrawer(context: ScreenContext): HTMLElement {
  const utility = createUtilityDrawer("通知", "最近需要关注的系统与业务变化");
  const loading = statePanel("loading", "正在读取告警事件…");
  utility.body.append(loading);
  const allAlerts = linkTo("P24", "查看全部告警");
  const runs = linkTo("P21", "查看运行记录");
  utility.footer.append(allAlerts, runs);
  void loadNotificationEvents(utility.body, context);
  return utility.overlay;
}

async function loadNotificationEvents(body: HTMLElement, context: ScreenContext): Promise<void> {
  try {
    const rows = await api("/api/v1/alerts/events?limit=20");
    body.replaceChildren();
    if (!Array.isArray(rows) || !rows.length) { body.append(statePanel("empty", "当前没有可读取的告警事件。")); return; }
    const list = document.createElement("div");
    list.className = "r04-notification-list";
    for (const row of rows as Row[]) {
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
  } catch (error) {
    body.replaceChildren();
    if (error instanceof ApiError && error.status === 401) context.onSessionExpired();
    body.append(statePanel("error", "通知数据暂时不可用。", () => void loadNotificationEvents(body, context)));
  }
}

function alertType(row: Row): string {
  if (row.priority === "CRITICAL") return "关键告警";
  if (row.opportunity_id) return "机会变化";
  if (row.keyword_id) return "关键词告警";
  return "系统告警";
}

function alertStatusLabel(value: unknown): string {
  return ({NEW: "新建", ACKNOWLEDGED: "已确认", DISMISSED: "已忽略", RESOLVED: "已解决"} as Record<string, string>)[String(value)] ?? text(value);
}

function alertTarget(row: Row): {href: string; label: string} {
  if (row.opportunity_id) return {href: routeFor("P13", {id: row.opportunity_id}), label: "查看机会"};
  if (row.keyword_id) return {href: routeFor("P10", {keyword_id: row.keyword_id}), label: "查看关键词"};
  return {href: routeFor("P24"), label: "查看告警详情"};
}

export function renderHelpDrawer(route: RouteState): HTMLElement {
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
  utility.footer.append(linkTo("P30", "查看系统诊断"), linkTo("P28", "查看账户与安全"), linkTo("P04", "403 权限说明", {requested: window.location.pathname}));
  return utility.overlay;
}

function createUtilityDrawer(titleValue: string, subtitleValue: string): {overlay: HTMLElement; body: HTMLElement; footer: HTMLElement} {
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
  const dismiss = (): void => overlay.remove();
  close.addEventListener("click", dismiss);
  scrim.addEventListener("click", dismiss);
  overlay.addEventListener("keydown", (event) => { if (event.key === "Escape") dismiss(); });
  panel.append(header, body, footer);
  overlay.append(scrim, panel);
  return {overlay, body, footer};
}

function arrow(): HTMLElement { const span = document.createElement("span"); span.className = "r04-help-arrow"; span.textContent = "→"; return span; }
function pathLabel(value: string): HTMLElement { const span = document.createElement("strong"); span.className = "r04-help-path-label"; span.textContent = `${value}：`; return span; }
function glossaryItem(titleValue: string, copyValue: string): HTMLElement { const item = document.createElement("div"); item.className = "r04-help-glossary-item"; const title = document.createElement("strong"); title.textContent = titleValue; const copy = document.createElement("p"); copy.textContent = copyValue; item.append(title, copy); return item; }
function pageLabel(screen: ScreenId): string { return ({P02: "工作台", P03: "全局搜索", P06: "最新情报", P12: "机会", P13: "机会详情", P18: "数据源", P21: "运行记录", P24: "告警"} as Record<string, string>)[screen] ?? "当前页面"; }

function renderForbidden(route: RouteState, session: AuthSession): HTMLElement {
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
  primaryActions.append(
    button("返回上一页", {variant: "primary", onClick: () => goBackOr("P02")}),
    button("返回工作台", {variant: "secondary", onClick: () => navigate("P02")}),
  );
  const account = linkTo("P28", "查看个人账户与安全");
  account.className = "r04-error-link";
  card.append(icon, code, title, copy, meta, primaryActions, account);
  host.append(card);
  return host;
}

function renderNotFound(route: RouteState): HTMLElement {
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
  actions.append(
    button("返回上一页", {variant: "primary", onClick: () => goBackOr("P02")}),
    button("全局搜索", {variant: "secondary", onClick: () => navigate("P03")}),
    button("返回工作台", {variant: "secondary", onClick: () => navigate("P02")}),
  );
  const opportunities = linkTo("P12", "查看机会列表");
  opportunities.className = "r04-error-link";
  card.append(code, title, copy, meta, actions, opportunities);
  page.append(card);
  return page;
}

function appendMeta(parent: HTMLElement, labelValue: string, value: string): void {
  const dt = document.createElement("dt"); dt.textContent = labelValue;
  const dd = document.createElement("dd"); dd.textContent = value;
  parent.append(dt, dd);
}

function objectIdFromPath(path: string): string {
  const value = path.split("/").filter(Boolean).pop();
  return value || "—";
}

function roleLabel(role: string): string {
  return ({VIEWER: "查看者", OPERATOR: "操作员", ADMIN: "管理员", OWNER: "所有者"} as Record<string, string>)[role] ?? role;
}

function goBackOr(fallback: ScreenId): void {
  if (window.history.length > 1) window.history.back();
  else navigate(fallback);
}

async function renderObservations(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Observations", "Raw evidence collected from registered sources, with provenance and acquisition metadata.");
  const filters = document.createElement("form"); filters.className = "r02-inline-form";
  const qWrap = input("Content keyword", {placeholder: "title, text, or query"});
  const sourceWrap = input("Source id", {placeholder: "optional"});
  const typeWrap = select("Item type", ["", "NEWS", "JOB", "PRODUCT", "REPOSITORY", "TREND"], "");
  const q = qWrap.querySelector<HTMLInputElement>("input"); const source = sourceWrap.querySelector<HTMLInputElement>("input"); const type = typeWrap.querySelector<HTMLSelectElement>("select");
  const submit = button("Apply filters", {variant: "primary", type: "submit"}); appendActionRow(filters, submit); filters.prepend(qWrap, sourceWrap, typeWrap);
  const results = document.createElement("div");
  const load = async (offset: number): Promise<void> => {
    results.replaceChildren(statePanel("loading", "Loading observations…"));
    const params = new URLSearchParams({limit: "50", offset: String(offset)}); if (q?.value.trim()) params.set("q", q.value.trim()); if (source?.value.trim()) params.set("source_id", source.value.trim()); if (type?.value) params.set("item_type", type.value);
    try {
      const data = await api(`/api/v1/observations?${params.toString()}`);
      const rows = (data.items ?? []).map((row: Row) => [linkTo("P07", text(row.title), {id: row.id, q: row.title, source_id: row.source_id}), text(row.source_id), text(row.item_type), badge(text(row.evidence_quality), row.evidence_quality === "A" ? "success" : "neutral"), formatDate(row.observed_at)]);
      const body = rows.length ? table(["Observation", "Source", "Type", "Quality", "Observed"], rows) : statePanel("empty", q?.value ? "No observations match the current filters." : "No observations have been collected yet.");
      results.replaceChildren(body);
      const pager = document.createElement("div"); pager.className = "r02-pagination"; pager.append(button("Previous", {disabled: offset <= 0, onClick: () => void load(Math.max(0, offset - 50))}), document.createTextNode(`Offset ${offset}`), button("Next", {disabled: !data.has_more, onClick: () => void load(offset + 50)})); results.append(pager);
    } catch (error) { results.replaceChildren(errorState(error, context, () => void load(offset))); }
  };
  filters.addEventListener("submit", (event) => { event.preventDefault(); void load(0); });
  append(host, filters, results); await load(0); return host;
}

async function renderObservationDetail(route: RouteState, context: ScreenContext): Promise<HTMLElement> {
  const id = route.params.get("id");
  const host = content("Observation detail", "A source observation with its evidence text and provenance.");
  if (!id) { append(host, statePanel("error", "Observation id is missing.")); return host; }
  try {
    const detailParams = new URLSearchParams({limit: "500"});
    if (route.params.get("q")) detailParams.set("q", route.params.get("q")!);
    if (route.params.get("source_id")) detailParams.set("source_id", route.params.get("source_id")!);
    const data = await api(`/api/v1/observations?${detailParams.toString()}`);
    const row = (data.items ?? []).find((item: Row) => String(item.id) === id);
    if (!row) { append(host, objectNotFound("Observation", id)); return host; }
    const details = document.createElement("dl"); details.className = "r02-detail-grid";
    for (const [label, value] of [["Title", row.title], ["Source", row.source_id], ["Type", row.item_type], ["Query", row.query], ["Quality", row.evidence_quality], ["Acquisition", row.acquisition_method], ["Observed", formatDate(row.observed_at)]]) { const dt = document.createElement("dt"); dt.textContent = label; const dd = document.createElement("dd"); dd.textContent = text(value); details.append(dt, dd); }
    const evidence = card("Evidence text", document.createElement("p")); evidence.querySelector("p")!.textContent = text(row.text);
    const actions = document.createElement("div"); appendActionRow(actions, button("Back to observations", {onClick: () => navigate("P06")}));
    append(host, card("Observation metadata", details), evidence, actions);
  } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderKeywords(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Keyword discovery", "Ranked keywords derived from observed evidence.");
  try {
    const rows = await api("/api/v1/keywords?limit=500");
    const tableRows = (rows ?? []).map((row: Row) => [linkTo("P10", text(row.keyword), {keyword_id: row.id}), badge(text(row.status), row.status === "TRENDING" ? "success" : "neutral"), number(row.score, 1), text(row.observation_count), text(row.source_count), formatDate(row.last_seen_at)]);
    append(host, tableRows.length ? table(["Keyword", "Status", "Score", "Observations", "Sources", "Last seen"], tableRows) : statePanel("empty", "No keywords have been derived yet."));
  } catch (error) { append(host, errorState(error, context, () => navigate("P08"))); }
  return host;
}

async function renderWatchKeywords(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Watch keywords", "Manage the seed keywords used by the existing probe planner.");
  const form = document.createElement("form"); form.className = "r02-inline-form";
  const keywordWrap = input("Keyword", {placeholder: "at least 2 characters"}); const notesWrap = input("Notes", {placeholder: "optional"});
  const keyword = keywordWrap.querySelector<HTMLInputElement>("input"); const notes = notesWrap.querySelector<HTMLInputElement>("input");
  const submit = button("Add watch keyword", {variant: "primary", type: "submit"}); appendActionRow(form, submit); form.prepend(keywordWrap, notesWrap);
  const list = document.createElement("div");
  form.addEventListener("submit", async (event) => { event.preventDefault(); submit.disabled = true; try { await api("/api/v1/watch-keywords", {method: "POST", body: JSON.stringify({keyword: keyword?.value ?? "", notes: notes?.value ?? "", priority: 3})}); form.reset(); await loadWatchKeywords(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } finally { submit.disabled = false; } });
  append(host, form, list); await loadWatchKeywords(list, context); return host;
}

async function loadWatchKeywords(list: HTMLElement, context: ScreenContext): Promise<void> {
  try {
    const rows = await api("/api/v1/watch-keywords");
    const tableRows = (rows ?? []).map((row: Row) => { const toggle = button(row.enabled ? "Disable" : "Enable", {variant: "ghost", onClick: async () => { toggle.disabled = true; try { await api(`/api/v1/watch-keywords/${row.id}`, {method: "PATCH", body: JSON.stringify({enabled: !row.enabled})}); await loadWatchKeywords(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } }}); return [text(row.keyword), row.enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.priority), text(row.notes), toggle]; });
    list.replaceChildren(tableRows.length ? table(["Keyword", "State", "Priority", "Notes", "Action"], tableRows) : statePanel("empty", "No watch keywords configured."));
  } catch (error) { list.replaceChildren(errorState(error, context)); }
}

async function renderTrend(route: RouteState, context: ScreenContext): Promise<HTMLElement> {
  const keywordId = route.params.get("keyword_id");
  const host = content("Keyword trend", "Trend summaries are read from the persisted keyword trend service.");
  if (!keywordId) { append(host, statePanel("ready", "Choose a keyword from discovery to inspect its trend."), linkTo("P08", "Browse keyword discovery")); return host; }
  try {
    const data = await api(`/api/v1/keywords/${encodeURIComponent(keywordId)}/trend`);
    const summary = card(`Trend for ${text(data.keyword, keywordId)}`, table(["Window", "Observations", "Growth"], [["7d", text(data.windows?.["7d"]), formatGrowth(data.growth?.["7d"])], ["30d", text(data.windows?.["30d"]), formatGrowth(data.growth?.["30d"])], ["90d", text(data.windows?.["90d"]), "—"]]));
    const points = (data.points ?? []).map((row: Row) => [text(row.day), text(row.observations), text(row.sources)]);
    append(host, summary, card("Daily points", points.length ? table(["Day", "Observations", "Sources"], points) : statePanel("empty", "No daily trend points are available.")));
  }
  catch (error) { append(host, errorState(error, context)); }
  return host;
}

function formatGrowth(value: unknown): string { const n = Number(value); return Number.isFinite(n) ? `${n >= 0 ? "+" : ""}${(n * 100).toFixed(1)}%` : "—"; }

async function renderGraph(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Keyword graph", "Related keyword edges returned by the graph service. Select a node to inspect its live relationships.");
  try {
    const data = await api("/api/v1/keyword-graph?limit=200&since_days=90"); const nodes = data.nodes ?? []; const edges = data.edges ?? [];
    const nodeRows = nodes.map((row: Row) => { const inspect = button("Inspect", {variant: "ghost", onClick: () => { const related = edges.filter((edge: Row) => String(edge.source) === String(row.id) || String(edge.target) === String(row.id)); const body = table(["Connected node", "Weight", "Last seen"], related.map((edge: Row) => [text(String(edge.source) === String(row.id) ? edge.target : edge.source), number(edge.weight, 1), formatDate(edge.last_seen_at)])); host.append(drawer(`Node: ${text(row.keyword)}`, body)); }}); return [text(row.keyword), text(row.id), inspect]; });
    append(host, card("Graph summary", table(["Metric", "Count"], [["Nodes", text(nodes.length)], ["Edges", text(edges.length)]])), nodeRows.length ? table(["Keyword node", "Id", "Detail"], nodeRows) : statePanel("empty", "No keyword relationships are available."));
  } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderOpportunities(context: ScreenContext): Promise<HTMLElement> {
  const host = document.createElement("div"); host.className = "r04-opportunity-list";
  const heading = document.createElement("div"); heading.className = "r04-opportunity-heading";
  const title = document.createElement("h1"); title.textContent = "机会";
  const subtitle = document.createElement("p"); subtitle.textContent = "按价值、证据与时效性查看系统识别出的机会";
  heading.append(title, subtitle); host.append(heading);
  const filters = document.createElement("form"); filters.className = "r04-opportunity-filters";
  const query = document.createElement("input"); query.type = "search"; query.name = "q"; query.placeholder = "搜索机会"; query.setAttribute("aria-label", "搜索机会");
  const stage = document.createElement("select"); stage.setAttribute("aria-label", "机会阶段"); addOption(stage, "", "阶段：所有"); addOption(stage, "DISCOVERY", "发现"); addOption(stage, "EARLY_GROWTH", "早期增长"); addOption(stage, "PRODUCTIZING", "产品化"); addOption(stage, "COMMERCIALIZING", "商业化"); addOption(stage, "DORMANT", "休眠");
  const minScore = document.createElement("select"); minScore.setAttribute("aria-label", "最低评分"); addOption(minScore, "0", "评分：所有"); addOption(minScore, "70", "70 分以上"); addOption(minScore, "90", "90 分以上");
  const research = document.createElement("select"); research.setAttribute("aria-label", "研究状态"); addOption(research, "", "研究：所有"); addOption(research, "NEW", "未处理"); addOption(research, "TRIAGED", "已分诊"); addOption(research, "TRACKING", "跟踪中"); addOption(research, "DONE", "已完成"); addOption(research, "DISMISSED", "已忽略");
  const starred = document.createElement("label"); starred.className = "r04-opportunity-checkbox"; const starredInput = document.createElement("input"); starredInput.type = "checkbox"; starredInput.name = "starred"; starred.append(starredInput, document.createTextNode("仅重点"));
  const submit = document.createElement("button"); submit.type = "submit"; submit.className = "r04-opportunity-submit"; submit.textContent = "筛选";
  const clear = document.createElement("button"); clear.type = "button"; clear.className = "r04-opportunity-clear"; clear.textContent = "清除";
  filters.append(query, stage, minScore, research, starred, submit, clear);
  const scopeNotice = readOnlyNotice("阶段写入接口未向用户安全暴露；列表中的阶段和研究状态均来自真实后端，只读展示。", "机会列表读取与权限说明");
  const results = document.createElement("div"); results.className = "r04-opportunity-results";
  let cursorStack: string[] = [];
  const load = async (cursor?: string): Promise<void> => {
    results.replaceChildren(statePanel("loading", "正在读取机会…"));
    const params = new URLSearchParams({limit: "50", include_dormant: stage.value === "DORMANT" ? "true" : "false"});
    if (cursor) params.set("cursor", cursor); if (query.value.trim()) params.set("q", query.value.trim()); if (stage.value && stage.value !== "DORMANT") params.set("stage", stage.value); if (minScore.value !== "0") params.set("min_score", minScore.value); if (research.value) params.set("research_status", research.value); if (starredInput.checked) params.set("starred", "true");
    try {
      const data = await api(`/api/v1/opportunities/page?${params.toString()}`);
      const rows = (data.items ?? []).map((row: Row) => [linkTo("P13", text(row.title), {id: row.id}), text(row.opportunity_key ?? row.id), scoreBadge(row.score), number(row.risk_score, 1), stageLabel(row.stage), text(row.evidence_count, "0"), badge(researchLabel(row.research?.status), row.research?.status === "TRACKING" || row.research?.status === "DONE" ? "success" : "neutral"), formatDate(row.last_seen_at)]);
      results.replaceChildren(rows.length ? table(["机会", "ID", "评分", "风险", "阶段", "证据数", "研究状态", "更新时间"], rows) : statePanel("empty", query.value ? "没有匹配当前筛选条件的机会。" : "当前没有可显示的机会。"));
      const pager = document.createElement("div"); pager.className = "r04-opportunity-pager";
      const previous = document.createElement("button"); previous.type = "button"; previous.textContent = "上一页"; previous.disabled = !cursorStack.length; previous.addEventListener("click", () => { const previousCursor = cursorStack.pop(); void load(previousCursor); });
      const pageText = document.createElement("span"); pageText.textContent = `${rows.length} 条记录${data.has_more ? " · 还有更多" : ""}`;
      const next = document.createElement("button"); next.type = "button"; next.textContent = "下一页"; next.disabled = !data.next_cursor; next.addEventListener("click", () => { if (data.next_cursor) { cursorStack.push(cursor ?? ""); void load(data.next_cursor); } });
      pager.append(previous, pageText, next); results.append(pager);
    } catch (error) { results.replaceChildren(errorState(error, context, () => void load(cursor))); }
  };
  filters.addEventListener("submit", (event) => { event.preventDefault(); cursorStack = []; void load(); });
  clear.addEventListener("click", () => { filters.reset(); cursorStack = []; void load(); });
  host.append(filters, scopeNotice, results); await load(); return host;
}

async function renderOpportunityOverview(route: RouteState, context: ScreenContext, id: string): Promise<HTMLElement> {
  const host = document.createElement("div"); host.className = "r04-opportunity-detail";
  try {
    const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}`);
    const header = document.createElement("header"); header.className = "r04-entity-header";
    const crumb = document.createElement("div"); crumb.className = "r04-entity-crumb"; crumb.append(linkTo("P12", "机会"), document.createTextNode(" / "), document.createTextNode(text(data.opportunity_key ?? id)));
    const title = document.createElement("h1"); title.textContent = text(data.title, "未命名机会");
    const chips = document.createElement("div"); chips.className = "r04-entity-chips"; chips.append(scoreBadge(data.score), badge(`阶段：${stageLabel(data.stage)}`, "info"), badge(`风险：${number(data.risk_score, 1)}`, "neutral"), badge(`研究：${researchLabel(data.research?.status)}`, "neutral"));
    const dates = document.createElement("p"); dates.className = "r04-entity-dates"; dates.textContent = `首次发现：${formatDate(data.first_seen_at)} · 最近更新：${formatDate(data.last_seen_at)}`;
    header.append(crumb, title, chips, dates);
    const tabs = document.createElement("nav"); tabs.className = "r04-entity-tabs"; tabs.setAttribute("aria-label", "机会详情导航");
    const activeTab = route.params.get("tab") ?? "overview";
    for (const [tab, label] of [["overview", "概览"], ["evidence", "证据"], ["analysis", "分析与研究"], ["history", "历史"]] as Array<[string, string]>) { const link = linkTo("P13", label, {id, tab}); link.className = activeTab === tab ? "is-active" : ""; link.setAttribute("aria-current", activeTab === tab ? "page" : "false"); tabs.append(link); }
    const grid = document.createElement("div"); grid.className = "r04-detail-grid-r04";
    const main = document.createElement("main"); main.className = "r04-detail-main";
    const summary = document.createElement("p"); summary.className = "r04-detail-summary-copy"; summary.textContent = text(data.analysis?.summary, "当前后端尚未返回可展示的机会摘要。");
    main.append(detailSectionWithBody("机会摘要", summary));
    const scoreRows = Object.entries(data.scores ?? {}).map(([key, value]) => [scoreLabel(key), number(value, 1)]);
    main.append(detailSectionWithBody("评分构成", scoreRows.length ? table(["维度", "分值"], scoreRows) : statePanel("empty", "暂无评分构成数据。")));
    const keywordRows = (data.keywords ?? []).map((row: Row) => [linkTo("P10", text(row.keyword), {keyword_id: row.id}), text(row.role), number(row.weight, 1)]);
    main.append(detailSectionWithBody("关联关键词", keywordRows.length ? table(["关键词", "角色", "权重"], keywordRows) : statePanel("empty", "暂无关联关键词。")));
    const side = document.createElement("aside"); side.className = "r04-detail-side";
    side.append(detailSectionWithBody("关键来源", sourceList(data.evidence ?? [])));
    side.append(detailSectionWithBody("已有研究", detailList([["状态", researchLabel(data.research?.status)], ["优先级", data.research?.priority], ["更新时间", formatDate(data.research?.updated_at)]])));
    side.append(capabilityUnavailableNotice("后端未暴露机会生命周期历史接口；这里只读展示首次发现和最近更新时间，不拼装虚假的变更时间线。", "历史记录暂不可用"));
    grid.append(main, side);
    host.append(readOnlyNotice("当前后端未开放安全的机会阶段状态变更接口，本页状态仅供查看。", "机会状态只读"), header, tabs, grid);
  } catch (error) { host.append(error instanceof ApiError && error.status === 404 ? objectNotFound("机会", id) : errorState(error, context)); }
  return host;
}

async function renderOpportunityDetail(route: RouteState, context: ScreenContext, mode: "detail" | "analysis" | "research" | "result"): Promise<HTMLElement> {
  const id = route.params.get("id");
  if (!id) { const missing = document.createElement("div"); missing.className = "r04-opportunity-detail"; missing.append(statePanel("error", "机会 ID 缺失。")); return missing; }
  if (mode === "detail") return renderOpportunityOverview(route, context, id);
  const title = mode === "analysis" ? "Structured analysis" : mode === "research" ? "Research workflow" : mode === "result" ? "Research result" : "Opportunity detail";
  const host = content(title, "Live opportunity detail, score breakdown, evidence citations, and research state.");
  if (!id) { append(host, statePanel("error", "Opportunity id is missing.")); return host; }
  try {
    const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}`);
    const summary = document.createElement("div"); summary.className = "r02-detail-summary";
    append(summary, card("Opportunity", detailList([["Title", data.title], ["Stage", data.stage], ["Score", number(data.score, 1)], ["Risk", number(data.risk_score, 1)], ["Analysis", data.analysis?.status], ["Research", data.research?.status]])), card("Scores", detailList(Object.entries(data.scores ?? {}).map(([key, value]) => [key, number(value, 1)]))));
    const actions = document.createElement("div");
    if (mode === "research" || mode === "result") appendActionRow(actions, button("Open analysis", {onClick: () => navigate("P14", {id})}), button("Open research", {onClick: () => navigate("P16", {id})}), button("Open research result", {onClick: () => navigate("P17", {id})}));
    if (mode !== "analysis") appendActionRow(actions, button("Back to opportunities", {onClick: () => navigate("P12")}));
    const researchForm = document.createElement("form"); researchForm.className = "r02-inline-form";
    const statusWrap = select("Research status", ["NEW", "TRIAGED", "TRACKING", "DONE", "DISMISSED"], text(data.research?.status, "NEW")); const priorityWrap = input("Priority", {type: "number", value: text(data.research?.priority, "0")}); const notesWrap = input("Notes", {value: text(data.research?.notes, "")});
    const save = button("Save research state", {variant: "primary", type: "submit"}); appendActionRow(researchForm, save); researchForm.prepend(statusWrap, priorityWrap, notesWrap);
    researchForm.addEventListener("submit", async (event) => { event.preventDefault(); save.disabled = true; try { await api(`/api/v1/opportunities/${id}/research`, {method: "PATCH", body: JSON.stringify({status: statusWrap.querySelector<HTMLSelectElement>("select")?.value, priority: Number(priorityWrap.querySelector<HTMLInputElement>("input")?.value ?? 0), notes: notesWrap.querySelector<HTMLInputElement>("input")?.value ?? ""})}); save.textContent = "Saved"; } catch (error) { researchForm.append(errorState(error, context)); } finally { save.disabled = false; } });
    const evidenceRows = (data.evidence ?? []).map((row: Row) => [badge(text(row.type), "info"), text(row.source), text(row.title), text(row.quality), formatDate(row.observed_at), row.url ? externalLink(row.url) : "—"]);
    const citationRows = (data.analysis?.citations ?? []).map((row: Row) => [text(row.evidence_id), text(row.source), text(row.title), text(row.type)]);
    append(host, summary, actions, mode === "analysis" ? card("Analysis", detailList(Object.entries(data.analysis ?? {}).filter(([key]) => !["citations", "conflict"].includes(key)).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : text(value)]))) : card("Analysis summary", detailList([["Summary", data.analysis?.summary], ["Target user", data.analysis?.target_user], ["Business model", data.analysis?.business_model], ["Monetization", data.analysis?.monetization], ["Risk notes", data.analysis?.risk_notes]])), mode === "result" ? card("Research result trace", citationRows.length ? table(["Evidence id", "Source", "Title", "Type"], citationRows) : statePanel("empty", "No persisted analysis citations are available.")) : card("Related keywords", table(["Keyword", "Role", "Weight"], (data.keywords ?? []).map((row: Row) => [text(row.keyword), text(row.role), number(row.weight, 1)]))), card("Evidence", evidenceRows.length ? table(["Type", "Source", "Title", "Quality", "Observed", "URL"], evidenceRows) : statePanel("empty", "No evidence citations are available.")), researchForm);
  } catch (error) { append(host, error instanceof ApiError && error.status === 404 ? objectNotFound("Opportunity", id) : errorState(error, context)); }
  return host;
}

function addOption(selectEl: HTMLSelectElement, value: string, label: string): void { const option = document.createElement("option"); option.value = value; option.textContent = label; selectEl.append(option); }
function scoreBadge(value: unknown): HTMLElement { return badge(`评分 ${number(value, 1)}`, Number(value) >= 80 ? "success" : Number(value) >= 60 ? "info" : "neutral"); }
function researchLabel(value: unknown): string { return ({NEW: "未处理", TRIAGED: "已分诊", TRACKING: "跟踪中", DONE: "已完成", DISMISSED: "已忽略"} as Record<string, string>)[String(value)] ?? text(value, "未处理"); }
function scoreLabel(value: string): string { return ({demand: "需求", supply: "供给", execution: "执行", cross_source: "跨来源", saturation: "饱和度"} as Record<string, string>)[value] ?? value; }
function detailSection(title: HTMLElement, body: HTMLElement): HTMLElement { const section = document.createElement("section"); section.className = "r04-detail-section"; section.append(title, body); return section; }
function detailSectionWithBody(titleValue: string, body: HTMLElement): HTMLElement { const title = document.createElement("h2"); title.textContent = titleValue; return detailSection(title, body); }
function sourceList(rows: Row[]): HTMLElement { const list = document.createElement("div"); list.className = "r04-source-list"; for (const row of rows.slice(0, 5)) { const item = document.createElement("div"); item.className = "r04-source-item"; let title: HTMLElement; if (row.url) { const link = externalLink(text(row.url)); link.textContent = text(row.title, "打开来源"); title = link; } else { const span = document.createElement("span"); span.textContent = text(row.title, "未命名来源"); title = span; } const meta = document.createElement("small"); meta.textContent = `${text(row.source)} · ${formatDate(row.observed_at)}`; item.append(title, meta); list.append(item); } return list.childElementCount ? list : statePanel("empty", "暂无关键来源。"); }
function detailList(entries: Array<[string, unknown]>): HTMLElement { const dl = document.createElement("dl"); dl.className = "r02-detail-grid"; for (const [key, value] of entries) { const dt = document.createElement("dt"); dt.textContent = key; const dd = document.createElement("dd"); dd.textContent = text(value); dl.append(dt, dd); } return dl; }
function objectNotFound(kind: string, id: string): HTMLElement { const panel = document.createElement("div"); panel.className = "r02-object-not-found"; const heading = document.createElement("h2"); heading.textContent = `${kind} not found`; const copy = document.createElement("p"); copy.textContent = `No live ${kind.toLowerCase()} record exists for id ${id}.`; const actions = document.createElement("div"); appendActionRow(actions, button("Go to dashboard", {variant: "primary", onClick: () => navigate("P02")}), button("Back", {onClick: () => history.back()})); panel.append(heading, copy, actions); return panel; }
function externalLink(url: string): HTMLAnchorElement { const link = document.createElement("a"); link.href = url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = "Open"; return link; }

async function renderResearch(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Research workflow", "Research records are currently represented by the opportunity research state API.");
  try { const data = await api("/api/v1/opportunities?page=0&limit=100"); const rows = (data ?? []).map((row: Row) => [linkTo("P16", text(row.title), {id: row.id}), badge(text(row.research?.status ?? "NEW"), row.research?.status === "TRACKING" ? "success" : "neutral"), text(row.research?.priority ?? 0), text(row.research?.notes ?? "")]); append(host, rows.length ? table(["Opportunity", "Status", "Priority", "Notes"], rows) : statePanel("empty", "No opportunities have research state.")); }
  catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderSources(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Sources", "Registered connectors and their runtime availability.");
  try { const rows = await api("/api/v1/sources"); const tableRows = (rows ?? []).map((row: Row) => [text(row.display_name ?? row.source_id), text(row.source_id), row.runtime_enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.kind ?? row.type), linkTo("P19", "Health", {id: row.source_id})]); append(host, tableRows.length ? table(["Source", "Id", "Runtime", "Kind", "Detail"], tableRows) : statePanel("empty", "No source connectors are registered.")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderSourceHealth(route: RouteState, context: ScreenContext): Promise<HTMLElement> {
  const sourceId = route.params.get("id"); const host = content("Source health", "Connector health and persisted circuit state.");
  try { const rows = await api("/api/v1/sources/health"); const selected = sourceId ? rows.filter((row: Row) => String(row.source_id) === sourceId) : rows; append(host, selected.length ? table(["Source", "Status", "Latency", "Last success", "Last error"], selected.map((row: Row) => [text(row.source_id), badge(text(row.status ?? row.runtime_status ?? "UNKNOWN"), row.status === "HEALTHY" ? "success" : "warning"), text(row.latency_ms ?? row.duration_ms), formatDate(row.last_success_at), text(row.last_error)])) : statePanel("empty", "No health record matches this source.")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderMonitoring(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Monitoring plan", "Probe planning is read-only here; execution remains an admin backend operation.");
  try { const data = await api("/api/v1/probes/plan"); const rows = Array.isArray(data) ? data : (data.tasks ?? data.queries ?? []); append(host, rows.length ? table(["Query", "Source", "Intent", "Reason"], rows.slice(0, 100).map((row: Row) => [text(row.query), text(row.source_id), text(row.intent), text(row.reason ?? row.priority)])) : card("Plan snapshot", table(["Field", "Value"], Object.entries(data ?? {}).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : text(value)])))); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderRuns(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Collection runs", "Recent connector runs and their persisted outcomes.");
  try { const rows = await api("/api/v1/collection-runs?limit=100"); const tableRows = (rows ?? []).map((row: Row) => [linkTo("P22", `Run ${row.id}`, {id: row.id}), text(row.source_id), text(row.query), badge(text(row.status), row.status === "SUCCEEDED" ? "success" : row.status === "FAILED" ? "danger" : "warning"), text(row.fetched), text(row.inserted), formatDate(row.started_at)]); append(host, tableRows.length ? table(["Run", "Source", "Query", "Status", "Fetched", "Inserted", "Started"], tableRows) : statePanel("empty", "No collection runs are recorded.")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderRunDetail(route: RouteState, context: ScreenContext): Promise<HTMLElement> {
  const id = route.params.get("id"); const host = content("Collection run detail", "The run record is loaded from the existing collection-runs endpoint.");
  try { const rows = await api("/api/v1/collection-runs?limit=500"); const row = (rows ?? []).find((item: Row) => String(item.id) === id); append(host, row ? card(`Run ${id}`, detailList(Object.entries(row).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value]))) : statePanel("empty", "Run not found."), linkTo("P21", "Back to collection runs")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderAnalysisQueue(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Analysis queue", "Opportunities waiting for or retrying structured analysis.");
  try { const data = await api("/api/v1/opportunities?include_dormant=true&limit=200"); const rows = (data ?? []).filter((row: Row) => ["PENDING", "DEGRADED", "FAILED"].includes(String(row.analysis_status))).map((row: Row) => [linkTo("P14", text(row.title), {id: row.id}), badge(text(row.analysis_status), row.analysis_status === "DEGRADED" ? "warning" : "info"), text(row.analysis_provider), text(row.analysis_attempt_count), formatDate(row.analysis_next_retry_at)]); append(host, rows.length ? table(["Opportunity", "State", "Provider", "Attempts", "Next retry"], rows) : statePanel("empty", "The analysis queue is empty.")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}

async function renderAlerts(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Alert inbox", "Alert lifecycle state is updated through the existing alert event API.");
  try { const data = await api("/api/v1/alerts/events?limit=100"); const rows = (data ?? []).map((row: Row) => { const action = row.status === "NEW" ? button("Acknowledge", {onClick: () => updateAlert(row.id, "ACKNOWLEDGED", host, context)}) : button("Resolve", {onClick: () => updateAlert(row.id, "RESOLVED", host, context)}); return [text(row.title), badge(text(row.status), row.status === "NEW" ? "warning" : "neutral"), text(row.priority), number(row.score, 1), formatDate(row.created_at), action]; }); append(host, rows.length ? table(["Alert", "Status", "Priority", "Score", "Created", "Action"], rows) : statePanel("empty", "No alert events are available.")); } catch (error) { append(host, errorState(error, context)); }
  return host;
}
async function updateAlert(id: number, status: string, host: HTMLElement, context: ScreenContext): Promise<void> { try { await api(`/api/v1/alerts/events/${id}`, {method: "PATCH", body: JSON.stringify({status})}); const next = await renderAlerts(context); host.replaceChildren(...Array.from(next.childNodes)); } catch (error) { host.append(errorState(error, context)); } }

async function renderAlertRules(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Alert rules", "Rules are persisted by the existing alert-rule endpoints.");
  const form = document.createElement("form"); form.className = "r02-inline-form"; const nameWrap = input("Rule name", {placeholder: "e.g. high signal"}); const name = nameWrap.querySelector<HTMLInputElement>("input"); const save = button("Create rule", {variant: "primary", type: "submit"}); appendActionRow(form, save); form.prepend(nameWrap); const list = document.createElement("div");
  form.addEventListener("submit", async (event) => { event.preventDefault(); save.disabled = true; try { await api("/api/v1/alerts/rules", {method: "POST", body: JSON.stringify({name: name?.value ?? ""})}); form.reset(); await loadAlertRules(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } finally { save.disabled = false; } }); append(host, form, list); await loadAlertRules(list, context); return host;
}
async function loadAlertRules(list: HTMLElement, context: ScreenContext): Promise<void> { try { const rows = await api("/api/v1/alerts/rules"); list.replaceChildren(rows.length ? table(["Name", "Enabled", "Min score", "Stages", "Updated"], rows.map((row: Row) => { const toggle = button(row.enabled ? "Disable" : "Enable", {onClick: async () => { toggle.disabled = true; try { await api(`/api/v1/alerts/rules/${row.id}`, {method: "PATCH", body: JSON.stringify({enabled: !row.enabled})}); await loadAlertRules(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } }}); return [text(row.name), row.enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), number(row.min_score, 1), text((row.stages ?? []).join(", ")), formatDate(row.updated_at), toggle]; })) : statePanel("empty", "No alert rules are configured.")); } catch (error) { list.replaceChildren(errorState(error, context)); } }

async function renderAudit(context: ScreenContext): Promise<HTMLElement> { const host = content("Audit log", "Administrative request and mutation records from the backend audit stream."); try { const rows = await api("/api/v1/audit?limit=200"); append(host, rows.length ? table(["Created", "Actor", "Action", "Resource", "Status", "Request"], rows.map((row: Row) => [formatDate(row.created_at), text(row.actor), text(row.action), text(row.resource), text(row.status_code), text(row.request_id)])) : statePanel("empty", "No audit events are recorded.")); } catch (error) { append(host, errorState(error, context)); } return host; }

async function renderUsers(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Users and roles", "Administrative identities from the existing RBAC user API. The server remains authoritative for OWNER invariants.");
  const form = document.createElement("form"); form.className = "r02-inline-form";
  const usernameWrap = input("Username", {placeholder: "new user"}); const passwordWrap = input("Initial password", {type: "password", placeholder: "at least 12 characters"}); const roleWrap = select("Role", ["VIEWER", "OPERATOR", "ADMIN", "OWNER"], "VIEWER");
  const username = usernameWrap.querySelector<HTMLInputElement>("input"); const password = passwordWrap.querySelector<HTMLInputElement>("input"); const role = roleWrap.querySelector<HTMLSelectElement>("select"); const create = button("Create user", {variant: "primary", type: "submit"}); appendActionRow(form, create); form.prepend(usernameWrap, passwordWrap, roleWrap);
  const list = document.createElement("div");
  form.addEventListener("submit", async (event) => { event.preventDefault(); create.disabled = true; try { await api("/api/v1/admin/users", {method: "POST", body: JSON.stringify({username: username?.value ?? "", password: password?.value ?? "", role: role?.value ?? "VIEWER", enabled: true})}); form.reset(); await loadUsers(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } finally { create.disabled = false; } });
  append(host, form, list); await loadUsers(list, context); return host;
}
async function loadUsers(list: HTMLElement, context: ScreenContext): Promise<void> { try { const rows = await api("/api/v1/admin/users"); const tableRows = (rows ?? []).map((row: Row) => { const controls = document.createElement("div"); controls.className = "r02-action-row"; const toggle = button(row.enabled ? "Disable" : "Enable", {variant: row.enabled ? "danger" : "secondary", onClick: async () => { toggle.disabled = true; try { await api(`/api/v1/admin/users/${row.id}`, {method: "PATCH", body: JSON.stringify({enabled: !row.enabled})}); await loadUsers(list, context); } catch (error) { controls.append(errorState(error, context)); toggle.disabled = false; } }}); const role = select("Role", ["VIEWER", "OPERATOR", "ADMIN", "OWNER"], text(row.role, "VIEWER")); const roleSelect = role.querySelector<HTMLSelectElement>("select"); const saveRole = button("Save role", {variant: "ghost", onClick: async () => { saveRole.disabled = true; try { await api(`/api/v1/admin/users/${row.id}`, {method: "PATCH", body: JSON.stringify({role: roleSelect?.value})}); await loadUsers(list, context); } catch (error) { controls.append(errorState(error, context)); saveRole.disabled = false; } }}); controls.append(role, saveRole, toggle); return [text(row.username), badge(text(row.role), row.role === "OWNER" ? "success" : "info"), row.enabled ? "Yes" : "No", formatDate(row.last_login_at), text(row.failed_login_count), controls]; }); list.replaceChildren(tableRows.length ? table(["Username", "Role", "Enabled", "Last login", "Failures", "Server-authorized actions"], tableRows) : statePanel("empty", "No users are configured.")); } catch (error) { list.replaceChildren(errorState(error, context)); } }

async function renderAccount(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Account and security", "Personal API tokens are managed through the existing authenticated token API. Token plaintext is shown once after creation.");
  const form = document.createElement("form"); form.className = "r02-inline-form"; const nameWrap = input("Token name", {placeholder: "local integration"}); const expiresWrap = input("Expires in days", {type: "number", placeholder: "optional"}); const name = nameWrap.querySelector<HTMLInputElement>("input"); const expires = expiresWrap.querySelector<HTMLInputElement>("input"); const issue = button("Issue API token", {variant: "primary", type: "submit"}); appendActionRow(form, issue); form.prepend(nameWrap, expiresWrap);
  const list = document.createElement("div");
  form.addEventListener("submit", async (event) => { event.preventDefault(); issue.disabled = true; try { const payload: Row = {name: name?.value ?? "", scopes: ["read"]}; if (expires?.value) payload.expires_in_days = Number(expires.value); const result = await api("/api/v1/auth/tokens", {method: "POST", body: JSON.stringify(payload)}); const secret = document.createElement("div"); const copy = document.createElement("p"); copy.textContent = "This token will not be shown again after closing this dialog."; const value = document.createElement("code"); value.className = "r02-secret-value"; value.textContent = text(result.token); const copyButton = button("Copy token", {variant: "secondary", onClick: () => { void navigator.clipboard?.writeText(text(result.token)); copyButton.textContent = "Copied"; }}); append(secret, copy, value, copyButton); host.append(modal("New API token", secret)); form.reset(); await loadTokens(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } finally { issue.disabled = false; } });
  append(host, form, list); await loadTokens(list, context); return host;
}
async function loadTokens(list: HTMLElement, context: ScreenContext): Promise<void> { try { const rows = await api("/api/v1/auth/tokens"); const tokenRows = (rows ?? []).map((row: Row) => { const revoke = button("Revoke", {variant: "danger", onClick: async () => { revoke.disabled = true; try { await api(`/api/v1/auth/tokens/${row.id}`, {method: "DELETE"}); await loadTokens(list, context); } catch (error) { list.replaceChildren(errorState(error, context)); } }}); return [text(row.name), text((row.scopes ?? []).join(", ")), formatDate(row.created_at), formatDate(row.expires_at), row.revoked_at ? badge("Revoked", "danger") : badge("Active", "success"), revoke]; }); list.replaceChildren(tokenRows.length ? table(["Name", "Scopes", "Created", "Expires", "State", "Action"], tokenRows) : statePanel("empty", "No personal API tokens are issued.")); } catch (error) { list.replaceChildren(errorState(error, context)); } }

function renderSettings(_route: RouteState, active: ScreenId, title: string, message: string): HTMLElement { const child = document.createElement("div"); append(child, card(title, statePanel("permission", message))); return settingsFrame(active, child); }

async function renderSourcePreferenceSettings(_route: RouteState, context: ScreenContext): Promise<HTMLElement> { const frame = document.createElement("div"); const inner = content("Source preference", "Runtime enablement and notes use the existing admin source-preference endpoint."); try { const rows = await api("/api/v1/sources"); const tableRows = (rows ?? []).map((row: Row) => { const toggle = button(row.runtime_enabled ? "Disable" : "Enable", {onClick: async () => { toggle.disabled = true; try { await api(`/api/v1/sources/${encodeURIComponent(row.source_id)}/preference`, {method: "PATCH", body: JSON.stringify({enabled: !row.runtime_enabled, note: row.preference_note ?? ""})}); const next = await renderSourcePreferenceSettings(_route, context); frame.replaceChildren(...Array.from(next.childNodes)); } catch (error) { frame.append(errorState(error, context)); } }}); return [text(row.source_id), row.runtime_enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.preference_note), toggle]; }); append(inner, tableRows.length ? table(["Source", "Runtime", "Note", "Action"], tableRows) : statePanel("empty", "No source preference records exist.")); } catch (error) { append(inner, errorState(error, context)); } frame.append(settingsFrame("P29-E", inner)); return frame; }

async function renderDiagnostics(context: ScreenContext): Promise<HTMLElement> { const host = content("System diagnostics", "Read-only runtime health checks from the application and provider registries."); const endpoints: Array<[string, string]> = [["Health", "/health"], ["Ready", "/ready"], ["Sources", "/api/v1/sources/health"], ["Analysis providers", "/api/v1/analysis/providers"], ["Provider route", "/api/v1/analysis/providers/route"]]; const results = await Promise.allSettled(endpoints.map(([, url]) => api(url))); const rows = results.map((result, index) => [endpoints[index][0], result.status === "fulfilled" ? badge("OK", "success") : badge("Failed", "danger"), result.status === "fulfilled" ? JSON.stringify(result.value) : text(result.reason)]); append(host, table(["Check", "Status", "Response"], rows)); const failed = results.find((result) => result.status === "rejected"); if (failed && failed.status === "rejected") host.append(errorState(failed.reason, context)); return host; }

function installScreenStyles(): void {
  if (document.getElementById("r02-screen-styles")) return;
  const style = document.createElement("style"); style.id = "r02-screen-styles"; style.textContent = `
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
    @media (max-width: 900px) { .r04-detail-grid-r04 { grid-template-columns: 1fr; } }
    @media (max-width: 640px) { .r04-entity-header h1 { font-size: 22px; } .r04-opportunity-filters input[type=search] { min-width: 140px; } }
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
  `; document.head.appendChild(style);
}
