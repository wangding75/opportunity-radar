import React, { useState } from 'react';
import {
  Search,
  Filter,
  Plus,
  Trash2,
  GitMerge,
  Activity,
  Briefcase,
  ExternalLink,
  ChevronRight,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Check,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { Sparkline } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P04_KeywordDiscovery: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('new');
  const [selectedKeyword, setSelectedKeyword] = useState('AI 浏览器插件');
  const [selectedCategory, setSelectedCategory] = useState('全部领域');
  const [timeRange, setTimeRange] = useState('7d');

  const keywordsList = [
    {
      id: 'KW-01',
      name: 'AI 浏览器插件',
      tags: ['产品/工具', 'AI应用'],
      volume: '18.7K',
      growth: '+38%',
      growthType: 'up' as const,
      sources: 24,
      relevance: 92,
      confidence: 86,
      time: '5分钟前',
      spark: [20, 25, 35, 30, 45, 60, 75, 95],
    },
    {
      id: 'KW-02',
      name: '零代码数据分析',
      tags: ['产品/工具', '数据分析'],
      volume: '9.2K',
      growth: '+26%',
      growthType: 'up' as const,
      sources: 18,
      relevance: 88,
      confidence: 78,
      time: '27分钟前',
      spark: [30, 32, 40, 45, 50, 65, 70, 80],
    },
    {
      id: 'KW-03',
      name: 'AI 会议纪要',
      tags: ['产品/工具', '办公效率'],
      volume: '6.5K',
      growth: '+18%',
      growthType: 'up' as const,
      sources: 16,
      relevance: 84,
      confidence: 71,
      time: '43分钟前',
      spark: [40, 45, 42, 50, 55, 60, 68, 72],
    },
    {
      id: 'KW-04',
      name: '多模态搜索',
      tags: ['技术/概念', '搜索'],
      volume: '4.1K',
      growth: '+64%',
      growthType: 'up' as const,
      sources: 22,
      relevance: 81,
      confidence: 68,
      time: '1小时前',
      spark: [15, 20, 30, 40, 55, 70, 85, 98],
    },
    {
      id: 'KW-05',
      name: '本地部署大模型',
      tags: ['技术/概念', '大模型'],
      volume: '3.6K',
      growth: '-6%',
      growthType: 'down' as const,
      sources: 15,
      relevance: 77,
      confidence: 63,
      time: '1小时前',
      spark: [60, 58, 55, 52, 50, 48, 47, 46],
    },
    {
      id: 'KW-06',
      name: 'AI 代码审查',
      tags: ['产品/工具', '开发工具'],
      volume: '2.8K',
      growth: '+22%',
      growthType: 'up' as const,
      sources: 12,
      relevance: 74,
      confidence: 61,
      time: '1小时前',
      spark: [35, 38, 40, 42, 48, 52, 56, 62],
    },
    {
      id: 'KW-07',
      name: '智能体应用商店',
      tags: ['产品/概念', 'AI应用'],
      volume: '2.3K',
      growth: '+71%',
      growthType: 'up' as const,
      sources: 20,
      relevance: 79,
      confidence: 64,
      time: '2小时前',
      spark: [10, 15, 25, 35, 50, 65, 80, 92],
    },
    {
      id: 'KW-08',
      name: '向量数据库选型',
      tags: ['技术/概念', '数据库'],
      volume: '2.1K',
      growth: '-9%',
      growthType: 'down' as const,
      sources: 9,
      relevance: 66,
      confidence: 49,
      time: '2小时前',
      spark: [50, 48, 46, 44, 42, 40, 38, 36],
    },
  ];

  return (
    <div>
      <Header
        title="关键词发现"
        subtitle="从多源观察中发现具有增长潜力的关键词候选，评估价值并沉淀为可监控、可运营的机会资产"
        extra={
          <button
            onClick={() => showToast('关键词评估指南已打开', 'info')}
            style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}
          >
            <span>如何评估关键词？</span>
          </button>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'new', label: '新发现', count: 128 },
          { key: 'tracked', label: '已关注', count: 34 },
          { key: 'ignored', label: '已忽略', count: 16 },
        ]}
      />

      {/* Main Split Layout: Table (Left) + Detail Panel (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', gap: 16 }}>
        {/* Left: Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Table Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: 260 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input type="text" placeholder="搜索关键词或主题" className="input-base" style={{ width: '100%', paddingLeft: 30, height: 32 }} />
            </div>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>领域: 全部领域</option>
              <option>人工智能</option>
              <option>新能源</option>
            </select>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>时间: 近7天</option>
              <option>近24小时</option>
              <option>近30天</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}><input type="checkbox" /></th>
                <th>关键词</th>
                <th style={{ width: 90 }}>月搜索量</th>
                <th style={{ width: 110 }}>增长趋势</th>
                <th style={{ width: 80, textAlign: 'center' }}>来源数</th>
                <th style={{ width: 80, textAlign: 'center' }}>相关度</th>
                <th style={{ width: 80, textAlign: 'center' }}>置信度</th>
                <th style={{ width: 90 }}>最新观测</th>
              </tr>
            </thead>
            <tbody>
              {keywordsList.map((kw) => {
                const isSelected = kw.name === selectedKeyword;
                return (
                  <tr
                    key={kw.id}
                    onClick={() => setSelectedKeyword(kw.name)}
                    style={{ backgroundColor: isSelected ? 'var(--color-primary-light)' : 'transparent' }}
                  >
                    <td><input type="checkbox" checked={isSelected} readOnly /></td>
                    <td>
                      <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {kw.name}
                      </div>
                      <div style={{ display: 'flex', gap: 4, marginTop: 2 }}>
                        {kw.tags.map((t, idx) => (
                          <span key={idx} style={{ fontSize: '12px', padding: '0 4px', backgroundColor: '#f1f5f9', borderRadius: 2, color: 'var(--text-muted)' }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>{kw.volume}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: kw.growthType === 'up' ? 'var(--color-success)' : 'var(--color-danger)' }}>
                          {kw.growth}
                        </span>
                        <Sparkline points={kw.spark} color={kw.growthType === 'up' ? '#10b981' : '#ef4444'} width={45} height={16} />
                      </div>
                    </td>
                    <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>{kw.sources}</td>
                    <td style={{ textAlign: 'center' }}><StatusBadge status={String(kw.relevance)} type="score" /></td>
                    <td style={{ textAlign: 'center' }}><StatusBadge status={String(kw.confidence)} type="score" /></td>
                    <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{kw.time}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <Pagination total={128} pageSize={10} currentPage={1} />
        </div>

        {/* Right: Selected Keyword Preview Panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 'fit-content' }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>&lt; 返回列表</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>1 / 128</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                {selectedKeyword}
              </h2>
              <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 6px', borderRadius: 4 }}>
                  产品/工具
                </span>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '2px 6px', borderRadius: 4 }}>
                  AI应用
                </span>
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>86</span>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>综合得分</div>
            </div>
          </div>

          {/* Metrics Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '10px 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>月搜索量</div>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>18.7K</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>增长率</div>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-success)' }}>+38%</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>来源数</div>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>24</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>观测时间</div>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>5分钟前</div>
            </div>
          </div>

          {/* Keyword Summary */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
              关键词概述
            </div>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              基于浏览器的 AI 扩展应用，帮助用户在网页场景中完成总结、翻译、写作、数据抓取等任务。
            </p>
          </div>

          {/* Evidence Sources */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                证据来源 (24)
              </div>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看更多 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { title: 'AI 浏览器插件市场 2024 年增长报告', source: '艾瑞咨询 · 5分钟前', type: '行业研报' },
                { title: 'Reddit · r/ArtificialIntelligence (讨论热度 +215%)', source: '30分钟前', type: '社交讨论' },
                { title: 'AI 浏览器插件掀起新一轮效率革命', source: '36Kr · 1小时前', type: '媒体资讯' },
              ].map((ev, i) => (
                <div key={i} style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', fontSize: 'var(--font-size-xs)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{ev.title}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>{ev.source}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Related Entities */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              相关实体
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['浏览器插件 (主题)', 'Chrome (产品)', '扩展程序 (技术)', '自动化办公 (场景)', 'GPT-4 (技术)'].map((e, idx) => (
                <span key={idx} style={{ fontSize: '12px', padding: '2px 8px', borderRadius: 'var(--radius-xs)', backgroundColor: '#f1f5f9', color: 'var(--text-secondary)' }}>
                  {e}
                </span>
              ))}
            </div>
          </div>

          {/* Action Buttons Toolbar */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6, marginBottom: 10 }}>
            <button onClick={() => showToast('已加入关注关键词', 'success')} className="btn btn-secondary btn-sm">
              <Plus size={13} />
              <span>加入关注</span>
            </button>
            <button onClick={() => showToast('已忽略该关键词', 'info')} className="btn btn-secondary btn-sm">
              <Trash2 size={13} />
              <span>忽略</span>
            </button>
            <button onClick={() => showToast('已发起关键词合并流程', 'info')} className="btn btn-secondary btn-sm">
              <GitMerge size={13} />
              <span>合并</span>
            </button>
            <button onClick={() => navigate('/monitoring')} className="btn btn-secondary btn-sm">
              <Activity size={13} />
              <span>创建监控</span>
            </button>
          </div>

          <button
            onClick={() => navigate('/opportunities')}
            className="btn btn-primary"
            style={{ width: '100%', fontSize: 'var(--font-size-sm)' }}
          >
            <Briefcase size={15} />
            <span>创建机会</span>
          </button>
        </div>
      </div>
    </div>
  );
};
