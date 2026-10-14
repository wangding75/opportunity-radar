import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  change?: string;
  changeType?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  iconBg?: string;
  iconColor?: string;
  onClick?: () => void;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subValue,
  change,
  changeType = 'up',
  icon,
  iconBg = 'var(--color-primary-light)',
  iconColor = 'var(--color-primary)',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className="card"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '16px 20px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
      }}
    >
      {icon && (
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 'var(--radius-lg)',
            backgroundColor: iconBg,
            color: iconColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            marginBottom: 4,
          }}
        >
          {title}
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span
            style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.2,
            }}
          >
            {value}
          </span>
          {subValue && (
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {subValue}
            </span>
          )}
        </div>
        {change && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              fontSize: 'var(--font-size-xs)',
              marginTop: 4,
              color:
                changeType === 'up'
                  ? 'var(--color-success)'
                  : changeType === 'down'
                  ? 'var(--color-danger)'
                  : 'var(--text-muted)',
              fontWeight: 500,
            }}
          >
            {changeType === 'up' && <ArrowUpRight size={13} />}
            {changeType === 'down' && <ArrowDownRight size={13} />}
            <span>{change}</span>
          </div>
        )}
      </div>
    </div>
  );
};
