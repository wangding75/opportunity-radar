import React, { useState } from 'react';
import {
  RefreshCw,
  SlidersHorizontal,
  AlertTriangle,
  Search,
  RotateCcw,
  CheckCircle,
  Clock,
  Layers,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { MOCK_QUEUE_TASKS } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P21_AnalysisQueue: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const typeSegments = [
    { label: '情报提取', count: 86, percentage: '46.2%', color: '#2563eb' },
    { label: '信息融合', count: 48, percentage: '25.8%', color: '#10b981' },
    { label: '报告生成', count: 32, percentage: '17.2%', color: '#f59e0b' },
    { label: '数据清洗', count: 12, percentage: '6.5%', color: '#8b5cf6' },
    { label: '其他', count: 8, percentage: '4.3%', color: '#94a3b8' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '分析队列' },
        ]}
        title="分析队列"
        subtitle="实时监控分析任务队列与 Worker 吞吐，及时发现积压与异常，保障处理效率。"
        actions={
          <>
            <button onClick={() => showToast('队列状态已刷新', 'info')} className="btn btn-secondary">
              <RefreshCw size={14} />
              <span>刷新队列</span>
            </button>
            <button onClick={() => showToast('已打开优先级调整面板', 'info')} className="btn btn-secondary">
              <SlidersHorizontal size={14} />
              <span>调整优先级</span>
            </button>
            <button onClick={() => showToast('正在筛选失败任务', 'info')} className="btn btn-primary">
              <AlertTriangle size={14} />
              <span>查看失败任务</span>
            </button>
          </>
        }
      />

      {/* Top 8 Metric Badges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 10, marginBottom: 16 }}>
        {[
          { label: '队列深度', val: '186', sub: '较上周 -12.6%', color: 'var(--text-primary)' },
          { label: '待处理', val: '78', sub: '较上周 -8.9%', color: '#2563eb' },
          { label: '处理中', val: '92', sub: '较上周 +15.3%', color: '#0284c7' },
          { label: '重试中', val: '16', sub: '较上周 +6.7%', color: '#f59e0b' },
          { label: '失败任务', val: '7', sub: '较上周 -30.0%', color: '#ef4444' },
          { label: '在线 Worker', val: '24 / 28', sub: '在线率 85.7%', color: '#10b981' },
          { label: '平均等待', val: '3分12秒', sub: '较上周 -22.1%', color: 'var(--text-primary)' },
          { label: '每分钟吞吐', val: '142.6', sub: '较上周 +9.4%', color: '#8b5cf6' },
        ].map((m, i) => (
          <div key={i} className="card" style={{ padding: '10px 12px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.label}</div>
            <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: m.color, marginTop: 2 }}>{m.val}</div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: 2 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Main Split: Left Tasks Table + Right Worker Status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16, marginBottom: 16 }}>
        {/* Left: Queue Tasks */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', width: 200 }}>
              <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索任务ID、机会、主题..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
              />
            </div>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>状态: 全部</option>
              <option>待处理</option>
              <option>处理中</option>
              <option>重试中</option>
              <option>失败</option>
            </select>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>优先级: 全部</option>
              <option>高</option>
              <option>中</option>
              <option>低</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 30 }}><input type="checkbox" /></th>
                <th>任务ID</th>
                <th>机会/主题</th>
                <th style={{ width: 80 }}>任务类型</th>
                <th style={{ width: 50, textAlign: 'center' }}>优先级</th>
                <th style={{ width: 70, textAlign: 'center' }}>状态</th>
                <th style={{ width: 90 }}>分配Worker</th>
                <th style={{ width: 90 }}>等待时长</th>
                <th style={{ width: 50, textAlign: 'center' }}>重试</th>
                <th style={{ width: 70 }}>预计完成</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_QUEUE_TASKS.map((task) => (
                <tr key={task.id}>
                  <td><input type="checkbox" /></td>
                  <td><span style={{ fontSize: '12px', color: 'var(--color-primary)', fontWeight: 500 }}>{task.id}</span></td>
                  <td><span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{task.targetName}</span></td>
                  <td><span style={{ fontSize: '12px', padding: '1px 5px', borderRadius: 2, backgroundColor: '#f1f5f9' }}>{task.taskType}</span></td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={task.priority} type="priority" /></td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={task.status} type="status" /></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{task.worker}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{task.waitingTime}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{task.retryCount}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{task.estimatedFinish}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={186} pageSize={10} currentPage={1} />
        </div>

        {/* Right: Worker Status */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              Worker 状态
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>24/28 在线</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { id: 'worker-01', status: '在线', load: '62%', count: 7, color: 'var(--color-success)' },
              { id: 'worker-02', status: '在线', load: '48%', count: 5, color: 'var(--color-success)' },
              { id: 'worker-03', status: '忙碌', load: '92%', count: 12, color: 'var(--color-danger)' },
              { id: 'worker-04', status: '在线', load: '36%', count: 4, color: 'var(--color-success)' },
              { id: 'worker-05', status: '在线', load: '55%', count: 6, color: 'var(--color-success)' },
              { id: 'worker-06', status: '离线', load: '—', count: 0, color: 'var(--text-muted)' },
            ].map((w, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: 80 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: w.status === '在线' ? '#10b981' : w.status === '忙碌' ? '#ef4444' : '#94a3b8' }} />
                  <span style={{ fontWeight: 600 }}>{w.id}</span>
                </div>
                <div style={{ flex: 1, margin: '0 10px', height: 5, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
                  {w.load !== '—' && <div style={{ width: w.load, height: '100%', backgroundColor: w.status === '忙碌' ? '#ef4444' : '#10b981' }} />}
                </div>
                <span style={{ color: 'var(--text-muted)', width: 40, textAlign: 'right' }}>{w.count} 任务</span>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--border-subtle)', textAlign: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 Worker (28) &gt;</span>
          </div>
        </div>
      </div>

      {/* Bottom 4 Cards: Trends + Task Distribution + Throughput + Failures */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        {/* Trend */}
        <div className="card" style={{ padding: '12px 14px' }}>
          <h3 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>队列趋势 (24h)</h3>
          <div style={{ height: 90 }}>
            <svg viewBox="0 0 200 70" style={{ width: '100%', height: '100%' }}>
              <polyline points="10,40 40,35 70,45 100,30 130,25 160,35 190,30" fill="none" stroke="#2563eb" strokeWidth="2" />
              <polyline points="10,55 40,50 70,58 100,52 130,48 160,54 190,50" fill="none" stroke="#10b981" strokeWidth="2" />
            </svg>
          </div>
        </div>

        {/* Types */}
        <div className="card" style={{ padding: '12px 14px' }}>
          <h3 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>任务类型分布</h3>
          <DonutChart total={186} totalLabel="总任务" segments={typeSegments} size={85} />
        </div>

        {/* Throughput */}
        <div className="card" style={{ padding: '12px 14px' }}>
          <h3 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>吞吐统计 (每分钟)</h3>
          <div style={{ height: 90 }}>
            <svg viewBox="0 0 200 70" style={{ width: '100%', height: '100%' }}>
              <polyline points="10,35 40,30 70,25 100,32 130,22 160,20 190,24" fill="none" stroke="#10b981" strokeWidth="2" />
              <polyline points="10,65 40,65 70,64 100,65 130,65 160,63 190,64" fill="none" stroke="#ef4444" strokeWidth="2" />
            </svg>
          </div>
        </div>

        {/* Recent Failures */}
        <div className="card" style={{ padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <h3 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>最近失败任务</h3>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
            <div><span style={{ fontWeight: 600 }}>T-00153</span> · 情报源解析超时</div>
            <div><span style={{ fontWeight: 600 }}>T-00148</span> · 数据源连接失败</div>
            <div><span style={{ fontWeight: 600 }}>T-00139</span> · 内容格式不匹配</div>
          </div>
        </div>
      </div>
    </div>
  );
};
