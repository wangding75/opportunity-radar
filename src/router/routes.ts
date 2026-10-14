export interface PageRouteConfig {
  id: string;
  title: string;
  path: string;
  module: string;
  primaryNav: '今日雷达' | '情报' | '机会' | '研究' | '监控' | '设置' | 'NONE';
  shell: 'APP_SHELL' | 'AUTH_SHELL' | 'MINIMAL_APP_SHELL';
}

export const PAGE_ROUTES: Record<string, PageRouteConfig> = {
  P01: { id: 'P01', title: '今日雷达', path: '/today', module: '情报发现', primaryNav: '今日雷达', shell: 'APP_SHELL' },
  P02: { id: 'P02', title: '情报列表', path: '/intelligence', module: '情报发现', primaryNav: '情报', shell: 'APP_SHELL' },
  P03: { id: 'P03', title: '情报详情', path: '/intelligence/INT-20260819-01842', module: '情报发现', primaryNav: '情报', shell: 'APP_SHELL' },
  P04: { id: 'P04', title: '关键词发现', path: '/keywords/discovery', module: '情报发现', primaryNav: '情报', shell: 'APP_SHELL' },
  P05: { id: 'P05', title: '关注关键词', path: '/keywords/tracked', module: '情报发现', primaryNav: '情报', shell: 'APP_SHELL' },
  P06: { id: 'P06', title: '趋势分析', path: '/trends', module: '情报发现', primaryNav: '情报', shell: 'APP_SHELL' },
  P07: { id: 'P07', title: '关系图谱', path: '/graph', module: '机会研判', primaryNav: '情报', shell: 'APP_SHELL' },
  P08: { id: 'P08', title: '机会池', path: '/opportunities', module: '机会研判', primaryNav: '机会', shell: 'APP_SHELL' },
  P09: { id: 'P09', title: '机会详情', path: '/opportunities/OPP-20260819-021', module: '机会研判', primaryNav: '机会', shell: 'APP_SHELL' },
  P10: { id: 'P10', title: '结构化分析', path: '/opportunities/OPP-20260819-021/analysis', module: '机会研判', primaryNav: '机会', shell: 'APP_SHELL' },
  P11: { id: 'P11', title: '研究工作流', path: '/research', module: '研究', primaryNav: '研究', shell: 'APP_SHELL' },
  P12: { id: 'P12', title: '研究工作流详情', path: '/research/RES-20260819-0011', module: '研究', primaryNav: '研究', shell: 'APP_SHELL' },
  P13: { id: 'P13', title: '研究结论', path: '/research/RES-20260819-0011/result', module: '研究', primaryNav: '研究', shell: 'APP_SHELL' },
  P14: { id: 'P14', title: '来源管理', path: '/sources', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P15: { id: 'P15', title: '来源详情', path: '/sources/reuters', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P16: { id: 'P16', title: '来源健康', path: '/sources/health', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P17: { id: 'P17', title: '监控计划', path: '/monitoring', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P18: { id: 'P18', title: '监控计划详情', path: '/monitoring/PLAN-2025-001', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P19: { id: 'P19', title: '运行记录', path: '/runs', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P20: { id: 'P20', title: '运行详情', path: '/runs/RUN-20260819-1048', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P21: { id: 'P21', title: '分析队列', path: '/analysis-queue', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P22: { id: 'P22', title: '告警中心', path: '/alerts', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P23: { id: 'P23', title: '告警规则', path: '/alert-rules', module: '监控与来源', primaryNav: '监控', shell: 'APP_SHELL' },
  P24: { id: 'P24', title: '工作区设置', path: '/settings/workspace', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P25: { id: 'P25', title: '成员管理', path: '/settings/members', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P26: { id: 'P26', title: '角色与权限', path: '/settings/roles', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P27: { id: 'P27', title: '账户安全', path: '/settings/security', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P28: { id: 'P28', title: '外部集成', path: '/settings/integrations', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P29: { id: 'P29', title: '审计日志', path: '/settings/audit', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P30: { id: 'P30', title: '系统诊断', path: '/settings/diagnostics', module: '设置与治理', primaryNav: '设置', shell: 'APP_SHELL' },
  P31: { id: 'P31', title: '全局搜索', path: '/search', module: '全局与系统状态', primaryNav: 'NONE', shell: 'APP_SHELL' },
  P32: { id: 'P32', title: '登录', path: '/login', module: '全局与系统状态', primaryNav: 'NONE', shell: 'AUTH_SHELL' },
  P33: { id: 'P33', title: '无权限', path: '/access-denied', module: '全局与系统状态', primaryNav: 'NONE', shell: 'MINIMAL_APP_SHELL' },
  P34: { id: 'P34', title: '页面未找到', path: '/404', module: '全局与系统状态', primaryNav: 'NONE', shell: 'MINIMAL_APP_SHELL' },
};

export const PATH_TO_PAGE: Record<string, string> = Object.entries(PAGE_ROUTES).reduce((acc, [id, cfg]) => {
  acc[cfg.path] = id;
  return acc;
}, {} as Record<string, string>);

export function matchRoute(pathname: string): PageRouteConfig {
  const cleanPath = pathname.split('?')[0].replace(/\/$/, '') || '/today';
  
  if (cleanPath === '' || cleanPath === '/') {
    return PAGE_ROUTES.P01;
  }
  
  const exactId = PATH_TO_PAGE[cleanPath];
  if (exactId && PAGE_ROUTES[exactId]) {
    return PAGE_ROUTES[exactId];
  }

  // Dynamic prefix matching
  if (cleanPath.startsWith('/intelligence/')) return PAGE_ROUTES.P03;
  if (cleanPath.startsWith('/opportunities/') && cleanPath.endsWith('/analysis')) return PAGE_ROUTES.P10;
  if (cleanPath.startsWith('/opportunities/')) return PAGE_ROUTES.P09;
  if (cleanPath.startsWith('/research/') && cleanPath.endsWith('/result')) return PAGE_ROUTES.P13;
  if (cleanPath.startsWith('/research/')) return PAGE_ROUTES.P12;
  if (cleanPath.startsWith('/sources/reuters')) return PAGE_ROUTES.P15;
  if (cleanPath.startsWith('/sources/health')) return PAGE_ROUTES.P16;
  if (cleanPath.startsWith('/monitoring/')) return PAGE_ROUTES.P18;
  if (cleanPath.startsWith('/runs/')) return PAGE_ROUTES.P20;

  return PAGE_ROUTES.P34; // 404
}

export interface RouteEntityParams {
  intelligenceId?: string;
  opportunityId?: string;
  researchId?: string;
  sourceId?: string;
  planId?: string;
  runId?: string;
}

/**
 * Extracts opaque UI identifiers without deciding their storage format. Once
 * BE-00 public IDs land, this remains the sole adapter between URL and data.
 */
export function getRouteEntityParams(pathname: string): RouteEntityParams {
  const clean = pathname.replace(/\/+$/, '');
  const match = (pattern: RegExp) => clean.match(pattern)?.[1];
  return {
    intelligenceId: match(/^\/intelligence\/([^/]+)$/),
    opportunityId: match(/^\/opportunities\/([^/]+)(?:\/analysis)?$/),
    researchId: match(/^\/research\/([^/]+)(?:\/result)?$/),
    sourceId: match(/^\/sources\/([^/]+)$/),
    planId: match(/^\/monitoring\/([^/]+)$/),
    runId: match(/^\/runs\/([^/]+)$/),
  };
}
