import React, { useState } from 'react';
import {
  Plus,
  Play,
  Search,
  Filter,
  MoreVertical,
  Activity,
  Calendar,
  Layers,
  ChevronRight,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { Tabs } from '../components/common/Tabs';
import { StatusBadge } from '../components/common/StatusBadge';
import { Pagination } from '../components/common/Pagination';
import { MOCK_MONITORING_PLANS } from '../mock/data';
import { useRouter } from '../router/RouterContext';

export const P17_MonitoringPlans: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const [activeTab, setActiveTab] = useState('ALL');
  const [searchValue, setSearchValue] = useState('');

  return (
    <div>
      <Header
        breadcrumbs={[
          { label: '监控', path: '/monitoring' },
          { label: '监控计划' },
        ]}
        title="监控计划"
        subtitle="配置与维护针对特定主题、实体或技术方向的自动化数据采集与研判计划"
        actions={
          <>
            <button
              onClick={() => openState('P17-S02')}
              className="btn btn-secondary"
            >
              <Sparkles size={14} />
              <span>从模板创建</span>
            </button>
            <button
              onClick={() => openState('P17-S01')}
              className="btn btn-primary"
            >
              <Plus size={14} />
              <span>新建监控计划</span>
            </button>
          </>
        }
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'ALL', label: '全部', count: 18 },
          { key: 'RUNNING', label: '运行中', count: 14 },
          { key: 'PAUSED', label: '已暂停', count: 3 },
          { key: 'DRAFT', label: '草稿', count: 1 },
        ]}
      />

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ position: 'relative', width: 260 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="搜索计划名称、关键词..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="input-base"
                style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 'var(--font-size-xs)' }}
              />
            </div>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>状态: 全部</option>
              <option>运行中</option>
              <option>已暂停</option>
            </select>
            <select className="input-base" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>
              <option>频率: 全部</option>
              <option>每 15 分钟</option>
              <option>每 30 分钟</option>
              <option>每小时</option>
            </select>
          </div>
        </div>

        {/* Monitoring Plans Table */}
        <table className="data-table">
          <thead>
            <tr>
              <th>计划名称</th>
              <th style={{ width: 140 }}>目标对象</th>
              <th style={{ width: 100 }}>执行频率</th>
              <th style={{ width: 90, textAlign: 'center' }}>来源数</th>
              <th style={{ width: 90, textAlign: 'center' }}>情报发现</th>
              <th style={{ width: 110 }}>下次执行</th>
              <th style={{ width: 90, textAlign: 'center' }}>状态</th>
              <th style={{ width: 120, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_MONITORING_PLANS.map((plan) => (
              <tr
                key={plan.id}
                onClick={() => navigate(`/monitoring/${plan.id}`)}
              >
                <td>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {plan.name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>ID: {plan.id}</div>
                </td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>{plan.target}</td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-primary)' }}>{plan.frequency}</td>
                <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>{plan.sourcesCount}</td>
                <td style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-primary)' }}>
                  {plan.signalsCount}
                </td>
                <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{plan.nextRun}</td>
                <td style={{ textAlign: 'center' }}>
                  <StatusBadge status={plan.status} type="status" />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openState('P17-S03');
                      }}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '2px 8px', fontSize: '12px' }}
                    >
                      <Play size={12} />
                      <span>运行</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/monitoring/${plan.id}`);
                      }}
                      style={{ color: 'var(--text-muted)', padding: 4 }}
                    >
                      <MoreVertical size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <Pagination total={18} pageSize={10} currentPage={1} />
      </div>
    </div>
  );
};
