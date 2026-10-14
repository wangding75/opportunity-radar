import React, { useState } from 'react';
import {
  Search,
  SlidersHorizontal,
  Bookmark,
  ChevronRight,
  ExternalLink,
  RotateCcw,
  Sparkles,
  Layers,
  FileText,
  Activity,
  AlertTriangle,
  User,
  HelpCircle,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P31_GlobalSearch: React.FC = () => {
  const { navigate, currentState, openState, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('ALL');
  const [keyword, setKeyword] = useState('AI Agent');

  const isEmptyState = currentState === 'P31-S01';

  const typeSegments = [
    { label: '机会', count: 168, percentage: '13%', color: '#2563eb' },
    { label: '情报', count: 856, percentage: '67%', color: '#10b981' },
    { label: '研究', count: 92, percentage: '7%', color: '#8b5cf6' },
    { label: '来源', count: 64, percentage: '5%', color: '#06b6d4' },
    { label: '监控计划', count: 36, percentage: '3%', color: '#f59e0b' },
    { label: '告警', count: 28, percentage: '2%', color: '#ef4444' },
    { label: '成员', count: 40, percentage: '3%', color: '#ec4899' },
  ];

  return (
    <div>
      <Header
        title="全局搜索"
        subtitle="搜索机会、情报、研究、来源、关键词、监控等所有内容"
        actions={
          <button
            onClick={() => showToast('已保存当前搜索条件', 'success')}
            className="btn btn-secondary"
          >
            <Bookmark size={14} />
            <span>保存搜索条件</span>
          </button>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'ALL', label: '全部', count: 1284 },
          { key: 'OPP', label: '机会', count: 168 },
          { key: 'INT', label: '情报', count: 856 },
          { key: 'RES', label: '研究', count: 92 },
          { key: 'SRC', label: '来源', count: 64 },
          { key: 'PLAN', label: '监控计划', count: 36 },
          { key: 'ALT', label: '告警', count: 28 },
          { key: 'MEM', label: '成员', count: 40 },
        ]}
      />

      {/* Main Split: Left Filters + Center Results + Right Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr 300px', gap: 16 }}>
        {/* Left: Filter Sidebar */}
        <div className="card" style={{ padding: '14px 16px', height: 'fit-content' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>筛选条件</span>
            <span onClick={() => showToast('已清空筛选条件', 'info')} style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>清空</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>时间范围</div>
              <select className="input-base" style={{ width: '100%', height: 28, fontSize: '12px' }}>
                <option>全部时间</option>
                <option>近24小时</option>
                <option>近7天</option>
              </select>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>领域</div>
              <select className="input-base" style={{ width: '100%', height: 28, fontSize: '12px' }}>
                <option>选择领域</option>
                <option>人工智能</option>
              </select>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>地区</div>
              <select className="input-base" style={{ width: '100%', height: 28, fontSize: '12px' }}>
                <option>选择地区</option>
                <option>全球</option>
              </select>
            </div>
            <button
              onClick={() => openState(isEmptyState ? '' : 'P31-S01')}
              className="btn btn-secondary btn-sm"
              style={{ marginTop: 8, fontSize: '12px' }}
            >
              {isEmptyState ? '切换为有结果状态' : '切换为无结果状态 (P31-S01)'}
            </button>
          </div>
        </div>

        {/* Center: Search Results / Empty State */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {isEmptyState ? (
            /* P31-S01 No Results State */
            <div className="card" style={{ padding: '48px 24px', textAlign: 'center' }}>
              <div style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: '#f1f5f9', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <Search size={28} />
              </div>
              <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                未找到与 "{keyword}" 相关的内容
              </h3>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 20 }}>
                请检查您的拼写，或尝试使用更通用的搜索词、减少筛选条件。
              </p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
                {['AI Agent', '大模型', '新能源', '人形机器人', '芯片'].map((kw, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setKeyword(kw);
                      openState('');
                    }}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '12px' }}
                  >
                    {kw}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Normal Results List */
            <>
              {/* Result 1: Opportunity */}
              <div
                onClick={() => navigate('/opportunities/OPP-20260819-021')}
                className="card hover-surface"
                style={{ padding: '16px 18px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '1px 6px', borderRadius: 2, fontWeight: 600 }}>机会</span>
                      <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>企业级 AI Agent 平台</h4>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: 6 }}>
                      机会评分 86 · 研判中 · 32 条证据 · AI Agent · 企业服务 · 全球
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>负责人: 张明 · 创建时间: 2026-08-16</div>
                  </div>
                  <StatusBadge status="86" type="score" />
                </div>
              </div>

              {/* Result 2: Intelligence */}
              <div
                onClick={() => navigate('/intelligence/INT-20260819-01842')}
                className="card hover-surface"
                style={{ padding: '16px 18px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: '12px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '1px 6px', borderRadius: 2, fontWeight: 600 }}>情报</span>
                  <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>Microsoft 发布新的 Agent orchestration 能力</h4>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 6 }}>
                  Reuters · 15 分钟前 · 可信度 92% · Microsoft 在 Build 大会上宣布全新的 Agent orchestration 框架，支持多 Agent 协同工作。
                </p>
              </div>

              {/* Result 3: Research */}
              <div
                onClick={() => navigate('/research/RES-20260819-0011')}
                className="card hover-surface"
                style={{ padding: '16px 18px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: '12px', color: '#8b5cf6', backgroundColor: '#f5f3ff', padding: '1px 6px', borderRadius: 2, fontWeight: 600 }}>研究</span>
                  <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>AI Agent 企业应用商业化研究</h4>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>已完成 · 标准深度 · 2026-08-15 · 负责人: 李想</div>
              </div>

              <Pagination total={1284} pageSize={3} currentPage={1} />
            </>
          )}
        </div>

        {/* Right: Analytics & Recent Searches */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Result Type Distribution */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              结果类型分布
            </h3>
            <DonutChart total={1284} totalLabel="总计" segments={typeSegments} size={110} />
          </div>

          {/* Related Keywords */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              相关关键词
            </h3>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['AI Agent (1,284)', 'Agent Framework (642)', '多 Agent 协同 (398)', 'AutoGPT (215)', 'LLM (1,120)'].map((kw, i) => (
                <span key={i} style={{ fontSize: '12px', padding: '2px 6px', borderRadius: 4, backgroundColor: '#f1f5f9', color: 'var(--text-secondary)' }}>
                  {kw}
                </span>
              ))}
            </div>
          </div>

          {/* Recent Searches */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                最近搜索
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer' }}>清除全部历史</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px', color: 'var(--text-secondary)' }}>
              <div>• AI Agent (刚刚)</div>
              <div>• 企业服务 (2 小时前)</div>
              <div>• AI 浏览器插件 (昨天)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
