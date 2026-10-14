import React, { useState } from 'react';
import {
  Plus,
  Copy,
  Check,
  X,
  Minus,
  Edit2,
  Shield,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P26_RolesAndPermissions: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [selectedRole, setSelectedRole] = useState('Owner');

  const roles = [
    { id: 'Owner', name: 'Owner', count: '1 人', desc: '拥有工作区的全部权限，可管理成员、角色、设置及计费等。', protected: true },
    { id: 'Admin', name: 'Admin', count: '3 人', desc: '管理工作区配置与成员，除所有者权限外的全部权限。', protected: true },
    { id: 'Analyst', name: 'Analyst', count: '18 人', desc: '可创建与编辑大部分业务内容，管理个人数据与分析。', protected: true },
    { id: 'Viewer', name: 'Viewer', count: '27 人', desc: '可查看已发布内容与报表，无法创建、编辑或删除。', protected: true },
    { id: 'Custom', name: '自定义角色', count: '3 个角色', desc: '按业务需要创建的自定义角色与权限组合。', protected: false },
  ];

  const permissionsMatrix = [
    { module: '情报', perms: [
      { name: '查看', owner: true, admin: true, analyst: true, viewer: true, customA: true, customB: true },
      { name: '创建', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: true },
      { name: '编辑', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: true },
      { name: '删除', owner: true, admin: true, analyst: false, viewer: false, customA: false, customB: false },
      { name: '管理', owner: true, admin: true, analyst: false, viewer: false, customA: false, customB: false },
    ]},
    { module: '机会', perms: [
      { name: '查看', owner: true, admin: true, analyst: true, viewer: true, customA: true, customB: true },
      { name: '创建', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: false },
      { name: '编辑', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: true },
      { name: '删除', owner: true, admin: true, analyst: false, viewer: false, customA: false, customB: false },
    ]},
    { module: '研究', perms: [
      { name: '查看', owner: true, admin: true, analyst: true, viewer: true, customA: false, customB: false },
      { name: '创建', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: true },
      { name: '编辑', owner: true, admin: true, analyst: true, viewer: false, customA: true, customB: true },
      { name: '删除', owner: true, admin: true, analyst: false, viewer: false, customA: false, customB: false },
      { name: '管理', owner: true, admin: true, analyst: false, viewer: false, customA: false, customB: false },
    ]},
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '角色与权限' },
        ]}
        title="角色与权限"
        subtitle="管理工作区角色与权限，控制成员对功能与数据的访问能力。"
        actions={
          <>
            <button
              onClick={() => openState('P26-S01')}
              className="btn btn-primary"
            >
              <Plus size={14} />
              <span>新建角色</span>
            </button>
            <button
              onClick={() => showToast('已复制当前角色权限模板', 'info')}
              className="btn btn-secondary"
            >
              <Copy size={14} />
              <span>复制角色</span>
            </button>
          </>
        }
      />

      {/* Role Cards Horizontal Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 20 }}>
        {roles.map((r) => {
          const isSelected = r.id === selectedRole;
          return (
            <div
              key={r.id}
              onClick={() => setSelectedRole(r.id)}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? 'var(--color-primary)' : 'var(--border-default)',
                boxShadow: isSelected ? '0 0 0 2px var(--color-primary-light)' : undefined,
                padding: '14px 16px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>{r.name}</h4>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{r.count}</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4, height: 42, overflow: 'hidden' }}>
                {r.desc}
              </p>
              <div style={{ marginTop: 8 }}>
                <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: 2, backgroundColor: r.protected ? '#eff6ff' : '#f1f5f9', color: r.protected ? 'var(--color-primary)' : 'var(--text-muted)' }}>
                  {r.protected ? '受保护' : '自定义'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Split: Left Permission Matrix + Right Role Details */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Left: Matrix Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              权限矩阵 (基于 {selectedRole})
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '12px', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><Check size={11} color="#10b981" /> 全部允许</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><Minus size={11} color="#3b82f6" /> 部分允许</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><X size={11} color="#ef4444" /> 未允许</span>
            </div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 140 }}>能力组 / 权限</th>
                <th style={{ width: 60, textAlign: 'center' }}>Owner</th>
                <th style={{ width: 60, textAlign: 'center' }}>Admin</th>
                <th style={{ width: 60, textAlign: 'center' }}>Analyst</th>
                <th style={{ width: 60, textAlign: 'center' }}>Viewer</th>
                <th style={{ width: 80, textAlign: 'center' }}>自定义角色A</th>
                <th style={{ width: 80, textAlign: 'center' }}>自定义角色B</th>
              </tr>
            </thead>
            <tbody>
              {permissionsMatrix.map((mod) => (
                <React.Fragment key={mod.module}>
                  {mod.perms.map((p, idx) => (
                    <tr key={idx}>
                      <td>
                        <span style={{ fontWeight: idx === 0 ? 600 : 400, color: idx === 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                          {idx === 0 ? mod.module : ''} - {p.name}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>{p.owner ? <Check size={13} color="#10b981" /> : <X size={13} color="#ef4444" />}</td>
                      <td style={{ textAlign: 'center' }}>{p.admin ? <Check size={13} color="#10b981" /> : <X size={13} color="#ef4444" />}</td>
                      <td style={{ textAlign: 'center' }}>{p.analyst ? <Check size={13} color="#10b981" /> : <Minus size={13} color="#3b82f6" />}</td>
                      <td style={{ textAlign: 'center' }}>{p.viewer ? <Check size={13} color="#10b981" /> : <X size={13} color="#ef4444" />}</td>
                      <td style={{ textAlign: 'center' }}>{p.customA ? <Check size={13} color="#10b981" /> : <X size={13} color="#ef4444" />}</td>
                      <td style={{ textAlign: 'center' }}>{p.customB ? <Check size={13} color="#10b981" /> : <X size={13} color="#ef4444" />}</td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: Role Detail Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                角色详情 ({selectedRole})
              </h3>
              <button onClick={() => openState('P26-S01')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>
                <Edit2 size={11} />
                <span>编辑</span>
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>角色标识</span>
                <span style={{ fontWeight: 600 }}>{selectedRole.toLowerCase()} (受保护)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>创建时间</span>
                <span>2024-01-12 09:34:12</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>最后更新</span>
                <span>2024-04-12 10:23:45</span>
              </div>
            </div>

            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>已分配成员 (1)</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '12px' }}>
                <div style={{ width: 22, height: 22, borderRadius: '50%', backgroundColor: 'var(--color-primary)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '12px' }}>
                  W
                </div>
                <span>王明 (您) · wangming@acme.com</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
