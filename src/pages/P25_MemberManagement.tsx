import React, { useState } from 'react';
import {
  UserPlus,
  Download,
  Search,
  Filter,
  MoreVertical,
  ChevronRight,
  Shield,
  Users,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { MOCK_MEMBERS } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P25_MemberManagement: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const roleSegments = [
    { label: '工作区管理员', count: 2, percentage: '8.3%', color: '#2563eb' },
    { label: '研究负责人', count: 3, percentage: '12.5%', color: '#8b5cf6' },
    { label: '高级分析师', count: 4, percentage: '16.7%', color: '#06b6d4' },
    { label: '分析师', count: 6, percentage: '25.0%', color: '#10b981' },
    { label: '研究员', count: 4, percentage: '16.7%', color: '#f59e0b' },
    { label: '助理分析师', count: 4, percentage: '16.7%', color: '#ec4899' },
    { label: '实习生', count: 1, percentage: '4.1%', color: '#94a3b8' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '成员管理' },
        ]}
        title="成员管理"
        subtitle="管理工作区成员、角色与协作权限，查看成员活动与使用情况。"
        actions={
          <>
            <button
              onClick={() => openState('P25-S01')}
              className="btn btn-primary"
            >
              <UserPlus size={14} />
              <span>邀请成员</span>
            </button>
            <button
              onClick={() => showToast('成员列表已导出为 Excel', 'info')}
              className="btn btn-secondary"
            >
              <Download size={14} />
              <span>导出成员</span>
            </button>
          </>
        }
      />

      {/* Top 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>成员总数</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>24</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 +2 (9.09%) ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>活跃成员</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>18</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>活跃率 75.0%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>待接受邀请</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#f59e0b' }}>3</div>
          <div style={{ fontSize: '12px', color: 'var(--color-primary)', marginTop: 2, cursor: 'pointer' }}>查看邀请 &gt;</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>席位使用情况</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>24 / 30</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>剩余 6 个席位</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>本周新增</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>2</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>较上周 -1</div>
        </div>
      </div>

      {/* Main Split: Left Members Table + Right Role Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Left: Table Card */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', width: 240 }}>
              <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索姓名、邮箱或角色..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
              />
            </div>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>所有角色</option>
              <option>工作区管理员</option>
              <option>高级分析师</option>
              <option>分析师</option>
            </select>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>所有状态</option>
              <option>正常</option>
              <option>暂停</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>头像 / 姓名</th>
                <th style={{ width: 150 }}>邮箱</th>
                <th style={{ width: 100 }}>角色</th>
                <th style={{ width: 65, textAlign: 'center' }}>负责机会</th>
                <th style={{ width: 65, textAlign: 'center' }}>负责研究</th>
                <th style={{ width: 85 }}>最近活跃</th>
                <th style={{ width: 85 }}>加入时间</th>
                <th style={{ width: 65, textAlign: 'center' }}>状态</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_MEMBERS.map((m) => (
                <tr key={m.id} onClick={() => openState('P25-S02')}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 26, height: 26, borderRadius: '50%', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', fontWeight: 700, fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {m.name.charAt(0)}
                      </div>
                      <span style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>{m.name}</span>
                    </div>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.email}</td>
                  <td>
                    <span style={{ fontSize: '12px', padding: '2px 6px', borderRadius: 4, backgroundColor: '#f1f5f9', color: 'var(--text-primary)' }}>
                      {m.role}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center', fontSize: '12px', fontWeight: 600 }}>{m.opportunitiesCount}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px' }}>{m.researchCount}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.lastActive}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.joinedAt}</td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={m.status} type="status" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={24} pageSize={8} currentPage={1} />
        </div>

        {/* Right: Role Distribution & Recent Activities */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Distribution */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              角色分布
            </h3>
            <DonutChart total={24} totalLabel="总数" segments={roleSegments} size={110} />
          </div>

          {/* Pending Invites */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                待处理邀请 (3)
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
              {[
                { email: 'zhoujian@radar.com', role: '分析师', time: '已邀请 2 天' },
                { email: 'sunyi@radar.com', role: '研究员', time: '已邀请 5 天' },
                { email: 'lizhe@radar.com', role: '分析师', time: '已邀请 7 天' },
              ].map((inv, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <div>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{inv.email}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{inv.role} · {inv.time}</div>
                  </div>
                  <span onClick={() => showToast('已重新发送邀请邮件', 'success')} style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>重新发送</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
