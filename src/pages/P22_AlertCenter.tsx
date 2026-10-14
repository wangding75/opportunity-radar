import React, { useState } from 'react';
import {
  Download,
  CheckSquare,
  Plus,
  Search,
  RotateCcw,
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  Clock,
  MoreVertical,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { MOCK_ALERTS } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P22_AlertCenter: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const alertSegments = [
    { label: '来源异常', count: 42, percentage: '32.8%', color: '#2563eb' },
    { label: '规则命中', count: 33, percentage: '25.8%', color: '#10b981' },
    { label: '队列积压', count: 22, percentage: '17.2%', color: '#f59e0b' },
    { label: '运行失败', count: 18, percentage: '14.1%', color: '#8b5cf6' },
    { label: '数据缺口', count: 13, percentage: '10.1%', color: '#06b6d4' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '告警中心' },
        ]}
        title="告警中心"
        subtitle="集中监控来自规则与数据源的告警事件，支持快速识别、分诊与处置，保障系统稳定与数据质量。"
        actions={
          <>
            <button onClick={() => showToast('告警数据已导出', 'info')} className="btn btn-secondary">
              <Download size={14} />
              <span>导出告警</span>
            </button>
            <button onClick={() => showToast('批量处理模式已开启', 'info')} className="btn btn-secondary">
              <CheckSquare size={14} />
              <span>批量处理</span>
            </button>
            <button onClick={() => navigate('/alert-rules')} className="btn btn-primary">
              <Plus size={14} />
              <span>新建规则</span>
            </button>
          </>
        }
      />

      {/* Top 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>未读告警</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>128</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 -18.6% ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>严重告警</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-danger)' }}>18</div>
          <div style={{ fontSize: '12px', color: 'var(--color-danger)', marginTop: 2 }}>较上周 +20.0% ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>处理中</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-warning)' }}>36</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 -10.0% ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>已解决 (24h)</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>156</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 +26.8% ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>误报率</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#8b5cf6' }}>8.3%</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 -1.5pp ↓</div>
        </div>
      </div>

      {/* Filter Row */}
      <div className="card" style={{ padding: '10px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ position: 'relative', width: 220 }}>
            <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="搜索告警标题、来源、规则..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="input-base"
              style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
            />
          </div>
          <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
            <option>严重级别: 全部</option>
            <option>严重</option>
            <option>高</option>
            <option>中</option>
          </select>
          <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
            <option>状态: 全部</option>
            <option>未读</option>
            <option>处理中</option>
            <option>已解决</option>
          </select>
          <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
            <option>时间范围: 近 7 天</option>
          </select>
        </div>
        <button onClick={() => setSearchValue('')} className="btn btn-ghost btn-sm">
          <RotateCcw size={12} />
          <span>重置</span>
        </button>
      </div>

      {/* Main Split: Left Alerts Table + Right Analytics Sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Alerts Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 30 }}><input type="checkbox" /></th>
                <th>告警ID</th>
                <th>告警标题</th>
                <th style={{ width: 65, textAlign: 'center' }}>严重级别</th>
                <th style={{ width: 90 }}>来源 / 规则</th>
                <th style={{ width: 110 }}>关联对象</th>
                <th style={{ width: 100 }}>触发时间</th>
                <th style={{ width: 65, textAlign: 'center' }}>状态</th>
                <th style={{ width: 70 }}>负责人</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_ALERTS.map((al) => (
                <tr key={al.id} onClick={() => openState('P22-S01')}>
                  <td><input type="checkbox" onClick={(e) => e.stopPropagation()} /></td>
                  <td><span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{al.id}</span></td>
                  <td><span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>{al.title}</span></td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={al.severity} type="priority" /></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{al.source}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{al.target}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{al.time}</td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={al.status} type="status" /></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{al.owner}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={128} pageSize={10} currentPage={1} />
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Distribution */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              告警类型分布
            </h3>
            <DonutChart total={128} totalLabel="总告警" segments={alertSegments} size={110} />
          </div>

          {/* Top High Frequency */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                高频告警 (近 7 天)
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看更多 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
              {[
                { name: '来源 TechCrunch 抓取失败', count: 16 },
                { name: '队列积压严重', count: 14 },
                { name: '来源 Crunchbase API 超时', count: 12 },
                { name: '外部 API 响应异常', count: 9 },
              ].map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 14, height: 14, borderRadius: 2, backgroundColor: idx < 3 ? '#2563eb' : '#f1f5f9', color: idx < 3 ? '#ffffff' : '#64748b', fontSize: '9px', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {idx + 1}
                    </span>
                    <span style={{ color: 'var(--text-primary)' }}>{item.name}</span>
                  </div>
                  <span style={{ fontWeight: 600 }}>{item.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Efficiency */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              处理效率 (24小时)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, textAlign: 'center' }}>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>42 分</div>
                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>平均响应</div>
              </div>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--color-success)' }}>2.6 时</div>
                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>平均解决</div>
              </div>
              <div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: '#2563eb' }}>96.7%</div>
                <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>SLA 达成</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
