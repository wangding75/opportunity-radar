import React, { useState } from 'react';
import {
  Bookmark,
  Plus,
  CheckCircle,
  Bell,
  ExternalLink,
  FileDown,
  Share2,
  FileText,
  Languages,
  Activity,
  Check,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { MOCK_INTELLIGENCE } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P03_IntelligenceDetail: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);

  const item = MOCK_INTELLIGENCE[0];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '情报', path: '/intelligence' },
          { label: '情报详情' },
        ]}
        title={item.title}
        actions={
          <>
            <button
              onClick={() => {
                setIsBookmarked(!isBookmarked);
                showToast(isBookmarked ? '已取消收藏' : '已加入收藏', 'info');
              }}
              className="btn btn-secondary"
            >
              <Bookmark size={15} fill={isBookmarked ? 'currentColor' : 'none'} />
              <span>{isBookmarked ? '已收藏' : '收藏'}</span>
            </button>
            <button
              onClick={() => showToast('已加入关注关键词: OpenAI 企业级私有化', 'success')}
              className="btn btn-secondary"
            >
              <Plus size={15} />
              <span>加入关键词</span>
            </button>
            <button
              onClick={() => openState('P03-S01')}
              className="btn btn-secondary"
              style={{ color: 'var(--color-primary)', borderColor: 'var(--color-primary-border)' }}
            >
              <CheckCircle size={15} color="var(--color-primary)" />
              <span>转为机会</span>
            </button>
            <button
              onClick={() => {
                setIsSubscribed(!isSubscribed);
                showToast(isSubscribed ? '已取消追踪订阅' : '已成功订阅此主题动态', 'success');
              }}
              className="btn btn-primary"
            >
              <Bell size={15} />
              <span>{isSubscribed ? '已订阅' : '订阅追踪'}</span>
            </button>
          </>
        }
      />

      {/* Source Meta Header Card */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          marginBottom: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              backgroundColor: '#7c3aed',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '18px',
            }}
          >
            ✦
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {item.source}
              </span>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', fontWeight: 500 }}>
                权威来源
              </span>
              <span style={{ fontSize: '12px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', fontWeight: 500 }}>
                官方
              </span>
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
              发布于 {item.publishedAt} · 作者: {item.author}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-danger)', backgroundColor: 'var(--color-danger-light)', padding: '4px 10px', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
            {item.priority}
          </span>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '4px 10px', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
            {item.reliability}
          </span>
        </div>
      </div>

      {/* Main 2-Column Split: Body (Left) + Sidebar Specs (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
        {/* Left Column: Full Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Summary Box */}
          <div className="card" style={{ borderLeft: '4px solid var(--color-primary)' }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              摘要
            </h3>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {item.summary}
            </p>
          </div>

          {/* Full Text Box */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              正文
            </h3>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-line' }}>
              {item.fullText}
            </div>
          </div>

          {/* Entities Box */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              实体
            </h3>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {item.entities.map((ent, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    backgroundColor: '#fafbfc',
                  }}
                >
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {ent.name}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{ent.type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tags Box */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              标签
            </h3>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {item.tags.map((t, idx) => (
                <span
                  key={idx}
                  style={{
                    fontSize: 'var(--font-size-xs)',
                    padding: '4px 12px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: '#eff6ff',
                    color: 'var(--color-primary)',
                    fontWeight: 500,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Key Insights Box */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
              关键洞察
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                'OpenAI 通过私有化部署与数据隔离策略，进一步打消大型企业在数据安全与合规方面的顾虑。',
                '与主流企业应用的深度集成将显著降低使用门槛，推动生成式 AI 在知识工作场景的广泛落地。',
                '企业级管理与分析能力的增强，有助于 IT 与业务部门更好地治理与衡量 AI 投入的价值回报。',
              ].map((ins, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <div
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-primary)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginTop: 2,
                      flexShrink: 0,
                    }}
                  >
                    <Check size={12} strokeWidth={3} />
                  </div>
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                    {ins}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Sidebar: Meta, Actions, Related Articles */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Card 1: 基本信息 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
              基本信息
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 'var(--font-size-xs)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>情报 ID</span>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>情报类型</span>
                <span style={{ color: 'var(--text-primary)' }}>公司动态</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>所属领域</span>
                <span style={{ color: 'var(--text-primary)' }}>人工智能 &gt; 企业服务</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>发布地区</span>
                <span style={{ color: 'var(--text-primary)' }}>美国</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>语言</span>
                <span style={{ color: 'var(--text-primary)' }}>中文</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>原文链接</span>
                <a
                  href="https://openai.com/blog/enterprise"
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--color-primary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                >
                  <span>openai.com/blog/...</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          </div>

          {/* Card 2: 相关操作 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              相关操作
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: '导出为 PDF', icon: <FileDown size={15} />, action: () => showToast('已生成 PDF 导出任务', 'info') },
                { label: '分享情报', icon: <Share2 size={15} />, action: () => showToast('已复制情报分享链接', 'success') },
                { label: '生成摘要', icon: <FileText size={15} />, action: () => showToast('AI 摘要已重新生成', 'info') },
                { label: '翻译为英文', icon: <Languages size={15} />, action: () => showToast('已翻译为英文视图', 'info') },
                { label: '加入监控', icon: <Activity size={15} />, action: () => navigate('/monitoring') },
              ].map((act, i) => (
                <button
                  key={i}
                  onClick={act.action}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: '#fafbfc',
                    border: '1px solid var(--border-default)',
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    transition: 'all 0.12s ease',
                  }}
                  className="hover-surface"
                >
                  <div style={{ color: 'var(--text-secondary)' }}>{act.icon}</div>
                  <span>{act.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Card 3: 相关内容 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
                相关内容
              </h3>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
                查看全部 (3)
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { title: '微软将 OpenAI 模型引入更多企业场景', time: '2025-05-12', source: 'The Verge', iconColor: '#00a4ef' },
                { title: '生成式 AI 企业部署的安全与合规指南', time: '2025-05-10', source: 'Gartner', iconColor: '#ea4335' },
                { title: 'Salesforce 与 OpenAI 扩大合作范围', time: '2025-05-09', source: 'TechCrunch', iconColor: '#00a1e0' },
              ].map((rel, i) => (
                <div
                  key={i}
                  onClick={() => showToast(`已跳转关联内容: ${rel.title}`, 'info')}
                  style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 4,
                      backgroundColor: '#eff6ff',
                      color: rel.iconColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '12px',
                      marginTop: 2,
                    }}
                  >
                    ●
                  </div>
                  <div>
                    <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                      {rel.title}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>
                      {rel.time} · {rel.source}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 4: 更多链接 */}
          <div className="card">
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
              更多链接
            </h3>
            <a
              href="https://openai.com"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-primary)',
              }}
            >
              <span>OpenAI 官方网站</span>
              <ExternalLink size={13} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
