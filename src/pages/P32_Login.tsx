import React, { useState } from 'react';
import {
  Radar,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  Zap,
  Globe,
  Sparkles,
  ArrowRight,
  Shield,
  Key,
} from 'lucide-react';
import { useRouter } from '../router/RouterContext';
import { useAuth } from '../app/AuthContext';
import './P32_Login.css';

export const P32_Login: React.FC = () => {
  const { navigate, currentState } = useRouter();
  const { signIn, status } = useAuth();
  const [email, setEmail] = useState('wang.ming@company.com');
  const [password, setPassword] = useState('••••••••••••');
  const [mfaCode, setMfaCode] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loginError, setLoginError] = useState<string>();

  const isMfaStep = currentState === 'P32-S01';

  const liveApiEnabled = import.meta.env.VITE_ENABLE_API === 'true';

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isMfaStep || !liveApiEnabled) return;
    setLoginError(undefined);
    try {
      await signIn(email, password);
      navigate('/today');
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : '登录失败，请重试。');
    }
  };

  return (
    <div className="login-page" style={{ minHeight: '100vh', width: '100vw', display: 'grid', gridTemplateColumns: '0.9fr 1.1fr', backgroundColor: '#f8fafc' }}>
      {/* Left Brand Area */}
      <div className="login-page__brand"
        style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#ffffff',
          padding: '64px 80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Background Radar Effect */}
        <div
          style={{
            position: 'absolute',
            bottom: -100,
            right: -100,
            width: 500,
            height: 500,
            borderRadius: '50%',
            border: '1px solid rgba(255,255,255,0.05)',
            boxShadow: '0 0 100px rgba(37,99,235,0.1)',
            pointerEvents: 'none',
          }}
        />

        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, zIndex: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', backgroundColor: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Radar size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 800, letterSpacing: -0.5 }}>机会雷达</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', letterSpacing: 1 }}>OPPORTUNITY RADAR</div>
          </div>
        </div>

        {/* Hero Title & Value Proposition */}
        <div style={{ zIndex: 10, maxWidth: 540 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px', borderRadius: 'var(--radius-full)', backgroundColor: 'rgba(37,99,235,0.2)', border: '1px solid rgba(37,99,235,0.4)', fontSize: '12px', color: '#60a5fa', marginBottom: 20 }}>
            <Sparkles size={13} />
            <span>智能情报 · 机会发现 · 研究闭环</span>
          </div>

          <h1 style={{ fontSize: '36px', fontWeight: 800, lineHeight: 1.2, marginBottom: 20 }}>
            从海量信号中<br />
            发现真正值得研究的<span style={{ color: '#38bdf8' }}>机会</span>
          </h1>

          <p style={{ fontSize: 'var(--font-size-sm)', color: '#94a3b8', lineHeight: 1.7, marginBottom: 36 }}>
            机会雷达帮助您持续捕获全球情报，智能识别机会信号，构建证据与关系图谱，让研究与决策更高效、更有洞察力。
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {[
              { title: '持续捕获全球情报', desc: '连接 100+ 高质量来源，7×24 实时捕获全球动态' },
              { title: '智能识别机会信号', desc: 'AI 模型深度分析，自动识别高潜力机会与趋势' },
              { title: '构建证据与关系图谱', desc: '多维证据关联，构建完整的机会图谱与影响分析' },
              { title: '从发现到研究闭环', desc: '一站式完成监控、分析、研究与结论，驱动决策落地' },
            ].map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ width: 24, height: 24, borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8', fontSize: '12px', fontWeight: 700, flexShrink: 0, marginTop: 2 }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: '#f8fafc' }}>{f.title}</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ fontSize: '12px', color: '#64748b', zIndex: 10 }}>
          © 2026 Opportunity Radar 机会雷达. 保留所有权利.
        </div>
      </div>

      {/* Right Login Form Container */}
      <div className="login-page__form-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '40px' }}>
        <div className="card login-page__form" style={{ width: '100%', maxWidth: 440, padding: '36px 40px', boxShadow: 'var(--shadow-lg)' }}>
          {!isMfaStep ? (
            /* Step 1: Username / Password Form */
            <div>
              <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                登录机会雷达
              </h2>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 24 }}>
                欢迎回来！请输入您的账号以继续
              </p>

              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                    邮箱地址
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Mail size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="请输入邮箱地址"
                      className="input-base"
                      style={{ width: '100%', paddingLeft: 36, height: 40 }}
                      required
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      密码
                    </label>
                    <span title="密码重置待后端接入后开放" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>忘记密码（待接入）</span>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="请输入密码"
                      className="input-base"
                      style={{ width: '100%', paddingLeft: 36, height: 40 }}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    id="remember"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <label htmlFor="remember" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    记住我
                  </label>
                </div>

                {loginError && <p className="login-page__error" role="alert">{loginError}</p>}
                <button disabled={!liveApiEnabled || status === 'loading'} type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 4 }}>
                  <span>{liveApiEnabled ? '登录' : '密码登录（待接入）'}</span>
                  <ArrowRight size={16} />
                </button>
              </form>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '24px 0' }}>
                <div style={{ flex: 1, height: 1, backgroundColor: 'var(--border-subtle)' }} />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>或使用以下方式登录</span>
                <div style={{ flex: 1, height: 1, backgroundColor: 'var(--border-subtle)' }} />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <button
                  type="button"
                  disabled
                  title="企业 SSO 待后端接入后开放"
                  className="btn btn-secondary"
                  style={{ width: '100%', height: 38 }}
                >
                  <Shield size={14} />
                  <span>使用企业 SSO 登录（待接入）</span>
                </button>
              </div>
            </div>
          ) : (
            /* Step 2 (P32-S01): MFA Verification */
            <div>
              <div style={{ width: 48, height: 48, borderRadius: '50%', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <Key size={24} />
              </div>
              <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                两步身份验证 (MFA)
              </h2>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 24 }}>
                请输入您的认证应用 (Authenticator) 中显示的 6 位验证码。
              </p>

              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <input
                    type="text"
                    maxLength={6}
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value)}
                    placeholder="123456"
                    className="input-base"
                    style={{ width: '100%', height: 44, fontSize: '20px', letterSpacing: 8, textAlign: 'center', fontWeight: 700 }}
                    autoFocus
                  />
                </div>

                <button disabled type="submit" className="btn btn-primary btn-lg" style={{ width: '100%' }}>
                  <span>验证并登录（待接入）</span>
                </button>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginTop: 10 }}>
                  <span style={{ color: 'var(--text-muted)' }}>&lt; 返回账号登录</span>
                  <span style={{ color: 'var(--text-muted)' }}>MFA 恢复（待接入）</span>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
