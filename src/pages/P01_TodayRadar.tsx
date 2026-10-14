import React from 'react';
import { AlertTriangle, ArrowUpRight, Building2, ChevronRight, Database, RefreshCw, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';
import { ChartFrame } from '../components/common/ChartFrame';
import { LineChart } from '../components/common/Charts';
import { ActionPanel, InsightBanner, Section, Surface } from '../components/common/Surface';
import { StatusBadge } from '../components/common/StatusBadge';
import { PageFrame, TriageLayout } from '../layouts/PageTemplates';
import { useRouter } from '../router/RouterContext';
import './P01_TodayRadar.css';

const opportunities = [
  { id: 'OPP-20260819-021', title: '企业级 AI 知识管理平台', reason: '采购信号与融资事件同时上升，适合优先验证私有化部署需求。', score: 85, freshness: '2 小时前', sector: '企业服务' },
  { id: 'OPP-20260819-022', title: '可持续航空燃料供应链优化', reason: '政策窗口与原料成本变动叠加，建议补充区域供给证据。', score: 72, freshness: '4 小时前', sector: '能源环保' },
  { id: 'OPP-20260819-023', title: '边缘计算在工业物联网中的应用', reason: '制造业客户扩容信号连续出现，需评估集成门槛。', score: 68, freshness: '6 小时前', sector: '工业互联网' },
];

const actions = [
  { label: '3 个来源连续采集失败', detail: 'TechCrunch、2 个行业源可能影响本周趋势完整性。', tone: 'risk' as const, target: '/sources/health' },
  { label: '12 条告警待研判', detail: '其中 2 条与企业 AI 机会相关。', tone: 'attention' as const, target: '/alerts' },
  { label: '7 个研究任务有更新', detail: '2 个结论已具备发布条件。', tone: 'neutral' as const, target: '/research' },
];

const trendData = [
  { label: '05-07', total: 390, abnormal: 190 }, { label: '05-08', total: 430, abnormal: 195 },
  { label: '05-09', total: 435, abnormal: 200 }, { label: '05-10', total: 540, abnormal: 220 },
  { label: '05-11', total: 660, abnormal: 225 }, { label: '05-12', total: 620, abnormal: 220 },
  { label: '05-13', total: 650, abnormal: 230 },
];

export const P01_TodayRadar: React.FC = () => {
  const { navigate } = useRouter();
  return (
    <PageFrame>
      <header className="radar-header">
        <div>
          <p className="radar-header__eyebrow">情报工作台 · 过去 24 小时</p>
          <h1>今日雷达</h1>
          <p>先处理高影响变化，再沿证据进入研判。</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/sources/health')}><RefreshCw size={16} />数据更新于 2 分钟前</button>
      </header>

      <TriageLayout
        brief={
          <InsightBanner title="企业 AI 信号升温，3 个机会值得优先研判。" action={<button type="button" className="btn btn-primary" onClick={() => navigate('/opportunities')}>查看优先机会<ChevronRight size={16} /></button>}>
            过去 24 小时发现 8 个机会；采购与融资类信号是本轮增长的主要来源。来源异常尚未影响该判断，但需要在发布前复核。
            <div className="radar-metrics" aria-label="今日关键指标">
              <span><strong>8</strong> 新机会</span><span><strong>23</strong> 重要信号</span><span><strong>5</strong> 异常趋势</span><span><strong>98.2%</strong> 数据源健康度</span>
            </div>
          </InsightBanner>
        }
        primary={
          <Surface padding="default">
            <Section title="优先机会" description="按影响、证据新鲜度与可行动性排序。" action={<button type="button" className="btn btn-ghost" onClick={() => navigate('/opportunities')}>机会池 <ChevronRight size={16} /></button>}>
              <div className="radar-opportunity-list">
                {opportunities.map((item, index) => <button key={item.id} type="button" className="radar-opportunity" onClick={() => navigate(`/opportunities/${item.id}`)}>
                  <span className="radar-opportunity__rank">0{index + 1}</span>
                  <span className="radar-opportunity__icon"><Building2 size={18} /></span>
                  <span className="radar-opportunity__content"><span className="radar-opportunity__title">{item.title}</span><span className="radar-opportunity__reason">{item.reason}</span><span className="radar-opportunity__meta">{item.sector} · {item.freshness}</span></span>
                  <span className="radar-opportunity__score"><StatusBadge status={String(item.score)} type="score" /><ArrowUpRight size={17} /></span>
                </button>)}
              </div>
            </Section>
          </Surface>
        }
        actionPanel={
          <ActionPanel title="需要处理" action={<button type="button" className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>全部告警</button>}>
            <div className="radar-actions">{actions.map(item => <button key={item.label} type="button" className={`radar-action radar-action--${item.tone}`} onClick={() => navigate(item.target)}>
              {item.tone === 'risk' ? <ShieldAlert size={18} /> : item.tone === 'attention' ? <AlertTriangle size={18} /> : <Sparkles size={18} />}<span><strong>{item.label}</strong><small>{item.detail}</small></span><ChevronRight size={16} />
            </button>)}</div>
          </ActionPanel>
        }
        supporting={
          <div className="radar-supporting">
            <ChartFrame title="信号变化" conclusion="过去 7 天总信号增长 67%，异常量保持在可控区间。" timeRange="2026-05-07 至 2026-05-13" source="采集与异常检测服务" action={<button type="button" className="btn btn-ghost btn-sm" onClick={() => navigate('/trends')}>趋势分析</button>}>
              <LineChart data={trendData} height={200} />
            </ChartFrame>
            <Surface padding="default">
              <Section title="系统可信度" description="优先保证结论可追溯，再扩大监控范围。" action={<button type="button" className="btn btn-ghost btn-sm" onClick={() => navigate('/settings/diagnostics')}>系统诊断</button>}>
                <div className="radar-health"><span><Database size={17} />数据源健康度 <strong>98.2%</strong></span><span><TrendingUp size={17} />运行中的监控计划 <strong>23 / 25</strong></span><span><AlertTriangle size={17} />需复核来源 <strong>3</strong></span></div>
              </Section>
            </Surface>
          </div>
        }
      />
    </PageFrame>
  );
};
