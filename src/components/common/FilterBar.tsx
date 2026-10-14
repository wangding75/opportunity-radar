import React from 'react';
import { Search, ChevronDown, Filter, RotateCcw } from 'lucide-react';

export interface FilterOption {
  key: string;
  label: string;
  options: Array<{ label: string; value: string }>;
  value: string;
  onChange: (val: string) => void;
}

interface FilterBarProps {
  searchValue?: string;
  onSearchChange?: (val: string) => void;
  searchPlaceholder?: string;
  filters?: FilterOption[];
  onReset?: () => void;
  extra?: React.ReactNode;
  tags?: Array<{ label: string; active?: boolean; onClick?: () => void }>;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchValue,
  onSearchChange,
  searchPlaceholder = '搜索标题、摘要、来源、实体...',
  filters,
  onReset,
  extra,
  tags,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          flexWrap: 'wrap',
        }}
      >
        {onSearchChange !== undefined && (
          <div
            style={{
              position: 'relative',
              flex: '1 1 240px',
              maxWidth: 360,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Search
              size={15}
              style={{
                position: 'absolute',
                left: 12,
                color: 'var(--text-muted)',
                pointerEvents: 'none',
              }}
            />
            <input
              type="text"
              value={searchValue || ''}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="input-base"
              style={{ width: '100%', paddingLeft: 36 }}
            />
          </div>
        )}

        {filters?.map((f) => (
          <div key={f.key} style={{ position: 'relative' }}>
            <select
              value={f.value}
              onChange={(e) => f.onChange(e.target.value)}
              className="input-base"
              style={{
                paddingRight: 28,
                appearance: 'none',
                cursor: 'pointer',
                backgroundColor: '#ffffff',
              }}
            >
              {f.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {f.label}: {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown
              size={14}
              style={{
                position: 'absolute',
                right: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
              }}
            />
          </div>
        ))}

        {onReset && (
          <button
            onClick={onReset}
            className="btn btn-ghost btn-sm"
            style={{ color: 'var(--text-secondary)' }}
            title="重置筛选"
          >
            <RotateCcw size={13} />
            <span>重置</span>
          </button>
        )}

        {extra && <div style={{ marginLeft: 'auto' }}>{extra}</div>}
      </div>

      {tags && tags.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>我的视图:</span>
          {tags.map((t, i) => (
            <button
              key={i}
              onClick={t.onClick}
              style={{
                padding: '4px 10px',
                fontSize: 'var(--font-size-xs)',
                borderRadius: 'var(--radius-full)',
                backgroundColor: t.active ? 'var(--color-primary-light)' : '#ffffff',
                color: t.active ? 'var(--color-primary)' : 'var(--text-secondary)',
                border: t.active ? '1px solid var(--color-primary-border)' : '1px solid var(--border-default)',
                fontWeight: t.active ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
