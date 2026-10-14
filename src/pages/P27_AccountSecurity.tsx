import React, { useState } from 'react';
import {
  Shield,
  Key,
  Smartphone,
  Laptop,
  CheckCircle,
  AlertTriangle,
  Lock,
  ChevronRight,
  LogOut,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P27_AccountSecurity: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '账户安全' },
        ]}
        title="账户安全"
        subtitle="管理个人账户的安全设置，保护您的身份与数据安全。"
      />

      {/* Top 4 KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 20 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>安全评分</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>82</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/100 · 良好</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上次提升 12 分 ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>MFA 状态</div>
          <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--color-danger)' }}>未开启</div>
          <button
            onClick={() => openState('P27-S01')}
            className="btn btn-primary btn-sm"
            style={{ marginTop: 6, fontSize: '12px', padding: '2px 8px' }}
          >
            开启双重验证
          </button>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>活跃会话</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>3</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>个设备</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>当前登录设备数</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>近 30 天异常登录</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-danger)' }}>1</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>次</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-danger)', marginTop: 2 }}>高风险登录已发现</div>
        </div>
      </div>

      {/* Main 2-Column Split: Security Panels + Activity Log */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 20 }}>
        {/* Left: 4 Security Config Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Card 1: 密码与登录方式 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              密码与登录方式
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>登录密码</span>
                <button onClick={() => showToast('请输入旧密码以修改密码', 'info')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>修改密码</button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>登录邮箱: wang.ming@company.com</span>
                <button onClick={() => showToast('更换邮箱流程已启动', 'info')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>更换邮箱</button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>手机号码: +86 138 **** 5678</span>
                <button onClick={() => showToast('更换手机流程已启动', 'info')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>更换手机</button>
              </div>
            </div>
          </div>

          {/* Card 2: 双重验证 (MFA) */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              双重验证 (MFA)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>状态: 未开启</span>
                <button onClick={() => openState('P27-S01')} className="btn btn-primary btn-sm" style={{ padding: '2px 8px' }}>开启双重验证</button>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.5 }}>
                使用 Google Authenticator 或其他 TOTP 验证器在登录时进行二次身份校验。
              </p>
            </div>
          </div>

          {/* Card 3: Passkey 与恢复代码 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              Passkey 与恢复代码
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Passkey: 未创建</span>
                <button onClick={() => showToast('创建 Passkey 提示已打开', 'info')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>创建 Passkey</button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>恢复代码: 未生成</span>
                <button onClick={() => showToast('已生成一组新的恢复备份代码', 'success')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>生成恢复代码</button>
              </div>
            </div>
          </div>

          {/* Card 4: API Token (访问令牌) */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              API Token (访问令牌)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>有效 Token: 2 个</span>
                <button onClick={() => showToast('已生成新 API 令牌: or_live_9a8f...', 'success')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px' }}>新建 Token</button>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>最后使用: 2024-04-12 16:32</div>
            </div>
          </div>
        </div>

        {/* Right: 最近登录活动 */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              最近登录活动
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
            {[
              { dev: 'macOS · Chrome 123', ip: '120.28.45.67 (中国 · 上海)', time: '2024-04-12 10:23', status: '当前会话', safe: true },
              { dev: 'iPhone 15 Pro · iOS 17.4', ip: '106.38.12.90 (中国 · 北京)', time: '2024-04-11 21:15', status: '成功登录', safe: true },
              { dev: 'Windows 10 · Chrome 122', ip: '165.220.101.45 (俄罗斯 · 莫斯科)', time: '2024-04-09 03:12', status: '异常登录已阻止', safe: false },
            ].map((act, i) => (
              <div key={i} style={{ padding: '6px 8px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ fontWeight: 600 }}>{act.dev}</span>
                  <span style={{ fontSize: '9px', color: act.safe ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 600 }}>{act.status}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{act.ip}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{act.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dangerous Actions Drawer Launcher */}
      <div className="card" style={{ border: '1px solid #fecaca', backgroundColor: '#fff5f5' }}>
        <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-danger)', marginBottom: 6 }}>
          危险操作
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: 12 }}>
          以下操作可能导致账户访问中断或数据不可用，请谨慎操作。
        </p>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => openState('P27-S02')} className="btn btn-secondary btn-sm">注销其他设备</button>
          <button onClick={() => openState('P27-S02')} className="btn btn-secondary btn-sm">重置双重验证</button>
          <button onClick={() => openState('P27-S02')} className="btn btn-primary btn-sm" style={{ backgroundColor: 'var(--color-danger)' }}>删除账户</button>
        </div>
      </div>
    </div>
  );
};
