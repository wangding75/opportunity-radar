import React, { useState } from 'react';
import {
  Edit3,
  MoreHorizontal,
  Plus,
  Play,
  Search,
  Globe,
  Clock,
  Activity,
  CheckCircle,
  AlertTriangle,
  Mail,
  MessageSquare,
  Webhook,
  Trash2,
  Edit2,
  TrendingUp,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { Sparkline } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P18_MonitoringPlanDetail: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('sources');
  const [searchValue, setSearchValue] = useState('');

  const sourcesList = [
    { name: 'TechCrunch', type: '新闻网站', domain: 'techcrunch.com', lang: '英文', health: '正常 98分', latency: '312ms' },
    { name: 'The Verge', type: '新闻网站', domain: 'theverge.com', lang: '英文', health: '正常 96分', latency: '289ms' },
    { name: '36Kr', type: '新闻网站', domain: '36kr.com', lang: '中文', health: '正常 94分', latency: '462ms' },
    { name: '硅谷科技评论', type: '新闻网站', domain: 'samit.com.cn', lang: '中文', health: '正常 95分', latency: '398ms' },
    { name: 'CB Insights', type: '研究报告', domain: 'cbinsights.com', lang: '英文', health: '需关注 68分', latency: '721ms' },
    { name: 'Crunchbase', type: '数据库', domain: 'crunchbase.com', lang: '英文', health: '正常 93分', latency: '567ms' },
    { name: 'Twitter/X AI 话题', type: '社交媒体', domain: 'x.com/search', lang: '多语言', health: '正常 92分', latency: '245ms' },
    { name: 'Reddit r/MachineLearning', type: '论坛社区', domain: 'reddit.com/r/MachineLearning', lang: '英文', health: '需关注 61分', latency: '892ms' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控计划', path: '/monitoring' },
          { label: 'PLAN-2025-001' },
          { label: '详情' },
        ]}
        title="AI 产业链动态监控"
        subtitle="跟踪全球 AI 产业链技术进展、企业动态、投融资与政策变化"
        extra={
          <div style={{ display: 'flex', gap: 6 }}>
            {['AI', '大模型', '算力'].map((t, idx) => (
              <span key={idx} style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 8px', borderRadius: 4 }}>
                {t}
              </span>
            ))}
          </div>
        }
        actions={
          <>
            <button
              onClick={() => openState('P17-S03')}
              className="btn btn-secondary"
            >
              <Play size={14} />
              <span>手动执行</span>
            </button>
            <button
              onClick={() => showToast('已打开监控计划编辑', 'info')}
              className="btn btn-secondary"
            >
              <Edit3 size={14} />
              <span>编辑计划</span>
            </button>
          </>
        }
      />

      {/* Top 6 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 14, marginBottom: 20 }}>
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>监控范围</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>全球</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>多语言</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>来源数量</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>28</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>活跃 26</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>执行频率</div>
          <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>每 30 分钟</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>下次执行 10:20</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>健康状态</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-success)' }}>正常</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>健康分 98 分</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>累计运行</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>1,286 次</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>近 7 天 432 次</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>发现情报</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-primary)' }}>1,245 条</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>近 7 天 456 条</div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'sources', label: '监控来源', count: 28 },
          { key: 'runs', label: '执行记录' },
          { key: 'intelligence', label: '发现情报' },
          { key: 'rules', label: '规则与过滤' },
          { key: 'notifications', label: '通知设置' },
          { key: 'history', label: '变更历史' },
        ]}
      />

      {/* Main Split Layout: Left Table + Right Stats Sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Left: Table Card */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ position: 'relative', width: 220 }}>
                <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="搜索来源名称、类型、域名..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="input-base"
                  style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
                />
              </div>
              <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
                <option>类型: 全部</option>
              </select>
              <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
                <option>状态: 全部</option>
              </select>
            </div>
            <button
              onClick={() => showToast('已添加新监控来源', 'success')}
              className="btn btn-primary btn-sm"
            >
              <Plus size={13} />
              <span>添加来源</span>
            </button>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>来源名称</th>
                <th style={{ width: 90 }}>类型</th>
                <th style={{ width: 140 }}>域名/渠道</th>
                <th style={{ width: 60 }}>语言</th>
                <th style={{ width: 100 }}>健康状态</th>
                <th style={{ width: 90 }}>最后检查</th>
                <th style={{ width: 80 }}>响应时间</th>
                <th style={{ width: 80, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {sourcesList.map((src, i) => (
                <tr key={i}>
                  <td><span style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>{src.name}</span></td>
                  <td><span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{src.type}</span></td>
                  <td style={{ fontSize: '12px', color: 'var(--color-primary)' }}>{src.domain}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{src.lang}</td>
                  <td>
                    <span style={{ fontSize: '12px', color: src.health.includes('正常') ? 'var(--color-success)' : 'var(--color-warning)', fontWeight: 500 }}>
                      {src.health}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>1 分钟前</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{src.latency}</td>
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                      <Edit2 size={13} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
                      <Trash2 size={13} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={28} pageSize={8} currentPage={1} />
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Health Gauge */}
          <div className="card" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              健康状态
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 64, height: 64, borderRadius: '50%', border: '4px solid var(--color-success)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-success)' }}>98</span>
                <span style={{ fontSize: '8px', color: 'var(--text-muted)' }}>健康分</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 'var(--font-size-xs)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                  <span style={{ color: 'var(--text-muted)' }}>整体状态</span>
                  <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>正常</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                  <span style={{ color: 'var(--text-muted)' }}>健康趋势</span>
                  <span style={{ color: 'var(--color-success)' }}>↑ 5 分</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                  <span style={{ color: 'var(--text-muted)' }}>近 7 天可用率</span>
                  <span style={{ fontWeight: 600 }}>99.6%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Execution Stats (7 days) */}
          <div className="card" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              执行统计 (近 7 天)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, textAlign: 'center', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>432</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>执行次数</div>
              </div>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--color-success)' }}>428</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>成功次数</div>
              </div>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--color-danger)' }}>4</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>失败次数</div>
              </div>
            </div>
            <Sparkline points={[50, 55, 60, 62, 58, 65, 70]} color="#10b981" width={280} height={30} />
          </div>

          {/* Notification Settings */}
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                通知设置
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>编辑</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Mail size={13} color="var(--text-muted)" />
                  <span>邮件通知</span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>已启用</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MessageSquare size={13} color="var(--text-muted)" />
                  <span>企业微信</span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>已启用</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Webhook size={13} color="var(--text-muted)" />
                  <span>Webhook</span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>已启用</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
