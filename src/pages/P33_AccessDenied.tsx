import React from 'react';
import {
  ShieldAlert,
  ArrowLeft,
  Key,
  Lock,
  FileQuestion,
  HelpCircle,
  Briefcase,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P33_AccessDenied: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '机会', path: '/opportunities' },
          { label: '企业级 AI Agent 平台', path: '/opportunities/OPP-20260819-021' },
          { label: '机会详情' },
        ]}
        title="访问受限"
        subtitle="权限校验未通过"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
        {/* Left: Access Denied Main Card */}
        <div className="card" style={{ padding: '48px 36px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
            <Lock size={36} />
          </div>

          <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            你没有权限访问此内容
          </h2>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', maxWidth: 480, lineHeight: 1.6, marginBottom: 28 }}>
            抱歉，您当前的角色没有访问此机会详情的权限。如需访问，请联系工作区管理员申请相应权限。
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, width: '100%', maxWidth: 480, padding: '16px 20px', borderRadius: 'var(--radius-md)', backgroundColor: '#f8fafc', border: '1px solid var(--border-subtle)', marginBottom: 32, textAlign: 'left' }}>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>当前角色</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                Analyst (分析师)
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>所需权限</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-primary)', marginTop: 2 }}>
                查看机会详情 (至少 Analyst)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => openState('P33-S01')}
              className="btn btn-primary btn-lg"
            >
              <Key size={16} />
              <span>申请访问权限</span>
            </button>
            <button
              onClick={() => window.history.back()}
              className="btn btn-secondary btn-lg"
            >
              <ArrowLeft size={16} />
              <span>返回上一页</span>
            </button>
            <button
              onClick={() => navigate('/opportunities')}
              className="btn btn-secondary btn-lg"
            >
              <Briefcase size={16} />
              <span>返回机会列表</span>
            </button>
          </div>
        </div>

        {/* Right: Resource Metadata & Restrictions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Resource Info */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              资源信息
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '12px' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 'var(--font-size-xs)' }}>企业级 AI Agent 平台</div>
              <div><span style={{ color: 'var(--text-muted)' }}>状态:</span> 研判中 · 评分 86</div>
              <div><span style={{ color: 'var(--text-muted)' }}>所在工作区:</span> 全球科技机会研究</div>
              <div><span style={{ color: 'var(--text-muted)' }}>创建时间:</span> 2026-08-14 09:32</div>
              <div><span style={{ color: 'var(--text-muted)' }}>创建人:</span> 李想</div>
              <div><span style={{ color: 'var(--text-muted)' }}>可见范围:</span> <span style={{ color: '#ef4444', fontWeight: 600 }}>特定角色可见</span></div>
            </div>
          </div>

          {/* Permissions Explanation */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              权限说明
            </h3>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              此资源仅对特定角色可见，包含以下限制：<br />
              • 无法查看机会详情内容<br />
              • 无法查看关联情报与研究<br />
              • 无法查看分析与结论<br />
              • 无法执行任何操作
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
