import React, { useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  ChevronRight,
  BookOpen,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { Pagination } from '../components/common/Pagination';
import { useRouter } from '../router/RouterContext';

export const P11_ResearchWorkflow: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('ALL');
  const [searchValue, setSearchValue] = useState('');

  const workflows = [
    {
      id: 'RES-20260819-0011',
      name: '企业级AI知识管理平台研究',
      opportunity: 'AI应用市场机会',
      opportunityId: 'OPP-20260819-021',
      owner: '张天宇',
      progress: 60,
      currentStep: '假设分析',
      status: '进行中',
      time: '15分钟前',
    },
    {
      id: 'RES-20260819-0012',
      name: '可持续航空燃料市场分析',
      opportunity: '新能源机会',
      opportunityId: 'OPP-20260819-022',
      owner: '王明',
      progress: 40,
      currentStep: '资料收集',
      status: '进行中',
      time: '1小时前',
    },
    {
      id: 'RES-20260819-0013',
      name: '边缘计算商业路径研究',
      opportunity: '工业互联网机会',
      opportunityId: 'OPP-20260819-023',
      owner: '张天宇',
      progress: 65,
      currentStep: '验证',
      status: '进行中',
      time: '2小时前',
    },
    {
      id: 'RES-20260819-0014',
      name: '基因编辑疗法竞争格局',
      opportunity: '生物科技机会',
      opportunityId: 'OPP-20260819-024',
      owner: '李强',
      progress: 20,
      currentStep: '问题定义',
      status: '进行中',
      time: '3小时前',
    },
    {
      id: 'RES-20260819-0015',
      name: '人形机器人供应链研究',
      opportunity: '机器人机会',
      opportunityId: 'OPP-20260819-026',
      owner: '赵敏',
      progress: 0,
      currentStep: '问题定义',
      status: '草稿',
      time: '5小时前',
    },
    {
      id: 'RES-20260819-0016',
      name: '空间计算资源生态研究',
      opportunity: '云计算机会',
      opportunityId: 'OPP-20260819-027',
      owner: '陈磊',
      progress: 100,
      currentStep: '结论',
      status: '已完成',
      time: '1天前',
    },
  ];

  return (
    <div>
      <Header
        title="研究工作流"
        subtitle="跟踪和管理所有研究项目的进展"
        actions={
          <button
            onClick={() => openState('P09-S05')}
            className="btn btn-primary"
          >
            <Plus size={15} />
            <span>新建研究</span>
          </button>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'ALL', label: '全部', count: 28 },
          { key: 'IN_PROGRESS', label: '进行中', count: 12 },
          { key: 'COMPLETED', label: '已完成', count: 10 },
          { key: 'PAUSED', label: '已暂停', count: 4 },
          { key: 'DRAFT', label: '草稿', count: 2 },
        ]}
      />

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Table Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 280 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="搜索研究工作流..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="input-base"
              style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 'var(--font-size-xs)' }}
            />
          </div>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部负责人</option>
            <option>张天宇</option>
            <option>王明</option>
            <option>李强</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部状态</option>
            <option>进行中</option>
            <option>已完成</option>
          </select>
          <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
            <option>全部类型</option>
            <option>商业研究</option>
            <option>技术评估</option>
          </select>
        </div>

        {/* Workflows Table */}
        <table className="data-table">
          <thead>
            <tr>
              <th>研究名称</th>
              <th style={{ width: 160 }}>关联机会</th>
              <th style={{ width: 100 }}>负责人</th>
              <th style={{ width: 160 }}>进度</th>
              <th style={{ width: 110 }}>当前步骤</th>
              <th style={{ width: 90, textAlign: 'center' }}>状态</th>
              <th style={{ width: 100 }}>更新时间</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((wf) => (
              <tr
                key={wf.id}
                onClick={() => navigate(`/research/${wf.id}`)}
              >
                <td>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {wf.name}
                  </div>
                </td>
                <td>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/opportunities/${wf.opportunityId}`);
                    }}
                    style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', cursor: 'pointer' }}
                  >
                    {wf.opportunity}
                  </span>
                </td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>{wf.owner}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 6, borderRadius: 3, backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${wf.progress}%`,
                          height: '100%',
                          backgroundColor: wf.progress === 100 ? '#10b981' : 'var(--color-primary)',
                        }}
                      />
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', minWidth: 30 }}>
                      {wf.progress}%
                    </span>
                  </div>
                </td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-primary)' }}>{wf.currentStep}</td>
                <td style={{ textAlign: 'center' }}>
                  <StatusBadge status={wf.status} type="status" />
                </td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{wf.time}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <Pagination total={28} pageSize={10} currentPage={1} />
      </div>
    </div>
  );
};
