import React, { useState } from 'react';
import {
  Settings,
  RefreshCw,
  PlayCircle,
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  Edit2,
  CheckCircle,
  AlertTriangle,
  Plus,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { Sparkline } from '../components/common/Charts';
import { useRouter } from '../router/RouterContext';

export const P15_SourceDetail: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '来源管理', path: '/sources' },
          { label: '来源详情' },
        ]}
        title="路透社 Reuters"
        subtitle="reuters.com · 官方"
        extra={
          <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 8px', borderRadius: 4, fontWeight: 500 }}>
            官方
          </span>
        }
        actions={
          <>
            <button onClick={() => showToast('已打开来源配置', 'info')} className="btn btn-secondary">
              <Settings size={14} />
              <span>编辑配置</span>
            </button>
            <button onClick={() => showToast('已触发立即同步', 'success')} className="btn btn-secondary">
              <RefreshCw size={14} />
              <span>立即同步</span>
            </button>
            <button onClick={() => navigate('/runs')} className="btn btn-secondary">
              <PlayCircle size={14} />
              <span>查看运行</span>
            </button>
            <button onClick={() => navigate('/sources')} className="btn btn-primary">
              <ArrowLeft size={14} />
              <span>返回来源管理</span>
            </button>
          </>
        }
      />

      {/* Top 6 KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 14, marginBottom: 20 }}>
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>健康评分</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>92</span>
            <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 500 }}>良好</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +2 ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>成功率 (7天)</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>99.5%</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +0.3pp ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>平均延迟 (7天)</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>1.2 <span style={{ fontSize: '12px' }}>分钟</span></span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -0.4 分钟 ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>今日采集量</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>92 <span style={{ fontSize: '12px' }}>条</span></span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +18 (24.3%) ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>最后同步时间</div>
          <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>08:42</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>13 分钟前</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>活跃监控计划</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>3 <span style={{ fontSize: '12px' }}>个</span></span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>全部正常运行</div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'overview', label: '概览' },
          { key: 'intelligence', label: '最近情报' },
          { key: 'runs', label: '运行记录' },
          { key: 'config', label: '配置' },
          { key: 'errors', label: '错误日志' },
        ]}
      />

      {/* Main Split: Left Charts & Lists + Right Meta & Relations */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 16 }}>
        {/* Left Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Card: 采集量与健康度趋势 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                采集量与健康度趋势 (近7天)
              </h3>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn btn-primary btn-sm" style={{ padding: '2px 8px' }}>7天</button>
                <button className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>30天</button>
              </div>
            </div>
            <div style={{ height: 140 }}>
              <svg viewBox="0 0 500 120" style={{ width: '100%', height: '100%' }}>
                {/* Bar chart bars for collected */}
                {[
                  { d: '05-10', bar: 70, score: 85 },
                  { d: '05-11', bar: 85, score: 88 },
                  { d: '05-12', bar: 90, score: 92 },
                  { d: '05-13', bar: 80, score: 90 },
                  { d: '05-14', bar: 75, score: 89 },
                  { d: '05-15', bar: 95, score: 93 },
                  { d: '05-16', bar: 82, score: 92 },
                ].map((item, idx) => (
                  <g key={idx}>
                    <rect x={35 + idx * 64} y={110 - item.bar} width="24" height={item.bar} fill="#60a5fa" rx="3" />
                    <circle cx={47 + idx * 64} cy={110 - item.score} r="3" fill="#10b981" />
                    <text x={47 + idx * 64} y="118" fontSize="8" fill="#94a3b8" textAnchor="middle">{item.d}</text>
                  </g>
                ))}
              </svg>
            </div>
          </div>

          {/* Card: 最近采集的情报 */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                最近采集的情报
              </h3>
              <span onClick={() => navigate('/intelligence')} style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>
                查看全部 &gt;
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {[
                { title: '美联储官员：通胀仍高于目标 未来数月或将维持利率不变', theme: '宏观经济', score: 92, time: '10 分钟前' },
                { title: '欧盟就数字市场法对苹果公司处以5亿欧元罚款', theme: '政策法规', score: 88, time: '22 分钟前' },
                { title: '沙特阿美一季度利润下降 受油价走弱影响', theme: '能源与大宗商品', score: 85, time: '35 分钟前' },
                { title: '谷歌宣布在印度追加100亿美元投资 加码AI布局', theme: '科技行业', score: 90, time: '46 分钟前' },
              ].map((intel, i) => (
                <div
                  key={i}
                  onClick={() => navigate('/intelligence/INT-20260819-01842')}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer' }}
                  className="hover-surface"
                >
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {intel.title}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>{intel.theme}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <StatusBadge status={String(intel.score)} type="score" />
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: 60, textAlign: 'right' }}>{intel.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* 来源档案 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                来源档案
              </h3>
              <Edit2 size={13} color="var(--color-primary)" style={{ cursor: 'pointer' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-xs)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>来源类型</span>
                <span>新闻媒体</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>域名</span>
                <span style={{ color: 'var(--color-primary)' }}>reuters.com</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>更新频率</span>
                <span>2 分钟</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>数据范围</span>
                <span>全球 · 经济金融 / 政策法规 / 科技</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>认证方式</span>
                <span>RSS Feed + 网页抓取</span>
              </div>
            </div>
          </div>

          {/* 关联监控计划 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                关联监控计划 (3)
              </h3>
              <span onClick={() => navigate('/monitoring')} style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>
                查看全部 &gt;
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { name: '全球政策与监管跟踪', status: '运行中', priority: '高', hits: 38 },
                { name: '金融市场重大事件', status: '运行中', priority: '中', hits: 27 },
                { name: '科技企业动态追踪', status: '运行中', priority: '中', hits: 19 },
              ].map((plan, i) => (
                <div key={i} onClick={() => navigate('/monitoring/PLAN-2025-001')} style={{ padding: '8px 10px', borderRadius: 'var(--radius-sm)', backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', fontSize: 'var(--font-size-xs)', cursor: 'pointer' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{plan.name}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <StatusBadge status={plan.status} type="health" />
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>命中: {plan.hits}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
