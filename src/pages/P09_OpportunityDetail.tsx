import React, { useState } from 'react';
import {
  Edit3,
  BookOpen,
  ArrowUpRight,
  User,
  Shield,
  Layers,
  ChevronRight,
  Clock,
  TrendingUp,
  Share2,
  Bookmark,
  CheckCircle2,
  Briefcase,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { MOCK_OPPORTUNITIES } from '../mock/data';
import { OpportunityDetail, getOpportunity } from '../features/opportunities/api';
import { useAsyncResource } from '../app/useAsyncResource';
import { EmptyState, ErrorState, LoadingState } from '../components/common/AsyncState';
import { useRouter } from '../router/RouterContext';
import './P09_OpportunityDetail.css';

const useLiveApi = import.meta.env.VITE_ENABLE_API === 'true';

function toOpportunityDetail(detail: OpportunityDetail) {
  const priority = detail.score >= 75 ? '高' : detail.score >= 55 ? '中' : '低';
  const status = detail.stage === 'DORMANT' ? '已归档' : detail.research.status === 'TRACKING' ? '持续跟踪' : detail.research.status === 'NEW' ? '新发现' : '研判中';
  return {
    id: detail.public_id,
    name: detail.title,
    category: detail.keywords[0]?.keyword || '未分类',
    score: Math.round(detail.score),
    priority: priority as '高' | '中' | '低',
    status: status as '研判中' | '新发现' | '持续跟踪' | '已忽略' | '已归档',
    evidenceCount: detail.evidence_count,
    marketSize: '待研究',
    growthRate: `风险评分 ${Math.round(detail.risk_score)}`,
    competition: '待研究',
    barrier: '待研究',
    owner: '尚未分配',
    ownerRole: '负责人工作流待接入',
    updatedAt: detail.last_seen_at,
    summary: detail.analysis.summary || '当前没有可展示的结构化分析摘要。',
    drivers: detail.keywords.map((row) => `${row.keyword}（${row.role}，权重 ${row.weight}）`),
    keyRisks: detail.analysis.risk_notes ? [detail.analysis.risk_notes] : [],
    timeline: detail.evidence.map((row) => ({
      source: row.source,
      title: row.title,
      time: new Date(row.observed_at).toLocaleString('zh-CN', { hour12: false }),
      reliability: `${row.quality} 级证据`,
    })),
    suggestedSteps: [
      { title: '补充市场证据', desc: '等待研究工作流接入后创建任务。' },
      { title: '评估风险项', desc: '等待状态与负责人工作流接入。' },
      { title: '启动结构化研究', desc: '等待研究领域模型与异步任务接入。' },
    ],
  };
}

export const P09_OpportunityDetail: React.FC = () => {
  const { navigate, entityParams } = useRouter();
  const [activeTab, setActiveTab] = useState('overview');
  const opportunityResource = useAsyncResource(
    (signal) => useLiveApi && entityParams.opportunityId
      ? getOpportunity(entityParams.opportunityId, signal)
      : Promise.resolve(undefined),
    [entityParams.opportunityId],
  );
  const opp = useLiveApi && opportunityResource.data ? toOpportunityDetail(opportunityResource.data) : !useLiveApi ? MOCK_OPPORTUNITIES[0] : undefined;

  if (useLiveApi && opportunityResource.phase === 'loading') return <LoadingState lines={8} />;
  if (useLiveApi && opportunityResource.phase === 'error' && opportunityResource.error) return <ErrorState error={opportunityResource.error} onRetry={opportunityResource.reload} />;
  if (!opp) return <EmptyState title="未找到机会" description="该机会可能已被归档，或链接使用了无效的公共 ID。" />;

  return (
    <div className="opportunity-detail">
      <Header
        breadcrumbs={[
          { label: '机会', path: '/opportunities' },
          { label: '机会详情' },
        ]}
        title={opp.name}
        subtitle={`${opp.category} · ${opp.priority}优先级`}
        actions={
          <>
            <button
              disabled
              title="状态工作流待后端接入后开放"
              className="btn btn-secondary"
            >
              <Edit3 size={14} />
              <span>修改状态（待接入）</span>
            </button>
            <button
              disabled
              title="负责人工作流待后端接入后开放"
              className="btn btn-secondary"
            >
              <User size={14} />
              <span>分配负责人（待接入）</span>
            </button>
            <button
              disabled
              title="结构化分析工作流待后端接入后开放"
              className="btn btn-secondary"
            >
              <Sparkles size={14} />
              <span>结构化分析（待接入）</span>
            </button>
            <button
              disabled
              title="研究工作流待后端接入后开放"
              className="btn btn-primary"
            >
              <BookOpen size={14} />
              <span>启动研究（待接入）</span>
            </button>
          </>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={(key) => {
          if (key === 'analysis') navigate(`/opportunities/${opp.id}/analysis`);
          else if (key === 'graph') navigate('/graph');
          else if (key === 'trends') navigate('/trends');
          else setActiveTab(key);
        }}
        items={[
          { key: 'overview', label: '概览' },
          { key: 'evidence', label: '证据', count: opp.evidenceCount },
          { key: 'trends', label: '趋势' },
          { key: 'graph', label: '图谱' },
          { key: 'analysis', label: '分析' },
          { key: 'research', label: '研究' },
          { key: 'notes', label: '备注' },
        ]}
      />

      {/* Top 4 KPI Cards */}
      <div className="opportunity-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 20 }}>
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>机会评分</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--color-success)' }}>
              {opp.score}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', fontWeight: 600 }}>
              较昨日 ↑ 4
            </span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>市场规模</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
              {opp.marketSize}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {opp.growthRate}
            </span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>竞争强度</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
              中等
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              主要竞品 8 家
            </span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>进入壁垒</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
              中等
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              技术 + 数据
            </span>
          </div>
        </div>
      </div>

      {/* Main 2-Column Layout */}
      <div className="opportunity-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20, marginBottom: 20 }}>
        {/* Left Area: Summary + Drivers + Evidence Timeline */}
        <div className="opportunity-narrative" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Card 1: 机会摘要 & 驱动因素 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              机会摘要
            </h3>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 18 }}>
              {opp.summary}
            </p>

            <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              关键驱动因素
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {opp.drivers.map((drv, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>•</span>
                  <span>{drv}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Card 2: 证据时间线 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
                证据时间线
              </h3>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
                查看全部 ({opp.evidenceCount})
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {opp.timeline.map((tl, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--color-primary)', marginTop: 5, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                      {tl.source} : {tl.title}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>
                      {tl.time} · {tl.reliability}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Sidebar: Status, Owner, Quick Actions */}
        <div className="opportunity-sidebar" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Card 1: 当前状态 */}
          <div className="card">
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
              当前状态
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>评分</div>
                <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>
                  {opp.score}
                </div>
              </div>
              <StatusBadge status={opp.status} type="status" />
            </div>

            <div style={{ paddingTop: 12, borderTop: '1px solid var(--border-subtle)', marginBottom: 14 }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>负责人</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {opp.owner}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{opp.ownerRole}</div>
            </div>

            {/* Quick Actions */}
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                快速操作
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <button
                  onClick={() => setActiveTab('evidence')}
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', justifyContent: 'flex-start' }}
                >
                  查看相关证据
                </button>
                <button
                  onClick={() => navigate('/trends')}
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', justifyContent: 'flex-start' }}
                >
                  查看趋势分析
                </button>
                <button
                  onClick={() => navigate('/graph')}
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', justifyContent: 'flex-start' }}
                >
                  查看关系图谱
                </button>
                <button
                  disabled
                  title="备注持久化待后端接入后开放"
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%', justifyContent: 'flex-start' }}
                >
                  添加备注
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Card: 推荐下一步 */}
      <div className="card opportunity-next">
        <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
          推荐下一步
        </h3>
        <div className="opportunity-next__list" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {opp.suggestedSteps.map((step, i) => (
            <button
              key={i}
              type="button"
              disabled
              title="下一步工作流待后端接入后开放"
              style={{
                padding: '16px 18px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: '#fafbfc',
                border: '1px solid var(--border-default)',
                cursor: 'pointer',
              }}
              className="hover-surface"
            >
              <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                {step.title}
              </h4>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {step.desc}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
