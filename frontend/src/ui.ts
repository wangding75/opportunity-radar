import { navigate, routeFor, type ScreenId } from "./router.js";

export type AsyncState = "loading" | "empty" | "error" | "partial" | "stale" | "permission" | "rate-limit" | "ready";
export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

export function button(label: string, options: {variant?: ButtonVariant; onClick?: () => void; type?: "button" | "submit"; disabled?: boolean} = {}): HTMLButtonElement {
  const el = document.createElement("button");
  el.type = options.type ?? "button";
  el.className = `r02-button r02-button-${options.variant ?? "secondary"}`;
  el.textContent = label;
  el.disabled = options.disabled ?? false;
  if (options.onClick) el.addEventListener("click", options.onClick);
  return el;
}

export function iconButton(label: string, ariaLabel: string, onClick: () => void): HTMLButtonElement {
  const el = button(label, {variant: "ghost", onClick});
  el.classList.add("r02-icon-button");
  el.setAttribute("aria-label", ariaLabel);
  return el;
}

export function input(label: string, options: {type?: string; value?: string; placeholder?: string; name?: string} = {}): HTMLElement {
  const wrap = document.createElement("label");
  wrap.className = "r02-field-wrap";
  const caption = document.createElement("span");
  caption.className = "r02-field-label";
  caption.textContent = label;
  const field = document.createElement("input");
  field.className = "r02-field";
  field.type = options.type ?? "text";
  field.value = options.value ?? "";
  field.placeholder = options.placeholder ?? "";
  if (options.name) field.name = options.name;
  wrap.append(caption, field);
  return wrap;
}

export function select(label: string, items: string[], value = ""): HTMLElement {
  const wrap = document.createElement("label");
  wrap.className = "r02-field-wrap";
  const caption = document.createElement("span");
  caption.className = "r02-field-label";
  caption.textContent = label;
  const field = document.createElement("select");
  field.className = "r02-field";
  items.forEach((item) => { const option = new Option(item, item, false, item === value); field.add(option); });
  wrap.append(caption, field);
  return wrap;
}

export function badge(text: string, tone: "neutral" | "success" | "warning" | "danger" | "info" = "neutral"): HTMLSpanElement {
  const el = document.createElement("span");
  el.className = `r02-badge r02-badge-${tone}`;
  el.textContent = text;
  return el;
}

export function card(title: string, body?: HTMLElement): HTMLElement {
  const el = document.createElement("section");
  el.className = "r02-card";
  const heading = document.createElement("h2");
  heading.className = "r02-card-title";
  heading.textContent = title;
  el.append(heading);
  if (body) el.append(body);
  return el;
}

export function statePanel(state: AsyncState, message?: string, retry?: () => void): HTMLElement {
  const el = document.createElement("div");
  el.className = `r02-state r02-state-${state}`;
  const title: Record<AsyncState, string> = {loading: "正在加载", empty: "暂无数据", error: "加载失败", partial: "部分数据可用", stale: "数据可能已过期", permission: "需要权限", "rate-limit": "请求过于频繁", ready: "已就绪"};
  el.innerHTML = `<strong>${title[state]}</strong><span>${message ?? ""}</span>`;
  if (retry) el.append(button("Retry", {variant: "secondary", onClick: retry}));
  return el;
}

export function readOnlyNotice(message = "当前页面仅供查阅，内容不可修改。未确认的写操作已从界面中移除。", title = "只读提示：仅供查阅"): HTMLElement {
  return capabilityNotice("r04-read-only-notice", "◉", title, message);
}

export function capabilityUnavailableNotice(message = "尚未确认具备安全且语义等价的后端接口，相关操作暂不可用。", title = "功能暂不可用"): HTMLElement {
  return capabilityNotice("r04-capability-unavailable", "⊘", title, message);
}

function capabilityNotice(className: string, iconValue: string, titleValue: string, messageValue: string): HTMLElement {
  const host = document.createElement("section");
  host.className = `r04-notice ${className}`;
  const icon = document.createElement("span");
  icon.className = "r04-notice-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = iconValue;
  const body = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = titleValue;
  const copy = document.createElement("p");
  copy.textContent = messageValue;
  body.append(heading, copy);
  host.append(icon, body);
  return host;
}

export function table(headers: string[], rows: Array<Array<string | HTMLElement>> = []): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "r02-table-wrap";
  const tableEl = document.createElement("table");
  tableEl.className = "r02-table";
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headers.forEach((header) => { const th = document.createElement("th"); th.textContent = header; headerRow.append(th); });
  thead.append(headerRow);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => { const tr = document.createElement("tr"); row.forEach((cell) => { const td = document.createElement("td"); typeof cell === "string" ? td.textContent = cell : td.append(cell); tr.append(td); }); tbody.append(tr); });
  tableEl.append(thead, tbody);
  wrap.append(tableEl);
  return wrap;
}

export function pagination(current: number, onPage: (page: number) => void): HTMLElement {
  const el = document.createElement("div");
  el.className = "r02-pagination";
  el.append(button("Previous", {disabled: current <= 1, onClick: () => onPage(current - 1)}), document.createTextNode(` Page ${current} `), button("Next", {onClick: () => onPage(current + 1)}));
  return el;
}

export function drawer(title: string, content: HTMLElement, close?: () => void): HTMLElement {
  const host = document.createElement("aside");
  host.className = "r02-overlay r02-drawer";
  host.setAttribute("aria-label", title);
  const header = document.createElement("div");
  header.className = "r02-overlay-header";
  const heading = document.createElement("h2");
  heading.textContent = title;
  header.append(heading, iconButton("×", "Close drawer", () => { host.remove(); close?.(); }));
  host.append(header, content);
  return host;
}

export function modal(title: string, content: HTMLElement, close?: () => void): HTMLElement {
  const backdrop = document.createElement("div");
  backdrop.className = "r02-overlay-backdrop";
  const host = drawer(title, content, close);
  host.classList.remove("r02-drawer");
  host.classList.add("r02-modal");
  backdrop.append(host);
  return backdrop;
}

export function tabs(items: Array<{label: string; screen: ScreenId}>, active: ScreenId): HTMLElement {
  const nav = document.createElement("nav");
  nav.className = "r02-tabs";
  nav.setAttribute("aria-label", "Section navigation");
  items.forEach((item) => {
    const link = document.createElement("a");
    link.href = routeFor(item.screen);
    link.className = item.screen === active ? "is-active" : "";
    link.textContent = item.label;
    link.setAttribute("aria-current", item.screen === active ? "page" : "false");
    nav.append(link);
  });
  return nav;
}

export function settingsFrame(active: ScreenId, child: HTMLElement): HTMLElement {
  const frame = document.createElement("section");
  frame.className = "r02-settings-frame";
  frame.dataset.component = "SettingsFrame";
  const settings = ["P29-A", "P29-B", "P29-C", "P29-D", "P29-E"] as ScreenId[];
  const nav = tabs(settings.map((screen) => ({screen, label: screen === "P29-A" ? "General" : screen === "P29-B" ? "Security" : screen === "P29-C" ? "Notifications" : screen === "P29-D" ? "Integrations" : "Source Preference"})), active);
  nav.dataset.component = "SettingsNavigation";
  const childFrame = document.createElement("div");
  childFrame.className = "r02-settings-child";
  childFrame.dataset.component = "SettingsChildFrame";
  childFrame.append(child);
  frame.append(nav, childFrame);
  return frame;
}

export function linkTo(screen: ScreenId, label: string, params: Record<string, string | number> = {}): HTMLAnchorElement {
  const link = document.createElement("a");
  link.href = routeFor(screen, params);
  link.textContent = label;
  return link;
}

export function appendActionRow(parent: HTMLElement, ...actions: HTMLElement[]): void {
  const row = document.createElement("div");
  row.className = "r02-action-row";
  row.append(...actions);
  parent.append(row);
}

export function installComponentStyles(): void {
  if (document.getElementById("r02-components")) return;
  const style = document.createElement("style");
  style.id = "r02-components";
  style.textContent = `
    .r02-button { min-height: 36px; padding: 8px 14px; border: 1px solid var(--r02-outline); border-radius: 8px; font-weight: 600; transition: border-color .15s ease, background .15s ease, color .15s ease; }
    .r02-button:disabled { cursor: not-allowed; opacity: .5; }
    .r02-button-primary { background: var(--r02-primary); border-color: var(--r02-primary); color: #fff; }
    .r02-button-primary:hover:not(:disabled) { background: var(--r02-primary-dark); }
    .r02-button-secondary { background: var(--r02-surface); color: var(--r02-text); }
    .r02-button-secondary:hover:not(:disabled), .r02-button-ghost:hover:not(:disabled) { border-color: var(--r02-outline-strong); background: var(--r02-surface-muted); }
    .r02-button-danger { background: var(--r02-danger); border-color: var(--r02-danger); color: #fff; }
    .r02-button-ghost { background: transparent; border-color: transparent; color: var(--r02-text-muted); }
    .r02-icon-button { width: 36px; padding: 6px; font-size: 20px; line-height: 1; }
    .r02-field-wrap { display: grid; gap: 5px; }
    .r02-field-label { color: var(--r02-text-muted); font-size: 12px; font-weight: 700; }
    .r02-field { min-height: 38px; border: 1px solid var(--r02-outline); border-radius: 8px; background: var(--r02-surface); color: var(--r02-text); padding: 8px 10px; }
    .r02-field:focus { border-color: var(--r02-primary); box-shadow: 0 0 0 2px rgba(37,99,235,.16); outline: 0; }
    .r02-card { background: var(--r02-surface); border: 1px solid var(--r02-outline); border-radius: 8px; padding: 16px; }
    .r02-card-title { margin: 0 0 14px; font-size: 16px; }
    .r02-badge { display: inline-flex; align-items: center; min-height: 24px; border-radius: 9999px; padding: 3px 9px; font-size: 12px; font-weight: 700; }
    .r02-badge-neutral { background: var(--r02-surface-muted); color: var(--r02-text-muted); }
    .r02-badge-success { background: var(--r02-success-soft); color: var(--r02-success); }
    .r02-badge-warning { background: var(--r02-warning-soft); color: var(--r02-warning); }
    .r02-badge-danger { background: var(--r02-danger-soft); color: var(--r02-danger); }
    .r02-badge-info { background: var(--r02-info-soft); color: var(--r02-info); }
    .r02-table-wrap { overflow: auto; border: 1px solid var(--r02-outline); border-radius: 8px; background: var(--r02-surface); }
    .r02-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .r02-table th, .r02-table td { padding: 10px 12px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--r02-outline); }
    .r02-table th { background: var(--r02-surface-muted); color: var(--r02-text-muted); font-size: 12px; letter-spacing: .03em; }
    .r02-table tr:last-child td { border-bottom: 0; }
    .r02-state { display: grid; gap: 6px; place-items: center; min-height: 160px; border: 1px dashed var(--r02-outline-strong); border-radius: 8px; padding: 24px; color: var(--r02-text-muted); text-align: center; }
    .r02-state-error, .r02-state-rate-limit { color: var(--r02-danger); background: var(--r02-danger-soft); }
    .r02-state-permission { color: var(--r02-warning); background: var(--r02-warning-soft); }
    .r02-state-partial, .r02-state-stale { color: var(--r02-warning); background: var(--r02-warning-soft); }
    .r02-pagination, .r02-action-row { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
    .r02-pagination { justify-content: flex-end; padding-top: 12px; color: var(--r02-text-muted); font-size: 13px; }
    .r02-tabs { display: flex; gap: 2px; flex-wrap: wrap; border-bottom: 1px solid var(--r02-outline); margin-bottom: 20px; }
    .r02-tabs a { padding: 10px 14px; color: var(--r02-text-muted); text-decoration: none; border-bottom: 2px solid transparent; }
    .r02-tabs a:hover { color: var(--r02-text); background: var(--r02-surface-muted); }
    .r02-tabs a.is-active { color: var(--r02-primary-dark); border-bottom-color: var(--r02-primary); font-weight: 700; }
    .r02-settings-frame { display: grid; gap: 0; }
    .r02-settings-child { min-width: 0; }
    .r02-overlay-backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(15,23,42,.28); display: grid; place-items: center; padding: 20px; }
    .r02-overlay { background: var(--r02-surface); border: 1px solid var(--r02-outline); box-shadow: 0 10px 15px -3px rgba(0,0,0,.05); overflow: auto; }
    .r02-drawer { position: fixed; top: 0; right: 0; bottom: 0; z-index: 30; width: min(620px, 96vw); padding: 24px; }
    .r02-modal { width: min(560px, 96vw); max-height: 90vh; border-radius: 12px; padding: 24px; }
    .r02-overlay-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
    .r02-overlay-header h2 { margin: 0; font-size: 18px; }
    .r04-notice { display: flex; align-items: flex-start; gap: 12px; padding: 16px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface); }
    .r04-notice-icon { flex: 0 0 auto; color: var(--or-text-muted); font-size: 20px; line-height: 1.2; }
    .r04-notice h2 { margin: 0; color: var(--or-text); font-size: 14px; }
    .r04-notice p { margin: 5px 0 0; color: var(--or-text-muted); font-size: 12px; line-height: 1.6; }
    .r04-capability-unavailable { border-style: dashed; background: var(--or-surface-muted); }
    .r04-capability-unavailable .r04-notice-icon { color: var(--or-text-muted); }
    @media (max-width: 640px) { .r02-table { min-width: 650px; } .r02-drawer { width: 100vw; } }
  `;
  document.head.appendChild(style);
}
