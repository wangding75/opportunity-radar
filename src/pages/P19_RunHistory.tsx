import React, { useState } from 'react';
import {
  Download,
  Filter,
  Search,
  RotateCcw,
  Play,
  FileText,
  ChevronRight,
  TrendingUp,
  AlertOctagon,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { MOCK_RUNS } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P19_RunHistory: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const statusSegments = [
    { label: '成功', count: 12075, percentage: '96.7%', color: '#10b981' },
    { label: '重试', count: 209, percentage: '1.7%', color: '#f59e0b' },
    { label: '失败', count: 68, percentage: '0.5%', color: '#ef4444' },
    { label: '运行中', count: 134, percentage: '1.1%', color: '#2563eb' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '运行记录' },
        ]}
        title="运行记录"
        subtitle="查看所有监控计划的运行历史与执行结果，支持筛选、导出与异常分析。"
        actions={
          <>
            <button onClick={() => showToast('运行记录已导出为 CSV', 'info')} className="btn btn-secondary">
              <Download size={14} />
              <span>导出记录</span>
            </button>
            <button onClick={() => showToast('高级筛选面板已打开', 'info')} className="btn btn-secondary">
              <Filter size={14} />
              <span>高级筛选</span>
            </button>
          </>
        }
      />

      {/* Top 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>总运行次数</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>12,486</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +186 次 ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>成功率</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>96.8%</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 +0.8% ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>平均耗时</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>2m 14s</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -18s ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>失败运行</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#ef4444' }}>68</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 -7 次 ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>运行中</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>6</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>较昨日 +2 次 ↑</div>
        </div>
      </div>

      {/* Filter Row */}
      <div className="card" style={{ padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ position: 'relative', width: 220 }}>
            <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="搜索 Run ID、计划名称..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="input-base"
              style={{ width: '100%', paddingLeft: 28, height: 32, fontSize: '12px' }}
            />
          </div>
          <select className="input-base" style={{ height: 32, fontSize: '12px' }}>
            <option>状态: 全部状态</option>
            <option>成功</option>
            <option>重试</option>
            <option>失败</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: '12px' }}>
            <option>触发方式: 全部方式</option>
            <option>自动调度</option>
            <option>定时触发</option>
            <option>手动触发</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: '12px' }}>
            <option>时间: 最近 7 天</option>
          </select>
        </div>
        <button onClick={() => setSearchValue('')} className="btn btn-ghost btn-sm">
          <RotateCcw size={13} />
          <span>重置</span>
        </button>
      </div>

      {/* Main Split: Left Run Table + Right Analytics Sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Runs Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>计划名称</th>
                <th style={{ width: 80 }}>触发方式</th>
                <th style={{ width: 60, textAlign: 'center' }}>来源数</th>
                <th style={{ width: 120 }}>开始时间</th>
                <th style={{ width: 70 }}>耗时</th>
                <th style={{ width: 70, textAlign: 'center' }}>采集数</th>
                <th style={{ width: 70, textAlign: 'center' }}>新增信号</th>
                <th style={{ width: 60, textAlign: 'center' }}>错误数</th>
                <th style={{ width: 70, textAlign: 'center' }}>状态</th>
                <th style={{ width: 120, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_RUNS.map((run) => (
                <tr key={run.id} onClick={() => navigate(`/runs/${run.id}`)}>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--color-primary)', fontWeight: 600 }}>{run.id}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>{run.planName}</span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{run.triggerType}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{run.sourcesCount}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{run.startTime}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{run.duration}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', fontWeight: 600 }}>{run.collectedCount}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', color: 'var(--color-primary)' }}>{run.newSignalsCount}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', color: (run.errorCount ?? 0) > 0 ? '#ef4444' : 'var(--text-muted)' }}>{run.errorCount ?? 0}</td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={run.status} type="status" />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: '12px' }}>
                      <span onClick={(e) => { e.stopPropagation(); navigate(`/runs/${run.id}`); }} style={{ color: 'var(--color-primary)', cursor: 'pointer' }}>详情</span>
                      <span style={{ color: 'var(--border-default)' }}>|</span>
                      <span onClick={(e) => { e.stopPropagation(); showToast('查看日志', 'info'); }} style={{ color: 'var(--color-primary)', cursor: 'pointer' }}>日志</span>
                      <span style={{ color: 'var(--border-default)' }}>|</span>
                      <span onClick={(e) => { e.stopPropagation(); showToast(`重新执行 ${run.id}`, 'success'); }} style={{ color: 'var(--color-primary)', cursor: 'pointer' }}>复跑</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={12486} pageSize={10} currentPage={1} />
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Status Distribution */}
          <div className="card" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              状态分布
            </h3>
            <DonutChart total={12486} totalLabel="总运行" segments={statusSegments} size={110} />
          </div>

          {/* Recent Anomalies */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                最近异常运行
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              {[
                { name: '半导体行业动态监控', time: '06-10 08:30', id: 'RUN-20260610-0830', status: '失败', color: '#ef4444' },
                { name: '企业财报与经营动态', time: '06-10 08:50', id: 'RUN-20260610-0850', status: '重试', color: '#f59e0b' },
                { name: '电商平台新品动向监控', time: '06-10 09:00', id: 'RUN-20260610-0900', status: '重试', color: '#f59e0b' },
              ].map((an, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{an.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{an.time} · {an.id}</div>
                  </div>
                  <span style={{ fontSize: '12px', color: an.color, fontWeight: 700 }}>{an.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
