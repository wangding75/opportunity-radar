import React, { useState } from 'react';
import {
  Download,
  Plus,
  Search,
  Star,
  ChevronRight,
  Filter,
  Briefcase,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { FilterBar } from '../components/common/FilterBar';
import { StatusBadge } from '../components/common/StatusBadge';
import { Sparkline } from '../components/common/Charts';
import { Pagination } from '../components/common/Pagination';
import { MOCK_OPPORTUNITIES, Opportunity } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P08_OpportunityPool: React.FC = () => {
  const { navigate, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('ALL');
  const [domainFilter, setDomainFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [timeFilter, setTimeFilter] = useState('30d');
  const [searchValue, setSearchValue] = useState('');
  const [starredMap, setStarredMap] = useState<Record<string, boolean>>({
    'OPP-20260819-021': true,
  });

  const toggleStar = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setStarredMap((prev) => {
      const next = !prev[id];
      showToast(next ? '已加入关注机会' : '已取消关注', 'info');
      return { ...prev, [id]: next };
    });
  };

  const filteredList = MOCK_OPPORTUNITIES.filter((opp) => {
    if (activeTab === 'NEW' && opp.status !== '新发现') return false;
    if (activeTab === 'EVAL' && opp.status !== '研判中') return false;
    if (activeTab === 'TRACK' && opp.status !== '持续跟踪') return false;
    if (activeTab === 'IGNORED' && opp.status !== '已忽略') return false;
    if (activeTab === 'ARCHIVED' && opp.status !== '已归档') return false;
    if (searchValue && !opp.name.toLowerCase().includes(searchValue.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <Header
        title="机会池"
        subtitle="发现并管理值得研究的机会，识别最具潜力的方向"
        actions={
          <>
            <button
              onClick={() => showToast('机会池数据已导出为 Excel', 'info')}
              className="btn btn-secondary"
            >
              <Download size={14} />
              <span>导出</span>
            </button>
            <button
              onClick={() => navigate('/opportunities/OPP-20260819-021')}
              className="btn btn-primary"
            >
              <Plus size={14} />
              <span>新建机会</span>
            </button>
          </>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'ALL', label: '全部', count: 326 },
          { key: 'NEW', label: '新发现', count: 84 },
          { key: 'EVAL', label: '研判中', count: 98 },
          { key: 'TRACK', label: '持续跟踪', count: 81 },
          { key: 'IGNORED', label: '已忽略', count: 38 },
          { key: 'ARCHIVED', label: '已归档', count: 25 },
        ]}
      />

      {/* Filter Bar */}
      <FilterBar
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        searchPlaceholder="搜索机会名称、标签..."
        filters={[
          {
            key: 'domain',
            label: '全部领域',
            value: domainFilter,
            onChange: setDomainFilter,
            options: [
              { label: '全部', value: 'ALL' },
              { label: '企业服务', value: 'ENTERPRISE' },
              { label: '新能源', value: 'ENERGY' },
              { label: '生物科技', value: 'BIOTECH' },
            ],
          },
          {
            key: 'priority',
            label: '全部优先级',
            value: priorityFilter,
            onChange: setPriorityFilter,
            options: [
              { label: '全部', value: 'ALL' },
              { label: '高优先级', value: 'HIGH' },
              { label: '中优先级', value: 'MEDIUM' },
              { label: '低优先级', value: 'LOW' },
            ],
          },
          {
            key: 'status',
            label: '全部状态',
            value: statusFilter,
            onChange: setStatusFilter,
            options: [
              { label: '全部', value: 'ALL' },
              { label: '研判中', value: 'EVAL' },
              { label: '持续跟踪', value: 'TRACK' },
            ],
          },
          {
            key: 'time',
            label: '近30天',
            value: timeFilter,
            onChange: setTimeFilter,
            options: [
              { label: '近30天', value: '30d' },
              { label: '近7天', value: '7d' },
              { label: '近90天', value: '90d' },
            ],
          },
        ]}
      />

      {/* Main Opportunities Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>机会名称</th>
              <th style={{ width: 140 }}>领域</th>
              <th style={{ width: 80, textAlign: 'center' }}>评分</th>
              <th style={{ width: 90, textAlign: 'center' }}>优先级</th>
              <th style={{ width: 100, textAlign: 'center' }}>研究状态</th>
              <th style={{ width: 80, textAlign: 'center' }}>证据数</th>
              <th style={{ width: 120 }}>趋势</th>
              <th style={{ width: 110 }}>更新时间</th>
              <th style={{ width: 70, textAlign: 'center' }}>关注</th>
            </tr>
          </thead>
          <tbody>
            {filteredList.map((opp) => {
              const isStarred = starredMap[opp.id];
              return (
                <tr
                  key={opp.id}
                  onClick={() => navigate(`/opportunities/${opp.id}`)}
                >
                  <td>
                    <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {opp.name}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--color-primary)', backgroundColor: 'var(--color-primary-light)', padding: '2px 8px', borderRadius: 4, fontWeight: 500 }}>
                      {opp.category.split('/')[0].trim()}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={String(opp.score)} type="score" />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={opp.priority} type="priority" />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusBadge status={opp.status} type="status" />
                  </td>
                  <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', fontWeight: 500 }}>
                    {opp.evidenceCount}
                  </td>
                  <td>
                    <Sparkline points={[20, 25, 35, 45, 60, 75, 85]} color="#2563eb" width={80} height={18} />
                  </td>
                  <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    {opp.updatedAt}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={(e) => toggleStar(opp.id, e)}
                      style={{ color: isStarred ? '#f59e0b' : 'var(--text-muted)', cursor: 'pointer', padding: 4 }}
                      title={isStarred ? '已关注' : '关注'}
                    >
                      <Star size={15} fill={isStarred ? 'currentColor' : 'none'} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <Pagination total={326} pageSize={10} currentPage={1} />
      </div>
    </div>
  );
};
