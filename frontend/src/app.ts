import { parseRoute, type RouteState } from "./router.js";
import { createAppShell, renderFramePlaceholder } from "./shell.js";
import { installR02Theme } from "./theme.js";

const SCREEN_LABELS: Record<string, string> = {
  P01: "登录", P02: "Dashboard", P03: "全局搜索", P04: "无权限", P05: "未找到", P06: "Observation",
  P07: "Observation 详情", P08: "关键词发现", P09: "关注关键词", P10: "趋势分析", P11: "关系图谱",
  P12: "Opportunity", P13: "Opportunity 详情", P14: "结构化分析", P15: "Research Workflow",
  P16: "Workflow 详情", P17: "Research Result", P18: "来源管理", P19: "Source Health", P20: "监控计划",
  P21: "运行记录", P22: "运行详情", P23: "Analysis Queue", P24: "告警收件箱", P25: "告警规则",
  P26: "审计日志", P27: "用户与角色", P28: "账户与安全", "P29-A": "设置 / 常规", "P29-B": "设置 / 安全",
  "P29-C": "设置 / 通知", "P29-D": "设置 / Integrations", "P29-E": "设置 / Source Preference", P30: "系统诊断",
};

export function renderApp(root: HTMLElement): void {
  installR02Theme();
  const render = (): void => {
    const route = parseRoute();
    root.replaceChildren(route.screen === "P01" ? renderLoginPlaceholder() : createAppShell(route.screen, renderSkeleton(route)));
  };
  window.addEventListener("hashchange", render);
  render();
}

function renderSkeleton(route: RouteState): HTMLElement {
  const wrapper = renderFramePlaceholder(route.screen);
  wrapper.dataset.screen = route.screen;
  return wrapper;
}

function renderLoginPlaceholder(): HTMLElement {
  const wrapper = document.createElement("main");
  wrapper.className = "r02-login";
  wrapper.innerHTML = `<section class="r02-login-card r02-skeleton" aria-labelledby="login-title"><div><span class="r02-brand-mark">R</span><h1 id="login-title">Opportunity Radar</h1><p>Unauthenticated entry frame reserved for T144.</p></div></section>`;
  return wrapper;
}
