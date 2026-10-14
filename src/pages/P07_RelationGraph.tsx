import React, { useState } from 'react';
import {
  Search,
  Camera,
  Plus,
  Briefcase,
  ExternalLink,
  ChevronDown,
  Layers,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { useRouter } from '../router/RouterContext';

export const P07_RelationGraph: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [selectedEntity, setSelectedEntity] = useState('OpenAI');
  const [searchEntity, setSearchEntity] = useState('');
  const [depth, setDepth] = useState('2');
  const [timeRange, setTimeRange] = useState('12m');

  const nodes = [
    { id: 'OpenAI', x: 280, y: 250, r: 36, color: '#2563eb', label: 'OpenAI', type: '公司', isCenter: true },
    { id: 'GPT-4o', x: 280, y: 100, r: 24, color: '#4f46e5', label: 'GPT-4o', type: '产品' },
    { id: 'Microsoft', x: 420, y: 130, r: 28, color: '#ea580c', label: 'Microsoft', type: '公司' },
    { id: 'Google', x: 450, y: 290, r: 26, color: '#059669', label: 'Google', type: '公司' },
    { id: 'Azure', x: 420, y: 400, r: 24, color: '#0284c7', label: 'Azure', type: '技术' },
    { id: 'Copilot', x: 340, y: 310, r: 22, color: '#0891b2', label: 'Copilot', type: '产品' },
    { id: 'NVIDIA', x: 295, y: 420, r: 26, color: '#16a34a', label: 'NVIDIA', type: '公司' },
    { id: 'RAG', x: 235, y: 310, r: 22, color: '#9333ea', label: 'RAG', type: '技术' },
    { id: 'ChatGPT', x: 180, y: 370, r: 26, color: '#0284c7', label: 'ChatGPT', type: '产品' },
    { id: '企业AI', x: 160, y: 240, r: 24, color: '#dc2626', label: '企业AI', type: '概念' },
    { id: 'Anthropic', x: 190, y: 130, r: 26, color: '#7c3aed', label: 'Anthropic', type: '公司' },
  ];

  const edges = [
    { from: 'OpenAI', to: 'GPT-4o' },
    { from: 'OpenAI', to: 'Microsoft' },
    { from: 'OpenAI', to: 'Google' },
    { from: 'OpenAI', to: 'Copilot' },
    { from: 'Copilot', to: 'Azure' },
    { from: 'OpenAI', to: 'NVIDIA' },
    { from: 'OpenAI', to: 'RAG' },
    { from: 'OpenAI', to: 'ChatGPT' },
    { from: 'OpenAI', to: '企业AI' },
    { from: 'OpenAI', to: 'Anthropic' },
  ];

  return (
    <div>
      <Header
        title="关系图谱"
        subtitle="探索实体之间的关联关系，发现潜在连接与机会"
        actions={
          <>
            <button
              onClick={() => showToast('图谱快照已保存至工作区', 'success')}
              className="btn btn-secondary"
            >
              <Camera size={14} />
              <span>保存快照</span>
            </button>
            <button
              onClick={() => navigate('/opportunities/OPP-20260819-021')}
              className="btn btn-primary"
            >
              <Briefcase size={14} />
              <span>从焦点创建机会</span>
            </button>
          </>
        }
      />

      {/* 3-Column Layout: Filter Sidebar + Graph Viewport + Details Pane */}
      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 280px', gap: 16 }}>
        {/* Left: Filter Sidebar */}
        <div className="card" style={{ padding: '16px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            图谱筛选
          </h3>

          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>
              实体类型
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 'var(--font-size-xs)' }}>
              {[
                { label: '公司', count: 128, bg: '#eff6ff', color: '#2563eb' },
                { label: '产品/技术', count: 86, bg: '#ecfdf5', color: '#059669' },
                { label: '关键词', count: 64, bg: '#f5f3ff', color: '#7c3aed' },
                { label: '人物', count: 42, bg: '#fffbeb', color: '#d97706' },
                { label: '机构/组织', count: 38, bg: '#f1f5f9', color: '#475569' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 6px', borderRadius: 4, backgroundColor: item.bg }}>
                  <span style={{ color: item.color, fontWeight: 500 }}>{item.label}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{item.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>
              关系类型
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 'var(--font-size-xs)' }}>
              {[
                { label: '投资', count: 256 },
                { label: '合作', count: 184 },
                { label: '竞争', count: 132 },
                { label: '关联', count: 298 },
                { label: '使用', count: 214 },
              ].map((rel, i) => (
                <label key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <input type="checkbox" defaultChecked />
                    <span style={{ color: 'var(--text-primary)' }}>{rel.label}</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>{rel.count}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500 }}>
              显示设置
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 'var(--font-size-xs)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input type="checkbox" defaultChecked />
                <span>显示标签</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input type="checkbox" defaultChecked />
                <span>高亮弱关系</span>
              </label>
            </div>
          </div>
        </div>

        {/* Center: Graph Viewport */}
        <div className="card" style={{ padding: 0, display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
          {/* Top Canvas Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', zIndex: 10 }}>
            <div style={{ position: 'relative', width: 220 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索实体名称"
                value={searchEntity}
                onChange={(e) => setSearchEntity(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 'var(--font-size-xs)' }}
              />
            </div>

            <select value={depth} onChange={(e) => setDepth(e.target.value)} className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option value="1">关系深度: 1层</option>
              <option value="2">关系深度: 2层</option>
              <option value="3">关系深度: 3层</option>
            </select>

            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option value="12m">时间范围: 12个月</option>
              <option value="6m">时间范围: 6个月</option>
              <option value="24m">时间范围: 24个月</option>
            </select>
          </div>

          {/* SVG Force Canvas */}
          <div style={{ flex: 1, minHeight: 480, width: '100%', backgroundColor: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 560 480" style={{ width: '100%', height: '100%', maxHeight: 520 }}>
              {/* Render edges */}
              {edges.map((edge, idx) => {
                const source = nodes.find((n) => n.id === edge.from)!;
                const target = nodes.find((n) => n.id === edge.to)!;
                return (
                  <line
                    key={idx}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#cbd5e1"
                    strokeWidth="1.5"
                  />
                );
              })}

              {/* Render nodes */}
              {nodes.map((node) => {
                const isSelected = node.id === selectedEntity;
                return (
                  <g
                    key={node.id}
                    onClick={() => {
                      setSelectedEntity(node.id);
                      showToast(`已聚焦实体: ${node.label}`, 'info');
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={node.r}
                      fill={node.color}
                      stroke={isSelected ? '#0f172a' : '#ffffff'}
                      strokeWidth={isSelected ? 3 : 2}
                      style={{ filter: isSelected ? 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))' : undefined }}
                    />
                    <text
                      x={node.x}
                      y={node.y + 4}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize={node.isCenter ? 12 : 10}
                      fontWeight="600"
                    >
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Right: Entity Detail Sidebar */}
        <div className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                {selectedEntity}
              </h2>
              <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 6px', borderRadius: 4 }}>
                  人工智能
                </span>
                <span style={{ fontSize: '12px', color: 'var(--color-purple)', backgroundColor: 'var(--color-purple-light)', padding: '2px 6px', borderRadius: 4 }}>
                  大模型
                </span>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', backgroundColor: 'var(--color-success-light)', padding: '2px 6px', borderRadius: 4 }}>
                  高活跃
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, padding: '12px 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>相关实体</div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                348
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>关联机会</div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                23
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10 }}>
              关键关系
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { name: 'Microsoft', tag: '合作', tagColor: 'var(--color-primary)', bg: 'var(--color-primary-light)' },
                { name: 'NVIDIA', tag: '技术', tagColor: 'var(--color-success)', bg: 'var(--color-success-light)' },
                { name: 'Anthropic', tag: '竞争', tagColor: 'var(--color-warning)', bg: 'var(--color-warning-light)' },
                { name: 'ChatGPT', tag: '产品', tagColor: 'var(--color-purple)', bg: 'var(--color-purple-light)' },
              ].map((rel, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', fontSize: 'var(--font-size-xs)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#2563eb' }} />
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rel.name}</span>
                  </div>
                  <span style={{ color: rel.tagColor, backgroundColor: rel.bg, padding: '1px 6px', borderRadius: 2, fontWeight: 500, fontSize: '12px' }}>
                    {rel.tag}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => navigate('/intelligence/INT-20260819-01842')}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: 'auto' }}
          >
            查看实体详情
          </button>
        </div>
      </div>
    </div>
  );
};
