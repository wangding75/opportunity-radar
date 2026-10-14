import React, { useState } from 'react';
import {
  RefreshCw,
  Search,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P16_SourceHealth: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const healthDist = [
    { label: '优秀 (90~100)', count: 12, percentage: '15.0%', color: '#10b981' },
    { label: '良好 (70~89)', count: 28, percentage: '35.0%', color: '#3b82f6' },
    { label: '一般 (50~69)', count: 10, percentage: '12.5%', color: '#f59e0b' },
    { label: '较差 (30~49)', count: 5, percentage: '6.3%', color: '#ea580c' },
    { label: '异常 (0~29)', count: 7, percentage: '8.8%', color: '#ef4444' },
    { label: '未接入', count: 12, percentage: '15.0%', color: '#94a3b8' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '来源健康' },
        ]}
        title="来源健康"
        subtitle="实时监控所有数据来源的稳定性、成功率、延迟与异常情况，帮助您及时发现和处置问题。"
        actions={
          <button onClick={() => showToast('数据源健康指标已刷新', 'success')} className="btn btn-secondary">
            <RefreshCw size={14} />
            <span>刷新数据</span>
          </button>
        }
      />

      {/* Top 5 KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>整体健康度</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--color-success)' }}>87</span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>良好 · 较昨日 +2.3 ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>正常来源</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>58</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>占比 72.5%</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +3 ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>降级来源</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: '#f59e0b' }}>15</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>占比 18.8%</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -1 ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>异常来源</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: '#ef4444' }}>7</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>占比 8.8%</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -2 ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>平均响应 (P95)</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>812 <span style={{ fontSize: '12px' }}>ms</span></span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -74 ms ↓</div>
        </div>
      </div>

      {/* Middle Split: Health Trend + Anomaly Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 16, marginBottom: 16 }}>
        {/* Left: Trend */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              健康趋势 (24h)
            </h3>
            <div style={{ display: 'flex', gap: 4 }}>
              <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px' }}>6h</button>
              <button className="btn btn-primary btn-sm" style={{ padding: '2px 6px' }}>24h</button>
              <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px' }}>7d</button>
            </div>
          </div>
          <div style={{ height: 160 }}>
            <svg viewBox="0 0 500 130" style={{ width: '100%', height: '100%' }}>
              <polyline points="20,40 60,38 100,42 140,40 180,48 220,45 260,38 300,42 340,40 380,44 420,38 460,35" fill="none" stroke="#2563eb" strokeWidth="2" />
              <polyline points="20,70 60,68 100,75 140,70 180,82 220,75 260,65 300,72 340,68 380,75 420,68 460,62" fill="none" stroke="#10b981" strokeWidth="2" />
              {['12:00', '16:00', '20:00', '05-16', '04:00', '08:00', '12:00'].map((d, i) => (
                <text key={i} x={20 + i * 73} y="125" fontSize="8" fill="#94a3b8" textAnchor="middle">{d}</text>
              ))}
            </svg>
          </div>
        </div>

        {/* Right: Anomaly Summary */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              异常摘要
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 7 条 &gt;</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {[
              { level: '高', src: 'Reddit', type: '解析失败', time: '11:48', status: '进行中' },
              { level: '高', src: 'LinkedIn', type: '认证失败', time: '11:32', status: '进行中' },
              { level: '中', src: 'Gartner', type: '请求超时', time: '10:58', status: '监控中' },
              { level: '中', src: 'TechCrunch', type: '限流/429', time: '10:12', status: '监控中' },
            ].map((an, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 14px', borderBottom: '1px solid var(--border-subtle)', fontSize: 'var(--font-size-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: an.level === '高' ? 'var(--color-danger)' : 'var(--color-warning)', fontWeight: 700 }}>{an.level}</span>
                  <span style={{ fontWeight: 600 }}>{an.src}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{an.type}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{an.time}</span>
                  <span style={{ fontSize: '12px', color: an.status === '进行中' ? 'var(--color-danger)' : 'var(--color-warning)' }}>{an.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Table: 来源健康列表 */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
            来源健康列表
          </h3>
          <div style={{ position: 'relative', width: 220 }}>
            <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input type="text" placeholder="搜索来源名称..." value={searchValue} onChange={(e) => setSearchValue(e.target.value)} className="input-base" style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }} />
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>来源</th>
              <th style={{ width: 100 }}>类型</th>
              <th style={{ width: 80, textAlign: 'center' }}>健康度</th>
              <th style={{ width: 90, textAlign: 'center' }}>成功率</th>
              <th style={{ width: 100, textAlign: 'center' }}>P95延迟</th>
              <th style={{ width: 80, textAlign: 'center' }}>错误数</th>
              <th style={{ width: 100 }}>最近同步</th>
              <th style={{ width: 80, textAlign: 'center' }}>状态</th>
              <th style={{ width: 90, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Reuters', type: '新闻媒体', health: 94, rate: '98.7%', p95: '642 ms', err: 12, time: '1 分钟前', status: '正常' },
              { name: 'TechCrunch', type: '新闻媒体', health: 82, rate: '93.1%', p95: '1.21 s', err: 28, time: '2 分钟前', status: '降级' },
              { name: 'Gartner', type: '研究机构', health: 75, rate: '90.2%', p95: '1.68 s', err: 41, time: '3 分钟前', status: '降级' },
              { name: 'SimilarWeb', type: '数据供应商', health: 91, rate: '97.4%', p95: '702 ms', err: 15, time: '1 分钟前', status: '正常' },
              { name: 'GitHub', type: '代码托管', health: 96, rate: '99.2%', p95: '513 ms', err: 6, time: '1 分钟前', status: '正常' },
              { name: 'Reddit', type: '社交媒体', health: 45, rate: '65.3%', p95: '2.35 s', err: 87, time: '5 分钟前', status: '异常' },
            ].map((row, i) => (
              <tr key={i} onClick={() => navigate('/sources/reuters')}>
                <td><span style={{ fontWeight: 600 }}>{row.name}</span></td>
                <td><span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.type}</span></td>
                <td style={{ textAlign: 'center' }}><StatusBadge status={String(row.health)} type="score" /></td>
                <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>{row.rate}</td>
                <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>{row.p95}</td>
                <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', color: row.err > 50 ? 'var(--color-danger)' : 'var(--text-secondary)' }}>{row.err}</td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{row.time}</td>
                <td style={{ textAlign: 'center' }}><StatusBadge status={row.status} type="health" /></td>
                <td style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>详情</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination total={26} pageSize={10} currentPage={1} />
      </div>
    </div>
  );
};
