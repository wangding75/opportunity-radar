import React, { useState } from 'react';
import {
  Compass,
  FileText,
  Briefcase,
  BookOpen,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
  Globe,
  Bell,
  ChevronDown,
  User,
  LogOut,
  Shield,
  Layers,
  Menu,
  X,
} from 'lucide-react';
import { useRouter } from '../../router/RouterContext';
import { ToastContainer } from '../common/Toast';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentRoute, currentPath, navigate, showToast } = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [domainMenuOpen, setDomainMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState('全部领域');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const navItems = [
    {
      id: '今日雷达',
      label: '今日雷达',
      path: '/today',
      icon: <Compass size={18} />,
    },
    {
      id: '情报',
      label: '情报',
      path: '/intelligence',
      icon: <FileText size={18} />,
    },
    {
      id: '机会',
      label: '机会',
      path: '/opportunities',
      icon: <Briefcase size={18} />,
    },
    {
      id: '研究',
      label: '研究',
      path: '/research',
      icon: <BookOpen size={18} />,
    },
    {
      id: '监控',
      label: '监控',
      path: '/monitoring',
      icon: <Activity size={18} />,
    },
    {
      id: '设置',
      label: '设置',
      path: '/settings/workspace',
      icon: <Settings size={18} />,
    },
  ];

  const domains = ['全部领域', '人工智能 & 大模型', '新能源 & 储能', '生物医药 & 基因', '工业互联 & 机器人', '云计算 & 算力'];

  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', width: '100%', backgroundColor: 'var(--surface-page)' }}>
      {/* Toast Notification Container */}
      <ToastContainer />

      {/* ---------------- Sidebar ---------------- */}
      {mobileNavOpen && <button className="app-sidebar-scrim" aria-label="关闭导航" onClick={() => setMobileNavOpen(false)} />}
      <aside
        className={`app-sidebar ${collapsed ? 'app-sidebar--collapsed' : ''} ${mobileNavOpen ? 'app-sidebar--mobile-open' : ''}`}
        style={{
          width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
          backgroundColor: 'var(--surface-sidebar)',
          borderRight: '1px solid var(--border-default)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          position: 'sticky',
          top: 0,
          height: '100vh',
            zIndex: 'var(--z-sidebar)',
          transition: 'width 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Brand Logo */}
        <div
          onClick={() => navigate('/today')}
          style={{
            height: 'var(--topbar-height)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: collapsed ? '0 18px' : '0 20px',
            borderBottom: '1px solid var(--border-subtle)',
            cursor: 'pointer',
          }}
        >
          {/* Blue Spiral Logo */}
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              flexShrink: 0,
              boxShadow: '0 2px 6px rgba(37, 99, 235, 0.3)',
            }}
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
              <path d="M2 12h20" />
            </svg>
          </div>
          {!collapsed && (
            <span style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.2px' }}>
              机会雷达
            </span>
          )}
        </div>

        {/* Primary Navigation List */}
        <nav style={{ flex: 1, padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {navItems.map((item) => {
            const isActive = currentRoute.primaryNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => { navigate(item.path); setMobileNavOpen(false); }}
                title={collapsed ? item.label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  width: '100%',
                  padding: collapsed ? '10px 0' : '10px 14px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--color-primary-light)' : 'transparent',
                  color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: 'var(--font-size-sm)',
                  transition: 'all 0.15s ease',
                  cursor: 'pointer',
                }}
              >
                <div style={{ color: isActive ? 'var(--color-primary)' : 'var(--text-muted)' }}>
                  {item.icon}
                </div>
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Collapse Toggle Footer */}
        <div
          style={{
            padding: '12px 14px',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="btn btn-ghost btn-sm"
            style={{
              width: '100%',
              justifyContent: collapsed ? 'center' : 'flex-start',
              color: 'var(--text-muted)',
              fontSize: 'var(--font-size-xs)',
            }}
          >
            {collapsed ? <ChevronRight size={15} /> : <><ChevronLeft size={15} /><span>收起</span></>}
          </button>
        </div>
      </aside>

      {/* ---------------- Main Content Area ---------------- */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* ---------------- Topbar ---------------- */}
        <header className="app-topbar"
          style={{
            height: 'var(--topbar-height)',
            backgroundColor: 'var(--surface-topbar)',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            position: 'sticky',
            top: 0,
            zIndex: 'var(--z-topbar)',
          }}
        >
          <button type="button" className="app-topbar__menu" aria-label={mobileNavOpen ? '关闭导航' : '打开导航'} onClick={() => setMobileNavOpen(!mobileNavOpen)}>
            {mobileNavOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          {/* Left: Global Search Box */}
          <div className="app-topbar__search" style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1, maxWidth: 460 }}>
            <div
              onClick={() => navigate('/search')}
              style={{
                position: 'relative',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
              }}
            >
              <Search
                size={15}
                style={{
                  position: 'absolute',
                  left: 12,
                  color: 'var(--text-muted)',
                }}
              />
              <input
                type="text"
                placeholder="搜索机会、情报、关键词、来源等..."
                readOnly
                className="input-base"
                style={{
                  width: '100%',
                  paddingLeft: 36,
                  paddingRight: 40,
                  cursor: 'pointer',
                  backgroundColor: '#f8fafc',
                  border: '1px solid var(--border-default)',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  right: 10,
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '1px 5px',
                  backgroundColor: '#ffffff',
                  fontWeight: 600,
                }}
              >
                ⌘K
              </span>
            </div>
          </div>

          {/* Right: Domain Selector, Notification Bell, User Profile */}
          <div className="app-topbar__actions" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Domain Selector */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setDomainMenuOpen(!domainMenuOpen)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: '#ffffff',
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                }}
              >
                <Globe size={15} color="var(--color-primary)" />
                <span>{selectedDomain}</span>
                <ChevronDown size={14} color="var(--text-muted)" />
              </button>

              {domainMenuOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: 6,
                    width: 200,
                    backgroundColor: '#ffffff',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-lg)',
                    border: '1px solid var(--border-default)',
                    padding: '4px 0',
                    zIndex: 1000,
                  }}
                >
                  {domains.map((dom) => (
                    <button
                      key={dom}
                      onClick={() => {
                        setSelectedDomain(dom);
                        setDomainMenuOpen(false);
                        showToast(`已切换业务领域: ${dom}`, 'info');
                      }}
                      style={{
                        display: 'block',
                        width: '100%',
                        textAlign: 'left',
                        padding: '8px 16px',
                        fontSize: 'var(--font-size-sm)',
                        color: selectedDomain === dom ? 'var(--color-primary)' : 'var(--text-primary)',
                        backgroundColor: selectedDomain === dom ? 'var(--color-primary-light)' : 'transparent',
                        fontWeight: selectedDomain === dom ? 600 : 400,
                        cursor: 'pointer',
                      }}
                    >
                      {dom}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Notification Bell */}
            <button
              onClick={() => navigate('/alerts')}
              style={{
                position: 'relative',
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-secondary)',
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-default)',
                cursor: 'pointer',
              }}
              title="告警与通知"
            >
              <Bell size={17} />
              <span
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  minWidth: 16,
                  height: 16,
                  padding: '0 4px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--color-danger)',
                  color: '#ffffff',
                  fontSize: '12px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid #ffffff',
                }}
              >
                12
              </span>
            </button>

            {/* User Profile Menu */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '4px 10px 4px 4px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: '#ffffff',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    backgroundColor: 'var(--color-primary-light)',
                    color: 'var(--color-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 'var(--font-size-xs)',
                  }}
                >
                  张
                </div>
                <div style={{ textAlign: 'left', display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                    张天宇
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>高级分析师</span>
                </div>
                <ChevronDown size={13} color="var(--text-muted)" />
              </button>

              {userMenuOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: 6,
                    width: 180,
                    backgroundColor: '#ffffff',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-lg)',
                    border: '1px solid var(--border-default)',
                    padding: '6px 0',
                    zIndex: 1000,
                  }}
                >
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      navigate('/settings/workspace');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      width: '100%',
                      padding: '8px 16px',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                    }}
                  >
                    <Settings size={15} color="var(--text-secondary)" />
                    <span>工作区设置</span>
                  </button>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      navigate('/settings/security');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      width: '100%',
                      padding: '8px 16px',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                    }}
                  >
                    <Shield size={15} color="var(--text-secondary)" />
                    <span>账户安全</span>
                  </button>

                  <div style={{ height: 1, backgroundColor: 'var(--border-subtle)', margin: '4px 0' }} />

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      navigate('/login');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      width: '100%',
                      padding: '8px 16px',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-danger)',
                      cursor: 'pointer',
                    }}
                  >
                    <LogOut size={15} color="var(--color-danger)" />
                    <span>退出登录</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* ---------------- Page Content Container ---------------- */}
        <main
          className="app-content"
          style={{
            flex: 1,
            padding: 'var(--page-gutter)',
            width: '100%',
            maxWidth: 'var(--content-max-width)',
            margin: '0 auto',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};
