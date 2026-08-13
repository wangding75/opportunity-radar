export const R02_TOKENS = {
  colors: {
    background: "#f7f9fb",
    surface: "#ffffff",
    surfaceMuted: "#f1f5f9",
    surfaceStrong: "#e6e8ea",
    text: "#0f172a",
    textMuted: "#475569",
    outline: "#e2e8f0",
    outlineStrong: "#cbd5e1",
    primary: "#2563eb",
    primaryDark: "#004ac6",
    primarySoft: "#dbeafe",
    success: "#166534",
    successSoft: "#dcfce7",
    warning: "#92400e",
    warningSoft: "#fef3c7",
    danger: "#991b1b",
    dangerSoft: "#fee2e2",
    info: "#1e40af",
    infoSoft: "#dbeafe",
  },
  spacing: {xs: "4px", sm: "8px", md: "16px", lg: "24px", xl: "32px"},
  radius: {sm: "4px", md: "8px", lg: "16px", full: "9999px"},
  layout: {navWidth: "240px", topbarHeight: "72px", maxContent: "1440px"},
  typography: {body: "14px", small: "13px", label: "12px", title: "24px"},
} as const;

let installed = false;

export function installR02Theme(): void {
  if (installed || document.getElementById("r02-theme")) return;
  installed = true;
  const style = document.createElement("style");
  style.id = "r02-theme";
  style.textContent = `
    :root {
      --r02-bg: ${R02_TOKENS.colors.background};
      --r02-surface: ${R02_TOKENS.colors.surface};
      --r02-surface-muted: ${R02_TOKENS.colors.surfaceMuted};
      --r02-surface-strong: ${R02_TOKENS.colors.surfaceStrong};
      --r02-text: ${R02_TOKENS.colors.text};
      --r02-text-muted: ${R02_TOKENS.colors.textMuted};
      --r02-outline: ${R02_TOKENS.colors.outline};
      --r02-outline-strong: ${R02_TOKENS.colors.outlineStrong};
      --r02-primary: ${R02_TOKENS.colors.primary};
      --r02-primary-dark: ${R02_TOKENS.colors.primaryDark};
      --r02-primary-soft: ${R02_TOKENS.colors.primarySoft};
      --r02-success: ${R02_TOKENS.colors.success};
      --r02-success-soft: ${R02_TOKENS.colors.successSoft};
      --r02-warning: ${R02_TOKENS.colors.warning};
      --r02-warning-soft: ${R02_TOKENS.colors.warningSoft};
      --r02-danger: ${R02_TOKENS.colors.danger};
      --r02-danger-soft: ${R02_TOKENS.colors.dangerSoft};
      --r02-info: ${R02_TOKENS.colors.info};
      --r02-info-soft: ${R02_TOKENS.colors.infoSoft};
      --r02-nav-width: ${R02_TOKENS.layout.navWidth};
      --r02-topbar-height: ${R02_TOKENS.layout.topbarHeight};
      --r02-max-content: ${R02_TOKENS.layout.maxContent};
      color-scheme: light;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body { margin: 0; background: var(--r02-bg); color: var(--r02-text); font-family: Inter, "PingFang SC", "Microsoft YaHei", ui-sans-serif, system-ui, sans-serif; font-size: 14px; line-height: 1.45; }
    button, input, select, textarea { font: inherit; }
    button, a { -webkit-tap-highlight-color: transparent; }
    button { cursor: pointer; }
    a { color: inherit; }
    :focus-visible { outline: 3px solid rgba(37, 99, 235, .28); outline-offset: 2px; }
    .r02-app { min-height: 100vh; }
    .r02-shell { min-height: 100vh; display: grid; grid-template-columns: var(--r02-nav-width) minmax(0, 1fr); }
    .r02-sidebar { background: var(--r02-surface); border-right: 1px solid var(--r02-outline); min-height: 100vh; padding: 20px 12px; position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; gap: 20px; }
    .r02-brand { display: flex; align-items: center; gap: 10px; padding: 4px 12px; text-decoration: none; }
    .r02-brand-mark { width: 30px; height: 30px; display: grid; place-items: center; border-radius: 8px; background: var(--r02-primary); color: white; font-weight: 700; }
    .r02-brand-copy { display: grid; gap: 1px; }
    .r02-brand-copy strong { font-size: 15px; letter-spacing: -.01em; }
    .r02-brand-copy span { color: var(--r02-text-muted); font-size: 11px; }
    .r02-nav { display: grid; gap: 3px; overflow: auto; }
    .r02-nav-group { padding: 10px 12px 5px; color: var(--r02-text-muted); font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
    .r02-nav-link { display: flex; align-items: center; gap: 10px; border: 0; border-left: 2px solid transparent; border-radius: 6px; background: transparent; color: var(--r02-text-muted); min-height: 38px; padding: 8px 12px; text-decoration: none; text-align: left; transition: background .15s ease, color .15s ease, border-color .15s ease; }
    .r02-nav-link:hover { background: var(--r02-surface-muted); color: var(--r02-text); }
    .r02-nav-link.is-active { background: var(--r02-primary-soft); border-left-color: var(--r02-primary); color: var(--r02-primary-dark); font-weight: 700; }
    .r02-nav-icon { width: 20px; text-align: center; font-size: 15px; }
    .r02-sidebar-footer { margin-top: auto; padding: 12px; border-top: 1px solid var(--r02-outline); color: var(--r02-text-muted); font-size: 12px; }
    .r02-main { min-width: 0; }
    .r02-topbar { min-height: var(--r02-topbar-height); background: rgba(255,255,255,.94); border-bottom: 1px solid var(--r02-outline); display: flex; align-items: center; gap: 16px; padding: 12px 32px; position: sticky; top: 0; z-index: 10; }
    .r02-topbar-title { min-width: 180px; font-size: 13px; font-weight: 700; }
    .r02-topbar-search { display: flex; align-items: center; gap: 8px; max-width: 520px; flex: 1; border: 1px solid var(--r02-outline); border-radius: 8px; background: var(--r02-surface-muted); color: var(--r02-text-muted); padding: 9px 12px; text-decoration: none; }
    .r02-topbar-search:hover { background: var(--r02-surface); border-color: var(--r02-outline-strong); }
    .r02-topbar-spacer { flex: 1; }
    .r02-topbar-user { display: flex; align-items: center; gap: 10px; color: var(--r02-text-muted); font-size: 13px; }
    .r02-avatar { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; background: var(--r02-primary-soft); color: var(--r02-primary-dark); font-weight: 700; }
    .r02-content { width: min(100%, var(--r02-max-content)); margin: 0 auto; padding: 32px; }
    .r02-page-frame { min-width: 0; }
    .r02-page-header { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 24px; }
    .r02-page-heading { min-width: 0; flex: 1; }
    .r02-breadcrumb { display: flex; align-items: center; gap: 6px; color: var(--r02-text-muted); font-size: 12px; margin-bottom: 8px; }
    .r02-page-title { margin: 0; font-size: 24px; line-height: 1.3; letter-spacing: -.02em; }
    .r02-page-subtitle { margin: 6px 0 0; color: var(--r02-text-muted); }
    .r02-page-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
    .r02-route-outlet { min-width: 0; }
    .r02-login { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
    .r02-login-card { width: min(100%, 440px); }
    .r02-skeleton { min-height: 280px; display: grid; place-items: center; border: 1px dashed var(--r02-outline-strong); border-radius: 12px; background: rgba(255,255,255,.56); color: var(--r02-text-muted); text-align: center; padding: 32px; }
    @media (max-width: 900px) {
      .r02-shell { grid-template-columns: 72px minmax(0, 1fr); }
      .r02-sidebar { padding: 16px 8px; }
      .r02-brand { justify-content: center; padding: 4px; }
      .r02-brand-copy, .r02-nav-group, .r02-nav-link span:not(.r02-nav-icon), .r02-sidebar-footer { display: none; }
      .r02-nav-link { justify-content: center; padding: 8px; }
      .r02-topbar, .r02-content { padding-left: 20px; padding-right: 20px; }
    }
    @media (max-width: 640px) {
      .r02-shell { display: block; }
      .r02-sidebar { min-height: auto; height: auto; position: sticky; top: 0; z-index: 20; border-right: 0; border-bottom: 1px solid var(--r02-outline); flex-direction: row; align-items: center; overflow-x: auto; }
      .r02-brand { flex: 0 0 auto; }
      .r02-nav { display: flex; flex: 1; overflow-x: auto; }
      .r02-nav-link { flex: 0 0 auto; min-width: 42px; }
      .r02-topbar { position: static; flex-wrap: wrap; }
      .r02-topbar-title { min-width: auto; }
      .r02-topbar-search { order: 3; max-width: none; flex-basis: 100%; }
      .r02-topbar-spacer { display: none; }
      .r02-content { padding: 20px 16px; }
      .r02-page-header { flex-direction: column; }
      .r02-page-actions { justify-content: flex-start; }
    }
  `;
  document.head.appendChild(style);
}
