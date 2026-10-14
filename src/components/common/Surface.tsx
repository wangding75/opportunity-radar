import React from 'react';
import './surface.css';

type SurfaceTone = 'surface' | 'raised' | 'plain';

export const Surface: React.FC<{
  children: React.ReactNode;
  className?: string;
  tone?: SurfaceTone;
  padding?: 'compact' | 'default' | 'spacious';
}> = ({ children, className = '', tone = 'surface', padding = 'default' }) => (
  <section className={`surface surface--${tone} surface--${padding} ${className}`.trim()}>{children}</section>
);

export const Section: React.FC<{
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}> = ({ title, description, action, children, className = '' }) => (
  <section className={`content-section ${className}`.trim()}>
    <header className="content-section__header">
      <div>
        <h2 className="content-section__title">{title}</h2>
        {description && <p className="content-section__description">{description}</p>}
      </div>
      {action && <div className="content-section__action">{action}</div>}
    </header>
    <div className="content-section__body">{children}</div>
  </section>
);

export const InsightBanner: React.FC<{
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  tone?: 'info' | 'attention' | 'risk';
}> = ({ title, children, action, tone = 'info' }) => (
  <section className={`insight-banner insight-banner--${tone}`}>
    <div className="insight-banner__content">
      <p className="insight-banner__eyebrow">当前判断</p>
      <h2 className="insight-banner__title">{title}</h2>
      <div className="insight-banner__body">{children}</div>
    </div>
    {action && <div className="insight-banner__action">{action}</div>}
  </section>
);

export const ActionPanel: React.FC<{
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}> = ({ title, children, action }) => (
  <aside className="action-panel">
    <div className="action-panel__header">
      <h2>{title}</h2>
      {action}
    </div>
    <div className="action-panel__body">{children}</div>
  </aside>
);
