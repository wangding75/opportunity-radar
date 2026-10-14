import React, { useState } from 'react';
import {
  Plus,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Edit2,
  MoreVertical,
  ChevronDown,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Database,
  ArrowRight,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P14_Sources: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('ALL');
  const [searchValue, setSearchValue] = useState('');

  const sourcesList = [
    {
      id: 'reuters',
      name: '路透社',
      domain: 'reuters.com',
      type: '新闻媒体',
      status: '已启用',
      health: 98,
      healthStatus: '健康',
      frequency: '每 15 分钟',
      lastSync: '2 分钟前',
      iconBg: '#eff6ff',
      iconColor: '#2563eb',
    },
    {
      id: 'techcrunch',
      name: 'TechCrunch',
      domain: 'techcrunch.com',
      type: '新闻媒体',
      status: '已启用',
      health: 98,
      healthStatus: '健康',
      frequency: '每 15 分钟',
      lastSync: '2 分钟前',
      iconBg: '#fef2f2',
      iconColor: '#dc2626',
    },
    {
      id: 'bloomberg',
      name: 'Bloomberg',
      domain: 'bloomberg.com',
      type: '新闻媒体',
      status: '已启用',
      health: 96,
      healthStatus: '健康',
      frequency: '每 30 分钟',
      lastSync: '5 分钟前',
      iconBg: '#f1f5f9',
      iconColor: '#0f172a',
    },
    {
      id: 'twitter',
      name: 'Twitter / X',
      domain: 'twitter.com',
      type: '社交媒体',
      status: '已启用',
      health: 72,
      healthStatus: '警告',
      frequency: '每 5 分钟',
      lastSync: '8 分钟前',
      iconBg: '#f8fafc',
      iconColor: '#000000',
    },
    {
      id: 'reddit',
      name: 'Reddit',
      domain: 'reddit.com',
      type: '社交媒体',
      status: '已启用',
      health: 91,
      healthStatus: '健康',
      frequency: '每 15 分钟',
      lastSync: '3 分钟前',
      iconBg: '#fff7ed',
      iconColor: '#ea580c',
    },
    {
      id: 'mckinsey',
      name: '麦肯锡行业报告',
      domain: 'mckinsey.com',
      type: '行业报告',
      status: '已启用',
      health: 95,
      healthStatus: '健康',
      frequency: '每天',
      lastSync: '1 小时前',
      iconBg: '#eff6ff',
      iconColor: '#1d4ed8',
    },
    {
      id: 'gartner',
      name: 'Gartner 报告',
      domain: 'gartner.com',
      type: '行业报告',
      status: '已启用',
      health: 97,
      healthStatus: '健康',
      frequency: '每天',
      lastSync: '2 小时前',
      iconBg: '#f0f9ff',
      iconColor: '#0284c7',
    },
    {
      id: 'crunchbase',
      name: 'Crunchbase',
      domain: 'crunchbase.com',
      type: '数据供应商',
      status: '已启用',
      health: 93,
      healthStatus: '健康',
      frequency: '每 1 小时',
      lastSync: '12 分钟前',
      iconBg: '#ecfdf5',
      iconColor: '#059669',
    },
  ];

  const healthSegments = [
    { label: '健康 (90%以上)', count: 48, percentage: '71%', color: '#10b981' },
    { label: '警告 (70%~90%)', count: 12, percentage: '18%', color: '#f59e0b' },
    { label: '异常 (低于70%)', count: 8, percentage: '12%', color: '#ef4444' },
  ];

  return (
    <div>
      <Header
        title="来源管理"
        subtitle="集中管理数据来源，支持连接配置、健康监控与分类管理"
        actions={
          <>
            <button
              onClick={() => showToast('请输入要连接的新数据源信息', 'info')}
              className="btn btn-secondary"
            >
              <Plus size={14} />
              <span>连接新来源</span>
            </button>
            <button
              onClick={() => showToast('已触发批量操作菜单', 'info')}
              className="btn btn-secondary"
            >
              <span>批量操作</span>
              <ChevronDown size={14} />
            </button>
            <button
              onClick={() => showToast('全量数据源同步任务已发起', 'success')}
              className="btn btn-primary"
            >
              <RefreshCw size={14} />
              <span>同步所有来源</span>
            </button>
          </>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'ALL', label: '全部来源', count: 68 },
          { key: 'NEWS', label: '新闻媒体', count: 24 },
          { key: 'SOCIAL', label: '社交媒体', count: 16 },
          { key: 'REPORT', label: '行业报告', count: 12 },
          { key: 'DATA', label: '数据供应商', count: 8 },
          { key: 'INTERNAL', label: '内部系统', count: 8 },
        ]}
      />

      {/* Main Split: Table + Right Side Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 16 }}>
        {/* Left: Sources Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: 260 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索来源名称、描述或域名..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 'var(--font-size-xs)' }}
              />
            </div>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>状态: 全部</option>
              <option>已启用</option>
              <option>已停用</option>
            </select>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>类型: 全部</option>
              <option>新闻媒体</option>
              <option>社交媒体</option>
            </select>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>健康状态: 全部</option>
              <option>健康</option>
              <option>警告</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 36 }}><input type="checkbox" /></th>
                <th>来源名称</th>
                <th style={{ width: 90 }}>类型</th>
                <th style={{ width: 80 }}>状态</th>
                <th style={{ width: 110 }}>健康状态</th>
                <th style={{ width: 100 }}>更新频率</th>
                <th style={{ width: 100 }}>最后同步</th>
                <th style={{ width: 90, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {sourcesList.map((src) => (
                <tr key={src.id} onClick={() => navigate(`/sources/${src.id}`)}>
                  <td><input type="checkbox" onClick={(e) => e.stopPropagation()} /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 28, height: 28, borderRadius: 6, backgroundColor: src.iconBg, color: src.iconColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '12px', flexShrink: 0 }}>
                        {src.name.charAt(0)}
                      </div>
                      <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {src.name}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{src.domain}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 6px', borderRadius: 4 }}>
                      {src.type}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '2px 6px', borderRadius: 4 }}>
                      {src.status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: src.healthStatus === '健康' ? '#10b981' : '#f59e0b' }} />
                      <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 500 }}>
                        {src.healthStatus} {src.health}%
                      </span>
                    </div>
                  </td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>{src.frequency}</td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{src.lastSync}</td>
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                      <button onClick={(e) => { e.stopPropagation(); navigate(`/sources/${src.id}`); }} style={{ color: 'var(--text-muted)', padding: 3 }}>
                        <Eye size={14} />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); showToast(`编辑来源: ${src.name}`, 'info'); }} style={{ color: 'var(--text-muted)', padding: 3 }}>
                        <Edit2 size={14} />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); showToast('更多配置', 'info'); }} style={{ color: 'var(--text-muted)', padding: 3 }}>
                        <MoreVertical size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={68} pageSize={8} currentPage={1} />
        </div>

        {/* Right Side Overview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Card 1: 来源概览 */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              来源概览
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, textAlign: 'center' }}>
              <div style={{ padding: '8px 2px', borderRadius: 4, backgroundColor: '#eff6ff' }}>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: '#2563eb' }}>68</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>全部来源</div>
              </div>
              <div style={{ padding: '8px 2px', borderRadius: 4, backgroundColor: '#ecfdf5' }}>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: '#10b981' }}>62</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>已启用</div>
              </div>
              <div style={{ padding: '8px 2px', borderRadius: 4, backgroundColor: '#fffbeb' }}>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: '#f59e0b' }}>4</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>警告</div>
              </div>
              <div style={{ padding: '8px 2px', borderRadius: 4, backgroundColor: '#fef2f2' }}>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: '#ef4444' }}>2</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>异常</div>
              </div>
            </div>
          </div>

          {/* Card 2: 健康状态分布 */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              健康状态分布
            </h3>
            <DonutChart total={68} totalLabel="总计" segments={healthSegments} size={110} />
          </div>

          {/* Card 3: 来源类型分布 */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              来源类型分布
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-xs)' }}>
              {[
                { label: '新闻媒体', count: 24, ratio: '35%', color: '#2563eb' },
                { label: '社交媒体', count: 16, ratio: '24%', color: '#10b981' },
                { label: '行业报告', count: 12, ratio: '18%', color: '#8b5cf6' },
                { label: '数据供应商', count: 8, ratio: '12%', color: '#f59e0b' },
                { label: '内部系统', count: 8, ratio: '12%', color: '#06b6d4' },
              ].map((t, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{t.label}</span>
                    <span style={{ fontWeight: 600 }}>{t.count} ({t.ratio})</span>
                  </div>
                  <div style={{ width: '100%', height: 5, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
                    <div style={{ width: t.ratio, height: '100%', backgroundColor: t.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 4: 最近同步任务 */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              最近同步任务
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-xs)' }}>
              {[
                { task: '同步 TechCrunch', status: '成功', time: '2 分钟前', color: 'var(--color-success)' },
                { task: '同步 Twitter/X', status: '警告', time: '8 分钟前', color: 'var(--color-warning)' },
                { task: '同步 公司财报 API', status: '成功', time: '实时', color: 'var(--color-success)' },
              ].map((job, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{job.task}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: '12px', color: job.color, fontWeight: 600 }}>{job.status}</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{job.time}</span>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => navigate('/runs')}
              style={{ fontSize: '12px', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: 4, marginTop: 10, cursor: 'pointer' }}
            >
              <span>查看所有同步任务</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Card: 健康监控趋势 */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
            健康监控趋势
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 'var(--font-size-xs)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 2, backgroundColor: '#10b981' }} />
              <span>健康 (&ge;90%)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 2, backgroundColor: '#f59e0b' }} />
              <span>警告 (70%~90%)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 8, height: 2, backgroundColor: '#ef4444' }} />
              <span>异常 (&lt;70%)</span>
            </div>
            <select className="input-base" style={{ height: 28, fontSize: '12px' }}>
              <option>近 24 小时</option>
              <option>近 7 天</option>
            </select>
          </div>
        </div>

        <div style={{ height: 120 }}>
          <svg viewBox="0 0 700 100" style={{ width: '100%', height: '100%' }}>
            <polyline points="30,25 90,20 150,22 210,35 270,30 330,38 390,28 450,30 510,24 570,22 630,20 680,24" fill="none" stroke="#10b981" strokeWidth="2" />
            <polyline points="30,65 90,62 150,60 210,58 270,60 330,62 390,60 450,58 510,60 570,62 630,65 680,64" fill="none" stroke="#f59e0b" strokeWidth="2" />
            <polyline points="30,85 90,85 150,85 210,85 270,85 330,85 390,85 450,85 510,85 570,85 630,85 680,85" fill="none" stroke="#ef4444" strokeWidth="2" />
            {['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'].map((t, i) => (
              <text key={i} x={30 + i * 59} y="98" fontSize="8" fill="#94a3b8" textAnchor="middle">{t}</text>
            ))}
          </svg>
        </div>
      </div>
    </div>
  );
};
