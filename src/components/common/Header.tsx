import React from 'react';
import { ChevronRight } from 'lucide-react';
import { useRouter } from '../../router/RouterContext';

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  extra?: React.ReactNode;
  actions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  extra,
  actions,
}) => {
  const { navigate } = useRouter();

  return (
    <div className="page-header" style={{ marginBottom: 20 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-muted)',
            marginBottom: 8,
          }}
        >
          {breadcrumbs.map((item, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <ChevronRight size={12} />}
              {item.path ? (
                <span
                  onClick={() => navigate(item.path!)}
                  style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}
                  className="hover-underline"
                >
                  {item.label}
                </span>
              ) : (
                <span>{item.label}</span>
              )}
            </React.Fragment>
          ))}
        </div>
      )}

      <div className="page-header__content"
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        <div className="page-header__heading">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 className="page-header__title"
              style={{
                fontSize: 'var(--font-size-3xl)',
                fontWeight: 700,
                color: 'var(--text-primary)',
                lineHeight: 1.25,
              }}
            >
              {title}
            </h1>
            {extra}
          </div>
          {subtitle && (
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--text-secondary)',
                marginTop: 4,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>

        {actions && (
          <div className="page-header__actions" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};
