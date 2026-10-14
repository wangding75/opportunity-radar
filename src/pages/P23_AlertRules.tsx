import React, { useState } from 'react';
import {
  Download,
  Plus,
  Search,
  CheckCircle,
  AlertTriangle,
  Play,
  Edit2,
  MoreVertical,
  Layers,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { StatusBadge } from '../components/common/StatusBadge';
import { DonutChart } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P23_AlertRules: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [searchValue, setSearchValue] = useState('');

  const severitySegments = [
    { label: '高', count: 34, percentage: '27.0%', color: '#ef4444' },
    { label: '中', count: 62, percentage: '49.2%', color: '#f59e0b' },
    { label: '低', count: 30, percentage: '23.8%', color: '#10b981' },
  ];

  const rulesList = [
    { name: '来源成功率低于阈值', target: '数据来源', condition: '成功率 < 90% (5分钟)', severity: '高', status: '已启用', lastTrigger: '06-10 10:12:43', hits: 128, author: '王明' },
    { name: '单来源错误数异常增长', target: '数据来源', condition: '错误数增长 > 50% (15分钟)', severity: '高', status: '已启用', lastTrigger: '06-10 09:48:21', hits: 86, author: '张磊' },
    { name: '队列等待时间过长', target: '处理队列', condition: '等待时间 > 120秒 (持续5分钟)', severity: '高', status: '已启用', lastTrigger: '06-10 09:12:09', hits: 64, author: '李想' },
    { name: 'Worker 离线告警', target: '处理节点', condition: '节点离线 > 1 (立即触发)', severity: '高', status: '已启用', lastTrigger: '06-10 08:55:33', hits: 42, author: '刘洋' },
    { name: '高频重复告警抑制异常', target: '告警系统', condition: '抑制率 > 80% (10分钟)', severity: '中', status: '已启用', lastTrigger: '06-10 08:31:17', hits: 38, author: '陈晨' },
    { name: '机会评分异常波动', target: '机会评分', condition: '波动幅度 > 30分 (30分钟)', severity: '中', status: '已启用', lastTrigger: '06-10 07:42:55', hits: 27, author: '王明' },
    { name: '情报去重命中率过低', target: '情报处理', condition: '去重命中率 < 60% (1小时)', severity: '中', status: '已停用', lastTrigger: '06-09 23:18:42', hits: 19, author: '张磊' },
    { name: '外部 API 响应超时', target: '外部服务', condition: '响应时间 > 5秒 (连续3次)', severity: '中', status: '已启用', lastTrigger: '06-09 22:45:10', hits: 16, author: '刘洋' },
  ];

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '告警规则' },
        ]}
        title="告警规则"
        subtitle="管理系统告警规则的阈值条件、触发逻辑与通知策略，保障及时发现潜在异常。"
        actions={
          <>
            <button onClick={() => showToast('已导出规则配置', 'info')} className="btn btn-secondary">
              <Download size={14} />
              <span>导入规则</span>
            </button>
            <button onClick={() => openState('P23-S01')} className="btn btn-primary">
              <Plus size={14} />
              <span>新建规则</span>
            </button>
          </>
        }
      />

      {/* Top 5 KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 16 }}>
        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>规则总数</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>126</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 +8.6% ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>已启用</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-success)' }}>98</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 +6.3% ↑</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>已停用</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-muted)' }}>28</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 -3.1% ↓</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>高严重级别</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#ef4444' }}>34</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>占比 27.0%</div>
        </div>

        <div className="card" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>近7天触发</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: '#8b5cf6' }}>412</div>
          <div style={{ fontSize: '12px', color: 'var(--color-success)', marginTop: 2 }}>较上周 +14.2% ↑</div>
        </div>
      </div>

      {/* Main Split: Left Rules Table + Right Analytics Sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 16 }}>
        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ position: 'relative', width: 220 }}>
              <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索规则名称、对象..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 28, height: 30, fontSize: '12px' }}
              />
            </div>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>全部状态</option>
              <option>已启用</option>
              <option>已停用</option>
            </select>
            <select className="input-base" style={{ height: 30, fontSize: '12px' }}>
              <option>全部严重级别</option>
              <option>高</option>
              <option>中</option>
              <option>低</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 30 }}><input type="checkbox" /></th>
                <th>规则名称</th>
                <th style={{ width: 85 }}>监控对象</th>
                <th>触发条件 / 阈值</th>
                <th style={{ width: 55, textAlign: 'center' }}>级别</th>
                <th style={{ width: 65, textAlign: 'center' }}>状态</th>
                <th style={{ width: 100 }}>最近触发</th>
                <th style={{ width: 60, textAlign: 'center' }}>命中</th>
                <th style={{ width: 60 }}>创建人</th>
                <th style={{ width: 60, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {rulesList.map((r, idx) => (
                <tr key={idx} onClick={() => openState('P23-S01')}>
                  <td><input type="checkbox" onClick={(e) => e.stopPropagation()} /></td>
                  <td><span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>{r.name}</span></td>
                  <td><span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{r.target}</span></td>
                  <td><span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{r.condition}</span></td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={r.severity} type="priority" /></td>
                  <td style={{ textAlign: 'center' }}><StatusBadge status={r.status} type="status" /></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{r.lastTrigger}</td>
                  <td style={{ textAlign: 'center', fontSize: '12px', fontWeight: 600 }}>{r.hits}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{r.author}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span onClick={(e) => { e.stopPropagation(); openState('P23-S01'); }} style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>编辑</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination total={126} pageSize={8} currentPage={1} />
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Distribution */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              严重级别分布
            </h3>
            <DonutChart total={126} totalLabel="总规则" segments={severitySegments} size={110} />
          </div>

          {/* High Frequency */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                近期高频规则
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看更多 &gt;</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '12px' }}>
              {[
                { name: '来源成功率低于阈值', hits: 128 },
                { name: '单来源错误数异常增长', hits: 86 },
                { name: '队列等待时间过长', hits: 64 },
                { name: 'Worker 离线告警', hits: 42 },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-primary)' }}>{item.name}</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{item.hits}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Rule Templates */}
      <div className="card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
            规则模板
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer' }}>查看更多 &gt;</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {[
            { title: '数据源可用性监控', desc: '监控数据源成功率与错误率', used: '24 次' },
            { title: '队列延迟监控', desc: '监控队列等待时间与积压', used: '18 次' },
            { title: '处理节点健康', desc: '监控 Worker 节点状态', used: '16 次' },
            { title: '外部服务响应监控', desc: '监控外部 API 响应时间', used: '21 次' },
          ].map((tpl, idx) => (
            <div key={idx} style={{ padding: '12px 14px', borderRadius: 6, backgroundColor: '#fafbfc', border: '1px solid var(--border-default)', fontSize: 'var(--font-size-xs)' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{tpl.title}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginBottom: 10 }}>{tpl.desc}</div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>已使用 {tpl.used}</span>
                <button onClick={() => openState('P23-S01')} className="btn btn-secondary btn-sm" style={{ padding: '2px 8px', fontSize: '12px' }}>
                  使用
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
