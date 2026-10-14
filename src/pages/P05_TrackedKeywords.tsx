import React, { useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  TrendingUp,
  Share2,
  Edit2,
  Trash2,
  Check,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Sparkline } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P05_TrackedKeywords: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');
  const [enabledState, setEnabledState] = useState<Record<string, boolean>>({
    'KW-01': true,
    'KW-02': true,
    'KW-03': true,
    'KW-04': true,
    'KW-05': true,
    'KW-06': true,
    'KW-07': true,
    'KW-08': false,
    'KW-09': false,
    'KW-10': true,
  });

  const trackedKeywords = [
    {
      id: 'KW-01',
      name: '生成式人工智能',
      tags: ['技术趋势'],
      time: '2024-06-15 10:23',
      sources: 128,
      totalIntelligence: '2,341',
      activity: 96,
      activityLevel: '极高',
      levelColor: 'var(--color-danger)',
      spark: [30, 35, 45, 40, 60, 75, 90, 96],
    },
    {
      id: 'KW-02',
      name: '固态电池',
      tags: ['新能源'],
      time: '2024-07-02 14:18',
      sources: 86,
      totalIntelligence: '1,789',
      activity: 88,
      activityLevel: '极高',
      levelColor: 'var(--color-danger)',
      spark: [25, 30, 42, 50, 65, 70, 82, 88],
    },
    {
      id: 'KW-03',
      name: '人形机器人',
      tags: ['机器人', '自动化'],
      time: '2024-05-28 09:41',
      sources: 93,
      totalIntelligence: '1,654',
      activity: 82,
      activityLevel: '很高',
      levelColor: 'var(--color-warning)',
      spark: [20, 28, 35, 48, 55, 68, 75, 82],
    },
    {
      id: 'KW-04',
      name: '量子计算',
      tags: ['前沿科技'],
      time: '2024-06-01 16:07',
      sources: 74,
      totalIntelligence: '1,203',
      activity: 71,
      activityLevel: '较高',
      levelColor: 'var(--color-warning)',
      spark: [35, 38, 42, 45, 52, 60, 65, 71],
    },
    {
      id: 'KW-05',
      name: '脑机接口',
      tags: ['医疗健康', '神经科技'],
      time: '2024-07-10 11:55',
      sources: 68,
      totalIntelligence: '987',
      activity: 63,
      activityLevel: '中等',
      levelColor: '#eab308',
      spark: [40, 42, 45, 50, 55, 58, 60, 63],
    },
    {
      id: 'KW-06',
      name: '碳中和',
      tags: ['ESG'],
      time: '2024-05-20 08:32',
      sources: 112,
      totalIntelligence: '2,015',
      activity: 60,
      activityLevel: '中等',
      levelColor: '#eab308',
      spark: [50, 52, 53, 55, 57, 58, 59, 60],
    },
    {
      id: 'KW-07',
      name: '半导体设备',
      tags: ['半导体'],
      time: '2024-06-03 13:20',
      sources: 79,
      totalIntelligence: '1,445',
      activity: 45,
      activityLevel: '较低',
      levelColor: 'var(--color-success)',
      spark: [40, 41, 42, 43, 44, 43, 44, 45],
    },
    {
      id: 'KW-08',
      name: 'Web3.0',
      tags: ['区块链', '互联网'],
      time: '2024-04-25 17:48',
      sources: 65,
      totalIntelligence: '1,102',
      activity: 32,
      activityLevel: '低',
      levelColor: 'var(--text-muted)',
      spark: [45, 42, 40, 38, 36, 35, 34, 32],
    },
    {
      id: 'KW-09',
      name: '元宇宙',
      tags: ['虚拟现实'],
      time: '2024-04-18 15:12',
      sources: 58,
      totalIntelligence: '864',
      activity: 28,
      activityLevel: '低',
      levelColor: 'var(--text-muted)',
      spark: [40, 38, 35, 34, 32, 30, 29, 28],
    },
    {
      id: 'KW-10',
      name: '卫星互联网',
      tags: ['通信技术'],
      time: '2024-06-12 09:30',
      sources: 71,
      totalIntelligence: '1,238',
      activity: 39,
      activityLevel: '较低',
      levelColor: 'var(--color-success)',
      spark: [30, 32, 34, 35, 36, 37, 38, 39],
    },
  ];

  const toggleStatus = (id: string, name: string) => {
    setEnabledState((prev) => {
      const next = !prev[id];
      showToast(`已${next ? '启用' : '暂停'}关键词追踪: ${name}`, 'info');
      return { ...prev, [id]: next };
    });
  };

  return (
    <div>
      <Header
        title="关注关键词"
        subtitle="管理您关注的关键词，追踪重要主题的最新动态"
      />

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Top Action Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => showToast('请输入要添加的新关注关键词', 'info')}
            className="btn btn-primary"
          >
            <Plus size={15} />
            <span>添加关键词</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ position: 'relative', width: 240 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                placeholder="搜索关键词..."
                className="input-base"
                style={{ width: '100%', paddingLeft: 30, height: 34 }}
              />
            </div>
            <button className="btn btn-secondary btn-sm" style={{ height: 34 }}>
              <Filter size={14} />
              <span>筛选</span>
            </button>
          </div>
        </div>

        {/* Table */}
        <table className="data-table">
          <thead>
            <tr>
              <th>关键词</th>
              <th style={{ width: 140 }}>关注时间 ↓</th>
              <th style={{ width: 90, textAlign: 'center' }}>来源数量</th>
              <th style={{ width: 100, textAlign: 'center' }}>情报总量 ↕</th>
              <th style={{ width: 110 }}>活跃度</th>
              <th style={{ width: 120 }}>最近动态</th>
              <th style={{ width: 80, textAlign: 'center' }}>状态</th>
              <th style={{ width: 160, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {trackedKeywords.map((kw) => {
              const isEnabled = enabledState[kw.id] ?? true;
              return (
                <tr key={kw.id}>
                  <td>
                    <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {kw.name}
                    </div>
                    <div style={{ display: 'flex', gap: 4, marginTop: 2 }}>
                      {kw.tags.map((t, idx) => (
                        <span key={idx} style={{ fontSize: '12px', padding: '1px 5px', backgroundColor: '#f1f5f9', borderRadius: 2, color: 'var(--text-secondary)' }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{kw.time}</td>
                  <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>{kw.sources}</td>
                  <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>{kw.totalIntelligence}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>{kw.activity}</span>
                      <span style={{ fontSize: '12px', color: kw.levelColor, backgroundColor: `${kw.levelColor}15`, padding: '1px 5px', borderRadius: 2, fontWeight: 600 }}>
                        {kw.activityLevel}
                      </span>
                    </div>
                  </td>
                  <td>
                    <Sparkline points={kw.spark} color={kw.spark[kw.spark.length - 1] > kw.spark[0] ? '#ef4444' : '#10b981'} width={80} height={20} />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <div
                      onClick={() => toggleStatus(kw.id, kw.name)}
                      style={{
                        width: 36,
                        height: 20,
                        borderRadius: 10,
                        backgroundColor: isEnabled ? 'var(--color-primary)' : '#cbd5e1',
                        padding: 2,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: isEnabled ? 'flex-end' : 'flex-start',
                        transition: 'background-color 0.15s ease',
                      }}
                    >
                      <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#ffffff', boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }} />
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 'var(--font-size-xs)' }}>
                      <button
                        onClick={() => navigate('/trends')}
                        style={{ color: 'var(--color-primary)', fontWeight: 500, cursor: 'pointer' }}
                      >
                        查看趋势
                      </button>
                      <span style={{ color: 'var(--border-default)' }}>|</span>
                      <button
                        onClick={() => navigate('/graph')}
                        style={{ color: 'var(--color-primary)', fontWeight: 500, cursor: 'pointer' }}
                      >
                        查看图谱
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <Pagination total={48} pageSize={10} currentPage={1} />
      </div>
    </div>
  );
};
