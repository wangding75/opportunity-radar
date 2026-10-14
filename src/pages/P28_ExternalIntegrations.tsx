import React, { useState } from 'react';
import {
  Plus,
  Zap,
  Settings,
  RefreshCw,
  MoreVertical,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Link2,
  ExternalLink,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P28_ExternalIntegrations: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();

  const destSegments = [
    { label: 'Slack', count: 42, percentage: '32.8%', color: '#2563eb' },
    { label: 'Email', count: 38, percentage: '29.7%', color: '#10b981' },
    { label: '飞书', count: 21, percentage: '16.4%', color: '#06b6d4' },
    { label: 'Teams', count: 15, percentage: '11.7%', color: '#8b5cf6' },
    { label: '钉钉', count: 8, percentage: '6.3%', color: '#f59e0b' },
    { label: '其他', count: 4, percentage: '3.1%', color: '#94a3b8' },
  ];

  const integrationsList = [
    { name: 'Slack', type: '协作工具', status: '运行正常', usage: '告警通知、日更摘要', target: '机会雷达团队 / #alerts', lastSync: '3 分钟前', rules: '告警规则 6 条' },
    { name: 'Microsoft Teams', type: '协作工具', status: '运行正常', usage: '告警通知、任务协作', target: '机会雷达团队 / General', lastSync: '18 分钟前', rules: '告警规则 4 条' },
    { name: '飞书', type: '协作工具', status: '运行正常', usage: '告警通知、文档引用', target: '机会雷达 / #情报速递', lastSync: '28 分钟前', rules: '监控计划 3 个' },
    { name: '钉钉', type: '协作工具', status: '异常', usage: '告警通知', target: '机会雷达 / 情报通知群', lastSync: '2 小时前', rules: '告警规则 2 条', needsFix: true },
    { name: 'Email', type: '通信渠道', status: '运行正常', usage: '告警邮件、日报发送', target: 'alerts@yourcompany.com', lastSync: '6 分钟前', rules: '监控计划 5 个' },
    { name: 'Webhook', type: '开发者工具', status: '运行正常', usage: '告警回调、自定义集成', target: 'https://api.yourcompany.com/webhook', lastSync: '5 分钟前', rules: '告警规则 7 条' },
    { name: 'Notion', type: '协同文档', status: '待授权', usage: '情报库同步、知识沉淀', target: '机会雷达知识库', lastSync: '授权已过期', rules: '监控计划 2 个', needsFix: true },
    { name: 'GitHub', type: '开发者工具', status: '运行正常', usage: '事件跟踪、Issue 创建', target: 'opportunity-radar/ops', lastSync: '1 小时前', rules: '监控计划 1 个' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '外部集成' },
        ]}
        title="外部集成"
        subtitle="连接第三方工具与服务，扩展信息触达与协作能力。"
        actions={
          <>
            <button onClick={() => openState('P28-S01')} className="btn btn-primary">
              <Plus size={14} />
              <span>新增连接</span>
            </button>
            <button onClick={() => showToast('已发起所有外部集成连通性测试', 'success')} className="btn btn-secondary">
              <Zap size={14} />
              <span>测试连接</span>
            </button>
          </>
        }
      />

      {/* Top 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>已连接</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>8</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上月 +2</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>运行正常</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>7</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>占比 87.5%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>异常集成</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#ef4444' }}>1</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>12.5%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>待授权</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#f59e0b' }}>2</div>
          <div style={{ fontSize: '12px', color: 'var(--color-primary)', marginTop: 2, cursor: 'pointer' }} onClick={() => openState('P28-S01')}>需要重新授权 &gt;</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>最近同步</div>
          <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>3 分钟前</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>Slack 频道 #alerts</div>
        </div>
      </div>

      {/* Main Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 16 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>集成</th>
              <th style={{ width: 100 }}>类型</th>
              <th style={{ width: 90, textAlign: 'center' }}>状态</th>
              <th>用途</th>
              <th>连接到</th>
              <th style={{ width: 100 }}>最近同步</th>
              <th style={{ width: 130 }}>关联规则/监控</th>
              <th style={{ width: 100, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {integrationsList.map((item, idx) => (
              <tr key={idx} onClick={() => item.needsFix && openState('P28-S01')}>
                <td><span style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>{item.name}</span></td>
                <td><span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.type}</span></td>
                <td style={{ textAlign: 'center' }}><StatusBadge status={item.status} type="status" /></td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.usage}</td>
                <td style={{ fontSize: '12px', color: 'var(--color-primary)' }}>{item.target}</td>
                <td style={{ fontSize: '12px', color: item.lastSync.includes('过期') ? '#ef4444' : 'var(--text-muted)' }}>{item.lastSync}</td>
                <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.rules}</td>
                <td style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                    <Settings size={13} color="var(--text-muted)" style={{ cursor: 'pointer' }} onClick={(e) => { e.stopPropagation(); openState('P28-S01'); }} />
                    <RefreshCw size={13} color="var(--text-muted)" style={{ cursor: 'pointer' }} onClick={(e) => { e.stopPropagation(); showToast(`已测试 ${item.name} 连通性`, 'success'); }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Bottom Split: Destinations + Events + Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr', gap: 16 }}>
        {/* Destinations */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
            通知去向 (近 7 天)
          </h3>
          <DonutChart total={128} totalLabel="近 7 天" segments={destSegments} size={110} />
        </div>

        {/* Recent Events */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              近期集成事件
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
            {[
              { title: 'Slack 连接成功', desc: '连接状态恢复，已同步通知规则', time: '今天 10:21', color: 'var(--color-success)' },
              { title: '钉钉 授权过期', desc: '请重新授权以继续接收通知', time: '今天 08:47', color: 'var(--color-danger)' },
              { title: 'Webhook 测试成功', desc: '接口响应正常 (200 OK)', time: '昨天 17:36', color: 'var(--color-success)' },
            ].map((ev, i) => (
              <div key={i} style={{ padding: '6px 8px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ fontWeight: 600, color: ev.color }}>{ev.title}</span>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{ev.time}</span>
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{ev.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration Preview */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              配置预览 (Slack)
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>运行正常</span>
          </div>
          <div style={{ padding: '10px', borderRadius: 6, backgroundColor: '#f8fafc', border: '1px solid var(--border-subtle)', fontSize: '12px', marginBottom: 10 }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>【机会雷达】高优先级告警</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.4 }}>
              来源: TechCrunch<br />
              标题: AI 芯片供应链出现新的断供风险<br />
              严重度: 高 · 时间: 2024-04-12 10:23
            </div>
          </div>
          <button onClick={() => showToast('已发送测试消息到 Slack #alerts', 'success')} className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
            发送测试消息
          </button>
        </div>
      </div>
    </div>
  );
};
