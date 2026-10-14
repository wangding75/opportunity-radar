import React, { useState } from 'react';
import {
  Edit,
  Download,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { useRouter } from '../router/RouterContext';

export const P10_StructuredAnalysis: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '机会', path: '/opportunities' },
          { label: '企业级AI知识管理平台', path: '/opportunities/OPP-20260819-021' },
          { label: '结构化分析' },
        ]}
        title="结构化分析"
        subtitle="企业级AI知识管理平台 · 从多维度解释机会成立的核心要素"
        actions={
          <>
            <button
              onClick={() => showToast('已进入编辑模式', 'info')}
              className="btn btn-secondary"
            >
              <Edit size={14} />
              <span>编辑分析</span>
            </button>
            <button
              onClick={() => showToast('分析报告已导出为 PDF', 'success')}
              className="btn btn-primary"
            >
              <Download size={14} />
              <span>导出分析</span>
            </button>
          </>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'overview', label: '分析总览' },
          { key: 'market', label: '市场分析' },
          { key: 'competition', label: '竞争格局' },
          { key: 'demand', label: '需求分析' },
          { key: 'feasibility', label: '可行性评估' },
        ]}
      />

      {/* Row 1: 综合评分 + 核心结论 */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 16, marginBottom: 16 }}>
        {/* Card 1: 综合评分 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 6 }}>
            综合评分
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
            <span style={{ fontSize: '40px', fontWeight: 800, color: 'var(--color-success)', lineHeight: 1 }}>
              85
            </span>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>/ 100</span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
              高机会
            </span>
          </div>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
            基于市场、需求、竞争、可行性和风险综合评估
          </p>
        </div>

        {/* Card 2: 核心结论 */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
            核心结论
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>•</span>
              <span>市场需求明确且继续增长</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>•</span>
              <span>技术成熟度提升，部署门槛下降</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>•</span>
              <span>竞争格局尚未固化，存在切入窗口</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>•</span>
              <span>商业模式清晰，企业付费意愿较强</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Row 2: 4 Dimension Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 6 }}>市场吸引力</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-success)' }}>高</span>
            <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
              <div style={{ width: '85%', height: '100%', backgroundColor: 'var(--color-success)' }} />
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 6 }}>需求强度</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-success)' }}>高</span>
            <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
              <div style={{ width: '80%', height: '100%', backgroundColor: 'var(--color-success)' }} />
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 6 }}>竞争压力</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-warning)' }}>中</span>
            <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
              <div style={{ width: '60%', height: '100%', backgroundColor: 'var(--color-warning)' }} />
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 6 }}>风险等级</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-warning)' }}>中</span>
            <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
              <div style={{ width: '55%', height: '100%', backgroundColor: 'var(--color-warning)' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: 市场规模 + 商业模式 + 主要风险 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {/* Card 1: 市场规模 & 增长柱状图 */}
        <div className="card">
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>市场规模</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
              320 亿
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', fontWeight: 600 }}>
              年复合增长率 28%
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: 120, paddingTop: 20 }}>
            {[
              { year: '2024', height: 35 },
              { year: '2025', height: 50 },
              { year: '2026', height: 75 },
              { year: '2027', height: 95 },
              { year: '2028', height: 120 },
            ].map((bar, i) => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1 }}>
                <div style={{ width: 28, height: bar.height, backgroundColor: '#93c5fd', borderRadius: '4px 4px 0 0' }} />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{bar.year}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 2: 商业模式 */}
        <div className="card">
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            商业模式
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
            {[
              { num: 1, text: '订阅制 SaaS' },
              { num: 2, text: '私有化部署' },
              { num: 3, text: '增值实施服务' },
            ].map((item) => (
              <div key={item.num} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 20, height: 20, borderRadius: '50%', backgroundColor: '#eff6ff', color: 'var(--color-primary)', fontSize: '12px', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {item.num}
                </div>
                <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)' }}>{item.text}</span>
              </div>
            ))}
          </div>

          <div style={{ paddingTop: 12, borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 6 }}>目标客户</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              • 中大型企业<br />
              • 知识密集型组织<br />
              • 专业服务机构
            </div>
          </div>
        </div>

        {/* Card 3: 主要风险 */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            主要风险
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginBottom: 20 }}>
            <li>• 数据安全与合规</li>
            <li>• 大模型供应商依赖</li>
            <li>• 客户采购周期较长</li>
          </ul>

          <div style={{ marginTop: 'auto', paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>风险等级</div>
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-warning)' }}>
              中等
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
