import { parseRoute } from "./router.js";
const SCREEN_LABELS = {
    P01: "登录", P02: "Dashboard", P03: "全局搜索", P04: "无权限", P05: "未找到", P06: "Observation",
    P07: "Observation 详情", P08: "关键词发现", P09: "关注关键词", P10: "趋势分析", P11: "关系图谱",
    P12: "Opportunity", P13: "Opportunity 详情", P14: "结构化分析", P15: "Research Workflow",
    P16: "Workflow 详情", P17: "Research Result", P18: "来源管理", P19: "Source Health", P20: "监控计划",
    P21: "运行记录", P22: "运行详情", P23: "Analysis Queue", P24: "告警收件箱", P25: "告警规则",
    P26: "审计日志", P27: "用户与角色", P28: "账户与安全", "P29-A": "设置 / 常规", "P29-B": "设置 / 安全",
    "P29-C": "设置 / 通知", "P29-D": "设置 / Integrations", "P29-E": "设置 / Source Preference", P30: "系统诊断",
};
export function renderApp(root) {
    const render = () => {
        const route = parseRoute();
        root.replaceChildren(renderSkeleton(route));
    };
    window.addEventListener("hashchange", render);
    render();
}
function renderSkeleton(route) {
    const wrapper = document.createElement("main");
    wrapper.dataset.screen = route.screen;
    wrapper.innerHTML = `<section aria-labelledby="skeleton-title"><p>R02 route skeleton</p><h1 id="skeleton-title">${SCREEN_LABELS[route.screen] ?? route.screen}</h1><p>AppShell and shared frame foundation are scheduled for T142/T143.</p></section>`;
    return wrapper;
}
