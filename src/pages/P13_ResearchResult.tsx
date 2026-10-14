import React, { useState } from 'react';
import {
  Download,
  Filter,
  Search,
  Star,
  MoreHorizontal,
  ChevronRight,
  Send,
  Sparkles,
  TrendingUp,
  FileCheck,
  CheckCircle,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart, Sparkline } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P13_ResearchResult: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const typeSegments = [
    { label: '趋势洞察', count: 32, percentage: '25.0%', color: '#2563eb' },
    { label: '机会评估', count: 28, percentage: '21.9%', color: '#8b5cf6' },
    { label: '可行性分析', count: 24, percentage: '18.8%', color: '#06b6d4' },
    { label: '策略建议', count: 20, percentage: '15.6%', color: '#f59e0b' },
    { label: '模式创新', count: 12, percentage: '9.4%', color: '#10b981' },
    { label: '预测分析', count: 8, percentage: '6.3%', color: '#3b82f6' },
    { label: '其他', count: 4, percentage: '3.1%', color: '#94a3b8' },
  ];

  const resultsList = [
    {
      id: 'RES-01',
      title: 'AI Agent在企业知识管理领域的应用趋势',
      type: '趋势洞察',
      priority: '高',
      score: 92,
      sources: 36,
      status: '已发布',
      author: '张分析师',
      date: '2025-05-12',
    },
    {
      id: 'RES-02',
      title: '生成式AI驱动的设计工具市场机会分析',
      type: '机会评估',
      priority: '高',
      score: 88,
      sources: 28,
      status: '已发布',
      author: '李研究员',
      date: '2025-05-12',
    },
    {
      id: 'RES-03',
      title: '边缘计算在工业物联网的落地可行性',
      type: '可行性分析',
      priority: '中',
      score: 76,
      sources: 24,
      status: '已发布',
      author: '王分析师',
      date: '2025-05-11',
    },
    {
      id: 'RES-04',
      title: '数字孪生技术的商业模式创新方向',
      type: '模式创新',
      priority: '中',
      score: 74,
      sources: 18,
      status: '评审中',
      author: '陈研究员',
      date: '2025-05-11',
    },
    {
      id: 'RES-05',
      title: '低代码平台的行业渗透率预测报告',
      type: '预测分析',
      priority: '中',
      score: 71,
      sources: 20,
      status: '已发布',
      author: '赵分析师',
      date: '2025-05-10',
    },
    {
      id: 'RES-06',
      title: '隐私计算在金融风控的应用前景',
      type: '趋势洞察',
      priority: '高',
      score: 91,
      sources: 32,
      status: '已发布',
      author: '张分析师',
      date: '2025-05-10',
    },
    {
      id: 'RES-07',
      title: 'AR远程协作工具的市场进入策略',
      type: '策略建议',
      priority: '低',
      score: 65,
      sources: 16,
      status: '草稿',
      author: '刘研究员',
      date: '2025-05-09',
    },
    {
      id: 'RES-08',
      title: '量子计算在药物研发的潜在价值',
      type: '机会评估',
      priority: '高',
      score: 87,
      sources: 22,
      status: '评审中',
      author: '周分析师',
      date: '2025-05-09',
    },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '研究', path: '/research' },
          { label: '研究结论' },
        ]}
        title="研究结论"
        subtitle="汇总研究产出，沉淀关键结论与洞察，驱动机会判断与行动。"
        actions={
          <button
            onClick={() => openState('P13-S01')}
            className="btn btn-primary"
          >
            <Send size={14} />
            <span>发布研究结论</span>
          </button>
        }
      />

      {/* Top 5 KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        {[
          { label: '结论总数', val: '128', sub: '较上月 +18 (16.4%)', spark: [20, 30, 45, 50, 65, 80, 100, 128], color: '#2563eb' },
          { label: '可行动结论', val: '62', sub: '占比 48.4%', spark: [10, 18, 25, 32, 45, 50, 58, 62], color: '#10b981' },
          { label: '高价值结论', val: '45', sub: '占比 35.2%', spark: [8, 14, 20, 26, 32, 38, 42, 45], color: '#f59e0b' },
          { label: '平均质量评分', val: '82', sub: '较上月 +6 分', spark: [65, 68, 70, 74, 76, 78, 80, 82], color: '#8b5cf6' },
          { label: '本月新增', val: '23', sub: '较上月 +7', spark: [5, 8, 12, 14, 16, 18, 20, 23], color: '#06b6d4' },
        ].map((kpi, idx) => (
          <div key={idx} className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 4 }}>{kpi.label}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                {kpi.val}
              </span>
              <Sparkline points={kpi.spark} color={kpi.color} width={60} height={18} />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 4 }}>{kpi.sub}</div>
          </div>
        ))}
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ padding: '10px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部状态</option>
            <option>已发布</option>
            <option>评审中</option>
            <option>草稿</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部结论类型</option>
            <option>趋势洞察</option>
            <option>机会评估</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部优先级</option>
            <option>高</option>
            <option>中</option>
            <option>低</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ position: 'relative', width: 240 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="搜索结论内容、关键词..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="input-base"
              style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 'var(--font-size-xs)' }}
            />
          </div>
          <button onClick={() => showToast('已导出结论数据', 'info')} className="btn btn-secondary btn-sm" style={{ height: 32 }}>
            <Download size={13} />
            <span>导出</span>
          </button>
        </div>
      </div>

      {/* Middle Split: Results Table (Left) + Distribution & Top 5 (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 16 }}>
        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              最新结论
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}>
              查看全部 &gt;
            </span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 36 }}></th>
                <th>结论标题</th>
                <th style={{ width: 100 }}>结论类型</th>
                <th style={{ width: 60, textAlign: 'center' }}>优先级</th>
                <th style={{ width: 70, textAlign: 'center' }}>质量评分</th>
                <th style={{ width: 60, textAlign: 'center' }}>来源</th>
                <th style={{ width: 80, textAlign: 'center' }}>状态</th>
                <th style={{ width: 80 }}>更新人</th>
                <th style={{ width: 90 }}>更新时间</th>
              </tr>
            </thead>
            <tbody>
              {resultsList.map((res) => (
                <tr key={res.id} onClick={() => openState('P13-S01')}>
                  <td><Star size={13} color="var(--text-muted)" /></td>
                  <td>
                    <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {res.title}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', padding: '1px 6px', borderRadius: 2, backgroundColor: '#eff6ff', color: 'var(--color-primary)' }}>
                      {res.type}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={res.priority} type="priority" />
                  </td>
                  <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-success)' }}>
                    {res.score}
                  </td>
                  <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    {res.sources}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={res.status} type="status" />
                  </td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>{res.author}</td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{res.date}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={128} pageSize={8} currentPage={1} />
        </div>

        {/* Right Pane: Type Distribution & Top 5 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Card 1: 结论类型分布 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                结论类型分布
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看详情 &gt;</span>
            </div>
            <DonutChart total={128} totalLabel="总数" segments={typeSegments} size={120} />
          </div>

          {/* Card 2: 高价值结论 TOP 5 */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                高价值结论 TOP 5
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { rank: 1, title: 'AI Agent在企业知识管理领域的应用趋势', score: 92 },
                { rank: 2, title: '隐私计算在金融风控的应用前景', score: 91 },
                { rank: 3, title: '生成式AI驱动的设计工具市场机会分析', score: 88 },
                { rank: 4, title: '量子计算在药物研发的潜在价值', score: 87 },
                { rank: 5, title: '边缘计算在工业物联网的落地可行性', score: 76 },
              ].map((top) => (
                <div key={top.rank} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flex: 1 }}>
                    <span style={{ width: 16, height: 16, borderRadius: 2, backgroundColor: top.rank <= 3 ? '#2563eb' : '#f1f5f9', color: top.rank <= 3 ? '#ffffff' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700, flexShrink: 0 }}>
                      {top.rank}
                    </span>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-primary)' }}>
                      {top.title}
                    </span>
                  </div>
                  <span style={{ fontWeight: 700, color: 'var(--color-success)', marginLeft: 8 }}>{top.score}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Split: 结论数量趋势 + 我的待处理 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        {/* Trend Chart */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              结论数量趋势
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 'var(--font-size-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 2, backgroundColor: '#2563eb' }} />
                <span>新增结论</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 2, backgroundColor: '#10b981' }} />
                <span>发布结论</span>
              </div>
            </div>
          </div>
          <div style={{ height: 130 }}>
            <svg viewBox="0 0 500 120" style={{ width: '100%', height: '100%' }}>
              <polyline points="20,90 60,75 100,82 140,65 180,72 220,55 260,60 300,45 340,50 380,40 420,48 460,52" fill="none" stroke="#2563eb" strokeWidth="2" />
              <polyline points="20,105 60,95 100,98 140,88 180,90 220,80 260,85 300,75 340,82 380,70 420,78 460,85" fill="none" stroke="#10b981" strokeWidth="2" />
              {['05-13', '05-14', '05-15', '05-16', '05-17', '05-18', '05-19', '05-20', '05-21', '05-22', '05-23', '05-24'].map((d, i) => (
                <text key={i} x={20 + i * 40} y="115" fontSize="8" fill="#94a3b8" textAnchor="middle">{d}</text>
              ))}
            </svg>
          </div>
        </div>

        {/* My Pending Items */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
              我的待处理
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看全部 &gt;</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, textAlign: 'center' }}>
            {[
              { count: 6, label: '待评审', color: '#8b5cf6' },
              { count: 4, label: '待补充', color: '#f59e0b' },
              { count: 3, label: '待发布', color: '#2563eb' },
              { count: 5, label: '草稿箱', color: '#64748b' },
            ].map((p, i) => (
              <div key={i} style={{ padding: '10px 4px', borderRadius: 'var(--radius-md)', backgroundColor: '#fafbfc', border: '1px solid var(--border-default)' }}>
                <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: p.color }}>{p.count}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>{p.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
