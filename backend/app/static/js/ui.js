import { routeFor } from "./router.js";
export function button(label, options = {}) {
    const el = document.createElement("button");
    el.type = options.type ?? "button";
    el.className = `r02-button r02-button-${options.variant ?? "secondary"}`;
    el.textContent = label;
    el.disabled = options.disabled ?? false;
    if (options.onClick)
        el.addEventListener("click", options.onClick);
    return el;
}
export function iconButton(label, ariaLabel, onClick) {
    const el = button(label, { variant: "ghost", onClick });
    el.classList.add("r02-icon-button");
    el.setAttribute("aria-label", ariaLabel);
    return el;
}
export function input(label, options = {}) {
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
    if (options.name)
        field.name = options.name;
    wrap.append(caption, field);
    return wrap;
}
export function select(label, items, value = "") {
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
export function badge(text, tone = "neutral") {
    const el = document.createElement("span");
    el.className = `r02-badge r02-badge-${tone}`;
    el.textContent = text;
    return el;
}
export function card(title, body) {
    const el = document.createElement("section");
    el.className = "r02-card";
    const heading = document.createElement("h2");
    heading.className = "r02-card-title";
    heading.textContent = title;
    el.append(heading);
    if (body)
        el.append(body);
    return el;
}
export function statePanel(state, message, retry) {
    const el = document.createElement("div");
    el.className = `r02-state r02-state-${state}`;
    const title = { loading: "正在加载", empty: "暂无数据", error: "加载失败", partial: "部分数据可用", stale: "数据可能已过期", permission: "需要权限", "rate-limit": "请求过于频繁", ready: "已就绪" };
    el.innerHTML = `<strong>${title[state]}</strong><span>${message ?? ""}</span>`;
    if (retry)
        el.append(button("Retry", { variant: "secondary", onClick: retry }));
    return el;
}
export function readOnlyNotice(message = "当前页面仅供查阅，内容不可修改。未确认的写操作已从界面中移除。", title = "只读提示：仅供查阅") {
    return capabilityNotice("r04-read-only-notice", "◉", title, message);
}
export function capabilityUnavailableNotice(message = "尚未确认具备安全且语义等价的后端接口，相关操作暂不可用。", title = "功能暂不可用") {
    return capabilityNotice("r04-capability-unavailable", "⊘", title, message);
}
function capabilityNotice(className, iconValue, titleValue, messageValue) {
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
export function table(headers, rows = []) {
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
export function pagination(current, onPage) {
    const el = document.createElement("div");
    el.className = "r02-pagination";
    el.append(button("Previous", { disabled: current <= 1, onClick: () => onPage(current - 1) }), document.createTextNode(` Page ${current} `), button("Next", { onClick: () => onPage(current + 1) }));
    return el;
}
export function drawer(title, content, close) {
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
export function modal(title, content, close) {
    const backdrop = document.createElement("div");
    backdrop.className = "r02-overlay-backdrop";
    const host = drawer(title, content, close);
    host.classList.remove("r02-drawer");
    host.classList.add("r02-modal");
    backdrop.append(host);
    return backdrop;
}
export function tabs(items, active) {
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
export function settingsFrame(active, child) {
    const frame = document.createElement("section");
    frame.className = "r02-settings-frame";
    frame.dataset.component = "SettingsFrame";
    const settings = ["P29-A", "P29-B", "P29-C", "P29-D", "P29-E"];
    const nav = tabs(settings.map((screen) => ({ screen, label: screen === "P29-A" ? "General" : screen === "P29-B" ? "Security" : screen === "P29-C" ? "Notifications" : screen === "P29-D" ? "Integrations" : "Source Preference" })), active);
    nav.dataset.component = "SettingsNavigation";
    const childFrame = document.createElement("div");
    childFrame.className = "r02-settings-child";
    childFrame.dataset.component = "SettingsChildFrame";
    childFrame.append(child);
    frame.append(nav, childFrame);
    return frame;
}
export function linkTo(screen, label, params = {}) {
    const link = document.createElement("a");
    link.href = routeFor(screen, params);
    link.textContent = label;
    return link;
}
export function appendActionRow(parent, ...actions) {
    const row = document.createElement("div");
    row.className = "r02-action-row";
    row.append(...actions);
    parent.append(row);
}
export function installComponentStyles() {
    if (document.getElementById("r02-components"))
        return;
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
    .r04-auth-page { min-height: 100vh; display: grid; justify-items: center; align-content: center; gap: 28px; padding: 24px 16px; overflow: auto; background: var(--or-bg); color: var(--or-text); }
    .r04-auth-card, .r04-help-card { width: min(100%, 400px); padding: 32px 40px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); box-shadow: 0 8px 20px rgba(15,23,42,.04); }
    .r04-auth-brand { display: grid; gap: 4px; margin-bottom: 28px; }
    .r04-auth-brand strong { color: var(--or-primary); font-size: 18px; letter-spacing: .01em; }
    .r04-auth-brand span { color: var(--or-text-muted); font-size: 12px; }
    .r04-auth-heading { display: grid; gap: 6px; margin-bottom: 24px; }
    .r04-auth-heading h1, .r04-help-card h1 { margin: 0; font-size: 22px; line-height: 1.3; }
    .r04-auth-heading p, .r04-help-card > p { margin: 0; color: var(--or-text-muted); font-size: 13px; line-height: 1.6; }
    .r04-auth-form { display: grid; gap: 16px; }
    .r04-auth-field { display: grid; gap: 7px; color: var(--or-text); font-size: 13px; font-weight: 600; }
    .r04-auth-field input { width: 100%; min-height: 40px; box-sizing: border-box; border: 1px solid var(--or-outline); border-radius: 6px; padding: 9px 11px; background: var(--or-surface); color: var(--or-text); font: inherit; font-weight: 400; }
    .r04-auth-field input:focus { border-color: var(--or-primary); box-shadow: 0 0 0 2px rgba(37,99,235,.14); outline: 0; }
    .r04-auth-field:has(.r04-password-toggle) { position: relative; }
    .r04-auth-field:has(.r04-password-toggle) input { padding-right: 42px; }
    .r04-password-toggle { position: absolute; right: 8px; bottom: 6px; width: 28px; height: 28px; border: 0; background: transparent; color: var(--or-text-muted); cursor: pointer; }
    .r04-auth-actions { display: flex; justify-content: flex-end; }
    .r04-auth-actions a, .r04-help-card a, .r04-error-card a, .r04-not-found-card a { color: var(--or-primary-dark); font-size: 13px; text-decoration: none; }
    .r04-auth-actions a:hover, .r04-help-card a:hover, .r04-error-card a:hover, .r04-not-found-card a:hover { text-decoration: underline; }
    .r04-auth-submit { min-height: 40px; border: 1px solid var(--or-primary); border-radius: 6px; background: var(--or-primary); color: #fff; cursor: pointer; font: inherit; font-weight: 700; }
    .r04-auth-submit:hover:not(:disabled) { background: var(--or-primary-dark); }
    .r04-auth-submit:disabled { cursor: wait; opacity: .65; }
    .r04-auth-alert { padding: 10px 12px; border-radius: 6px; font-size: 12px; line-height: 1.5; }
    .r04-auth-alert-error { border: 1px solid var(--or-danger); background: var(--or-danger-soft); color: var(--or-danger); }
    .r04-auth-specimens { width: min(100%, 400px); padding-top: 20px; border-top: 1px solid var(--or-outline); }
    .r04-auth-specimens h2 { margin: 0 0 12px; color: var(--or-text-muted); font-size: 12px; font-weight: 700; }
    .r04-auth-state { display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; color: var(--or-text-muted); font-size: 12px; line-height: 1.5; }
    .r04-auth-state strong, .r04-auth-state span { display: block; }
    .r04-auth-state-icon { width: 16px; flex: 0 0 16px; text-align: center; font-weight: 700; }
    .r04-auth-state-validation .r04-auth-state-icon, .r04-auth-state-rate-limit .r04-auth-state-icon { color: var(--or-warning); }
    .r04-auth-state-failure .r04-auth-state-icon, .r04-auth-state-unavailable .r04-auth-state-icon { color: var(--or-danger); }
    .r04-help-card { width: min(100%, 460px); display: grid; gap: 20px; }
    .r04-help-icon { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: var(--or-primary-soft); color: var(--or-primary); font-size: 20px; }
    .r04-help-notice, .r04-help-safety { padding: 12px 14px; border-radius: 6px; font-size: 13px; line-height: 1.6; }
    .r04-help-notice { background: var(--or-info-soft); color: var(--or-text); }
    .r04-help-safety { border: 1px solid var(--or-warning); background: var(--or-warning-soft); color: var(--or-text); }
    .r04-help-section { display: grid; gap: 6px; }
    .r04-help-section h2 { margin: 0; font-size: 14px; }
    .r04-help-section p, .r04-help-section ul { margin: 0; color: var(--or-text-muted); font-size: 13px; line-height: 1.6; }
    .r04-help-section ul { padding-left: 18px; }
    .r04-help-footer { display: flex; flex-wrap: wrap; gap: 14px; padding-top: 4px; border-top: 1px solid var(--or-outline); }
    .r04-error-page, .r04-not-found-page { width: 100%; display: grid; place-items: center; min-height: 100%; padding: 24px; box-sizing: border-box; }
    .r04-error-card, .r04-not-found-card { width: min(100%, 560px); padding: 32px; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); box-shadow: 0 8px 20px rgba(15,23,42,.04); }
    .r04-error-card { display: grid; gap: 20px; }
    .r04-error-icon { color: var(--or-warning); font-size: 28px; }
    .r04-error-card h1, .r04-not-found-card h1 { margin: 0; font-size: 24px; line-height: 1.3; }
    .r04-error-card p, .r04-not-found-card p { margin: 0; color: var(--or-text-muted); font-size: 13px; line-height: 1.6; }
    .r04-error-meta { display: grid; gap: 8px; padding: 14px; background: var(--or-surface-muted); border-radius: 6px; }
    .r04-error-meta div { display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: 12px; font-size: 12px; line-height: 1.5; }
    .r04-error-meta dt { color: var(--or-text-muted); }
    .r04-error-meta dd { min-width: 0; margin: 0; overflow-wrap: anywhere; color: var(--or-text); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    .r04-error-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .r04-error-actions button { min-height: 36px; padding: 8px 14px; border: 1px solid var(--or-outline); border-radius: 6px; background: var(--or-surface); color: var(--or-text); cursor: pointer; font: inherit; }
    .r04-error-actions button:first-child { border-color: var(--or-primary); background: var(--or-primary); color: #fff; }
    .r04-error-actions button:hover { border-color: var(--or-primary); }
    .r04-not-found-page { min-height: 100vh; background: var(--or-bg); }
    .r04-not-found-card { display: grid; justify-items: center; gap: 16px; text-align: center; }
    .r04-not-found-code { color: var(--or-primary); font-size: 56px; font-weight: 800; line-height: 1; }
    .r04-not-found-card .r04-error-meta { width: 100%; text-align: left; }
    .r04-not-found-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 14px; }
    .or-frame-utility { min-height: calc(100vh - 96px); display: grid; place-items: center; background: var(--or-bg); border-color: transparent; }
    .or-frame-utility .or-route-outlet { width: min(100%, 640px); padding: 24px; box-sizing: border-box; }
    @media (max-width: 640px) { .r04-auth-card, .r04-help-card, .r04-error-card, .r04-not-found-card { padding: 24px; } .r04-error-page, .r04-not-found-page { padding: 16px; } .r04-error-meta div { grid-template-columns: 1fr; gap: 2px; } }
    @media (max-width: 640px) { .r02-table { min-width: 650px; } .r02-drawer { width: 100vw; } }
  `;
    document.head.appendChild(style);
}
