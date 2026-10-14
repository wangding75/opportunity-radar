import React from 'react';

export interface TabItem {
  key: string;
  label: string;
  count?: number | string;
}

interface TabsProps {
  items: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
  style?: React.CSSProperties;
}

export const Tabs: React.FC<TabsProps> = ({ items, activeKey, onChange, style }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        borderBottom: '1px solid var(--border-default)',
        marginBottom: 16,
        ...style,
      }}
    >
      {items.map((item) => {
        const isActive = item.key === activeKey;
        return (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 0',
              fontSize: 'var(--font-size-sm)',
              fontWeight: isActive ? 600 : 500,
              color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
              borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
              marginBottom: -1,
              transition: 'all 0.15s ease',
              cursor: 'pointer',
            }}
          >
            <span>{item.label}</span>
            {item.count !== undefined && (
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: isActive ? 'var(--color-primary-light)' : 'var(--border-subtle)',
                  color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
                  fontWeight: 600,
                }}
              >
                {item.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
