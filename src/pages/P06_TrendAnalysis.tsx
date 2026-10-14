import React, { useState } from 'react';
import {
  TrendingUp,
  Download,
  Calendar,
  Layers,
  Zap,
  AlertTriangle,
  Sun,
  Clock,
  ChevronRight,
  Info,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { KpiCard } from '../components/common/KpiCard';
import { DonutChart } from '../components/common/Charts';
import { useRouter } from '../router/RouterContext';

export const P06_TrendAnalysis: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('overview');
  const [keyword, setKeyword] = useState('固态电池');
  const [timeRange, setTimeRange] = useState('30d');

  const signalTypeSegments = [
    { label: '新闻报道', count: 895, percentage: '35.2%', color: '#2563eb' },
    { label: '研究论文', count: 613, percentage: '24.1%', color: '#10b981' },
    { label: '专利', count: 453, percentage: '17.8%', color: '#f59e0b' },
    { label: '公司动态', count: 321, percentage: '12.6%', color: '#8b5cf6' },
    { label: '政策法规', count: 165, percentage: '6.5%', color: '#06b6d4' },
    { label: '其他', count: 95, percentage: '3.8%', color: '#94a3b8' },
  ];

  const sourceSegments = [
    { label: '新闻媒体', count: 984, percentage: '38.7%', color: '#2563eb' },
    { label: '研究机构', count: 567, percentage: '22.3%', color: '#10b981' },
    { label: '企业官网', count: 417, percentage: '16.4%', color: '#f59e0b' },
    { label: '专利数据库', count: 302, percentage: '11.9%', color: '#8b5cf6' },
    { label: '政府/协会', count: 171, percentage: '6.7%', color: '#06b6d4' },
    { label: '社交媒体', count: 101, percentage: '4.0%', color: '#ec4899' },
  ];

  return (
    <div>
      <Header
        title="趋势分析"
        subtitle="追踪关键词或主题的信号变化趋势，识别异常波动与潜在机会"
      />

      {/* Control Bar */}
      <div className="card" style={{ padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>关键词</span>
            <select value={keyword} onChange={(e) => setKeyword(e.target.value)} className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>
              <option>固态电池</option>
              <option>生成式人工智能</option>
              <option>人形机器人</option>
              <option>量子计算</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>时间范围</span>
            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option value="30d">近30天</option>
              <option value="7d">近7天</option>
              <option value="90d">近90天</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>对比范围</span>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>前30天</option>
              <option>去年同期</option>
            </select>
          </div>

          <button onClick={() => showToast('已添加对比项', 'info')} className="btn btn-ghost btn-sm" style={{ border: '1px dashed var(--border-default)' }}>
            + 添加对比
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={() => showToast('趋势图表已重新渲染', 'success')} className="btn btn-primary btn-sm">
            应用
          </button>
          <button onClick={() => showToast('已导出分析报告', 'info')} className="btn btn-secondary btn-sm">
            <Download size={13} />
            <span>导出</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'overview', label: '趋势概览' },
          { key: 'sources', label: '信号来源' },
          { key: 'geo', label: '地域分布' },
          { key: 'opportunities', label: '相关机会' },
        ]}
      />

      {/* 4 Top KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 16 }}>
        <KpiCard
          title="总信号数"
          value="2,542"
          change="较前30天 ↑ 38.6%"
          changeType="up"
          icon={<Layers size={18} />}
          iconBg="#f5f3ff"
          iconColor="#8b5cf6"
        />
        <KpiCard
          title="日均增长"
          value="6.2%"
          change="较前30天 ↑ 2.1%"
          changeType="up"
          icon={<Clock size={18} />}
          iconBg="#ecfdf5"
          iconColor="#10b981"
        />
        <KpiCard
          title="异常波动"
          value="3 次"
          change="较前30天 ↑ 1 次"
          changeType="up"
          icon={<AlertTriangle size={18} />}
          iconBg="#fef2f2"
          iconColor="#ef4444"
        />
        <KpiCard
          title="关联机会数"
          value="42"
          change="较前30天 ↑ 9"
          changeType="up"
          icon={<Sun size={18} />}
          iconBg="#fffbeb"
          iconColor="#f59e0b"
          onClick={() => navigate('/opportunities')}
        />
      </div>

      {/* Main Signal Trend + Key Indicators */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 16 }}>
        {/* Signal Trend Chart Card */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
                信号趋势
              </h3>
              <Info size={14} color="var(--text-muted)" />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 'var(--font-size-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 2, backgroundColor: '#2563eb' }} />
                <span>当前期 (近30天)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 2, borderTop: '2px dashed #94a3b8' }} />
                <span>对比期 (前30天)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#ef4444' }} />
                <span>异常点</span>
              </div>
              <button onClick={() => showToast('图表已导出', 'info')} className="btn btn-secondary btn-sm">
                导出图表
              </button>
            </div>
          </div>

          {/* SVG Complex Trend Chart */}
          <div style={{ width: '100%', height: 220, position: 'relative' }}>
            <svg viewBox="0 0 600 200" style={{ width: '100%', height: '100%' }}>
              {/* Grid lines */}
              {[0, 30, 60, 90, 120, 150, 180].map((val) => {
                const y = 180 - (val / 180) * 160;
                return (
                  <g key={val}>
                    <line x1="30" y1={y} x2="590" y2={y} stroke="#f1f5f9" strokeDasharray="3 3" />
                    <text x="24" y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">{val}</text>
                  </g>
                );
              })}

              {/* Dashed comparison line */}
              <polyline
                points="40,140 80,135 120,145 160,130 200,125 240,110 280,120 320,130 360,140 400,130 440,125 480,120 520,135 560,130"
                fill="none"
                stroke="#cbd5e1"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />

              {/* Main trend line */}
              <polyline
                points="40,110 80,125 120,115 160,135 200,105 240,118 280,75 320,95 360,130 400,105 440,70 480,68 520,95 560,100"
                fill="none"
                stroke="#2563eb"
                strokeWidth="2.5"
              />

              {/* Anomaly peak circle & label */}
              <circle cx="280" cy="75" r="5" fill="#ffffff" stroke="#ef4444" strokeWidth="2.5" />
              <rect x="290" y="66" width="54" height="18" rx="4" fill="#fef2f2" stroke="#fecaca" />
              <text x="296" y="79" fontSize="12" fill="#ef4444" fontWeight="600">异常波动</text>

              {/* X Axis Labels */}
              {['10-15', '10-18', '10-21', '10-24', '10-27', '10-30', '11-02', '11-05', '11-08', '11-11', '11-14'].map((d, i) => (
                <text key={i} x={40 + i * 52} y="195" textAnchor="middle" fontSize="9" fill="#94a3b8">{d}</text>
              ))}
            </svg>
          </div>
        </div>

        {/* Key Indicators Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
              关键指标
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
              查看全部
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-xs)' }}>
            {[
              { label: '信号总量', val: '2,542', change: '↑ 38.6%', type: 'up' },
              { label: '日均信号量', val: '84.7', change: '↑ 6.2%', type: 'up' },
              { label: '峰值日信号量', val: '156 (10-27)', change: '↑ 72.2%', type: 'up' },
              { label: '异常波动次数', val: '3', change: '↑ 1', type: 'up' },
              { label: '信号持续天数', val: '30', change: '—', type: 'neutral' },
              { label: '信号密度 (条/天/百万)', val: '12.6', change: '↑ 3.4%', type: 'up' },
              { label: '关联机会数', val: '42', change: '↑ 9', type: 'up' },
            ].map((ind, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>{ind.label}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{ind.val}</span>
                  <span style={{ color: ind.type === 'up' ? 'var(--color-success)' : 'var(--text-muted)', fontWeight: 500 }}>
                    {ind.change}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom 3 Cards: Signal Type + Source Composition + Anomaly Log */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {/* Card 1: 信号类型分布 */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
              信号类型分布
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
              查看全部
            </span>
          </div>
          <DonutChart total={2542} totalLabel="总信号" segments={signalTypeSegments} />
        </div>

        {/* Card 2: 信号来源构成 */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
              信号来源构成
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
              查看全部
            </span>
          </div>
          <DonutChart total={2542} totalLabel="总信号" segments={sourceSegments} />
        </div>

        {/* Card 3: 异常波动记录 */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
              异常波动记录
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
              查看全部
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { date: '2024-10-27', val: '156', desc: '多家车企发布固态电池量产时间表，行业关注度显著提升', tag: '新闻报道', level: '高' },
              { date: '2024-11-08', val: '132', desc: '某研究机构发布高能量密度固态电池新进展报告', tag: '研究论文', level: '中' },
              { date: '2024-11-12', val: '128', desc: '地方政府出台固态电池产业支持政策', tag: '政策法规', level: '中' },
            ].map((rec, i) => (
              <div key={i} style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', fontSize: 'var(--font-size-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: rec.level === '高' ? '#ef4444' : '#f59e0b' }} />
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rec.date}</span>
                    <span style={{ color: 'var(--text-muted)' }}>异常值: {rec.val}</span>
                  </div>
                  <span style={{ fontSize: '12px', color: rec.level === '高' ? 'var(--color-danger)' : 'var(--color-warning)', fontWeight: 600 }}>
                    {rec.level}
                  </span>
                </div>
                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 4 }}>
                  {rec.desc}
                </div>
                <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '1px 5px', borderRadius: 2 }}>
                  {rec.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
