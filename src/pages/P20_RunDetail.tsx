import React, { useState } from 'react';
import {
  ArrowLeft,
  RotateCw,
  Download,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Layers,
  FileText,
  ChevronRight,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { useRouter } from '../router/RouterContext';

export const P20_RunDetail: React.FC = () => {
  const { navigate, showToast } = useRouter();

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '执行历史', path: '/runs' },
          { label: '运行详情' },
        ]}
        title="运行详情"
        subtitle="运行 ID : RUN-20260610-0950 · 监控计划 : 全球并购动态监控 · 触发方式 : 定时触发 (每 30 分钟)"
        extra={<StatusBadge status="成功" type="health" />}
        actions={
          <>
            <button onClick={() => showToast('已触发重新运行', 'success')} className="btn btn-primary">
              <RotateCw size={14} />
              <span>重新运行</span>
            </button>
            <button onClick={() => showToast('已导出完整执行日志', 'info')} className="btn btn-secondary">
              <Download size={14} />
              <span>导出日志</span>
            </button>
            <button onClick={() => navigate('/runs')} className="btn btn-secondary">
              <ArrowLeft size={14} />
              <span>返回运行记录</span>
            </button>
          </>
        }
      />

      {/* Top 6 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>运行状态</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-success)' }}>成功</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>全部任务完成</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>开始时间</div>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>2026-06-10 09:50:00</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>计划时间: 09:50:00</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>结束时间</div>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>2026-06-10 09:58:42</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>实际结束</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>总耗时</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>8分42秒</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较平均耗时 -12%</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>触发方式</div>
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700 }}>定时触发</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>每 30 分钟</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>执行完成度</div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-success)' }}>100%</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>目标任务完成</div>
        </div>
      </div>

      {/* Middle Split: Timeline (Left) + Source Execution (Center) + Result Stats (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 280px', gap: 16, marginBottom: 16 }}>
        {/* Left: 阶段时间线 */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            阶段时间线
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: '12px' }}>
            {[
              { stage: '任务启动', time: '06-10 09:50:00', duration: '', status: '成功' },
              { stage: '来源采集', time: '06-10 09:50:05', duration: '耗时 3分12秒', status: '成功' },
              { stage: '去重清洗', time: '06-10 09:53:17', duration: '耗时 1分24秒', status: '成功' },
              { stage: '结构分析', time: '06-10 09:54:41', duration: '耗时 2分18秒', status: '成功' },
              { stage: '结果入库', time: '06-10 09:57:00', duration: '耗时 1分02秒', status: '成功' },
              { stage: '通知/完成', time: '06-10 09:58:42', duration: '耗时 42秒', status: '成功' },
            ].map((stg, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', marginTop: 3, flexShrink: 0 }} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{stg.stage}</span>
                    <span style={{ fontSize: '9px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '0 4px', borderRadius: 2 }}>{stg.status}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{stg.time}</div>
                  {stg.duration && <div style={{ fontSize: '9px', color: 'var(--text-secondary)' }}>{stg.duration}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center: 来源执行明细 */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              来源执行明细
            </h3>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>来源</th>
                <th style={{ width: 70 }}>状态</th>
                <th style={{ width: 65 }}>耗时</th>
                <th style={{ width: 65, textAlign: 'center' }}>采集数</th>
                <th style={{ width: 65, textAlign: 'center' }}>新增数</th>
                <th style={{ width: 65, textAlign: 'center' }}>去重数</th>
                <th style={{ width: 55, textAlign: 'center' }}>失败数</th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: 'Reuters', status: '成功', cost: '42秒', col: '1,256', add: '312', dup: '944', fail: 0 },
                { name: 'TechCrunch', status: '成功', cost: '38秒', col: '842', add: '201', dup: '641', fail: 0 },
                { name: 'SimilarWeb', status: '部分失败', cost: '1分12秒', col: '1,102', add: '276', dup: '826', fail: 3 },
                { name: 'GitHub', status: '成功', cost: '1分05秒', col: '3,896', add: '653', dup: '3,243', fail: 0 },
                { name: 'Reddit', status: '重试成功', cost: '1分48秒', col: '2,345', add: '421', dup: '1,924', fail: 2 },
                { name: 'LinkedIn', status: '部分失败', cost: '1分28秒', col: '1,765', add: '312', dup: '1,453', fail: 1 },
                { name: 'Gartner', status: '超时', cost: '2分00秒', col: '0', add: '0', dup: '0', fail: 1 },
              ].map((row, i) => (
                <tr key={i}>
                  <td><span style={{ fontWeight: 600, fontSize: '12px' }}>{row.name}</span></td>
                  <td><StatusBadge status={row.status} type="status" /></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.cost}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{row.col}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', color: 'var(--color-primary)', fontWeight: 600 }}>{row.add}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{row.dup}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', color: row.fail > 0 ? '#ef4444' : 'var(--text-muted)' }}>{row.fail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: 采集结果统计 */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            采集结果统计
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { label: '采集总数', val: '11,484', sub: '+8.7%', color: 'var(--text-primary)' },
              { label: '新增情报', val: '2,273', sub: '+6.3%', color: 'var(--color-primary)' },
              { label: '去重数量', val: '9,211', sub: '+9.4%', color: 'var(--text-secondary)' },
              { label: '失败数量', val: '7', sub: '-36.4%', color: '#ef4444' },
              { label: '重试次数', val: '7', sub: '-22.2%', color: '#f59e0b' },
              { label: '入库数量', val: '2,273', sub: '+6.3%', color: 'var(--color-success)' },
            ].map((stat, idx) => (
              <div key={idx} style={{ padding: '8px 10px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{stat.label}</div>
                <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: stat.color, marginTop: 2 }}>{stat.val}</div>
                <div style={{ fontSize: '9px', color: 'var(--color-success)' }}>较上次 {stat.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Split: Errors Table (Left) + Queue Result (Center) + Logs (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        {/* Errors */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
            错误与重试
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
            {[
              { type: '超时 (Timeout)', src: 'Gartner', info: '请求超时 (120.0s)', res: '重试 3 次后失败', level: '高' },
              { type: '限流 (Rate Limit)', src: 'Reddit', info: 'HTTP 429 Too Many Requests', res: '重试 2 次后成功', level: '中' },
              { type: '解析失败', src: 'SimilarWeb', info: 'JSON 解析失败', res: '跳过该条，继续执行', level: '中' },
            ].map((err, i) => (
              <div key={i} style={{ padding: '6px 8px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ fontWeight: 600, color: err.level === '高' ? '#ef4444' : '#f59e0b' }}>{err.type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{err.src}</span>
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{err.info}</div>
                <div style={{ color: 'var(--color-primary)', fontSize: '12px', marginTop: 2 }}>{err.res}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Analysis Queue 结果 */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
            Analysis Queue 结果
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, textAlign: 'center', marginBottom: 12 }}>
            <div style={{ padding: '6px 2px', borderRadius: 4, backgroundColor: '#eff6ff' }}>
              <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: '#2563eb' }}>156</div>
              <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>待分析</div>
            </div>
            <div style={{ padding: '6px 2px', borderRadius: 4, backgroundColor: '#ecfdf5' }}>
              <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: '#10b981' }}>2,089</div>
              <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>分析成功</div>
            </div>
            <div style={{ padding: '6px 2px', borderRadius: 4, backgroundColor: '#fef2f2' }}>
              <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: '#ef4444' }}>28</div>
              <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>分析失败</div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>分析结果趋势 (最近 30 次运行)</div>
          <div style={{ height: 60 }}>
            <svg viewBox="0 0 300 60" style={{ width: '100%', height: '100%' }}>
              {[15, 22, 28, 35, 42, 38, 45, 50, 48, 52, 55, 49, 58].map((h, idx) => (
                <rect key={idx} x={10 + idx * 22} y={55 - h} width="12" height={h} fill="#10b981" rx="2" />
              ))}
            </svg>
          </div>
        </div>

        {/* 运行日志 */}
        <div className="card" style={{ padding: '14px 16px', backgroundColor: '#0f172a', color: '#f8fafc', fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, borderBottom: '1px solid #334155', paddingBottom: 6 }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>运行日志</span>
            <span style={{ fontSize: '12px', color: '#38bdf8', cursor: 'pointer' }}>查看完整日志 &gt;</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px', lineHeight: 1.4 }}>
            <div><span style={{ color: '#64748b' }}>09:50:00</span> <span style={{ color: '#38bdf8' }}>[INFO]</span> 运行开始: RUN-20260610-0950</div>
            <div><span style={{ color: '#64748b' }}>09:50:05</span> <span style={{ color: '#38bdf8' }}>[INFO]</span> 来源采集阶段开始 (8 个来源)</div>
            <div><span style={{ color: '#64748b' }}>09:50:08</span> <span style={{ color: '#fbbf24' }}>[WARN]</span> SimilarWeb 部分失败: 3 条解析异常</div>
            <div><span style={{ color: '#64748b' }}>09:50:20</span> <span style={{ color: '#f87171' }}>[ERROR]</span> Gartner 请求超时 (120.0s), 重试第 1 次</div>
            <div><span style={{ color: '#64748b' }}>09:53:17</span> <span style={{ color: '#38bdf8' }}>[INFO]</span> 去重清洗完成: 去重 9,211 条</div>
            <div><span style={{ color: '#64748b' }}>09:58:42</span> <span style={{ color: '#4ade80' }}>[INFO]</span> 运行完成，用时 8分42秒，状态: 成功</div>
          </div>
        </div>
      </div>
    </div>
  );
};
