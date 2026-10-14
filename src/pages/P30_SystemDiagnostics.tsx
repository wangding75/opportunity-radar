import React, { useState } from 'react';
import {
  RefreshCw,
  Download,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  Activity,
  Zap,
  Server,
  Database,
  Layers,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { useRouter } from '../router/RouterContext';

export const P30_SystemDiagnostics: React.FC = () => {
  const { navigate, showToast } = useRouter();

  const services = [
    { name: '情报采集', desc: '采集全球信息源', status: '正常', rate: '99.6%', latency: '320ms', exception: '—', scope: '无' },
    { name: '来源连接', desc: '连接与数据同步', status: '降级', rate: '96.1%', latency: '1.2s', exception: 'LinkedIn 授权过期', scope: '部分来源' },
    { name: '解析与去重', desc: '内容解析与去重', status: '正常', rate: '99.2%', latency: '480ms', exception: '—', scope: '无' },
    { name: '分析队列', desc: 'Analysis Queue', status: '降级', rate: '97.3%', latency: '1.5s', exception: '队列积压 负载 92%', scope: '分析延迟' },
    { name: '机会分析', desc: 'Opportunity Analysis', status: '正常', rate: '98.8%', latency: '690ms', exception: '—', scope: '无' },
    { name: '研究生成', desc: 'Research Generation', status: '正常', rate: '99.3%', latency: '1.1s', exception: '—', scope: '无' },
    { name: '告警服务', desc: 'Alert Service', status: '正常', rate: '99.7%', latency: '210ms', exception: '—', scope: '无' },
    { name: '通知服务', desc: 'Notification Service', status: '降级', rate: '93.2%', latency: '2.6s', exception: 'Webhook 连续失败', scope: '通知延迟' },
    { name: '外部集成', desc: 'Integrations', status: '正常', rate: '98.5%', latency: '430ms', exception: '—', scope: '无' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '系统诊断' },
        ]}
        title="系统诊断"
        subtitle="全面监控系统运行状态，快速定位问题并采取措施"
        actions={
          <>
            <button onClick={() => showToast('已触发系统全量重新检测', 'info')} className="btn btn-secondary">
              <RefreshCw size={14} />
              <span>重新检测</span>
            </button>
            <button onClick={() => showToast('系统诊断报告已生成', 'success')} className="btn btn-primary">
              <Download size={14} />
              <span>导出诊断报告</span>
            </button>
          </>
        }
      />

      {/* Top 6 KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>系统健康度</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>96</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/100 · 良好</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↑ 2</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>正常组件</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>11</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>总计 14 个</div>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>降级组件</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#f59e0b' }}>2</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↓ 1</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>异常组件</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#ef4444' }}>1</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>较昨日 持平</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>最近 24h 错误</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>38</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↓ 12 (24%)</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>平均恢复时间</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>18 <span style={{ fontSize: '12px' }}>分钟</span></div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较昨日 ↓ 5 分钟</div>
        </div>
      </div>

      {/* Main Split: Left Services Table + Right Pipeline & Diagnosis Tools */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
        {/* Left: Core Services */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              核心服务状态
            </h3>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>服务组件</th>
                <th style={{ width: 65, textAlign: 'center' }}>状态</th>
                <th style={{ width: 80, textAlign: 'center' }}>成功率</th>
                <th style={{ width: 75 }}>P95延迟</th>
                <th>最近异常</th>
                <th style={{ width: 75 }}>影响范围</th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc, i) => (
                <tr key={i}>
                  <td>
                    <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>{svc.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{svc.desc}</div>
                  </td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={svc.status} type="status" /></td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{svc.rate}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{svc.latency}</td>
                  <td style={{ fontSize: '12px', color: svc.exception === '—' ? 'var(--text-muted)' : '#ef4444' }}>{svc.exception}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{svc.scope}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: Pipeline & Diagnostics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Pipeline */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              数据链路诊断
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', textAlign: 'center' }}>
              {[
                { name: '来源', status: '正常', sub: '24/26', color: 'var(--color-success)' },
                { name: '采集', status: '正常', sub: '98.8%', color: 'var(--color-success)' },
                { name: '解析', status: '正常', sub: '99.2%', color: 'var(--color-success)' },
                { name: '去重', status: '正常', sub: '98.9%', color: 'var(--color-success)' },
                { name: '分析队列', status: '降级', sub: '负载 92%', color: '#f59e0b' },
                { name: '机会生成', status: '正常', sub: '1,284 个', color: 'var(--color-success)' },
                { name: '告警/通知', status: '异常', sub: '延迟 2.6s', color: '#ef4444' },
              ].map((p, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: p.color }} />
                  <span style={{ fontWeight: 600, marginTop: 2 }}>{p.name}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '9px' }}>{p.sub}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Anomalies */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                最近异常事件
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
              {[
                { title: 'LinkedIn 授权过期，部分信息源失效', time: '10:28', status: '进行中', color: '#ef4444' },
                { title: 'Reddit API 限流，采集成功率下降', time: '10:15', status: '降级中', color: '#f59e0b' },
                { title: 'Analysis Queue Worker 负载 92%', time: '10:12', status: '降级中', color: '#f59e0b' },
                { title: 'Webhook 连续失败，通知发送异常', time: '09:58', status: '异常', color: '#ef4444' },
              ].map((ev, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <div>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{ev.title}</div>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{ev.time}</div>
                  </div>
                  <span style={{ fontSize: '9px', color: ev.color, fontWeight: 700 }}>{ev.status}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Diagnostic Action Buttons */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              诊断操作
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              <button onClick={() => showToast('正在执行全面系统自检', 'info')} className="btn btn-secondary btn-sm" style={{ fontSize: '12px' }}>重新检测</button>
              <button onClick={() => showToast('正在测试所有外部数据源', 'info')} className="btn btn-secondary btn-sm" style={{ fontSize: '12px' }}>测试全部来源</button>
              <button onClick={() => showToast('正在测试外部集成连通性', 'info')} className="btn btn-secondary btn-sm" style={{ fontSize: '12px' }}>测试外部集成</button>
              <button onClick={() => navigate('/runs')} className="btn btn-secondary btn-sm" style={{ fontSize: '12px' }}>查看错误日志</button>
              <button onClick={() => navigate('/runs')} className="btn btn-secondary btn-sm" style={{ fontSize: '12px' }}>查看运行记录</button>
              <button onClick={() => showToast('已生成诊断报告并下载', 'success')} className="btn btn-primary btn-sm" style={{ fontSize: '12px' }}>导出诊断报告</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
