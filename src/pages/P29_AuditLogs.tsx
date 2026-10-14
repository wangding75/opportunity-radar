import React, { useState } from 'react';
import {
  Download,
  Filter,
  Search,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronRight,
  Shield,
  FileText,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P29_AuditLogs: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');
  const [selectedLog, setSelectedLog] = useState<any>(null);

  const logsList = [
    {
      id: 'LOG-01',
      time: '2024-04-12 16:38:22',
      user: '王明',
      role: '分析师',
      action: '修改监控计划',
      targetType: '监控计划',
      targetName: 'AI 投资趋势监控 (每日)',
      status: '成功',
      ip: '101.88.12.34 (Chrome / macOS)',
      source: 'Web 控制台',
      traceId: '7f3d9a1b6c4e8d2f',
      detail: '修改计划执行频率由 08:00 改为 07:00，增加数据源 3 个。',
    },
    {
      id: 'LOG-02',
      time: '2024-04-12 16:10:05',
      user: '李想',
      role: '分析师',
      action: '停用来源',
      targetType: '来源',
      targetName: 'Crunchbase',
      status: '成功',
      ip: '101.88.12.56 (Chrome / macOS)',
      source: 'Web 控制台',
      traceId: '1b2c3d4e5f6a7b8c',
      detail: '因 API 速率超出配额，临时停用该数据源。',
    },
    {
      id: 'LOG-03',
      time: '2024-04-12 15:55:11',
      user: '王明',
      role: '分析师',
      action: '修改告警规则',
      targetType: '告警规则',
      targetName: '高价值机会阈值告警',
      status: '成功',
      ip: '101.88.12.34 (Chrome / macOS)',
      source: 'Web 控制台',
      traceId: '4c5d6e7f8a9b0c1d',
      detail: '将机会综合评分触发阈值由 80 调整为 85。',
    },
    {
      id: 'LOG-04',
      time: '2024-04-12 15:32:47',
      user: '张涛',
      role: '研究主管',
      action: '发布研究结论',
      targetType: '研究结论',
      targetName: '2024 Q2 全球 AI 投资趋势洞察',
      status: '成功',
      ip: '101.88.12.78 (Chrome / Windows)',
      source: 'Web 控制台',
      traceId: '9e0f1a2b3c4d5e6f',
      detail: '正式发布研究报告至团队知识库。',
    },
    {
      id: 'LOG-05',
      time: '2024-04-12 12:57:09',
      user: '李想',
      role: '分析师',
      action: '导出情报数据',
      targetType: '情报',
      targetName: 'AI 领域并购情报 (全部)',
      status: '失败',
      ip: '101.88.12.56 (Chrome / macOS)',
      source: 'Web 控制台',
      traceId: '8b9c0d1e2f3a4b5c',
      detail: '单次导出记录超过 50,000 条上限，已被系统拦截。',
    },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '审计日志' },
        ]}
        title="审计日志"
        subtitle="记录所有用户在工作区中的关键操作行为，支持审计追踪与安全合规。"
        actions={
          <>
            <button onClick={() => showToast('审计日志已导出为加密包', 'success')} className="btn btn-secondary">
              <Download size={14} />
              <span>导出日志</span>
            </button>
            <button onClick={() => showToast('高级筛选面板已打开', 'info')} className="btn btn-secondary">
              <Filter size={14} />
              <span>高级筛选</span>
            </button>
          </>
        }
      />

      {/* Top 4 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>今日事件数</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>2,138</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↑ 18.6%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>敏感操作</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#f59e0b' }}>87</div>
          <div style={{ fontSize: '12px', color: '#f59e0b', marginTop: 2 }}>较昨日 ↑ 21.4%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>失败操作</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#ef4444' }}>23</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↓ 8.0%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>活跃操作者</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>28</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↑ 12.5%</div>
        </div>
      </div>

      {/* Main Split: Left Table + Right Detail Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedLog ? '1fr 340px' : '1fr', gap: 16 }}>
        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', width: 240 }}>
              <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索对象名称 / Trace ID..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
              />
            </div>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>操作者: 全部</option>
              <option>王明</option>
              <option>李想</option>
            </select>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>结果: 全部</option>
              <option>成功</option>
              <option>失败</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 140 }}>时间</th>
                <th style={{ width: 100 }}>操作者</th>
                <th style={{ width: 110 }}>动作</th>
                <th style={{ width: 90 }}>对象类型</th>
                <th>对象名称</th>
                <th style={{ width: 70, textAlign: 'center' }}>结果</th>
                <th style={{ width: 150 }}>IP / 设备</th>
                <th style={{ width: 100 }}>Trace ID</th>
              </tr>
            </thead>
            <tbody>
              {logsList.map((log) => (
                <tr key={log.id} onClick={() => setSelectedLog(log)}>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{log.time}</td>
                  <td>
                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{log.user}</div>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{log.role}</div>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{log.action}</td>
                  <td>
                    <span style={{ fontSize: '12px', padding: '1px 5px', borderRadius: 2, backgroundColor: '#f1f5f9', color: 'var(--text-secondary)' }}>
                      {log.targetType}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-primary)' }}>{log.targetName}</span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={log.status} type="health" />
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{log.ip}</td>
                  <td style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>{log.traceId}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={2138} pageSize={5} currentPage={1} />
        </div>

        {/* Right Detail Pane (when selected) */}
        {selectedLog && (
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                日志详情
              </h3>
              <button onClick={() => setSelectedLog(null)} className="btn btn-ghost btn-sm" style={{ padding: 2 }}>✕</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              <div><span style={{ color: 'var(--text-muted)' }}>时间:</span> {selectedLog.time}</div>
              <div><span style={{ color: 'var(--text-muted)' }}>操作者:</span> {selectedLog.user} ({selectedLog.role})</div>
              <div><span style={{ color: 'var(--text-muted)' }}>动作:</span> {selectedLog.action}</div>
              <div><span style={{ color: 'var(--text-muted)' }}>对象:</span> {selectedLog.targetName}</div>
              <div><span style={{ color: 'var(--text-muted)' }}>结果:</span> <span style={{ color: selectedLog.status === '成功' ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 600 }}>{selectedLog.status}</span></div>
              <div><span style={{ color: 'var(--text-muted)' }}>Trace ID:</span> <span style={{ fontFamily: 'monospace' }}>{selectedLog.traceId}</span></div>
              <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>变更详情:</div>
                <div style={{ padding: 8, borderRadius: 4, backgroundColor: '#f8fafc', border: '1px solid var(--border-default)', fontSize: '12px', lineHeight: 1.5 }}>
                  {selectedLog.detail}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
