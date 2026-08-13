import { api, ApiError } from "./client.js";
import { routeFor, navigate, type RouteState, type ScreenId } from "./router.js";
import { appendActionRow, badge, button, card, drawer, input, linkTo, select, settingsFrame, statePanel, table, tabs } from "./ui.js";

export type AuthSession = {label: string; role: string};
export type ScreenContext = {onSessionExpired: () => void; onForbidden?: () => void};
type Row = Record<string, any>;

export async function renderScreen(route: RouteState, _session: AuthSession, context: ScreenContext): Promise<HTMLElement> {
  installScreenStyles();
  switch (route.screen) {
    case "P02": return renderDashboard(context);
    case "P03": return renderSearch(context);
    case "P04": return renderForbidden();
    case "P05": return renderNotFound(route);
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
  const host = content("Decision dashboard", "Evidence-backed signals, opportunities, and operating health from the live API.");
  let data: Row;
  try { data = await api("/api/v1/dashboard"); } catch (error) { append(host, errorState(error, context, () => navigate("P02"))); return host; }
  const totals = data.totals ?? {};
  const metrics = document.createElement("div");
  metrics.className = "r02-kpi-grid";
  append(metrics,
    kpi("Observations", totals.observations, routeFor("P06")),
    kpi("Keywords", totals.keywords, routeFor("P08")),
    kpi("Active opportunities", totals.opportunities, routeFor("P12")),
    kpi("Sources", totals.sources, routeFor("P18")),
    kpi("New alerts", totals.unread_alerts, routeFor("P24")),
    kpi("Pending analysis", totals.pending_external_analysis, routeFor("P23")),
  );
  append(host, metrics);

  const split = document.createElement("div");
  split.className = "r02-two-column";
  const opportunities = Array.isArray(data.top_opportunities) ? data.top_opportunities : [];
  const opportunityRows = opportunities.slice(0, 8).map((row: Row) => [
    linkTo("P13", text(row.title), {id: row.id}), badge(text(row.stage), row.stage === "COMMERCIALIZING" ? "success" : "info"), number(row.score, 1), text(row.analysis_status),
  ]);
  const opportunityCard = card("Top opportunities", opportunityRows.length ? table(["Opportunity", "Stage", "Score", "Analysis"], opportunityRows) : statePanel("empty", "No opportunity records are available."));
  const keywordRows = (Array.isArray(data.top_keywords) ? data.top_keywords : []).slice(0, 8).map((row: Row) => [
    linkTo("P10", text(row.keyword), {keyword_id: row.id}), number(row.score, 1), text(row.status), text(row.observations),
  ]);
  const keywordCard = card("Leading keywords", keywordRows.length ? table(["Keyword", "Score", "Status", "Observations"], keywordRows) : statePanel("empty", "No keyword records are available."));
  append(split, opportunityCard, keywordCard);
  append(host, split);

  const latestRows = (Array.isArray(data.latest_items) ? data.latest_items : []).slice(0, 10).map((row: Row) => [text(row.source), text(row.type), text(row.title), formatDate(row.observed_at)]);
  append(host, card("Latest evidence", latestRows.length ? table(["Source", "Type", "Title", "Observed"], latestRows) : statePanel("empty", "No evidence has been collected yet.")));
  return host;
}

async function renderSearch(context: ScreenContext): Promise<HTMLElement> {
  const host = content("Global search", "Search the existing opportunity, observation, and keyword read models in parallel.");
  const form = document.createElement("form");
  form.className = "r02-search-form";
  const queryWrap = input("Search query", {placeholder: "keyword, title, or evidence text"});
  const categoryWrap = select("Category", ["all", "opportunities", "observations", "keywords"], "all");
  const query = queryWrap.querySelector<HTMLInputElement>("input");
  const category = categoryWrap.querySelector<HTMLSelectElement>("select");
  const submit = button("Search", {variant: "primary", type: "submit"});
  appendActionRow(form, submit);
  form.prepend(queryWrap, categoryWrap);
  const results = document.createElement("div");
  results.className = "r02-search-results";
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void runSearch(text(query?.value, "").trim(), text(category?.value, "all"), results, context);
  });
  append(host, form, results);
  const initial = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("q");
  if (initial) { if (query) query.value = initial; void runSearch(initial, "all", results, context); }
  else results.append(statePanel("ready", "Enter a query to search live records."));
  return host;
}

async function runSearch(query: string, category: string, results: HTMLElement, context: ScreenContext): Promise<void> {
  results.replaceChildren(statePanel("loading", "Searching live records…"));
  if (!query) { results.replaceChildren(statePanel("empty", "Enter a query first.")); return; }
  const jobs: Promise<unknown>[] = [];
  if (category === "all" || category === "opportunities") jobs.push(api(`/api/v1/opportunities/page?q=${encodeURIComponent(query)}&limit=50`));
  else jobs.push(Promise.resolve({items: []}));
  if (category === "all" || category === "observations") jobs.push(api(`/api/v1/observations?q=${encodeURIComponent(query)}&limit=50`));
  else jobs.push(Promise.resolve({items: []}));
  if (category === "all" || category === "keywords") jobs.push(api("/api/v1/keywords?limit=500"));
  else jobs.push(Promise.resolve([]));
  const settled = await Promise.allSettled(jobs);
  const failed = settled.find((item) => item.status === "rejected");
  if (failed && failed.status === "rejected" && settled.every((item) => item.status === "rejected")) { results.replaceChildren(errorState(failed.reason, context)); return; }
  const [opportunities, observations, keywords] = settled.map((item) => item.status === "fulfilled" ? item.value : null) as [Row | null, Row | null, Row[] | null];
  const rows: Array<Array<string | HTMLElement>> = [];
  for (const row of opportunities?.items ?? []) rows.push([badge("Opportunity", "success"), linkTo("P13", text(row.title), {id: row.id}), text(row.summary), number(row.score, 1)]);
  for (const row of observations?.items ?? []) rows.push([badge("Observation", "info"), linkTo("P07", text(row.title), {id: row.id}), text(row.text), formatDate(row.observed_at)]);
  for (const row of (keywords ?? []).filter((item: Row) => `${item.keyword} ${item.canonical}`.toLowerCase().includes(query.toLowerCase()))) rows.push([badge("Keyword", "warning"), linkTo("P10", text(row.keyword), {keyword_id: row.id}), text(row.status), number(row.score, 1)]);
  if (!rows.length) results.replaceChildren(statePanel("empty", `No live records matched “${query}”.`));
  else { const panel = card(`Results for “${query}”`, table(["Type", "Record", "Context", "Signal"], rows)); results.replaceChildren(panel); }
  if (failed) results.prepend(statePanel("partial", "Some search categories could not be loaded; visible results are still live."));
}

function renderForbidden(): HTMLElement {
  const host = content("Access restricted", "This route is known, but the current role is not allowed to read it.");
  const actions = document.createElement("div");
  appendActionRow(actions, button("Back", {onClick: () => history.back()}), button("Go to dashboard", {variant: "primary", onClick: () => navigate("P02")}));
  append(host, statePanel("permission", "Ask an administrator for the required capability."), actions);
  return host;
}

function renderNotFound(route: RouteState): HTMLElement {
  const host = content("Route not found", "The requested path is not part of the R02 screen registry.");
  const requested = route.params.get("requested") ?? "unknown";
  const copy = document.createElement("p"); copy.textContent = `Requested path: ${requested}`;
  const actions = document.createElement("div"); appendActionRow(actions, button("Back", {onClick: () => history.back()}), button("Go to dashboard", {variant: "primary", onClick: () => navigate("P02")}));
  append(host, statePanel("empty", "Choose a registered workspace screen."), copy, actions);
  return host;
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
      const rows = (data.items ?? []).map((row: Row) => [linkTo("P07", text(row.title), {id: row.id, q: q?.value ?? ""}), text(row.source_id), text(row.item_type), badge(text(row.evidence_quality), row.evidence_quality === "A" ? "success" : "neutral"), formatDate(row.observed_at)]);
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
    const data = await api("/api/v1/observations?limit=500");
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
  const host = content("Opportunities", "Ranked opportunity clusters with evidence counts, stage, and analysis state.");
  const filters = document.createElement("form"); filters.className = "r02-inline-form"; const qWrap = input("Search", {placeholder: "title or summary"}); const stageWrap = select("Stage", ["", "DISCOVERY", "EARLY_GROWTH", "PRODUCTIZING", "COMMERCIALIZING", "DORMANT"], ""); const q = qWrap.querySelector<HTMLInputElement>("input"); const stage = stageWrap.querySelector<HTMLSelectElement>("select"); const submit = button("Apply filters", {variant: "primary", type: "submit"}); appendActionRow(filters, submit); filters.prepend(qWrap, stageWrap);
  const results = document.createElement("div");
  const load = async (offset: number): Promise<void> => { results.replaceChildren(statePanel("loading", "Loading opportunities…")); const params = new URLSearchParams({limit: "50", offset: String(offset), include_dormant: stage?.value === "DORMANT" ? "true" : "false"}); if (q?.value.trim()) params.set("q", q.value.trim()); if (stage?.value && stage.value !== "DORMANT") params.set("stage", stage.value); try { const data = await api(`/api/v1/opportunities?${params.toString()}`); const rows = (data ?? []).map((row: Row) => [linkTo("P13", text(row.title), {id: row.id, q: q?.value ?? ""}), badge(text(row.stage), row.stage === "COMMERCIALIZING" ? "success" : "info"), number(row.score, 1), number(row.risk_score, 1), text(row.evidence_count), text(row.research?.status ?? "NEW"), badge(text(row.analysis_status), row.analysis_status === "READY" ? "success" : "warning")]); results.replaceChildren(rows.length ? table(["Opportunity", "Stage", "Score", "Risk", "Evidence", "Research", "Analysis"], rows) : statePanel("empty", q?.value ? "No opportunities match the current filters." : "No active opportunities are available.")); const pager = document.createElement("div"); pager.className = "r02-pagination"; pager.append(button("Previous", {disabled: offset <= 0, onClick: () => void load(Math.max(0, offset - 50))}), document.createTextNode(`Offset ${offset}`), button("Next", {disabled: data.length < 50, onClick: () => void load(offset + 50)})); results.append(pager); } catch (error) { results.replaceChildren(errorState(error, context, () => void load(offset))); } };
  filters.addEventListener("submit", (event) => { event.preventDefault(); void load(0); }); append(host, filters, results); await load(0); return host;
}

async function renderOpportunityDetail(route: RouteState, context: ScreenContext, mode: "detail" | "analysis" | "research" | "result"): Promise<HTMLElement> {
  const id = route.params.get("id");
  const title = mode === "analysis" ? "Structured analysis" : mode === "research" ? "Research workflow" : mode === "result" ? "Research result" : "Opportunity detail";
  const host = content(title, "Live opportunity detail, score breakdown, evidence citations, and research state.");
  if (!id) { append(host, statePanel("error", "Opportunity id is missing.")); return host; }
  try {
    const data = await api(`/api/v1/opportunities/${encodeURIComponent(id)}`);
    const summary = document.createElement("div"); summary.className = "r02-detail-summary";
    append(summary, card("Opportunity", detailList([["Title", data.title], ["Stage", data.stage], ["Score", number(data.score, 1)], ["Risk", number(data.risk_score, 1)], ["Analysis", data.analysis?.status], ["Research", data.research?.status]])), card("Scores", detailList(Object.entries(data.scores ?? {}).map(([key, value]) => [key, number(value, 1)]))));
    const actions = document.createElement("div");
    if (mode === "detail" || mode === "research" || mode === "result") appendActionRow(actions, button("Open analysis", {onClick: () => navigate("P14", {id})}), button("Open research", {onClick: () => navigate("P16", {id})}), button("Open research result", {onClick: () => navigate("P17", {id})}));
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

async function renderUsers(context: ScreenContext): Promise<HTMLElement> { const host = content("Users and roles", "Administrative identities from the existing RBAC user API."); try { const rows = await api("/api/v1/admin/users"); append(host, rows.length ? table(["Username", "Role", "Enabled", "Last login", "Failures"], rows.map((row: Row) => [text(row.username), badge(text(row.role), row.role === "OWNER" ? "success" : "info"), row.enabled ? "Yes" : "No", formatDate(row.last_login_at), text(row.failed_login_count)])) : statePanel("empty", "No users are configured.")); } catch (error) { append(host, errorState(error, context)); } return host; }

async function renderAccount(context: ScreenContext): Promise<HTMLElement> { const host = content("Account and security", "Personal API tokens are managed through the existing authenticated token API."); try { const rows = await api("/api/v1/auth/tokens"); const tokenRows = (rows ?? []).map((row: Row) => { const revoke = button("Revoke", {variant: "danger", onClick: async () => { revoke.disabled = true; try { await api(`/api/v1/auth/tokens/${row.id}`, {method: "DELETE"}); const next = await renderAccount(context); host.replaceChildren(...Array.from(next.childNodes)); } catch (error) { host.append(errorState(error, context)); } }}); return [text(row.name), text((row.scopes ?? []).join(", ")), formatDate(row.created_at), formatDate(row.expires_at), row.revoked_at ? badge("Revoked", "danger") : badge("Active", "success"), revoke]; }); append(host, card("API tokens", tokenRows.length ? table(["Name", "Scopes", "Created", "Expires", "State", "Action"], tokenRows) : statePanel("empty", "No personal API tokens are issued."))); } catch (error) { append(host, errorState(error, context)); } return host; }

function renderSettings(route: RouteState, active: ScreenId, title: string, message: string): HTMLElement { const child = document.createElement("div"); append(child, card(title, statePanel("permission", message))); return settingsFrame(active, child); }

async function renderSourcePreferenceSettings(route: RouteState, context: ScreenContext): Promise<HTMLElement> { const host = document.createElement("div"); const inner = content("Source preference", "Runtime enablement and notes use the existing admin source-preference endpoint."); try { const rows = await api("/api/v1/sources"); const tableRows = (rows ?? []).map((row: Row) => { const toggle = button(row.runtime_enabled ? "Disable" : "Enable", {onClick: async () => { toggle.disabled = true; try { await api(`/api/v1/sources/${encodeURIComponent(row.source_id)}/preference`, {method: "PATCH", body: JSON.stringify({enabled: !row.runtime_enabled, note: row.preference_note ?? ""})}); const next = await renderSourcePreferenceSettings(route, context); host.replaceChildren(...Array.from(next.childNodes)); } catch (error) { host.append(errorState(error, context)); } }}); return [text(row.source_id), row.runtime_enabled ? badge("Enabled", "success") : badge("Disabled", "neutral"), text(row.preference_note), toggle]; }); append(inner, tableRows.length ? table(["Source", "Runtime", "Note", "Action"], tableRows) : statePanel("empty", "No source preference records exist.")); } catch (error) { append(inner, errorState(error, context)); } append(host, settingsFrame("P29-E", inner)); return host; }

async function renderDiagnostics(context: ScreenContext): Promise<HTMLElement> { const host = content("System diagnostics", "Read-only runtime health checks from the application and provider registries."); const endpoints: Array<[string, string]> = [["Health", "/health"], ["Ready", "/ready"], ["Sources", "/api/v1/sources/health"], ["Analysis providers", "/api/v1/analysis/providers"], ["Provider route", "/api/v1/analysis/providers/route"]]; const results = await Promise.allSettled(endpoints.map(([, url]) => api(url))); const rows = results.map((result, index) => [endpoints[index][0], result.status === "fulfilled" ? badge("OK", "success") : badge("Failed", "danger"), result.status === "fulfilled" ? JSON.stringify(result.value) : text(result.reason)]); append(host, table(["Check", "Status", "Response"], rows)); const failed = results.find((result) => result.status === "rejected"); if (failed && failed.status === "rejected") host.append(errorState(failed.reason, context)); return host; }

function installScreenStyles(): void {
  if (document.getElementById("r02-screen-styles")) return;
  const style = document.createElement("style"); style.id = "r02-screen-styles"; style.textContent = `
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
