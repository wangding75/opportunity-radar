import React, { useState } from 'react';
import {
  Save,
  Globe,
  Database,
  Trash2,
  Download,
  RotateCcw,
  Plus,
  Shield,
  Bell,
  AlertTriangle,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';
import './P24_WorkspaceSettings.css';

export const P24_WorkspaceSettings: React.FC = () => {
  const { navigate } = useRouter();
  const [activeSection, setActiveSection] = useState('basic');

  return (
    <div className="workspace-settings">
      <Header
        breadcrumbs={[
          { label: '设置', path: '/settings' },
          { label: '工作区设置' },
        ]}
        title="工作区设置"
        subtitle="管理和自定义当前工作区的默认行为与偏好设置。"
      />

      <div className="workspace-settings__layout" style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 20 }}>
        {/* Left Subnav */}
        <div className="card workspace-settings__nav" style={{ padding: '8px 0', height: 'fit-content' }}>
          {[
            { key: 'basic', label: '基本信息' },
            { key: 'scope', label: '研究范围' },
            { key: 'discovery', label: '机会发现' },
            { key: 'research', label: '研究设置' },
            { key: 'storage', label: '数据与保存' },
            { key: 'notifications', label: '通知默认值' },
            { key: 'danger', label: '危险操作', danger: true },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setActiveSection(item.key)}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                padding: '8px 16px',
                fontSize: 'var(--font-size-xs)',
                fontWeight: activeSection === item.key ? 600 : 400,
                color: activeSection === item.key ? (item.danger ? 'var(--color-danger)' : 'var(--color-primary)') : (item.danger ? 'var(--color-danger)' : 'var(--text-secondary)'),
                backgroundColor: activeSection === item.key ? (item.danger ? 'var(--color-danger-light)' : 'var(--color-primary-light)') : 'transparent',
                borderLeft: activeSection === item.key ? `3px solid ${item.danger ? 'var(--color-danger)' : 'var(--color-primary)'}` : '3px solid transparent',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Right Content */}
        <div className="workspace-settings__content" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Row 1: 基本信息 + 默认研究范围 */}
          <div className="workspace-settings__row workspace-settings__row--hero" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
            {/* 工作区基本信息 */}
            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
                工作区基本信息
              </h3>
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 16 }}>
                <div style={{ width: 64, height: 64, borderRadius: 12, backgroundColor: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontWeight: 800, fontSize: '20px' }}>
                  OR
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>工作区名称</div>
                  <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--text-primary)' }}>全球科技机会研究</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.4 }}>
                    聚焦全球科技领域机会发现与深入研究，涵盖 AI、大模型、机器人、半导体等方向。
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button disabled title="工作区设置待后端接入后开放" className="btn btn-primary btn-sm">编辑信息（待接入）</button>
                <button disabled title="工作区设置待后端接入后开放" className="btn btn-secondary btn-sm">更换 Logo（待接入）</button>
              </div>
            </div>

            {/* 默认研究范围 */}
            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                默认研究范围
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>默认领域</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {['AI', '大模型', '机器人', '半导体'].map((t, idx) => (
                      <span key={idx} style={{ padding: '2px 8px', borderRadius: 4, backgroundColor: '#f1f5f9' }}>{t}</span>
                    ))}
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0 6px', height: 22 }}>+</button>
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>默认地区</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {['全球', '中国', '美国', '欧洲'].map((t, idx) => (
                      <span key={idx} style={{ padding: '2px 8px', borderRadius: 4, backgroundColor: '#f1f5f9' }}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Row 2: 机会发现默认策略 + 研究默认设置 */}
          <div className="workspace-settings__row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                机会发现默认策略
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>最低机会评分</span>
                  <input disabled type="number" defaultValue={60} className="input-base" style={{ width: 70, height: 26, fontSize: '12px' }} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>最低置信度</span>
                  <input disabled type="text" defaultValue="65%" className="input-base" style={{ width: 70, height: 26, fontSize: '12px' }} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>相似机会自动合并</span>
                  <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>开启</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                研究默认设置
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>默认模板</span>
                  <select disabled className="input-base" style={{ height: 26, fontSize: '12px' }}>
                    <option>市场机会研究</option>
                  </select>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>自动结构化分析</span>
                  <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>开启</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>自动生成结论</span>
                  <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>开启</span>
                </div>
              </div>
            </div>
          </div>

          {/* Row 3: 数据与保存策略 + 默认通知行为 */}
          <div className="workspace-settings__row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
                数据与保存策略
              </h3>
              <div style={{ fontSize: '12px', marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>存储空间使用</span>
                <span style={{ fontWeight: 700 }}>38.6 GB / 100 GB</span>
              </div>
              <div style={{ width: '100%', height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden', marginBottom: 12 }}>
                <div style={{ width: '38.6%', height: '100%', backgroundColor: 'var(--color-primary)' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '12px', color: 'var(--text-secondary)' }}>
                <div>• 情报与附件: 24.1 GB (永久保存)</div>
                <div>• 运行记录: 10.2 GB (180 天)</div>
                <div>• 原始网页快照: 4.3 GB (90 天)</div>
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
                默认通知行为
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>高严重告警 (站内 + Email)</span>
                  <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>开启</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>机会评分突破阈值</span>
                  <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>开启</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>每日摘要 (Email)</span>
                  <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>开启</span>
                </div>
              </div>
            </div>
          </div>

          {/* Dangerous Actions Row */}
          <div className="card workspace-settings__danger" style={{ border: '1px solid #fecaca', backgroundColor: '#fff5f5' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-danger)', marginBottom: 6 }}>
              危险操作
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: 12 }}>
              以下操作可能导致数据丢失或不可逆的影响，请谨慎操作。
            </p>
            <div className="workspace-settings__danger-actions" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
              <button disabled className="btn btn-secondary btn-sm">导出工作区数据（待接入）</button>
              <button disabled className="btn btn-secondary btn-sm">清理历史运行数据（待接入）</button>
              <button disabled className="btn btn-secondary btn-sm">重置默认配置（待接入）</button>
              <button disabled className="btn btn-primary btn-sm" style={{ backgroundColor: 'var(--color-danger)' }}>删除工作区（待接入）</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
