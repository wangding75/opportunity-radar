import React, { useCallback, useState } from 'react';
import {
  Sparkles,
  Settings,
  Plus,
  Bookmark,
  MoreHorizontal,
  ExternalLink,
  ChevronDown,
  Maximize2,
  X,
  Search,
  Check,
  Briefcase,
  Share2,
  EyeOff,
} from 'lucide-react';
import { Header } from '../components/common/Header';
import { FilterBar } from '../components/common/FilterBar';
import { StatusBadge } from '../components/common/StatusBadge';
import { Pagination } from '../components/common/Pagination';
import { MOCK_INTELLIGENCE, IntelligenceItem } from '../mock/data';
import { ObservationItem, ObservationUserState, listObservations, putObservationState } from '../features/intelligence/api';
import { useAsyncResource } from '../app/useAsyncResource';
import { useAuth } from '../app/AuthContext';
import { ApiError } from '../api/client';
import { EmptyState, ErrorState, LoadingState } from '../components/common/AsyncState';
import { useRouter } from '../router/RouterContext';
import './P02_IntelligenceList.css';

const useLiveApi = import.meta.env.VITE_ENABLE_API === 'true';

const qualityToScore: Record<ObservationItem['evidence_quality'], number> = { A: 90, B: 75, C: 60, D: 45, E: 30 };
const qualityToReliability: Record<ObservationItem['evidence_quality'], IntelligenceItem['reliability']> = {
  A: '高置信度', B: '高置信度', C: '中置信度', D: '低置信度', E: '低置信度',
};

function toIntelligenceItem(row: ObservationItem): IntelligenceItem {
  return {
    id: row.public_id,
    title: row.title || '未命名观察',
    source: row.source_id,
    sourceType: '行业媒体',
    publishedAt: new Date(row.observed_at).toLocaleString('zh-CN', { hour12: false }),
    author: row.source_id,
    summary: row.text || '该观察没有可展示的摘要。',
    fullText: row.text || '',
    score: qualityToScore[row.evidence_quality],
    reliability: qualityToReliability[row.evidence_quality],
    priority: qualityToScore[row.evidence_quality] >= 75 ? '高相关' : qualityToScore[row.evidence_quality] >= 60 ? '中相关' : '低相关',
    tags: [row.item_type, row.query].filter(Boolean),
    entities: [],
    keySignals: row.query ? [`采集查询：${row.query}`] : [],
  };
}

function observedAfterFor(timeFilter: string): string | undefined {
  const hoursByFilter: Record<string, number> = { '24h': 24, '7d': 24 * 7, '30d': 24 * 30 };
  const hours = hoursByFilter[timeFilter];
  return hours ? new Date(Date.now() - hours * 60 * 60 * 1000).toISOString() : undefined;
}

function stateErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    const suffix = error.payload.requestId ? `（请求 ID: ${error.payload.requestId}）` : '';
    return `${error.payload.message || fallback}${suffix}`;
  }
  return fallback;
}

export const P02_IntelligenceList: React.FC = () => {
  const { navigate, openState, showToast } = useRouter();
  const { status: authStatus } = useAuth();
  const [selectedId, setSelectedId] = useState<string>('INT-20260819-01842');
  const [searchValue, setSearchValue] = useState('');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [tagFilter, setTagFilter] = useState('ALL');
  const [timeFilter, setTimeFilter] = useState('7d');
  const [activeViewTag, setActiveViewTag] = useState('全部观察');
  const observationResource = useAsyncResource(
    (signal) => useLiveApi
      ? listObservations({ q: searchValue, sourceId: sourceFilter, itemType: tagFilter, observedAfter: observedAfterFor(timeFilter), signal })
      : Promise.resolve(undefined),
    [searchValue, sourceFilter, tagFilter, timeFilter],
  );
  const items = useLiveApi ? (observationResource.data?.items || []).map(toIntelligenceItem) : MOCK_INTELLIGENCE;
  const rawItemsById = new Map((observationResource.data?.items || []).map((row) => [row.public_id, row]));
  const selectedItem = items.find((i) => i.id === selectedId) || items[0];

  // 服务端返回的当前用户状态。null 表示该用户没有状态（未登录/从未写入），
  // 绝不能在前端伪造成默认收藏值。
  const [userStates, setUserStates] = useState<Record<string, ObservationUserState>>({});
  const [pendingStateIds, setPendingStateIds] = useState<Set<string>>(new Set());
  const [failedStateIds, setFailedStateIds] = useState<Set<string>>(new Set());
  const canWriteState = useLiveApi && authStatus === 'authenticated';

  const mergeServerStates = useCallback((rows: ObservationItem[]) => {
    setUserStates(() => {
      const next: Record<string, ObservationUserState> = {};
      for (const row of rows) {
        if (row.user_state) next[row.public_id] = row.user_state;
      }
      return next;
    });
  }, []);

  React.useEffect(() => {
    if (useLiveApi && observationResource.data?.items) {
      mergeServerStates(observationResource.data.items);
    }
  }, [observationResource.data, mergeServerStates]);

  const patchState = useCallback(async (publicId: string, patch: { bookmarked?: boolean; dismissed?: boolean }, successTitle: string) => {
    if (pendingStateIds.has(publicId)) return;
    setPendingStateIds((prev) => new Set(prev).add(publicId));
    setFailedStateIds((prev) => {
      const next = new Set(prev);
      next.delete(publicId);
      return next;
    });
    try {
      const response = await putObservationState(publicId, patch);
      setUserStates((prev) => {
        const next: Record<string, ObservationUserState> = { ...prev };
        if (response.user_state) next[publicId] = response.user_state;
        else delete next[publicId];
        return next;
      });
      showToast(successTitle, 'success');
    } catch (error) {
      // 失败必须可见：显示错误并保留原状态，不回退成“未收藏”也不假装成功。
      setFailedStateIds((prev) => new Set(prev).add(publicId));
      showToast('状态保存失败', 'error', stateErrorMessage(error, '请稍后重试。'));
    } finally {
      setPendingStateIds((prev) => {
        const next = new Set(prev);
        next.delete(publicId);
        return next;
      });
    }
  }, [pendingStateIds, showToast]);

  const isLoading = useLiveApi && observationResource.phase === 'loading' && !observationResource.data;
  const liveError = useLiveApi && observationResource.phase === 'error' ? observationResource.error : undefined;

  const renderBookmarkButton = (publicId: string) => {
    const state = userStates[publicId] || null;
    const isBookmarked = state?.bookmarked ?? false;
    const hasState = state !== null;
    const isPending = pendingStateIds.has(publicId);
    const isFailed = failedStateIds.has(publicId);
    const disabled = !canWriteState || isPending;
    const title = !canWriteState
      ? '登录后才能收藏观察'
      : isPending
        ? '正在保存…'
        : isFailed
          ? '上次保存失败，点击重试'
          : hasState && isBookmarked
            ? '取消收藏'
            : '收藏';
    return (
      <button
        disabled={disabled}
        data-testid={`bookmark-${publicId}`}
        onClick={(e) => {
          e.stopPropagation();
          void patchState(publicId, { bookmarked: !isBookmarked }, isBookmarked ? '已取消收藏' : '已收藏');
        }}
        style={{
          color: isFailed ? 'var(--color-danger)' : hasState && isBookmarked ? '#f59e0b' : 'var(--text-muted)',
          padding: 4,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
        title={title}
        aria-label={title}
      >
        <Bookmark size={15} fill={hasState && isBookmarked ? 'currentColor' : 'none'} />
      </button>
    );
  };

  const renderDismissButton = (publicId: string) => {
    const state = userStates[publicId] || null;
    const isDismissed = state?.dismissed ?? false;
    const isPending = pendingStateIds.has(publicId);
    const isFailed = failedStateIds.has(publicId);
    const disabled = !canWriteState || isPending;
    const title = !canWriteState
      ? '登录后才能忽略观察'
      : isPending
        ? '正在保存…'
        : isFailed
          ? '上次保存失败，点击重试'
          : isDismissed
            ? '取消忽略'
            : '忽略该观察';
    return (
      <button
        disabled={disabled}
        data-testid={`dismiss-${publicId}`}
        onClick={(e) => {
          e.stopPropagation();
          void patchState(publicId, { dismissed: !isDismissed }, isDismissed ? '已取消忽略' : '已忽略');
        }}
        style={{
          color: isFailed ? 'var(--color-danger)' : state && isDismissed ? 'var(--text-secondary)' : 'var(--text-muted)',
          padding: 4,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
        title={title}
        aria-label={title}
      >
        <EyeOff size={15} />
      </button>
    );
  };

  return (
    <div className="intelligence-page">
      <Header
        title="观察列表"
        subtitle="聚合全球信源，发现早期信号，把握市场先机"
        extra={
          <span style={{ display: 'inline-flex', alignItems: 'center', color: '#10b981' }}>
            <Sparkles size={18} />
          </span>
        }
        actions={
          <>
            <button
              disabled
              title="订阅规则功能待后端接入后开放"
              className="btn btn-secondary"
            >
              <Settings size={15} />
              <span>订阅设置（待接入）</span>
            </button>
            <button
              disabled
              title="人工创建观察功能待后端接入后开放"
              className="btn btn-primary"
            >
              <Plus size={15} />
              <span>新建观察（待接入）</span>
              <ChevronDown size={14} />
            </button>
          </>
        }
      />

      {/* Filter Bar */}
      <FilterBar
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        filters={[
          {
            key: 'source',
            label: '来源',
            value: sourceFilter,
            onChange: setSourceFilter,
            options: [
              { label: '全部', value: 'ALL' },
              { label: 'GitHub', value: 'github' },
              { label: 'Google Trends RSS', value: 'google_trends_rss' },
              { label: '已接入应用', value: 'instrumented_app' },
            ],
          },
          {
            key: 'tag',
            label: '对象类型',
            value: tagFilter,
            onChange: setTagFilter,
            options: [
              { label: '全部', value: 'ALL' },
              { label: '产品', value: 'PRODUCT' },
              { label: '仓库', value: 'REPOSITORY' },
              { label: '招聘', value: 'JOB' },
              { label: '趋势', value: 'TREND' },
            ],
          },
          {
            key: 'time',
            label: '时间',
            value: timeFilter,
            onChange: setTimeFilter,
            options: [
              { label: '近 24 小时', value: '24h' },
              { label: '近 7 天', value: '7d' },
              { label: '近 30 天', value: '30d' },
            ],
          },
        ]}
        tags={[
          { label: '全部观察', active: activeViewTag === '全部观察', onClick: () => setActiveViewTag('全部观察') },
          { label: '行业热点', active: activeViewTag === '行业热点', onClick: () => setActiveViewTag('行业热点') },
          { label: '政策法规', active: activeViewTag === '政策法规', onClick: () => setActiveViewTag('政策法规') },
          { label: '投融资动态', active: activeViewTag === '投融资动态', onClick: () => setActiveViewTag('投融资动态') },
          { label: '技术突破', active: activeViewTag === '技术突破', onClick: () => setActiveViewTag('技术突破') },
          { label: '市场动态', active: activeViewTag === '市场动态', onClick: () => setActiveViewTag('市场动态') },
        ]}
      />

      {useLiveApi && authStatus === 'anonymous' && (
        <div
          className="card"
          data-testid="anonymous-state-hint"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 16px',
            marginBottom: 16,
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-secondary)',
            borderLeft: '4px solid var(--color-warning)',
          }}
        >
          <Search size={14} />
          <span>当前处于未登录状态：收藏与忽略不可用，用户状态显示为空（null），不会伪造收藏数据。</span>
        </div>
      )}

      {/* Main Split Layout: Table (Left) + Detail Preview (Right) */}
      <div className="intelligence-split" style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: 16 }}>
        {/* Left: Intelligence Table */}
        <div className="card intelligence-table-surface" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 120 }}>来源</th>
                <th>标题 / 摘要</th>
                <th style={{ width: 150 }}>标签</th>
                <th style={{ width: 100 }}>时间</th>
                <th style={{ width: 80, textAlign: 'center' }}>置信度</th>
                <th style={{ width: 110, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isSelected = item.id === selectedId;
                const state = userStates[item.id] || null;
                return (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    style={{
                      backgroundColor: isSelected ? 'var(--color-primary-light)' : 'transparent',
                      opacity: state?.dismissed ? 0.55 : 1,
                    }}
                    data-dismissed={state?.dismissed ? 'true' : undefined}
                  >
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div
                          style={{
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            backgroundColor: '#eff6ff',
                            color: 'var(--color-primary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '12px',
                            fontWeight: 700,
                          }}
                        >
                          {item.source.charAt(0)}
                        </div>
                        <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 500 }}>
                          {item.source.split('·')[0].trim()}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div
                        style={{
                          fontSize: 'var(--font-size-sm)',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          marginBottom: 4,
                        }}
                      >
                        {item.title}
                      </div>
                      <div
                        style={{
                          fontSize: 'var(--font-size-xs)',
                          color: 'var(--text-secondary)',
                          display: '-webkit-box',
                          WebkitLineClamp: 1,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {item.summary}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {item.tags.slice(0, 2).map((t, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: '12px',
                              padding: '1px 6px',
                              borderRadius: 'var(--radius-xs)',
                              backgroundColor: '#f1f5f9',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            {t}
                          </span>
                        ))}
                        {item.tags.length > 2 && (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            +{item.tags.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                        {item.publishedAt.includes(' ') ? item.publishedAt.split(' ')[0] : item.publishedAt}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <StatusBadge status={String(item.score)} type="score" />
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                        {renderBookmarkButton(item.id)}
                        {renderDismissButton(item.id)}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/intelligence/${item.id}`);
                          }}
                          style={{ color: 'var(--text-muted)', padding: 4, cursor: 'pointer' }}
                          title="详情"
                        >
                          <MoreHorizontal size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="intelligence-mobile-list">
            {items.map((item) => (
              <div key={item.id} className="intelligence-mobile-row" style={{ display: 'contents' }}>
                <button type="button" className="intelligence-mobile-row" onClick={() => navigate(`/intelligence/${item.id}`)}>
                  <span className="intelligence-mobile-row__source">{item.source.charAt(0)}</span>
                  <span className="intelligence-mobile-row__body"><strong>{item.title}</strong><small>{item.summary}</small><em>{item.source} · {item.publishedAt}</em></span>
                  <StatusBadge status={String(item.score)} type="score" />
                </button>
                <div style={{ display: 'flex', gap: 6, padding: '0 var(--space-4) var(--space-3)', marginLeft: 52 }}>
                  {renderBookmarkButton(item.id)}
                  {renderDismissButton(item.id)}
                </div>
              </div>
            ))}
          </div>

          {isLoading && <LoadingState lines={6} />}
          {liveError && <ErrorState error={liveError} onRetry={observationResource.reload} />}
          {useLiveApi && !isLoading && !liveError && items.length === 0 && <EmptyState title="暂无观察" description="调整筛选条件，或等待采集任务写入新的观察。" />}
          {!useLiveApi && <Pagination total={1248} pageSize={20} currentPage={1} />}
        </div>

        {/* Right: Quick Detail Preview Panel */}
        {selectedItem && <div className="card intelligence-preview" style={{ display: 'flex', flexDirection: 'column', height: 'fit-content' }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <StatusBadge status={selectedItem.reliability} type="health" />
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button
                onClick={() => navigate(`/intelligence/${selectedItem.id}`)}
                className="btn btn-ghost btn-sm"
                title="全页打开"
              >
                <Maximize2 size={14} />
              </button>
            </div>
          </div>

          {/* Title & Source */}
          <h2
            style={{
              fontSize: 'var(--font-size-md)',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.4,
              marginBottom: 10,
            }}
          >
            {selectedItem.title}
          </h2>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 'var(--font-size-xs)',
              color: 'var(--text-muted)',
              marginBottom: 16,
            }}
          >
            <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{selectedItem.source}</span>
            <span>·</span>
            <span>{selectedItem.publishedAt}</span>
          </div>

          {/* Summary */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              摘要
            </div>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {selectedItem.summary}
            </p>
          </div>

          {/* Key Signals */}
          {selectedItem.keySignals && selectedItem.keySignals.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                关键信号
              </div>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {selectedItem.keySignals.map((sig, i) => (
                  <li
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 6,
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--text-primary)',
                      lineHeight: 1.4,
                    }}
                  >
                    <span style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: '#10b981', marginTop: 5, flexShrink: 0 }} />
                    <span>{sig}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Related Entities */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
              相关实体
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {selectedItem.entities.map((ent, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    backgroundColor: '#fafbfc',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {ent.name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 2 }}>
                    {ent.type}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Original link */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
              原始链接
            </div>
            <a
              href="https://www.reuters.com"
              target="_blank"
              rel="noreferrer"
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-primary)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <span>https://www.reuters.com/technology/openai-gpt-4o</span>
              <ExternalLink size={12} />
            </a>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 'auto', paddingTop: 12 }}>
            <button
              disabled
              title="关键词关联功能待后端接入后开放"
              className="btn btn-secondary"
              style={{ fontSize: 'var(--font-size-xs)' }}
            >
              + 加入关键词（待接入）
            </button>
            <button
              onClick={() => openState('P03-S01')}
              className="btn btn-primary"
              style={{ fontSize: 'var(--font-size-xs)' }}
            >
              <Briefcase size={14} />
              <span>转为机会</span>
            </button>
          </div>
        </div>}
      </div>
    </div>
  );
};
