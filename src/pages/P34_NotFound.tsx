import React, { useState } from 'react';
import {
  Search,
  Home,
  Briefcase,
  Compass,
  BookOpen,
  Activity,
  HelpCircle,
  MessageCircle,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P34_NotFound: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      navigate('/search');
    }
  };

  return (
    <div>
      <Header
        title="404 页面未找到"
        subtitle="请求的资源不存在"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
        {/* Left: 404 Main Area */}
        <div className="card" style={{ padding: '48px 36px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ fontSize: '72px', fontWeight: 900, color: 'var(--color-primary)', lineHeight: 1, marginBottom: 12, letterSpacing: -2 }}>
            404
          </div>
          <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            找不到这个页面
          </h2>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginBottom: 28 }}>
            抱歉，您访问的页面不存在或已被移除。可能的原因：
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, width: '100%', maxWidth: 540, marginBottom: 32 }}>
            {[
              { label: '链接已失效' },
              { label: '资源已归档或删除' },
              { label: '地址输入有误' },
              { label: '页面路径已变更' },
            ].map((r, i) => (
              <div key={i} style={{ padding: '12px 8px', borderRadius: 'var(--radius-md)', backgroundColor: '#f8fafc', border: '1px solid var(--border-subtle)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                {r.label}
              </div>
            ))}
          </div>

          {/* Quick Search */}
          <form onSubmit={handleSearch} style={{ width: '100%', maxWidth: 540, display: 'flex', gap: 8, marginBottom: 32 }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="试试全局搜索，帮你快速找到目标内容..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 36, height: 38 }}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ height: 38 }}>
              <span>搜索</span>
            </button>
          </form>

          {/* Quick Access Portals */}
          <div style={{ width: '100%', maxWidth: 540 }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 10, textAlign: 'left' }}>快速前往</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
              {[
                { label: '今日雷达', path: '/today', icon: <Home size={14} /> },
                { label: '机会池', path: '/opportunities', icon: <Briefcase size={14} /> },
                { label: '情报', path: '/intelligence', icon: <Compass size={14} /> },
                { label: '研究', path: '/research', icon: <BookOpen size={14} /> },
                { label: '监控', path: '/monitoring', icon: <Activity size={14} /> },
              ].map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => navigate(p.path)}
                  className="btn btn-secondary btn-sm"
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px 4px', gap: 4, height: 'auto' }}
                >
                  {p.icon}
                  <span style={{ fontSize: '12px' }}>{p.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Recent Visited & Help */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Recently Visited */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              最近访问
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              {[
                { title: '企业级 AI Agent 平台', time: '2 小时前', path: '/opportunities/OPP-20260819-021' },
                { title: 'AI Agent 企业应用商业化研究', time: '昨天', path: '/research/RES-20260819-0011' },
                { title: 'AI Agent 商业化机会监控计划', time: '2 天前', path: '/monitoring/PLAN-2025-001' },
              ].map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => navigate(item.path)}
                  style={{ padding: '6px 8px', borderRadius: 4, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', cursor: 'pointer' }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.title}</div>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: 2 }}>{item.time}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Help Links */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              需要帮助？
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              <div onClick={() => showToast('已打开帮助中心文档', 'info')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--color-primary)', cursor: 'pointer' }}>
                <span>帮助中心文档</span>
                <ExternalLink size={12} />
              </div>
              <div onClick={() => showToast('人工客服已接入', 'info')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--color-primary)', cursor: 'pointer' }}>
                <span>联系在线客服</span>
                <ExternalLink size={12} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
