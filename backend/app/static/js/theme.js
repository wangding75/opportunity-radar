export const R04_TOKENS = {
    colors: {
        background: "#f8fafc",
        surface: "#ffffff",
        surfaceMuted: "#f1f5f9",
        surfaceStrong: "#e2e8f0",
        text: "#0f172a",
        textMuted: "#475569",
        outline: "#e2e8f0",
        outlineStrong: "#cbd5e1",
        primary: "#2563eb",
        primaryDark: "#1d4ed8",
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
    spacing: { xs: "4px", sm: "8px", md: "16px", lg: "24px", xl: "32px" },
    radius: { sm: "6px", md: "8px", lg: "8px", full: "9999px" },
    layout: { navWidth: "216px", brandHeight: "64px", topbarHeight: "56px", contentX: "24px", contentY: "20px" },
    typography: { body: "14px", small: "13px", label: "12px", title: "20px" },
};
// Keep the old export name as a source-compatibility bridge while pages are migrated
// task-by-task. It points to the R04 values and is not a second visual theme.
export const R02_TOKENS = R04_TOKENS;
let installed = false;
export function installR04Theme() {
    if (installed || document.getElementById("r04-theme"))
        return;
    installed = true;
    const style = document.createElement("style");
    style.id = "r04-theme";
    style.textContent = `
    :root {
      --or-bg: ${R04_TOKENS.colors.background};
      --or-surface: ${R04_TOKENS.colors.surface};
      --or-surface-muted: ${R04_TOKENS.colors.surfaceMuted};
      --or-surface-strong: ${R04_TOKENS.colors.surfaceStrong};
      --or-text: ${R04_TOKENS.colors.text};
      --or-text-muted: ${R04_TOKENS.colors.textMuted};
      --or-outline: ${R04_TOKENS.colors.outline};
      --or-outline-strong: ${R04_TOKENS.colors.outlineStrong};
      --or-primary: ${R04_TOKENS.colors.primary};
      --or-primary-dark: ${R04_TOKENS.colors.primaryDark};
      --or-primary-soft: ${R04_TOKENS.colors.primarySoft};
      --or-success: ${R04_TOKENS.colors.success};
      --or-success-soft: ${R04_TOKENS.colors.successSoft};
      --or-warning: ${R04_TOKENS.colors.warning};
      --or-warning-soft: ${R04_TOKENS.colors.warningSoft};
      --or-danger: ${R04_TOKENS.colors.danger};
      --or-danger-soft: ${R04_TOKENS.colors.dangerSoft};
      --or-info: ${R04_TOKENS.colors.info};
      --or-info-soft: ${R04_TOKENS.colors.infoSoft};
      --or-nav-width: ${R04_TOKENS.layout.navWidth};
      --or-brand-height: ${R04_TOKENS.layout.brandHeight};
      --or-topbar-height: ${R04_TOKENS.layout.topbarHeight};
      --or-content-x: ${R04_TOKENS.layout.contentX};
      --or-content-y: ${R04_TOKENS.layout.contentY};

      /* Compatibility aliases for non-visual helpers being migrated later. */
      --r02-bg: var(--or-bg);
      --r02-surface: var(--or-surface);
      --r02-surface-muted: var(--or-surface-muted);
      --r02-surface-strong: var(--or-surface-strong);
      --r02-text: var(--or-text);
      --r02-text-muted: var(--or-text-muted);
      --r02-outline: var(--or-outline);
      --r02-outline-strong: var(--or-outline-strong);
      --r02-primary: var(--or-primary);
      --r02-primary-dark: var(--or-primary-dark);
      --r02-primary-soft: var(--or-primary-soft);
      --r02-success: var(--or-success);
      --r02-success-soft: var(--or-success-soft);
      --r02-warning: var(--or-warning);
      --r02-warning-soft: var(--or-warning-soft);
      --r02-danger: var(--or-danger);
      --r02-danger-soft: var(--or-danger-soft);
      --r02-info: var(--or-info);
      --r02-info-soft: var(--or-info-soft);
      color-scheme: light;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { width: 100%; height: 100%; }
    body { margin: 0; overflow: hidden; background: var(--or-bg); color: var(--or-text); font-family: Inter, "PingFang SC", "Microsoft YaHei", ui-sans-serif, system-ui, sans-serif; font-size: 14px; line-height: 1.45; }
    #app { width: 100%; height: 100%; }
    button, input, select, textarea { font: inherit; }
    button, a { -webkit-tap-highlight-color: transparent; }
    button { cursor: pointer; }
    button:disabled { cursor: not-allowed; }
    a { color: inherit; }
    :focus-visible { outline: 3px solid rgba(37, 99, 235, .28); outline-offset: 2px; }

    .or-app-shell { width: 100%; height: 100%; min-width: 0; }
    .or-sidebar { position: fixed; inset: 0 auto 0 0; z-index: 20; width: var(--or-nav-width); height: 100%; display: flex; flex-direction: column; background: var(--or-surface); border-right: 1px solid var(--or-outline); }
    .or-brand { height: var(--or-brand-height); flex: 0 0 var(--or-brand-height); display: flex; flex-direction: column; justify-content: center; padding: 0 24px; border-bottom: 1px solid var(--or-outline); color: var(--or-text); text-decoration: none; }
    .or-brand strong { font-size: 15px; line-height: 1.15; letter-spacing: -.01em; }
    .or-brand span { margin-top: 3px; color: var(--or-text-muted); font-size: 11px; font-weight: 500; }
    .or-nav { flex: 1; min-height: 0; overflow-y: auto; padding: 16px 12px; }
    .or-nav-section { margin: 0 0 4px; }
    .or-nav-primary, .or-nav-child, .or-sidebar-footer a { display: flex; align-items: center; gap: 12px; width: 100%; border: 0; border-radius: 4px; color: var(--or-text-muted); text-decoration: none; text-align: left; transition: background .15s ease, color .15s ease; }
    .or-nav-primary { min-height: 40px; padding: 8px 12px; font-size: 13px; font-weight: 500; }
    .or-nav-primary:hover, .or-nav-child:hover, .or-sidebar-footer a:hover { background: var(--or-surface-muted); color: var(--or-text); }
    .or-nav-primary.is-active { position: relative; background: var(--or-primary-soft); color: var(--or-primary-dark); font-weight: 700; }
    .or-nav-primary.is-active::before { content: ""; position: absolute; left: 0; top: 20%; width: 3px; height: 60%; border-radius: 0 3px 3px 0; background: var(--or-primary); }
    .or-nav-icon { width: 18px; flex: 0 0 18px; color: currentColor; font-size: 18px; line-height: 1; text-align: center; }
    .or-nav-chevron { margin-left: auto; font-size: 14px; }
    .or-nav-children { display: grid; gap: 2px; margin: 2px 0 6px 27px; padding-left: 12px; border-left: 1px solid var(--or-outline-strong); }
    .or-nav-child { min-height: 32px; padding: 6px 10px; font-size: 12px; }
    .or-nav-child.is-active { color: var(--or-primary-dark); font-weight: 700; }
    .or-sidebar-footer { flex: 0 0 auto; display: grid; gap: 2px; padding: 12px; border-top: 1px solid var(--or-outline); }
    .or-sidebar-footer a { min-height: 32px; padding: 6px 12px; font-size: 12px; }

    .or-main { min-width: 0; height: 100%; margin-left: var(--or-nav-width); display: flex; flex-direction: column; }
    .or-topbar { position: fixed; top: 0; right: 0; left: var(--or-nav-width); z-index: 10; height: var(--or-topbar-height); display: flex; align-items: center; gap: 16px; padding: 0 24px; background: var(--or-surface); border-bottom: 1px solid var(--or-outline); }
    .or-topbar-search { position: relative; display: flex; align-items: center; gap: 10px; width: min(480px, 100%); height: 36px; padding: 0 12px; border: 1px solid transparent; border-radius: 4px; background: var(--or-surface-muted); color: var(--or-text-muted); text-decoration: none; font-size: 13px; }
    .or-topbar-search:hover { border-color: var(--or-outline-strong); background: var(--or-surface); }
    .or-topbar-search-icon { color: var(--or-text); font-size: 18px; line-height: 1; }
    .or-topbar-spacer { flex: 1; }
    .or-topbar-actions { display: flex; align-items: center; gap: 6px; }
    .or-topbar-action { position: relative; display: grid; place-items: center; width: 32px; height: 32px; padding: 0; border: 0; border-radius: 50%; background: transparent; color: var(--or-text-muted); font-size: 19px; }
    .or-topbar-action:hover { background: var(--or-surface-muted); color: var(--or-primary); }
    .or-topbar-divider { width: 1px; height: 16px; margin: 0 8px; background: var(--or-outline-strong); }
    .or-avatar { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid var(--or-outline-strong); border-radius: 50%; background: var(--or-primary-soft); color: var(--or-primary-dark); font-size: 12px; font-weight: 700; text-decoration: none; }
    .or-notification-dot { position: absolute; top: 5px; right: 5px; width: 7px; height: 7px; border: 1px solid var(--or-surface); border-radius: 50%; background: #dc2626; }
    .or-content { min-width: 0; height: calc(100% - var(--or-topbar-height)); margin-top: var(--or-topbar-height); overflow: auto; padding: var(--or-content-y) var(--or-content-x); }
    .or-page-frame { min-width: 0; min-height: calc(100vh - 96px); overflow: hidden; border: 1px solid var(--or-outline-strong); border-radius: 8px; background: var(--or-surface); }
    .or-page-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; min-height: 104px; padding: 20px 30px; border-bottom: 1px solid var(--or-outline); background: var(--or-surface); }
    .or-page-heading { min-width: 0; }
    .or-breadcrumb { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; color: var(--or-text-muted); font-size: 12px; }
    .or-breadcrumb a { color: var(--or-primary-dark); text-decoration: none; }
    .or-breadcrumb a:hover { text-decoration: underline; }
    .or-page-title { margin: 0; color: var(--or-text); font-size: 20px; line-height: 1.2; letter-spacing: -.015em; }
    .or-page-subtitle { margin: 6px 0 0; color: var(--or-text-muted); font-size: 13px; }
    .or-route-outlet { min-width: 0; padding: 24px 30px 32px; }
    .or-placeholder { min-height: 240px; display: grid; place-items: center; padding: 32px; color: var(--or-text-muted); text-align: center; }

    @media (max-width: 900px) {
      .or-sidebar { width: 64px; }
      .or-main { margin-left: 64px; }
      .or-topbar { left: 64px; }
      .or-brand { padding: 0; align-items: center; }
      .or-brand strong { font-size: 0; }
      .or-brand strong::first-letter { font-size: 18px; }
      .or-brand span, .or-nav-primary > span:not(.or-nav-icon), .or-nav-chevron, .or-nav-children, .or-sidebar-footer a > span:not(.or-nav-icon) { display: none; }
      .or-nav { padding: 12px 8px; }
      .or-nav-primary, .or-sidebar-footer a { justify-content: center; padding: 8px; }
      .or-page-header { padding-inline: 20px; }
      .or-route-outlet { padding-inline: 20px; }
    }
    @media (max-width: 640px) {
      body { overflow: auto; }
      .or-sidebar { position: sticky; top: 0; width: 100%; height: 56px; flex-direction: row; }
      .or-brand { width: 156px; height: 56px; flex-basis: 156px; padding: 0 16px; align-items: flex-start; }
      .or-brand strong, .or-brand span, .or-nav-primary > span:not(.or-nav-icon), .or-sidebar-footer a > span:not(.or-nav-icon) { display: block; }
      .or-brand strong { font-size: 13px; }
      .or-brand span { font-size: 10px; }
      .or-nav { display: flex; gap: 4px; padding: 8px; overflow-x: auto; }
      .or-nav-section { flex: 0 0 auto; margin: 0; }
      .or-nav-primary { width: auto; white-space: nowrap; }
      .or-sidebar-footer { display: none; }
      .or-main { height: auto; min-height: calc(100vh - 56px); margin-left: 0; }
      .or-topbar { position: sticky; left: 0; height: auto; min-height: 56px; padding: 10px 16px; flex-wrap: wrap; }
      .or-topbar-search { order: 3; width: 100%; }
      .or-content { height: auto; min-height: calc(100vh - 112px); margin-top: 0; padding: 16px; }
      .or-page-header { align-items: flex-start; flex-direction: column; padding: 18px 16px; }
      .or-route-outlet { padding: 18px 16px 24px; }
    }
  `;
    document.head.appendChild(style);
}
// Existing imports outside the shell are migrated incrementally in later tasks.
export const installR02Theme = installR04Theme;
