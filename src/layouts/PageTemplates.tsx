import React from 'react';
import './pageTemplates.css';

interface TemplateProps {
  children: React.ReactNode;
  className?: string;
}

export const PageFrame: React.FC<TemplateProps> = ({ children, className = '' }) => (
  <section className={`page-frame ${className}`.trim()}>{children}</section>
);

export const TriageLayout: React.FC<{
  brief: React.ReactNode;
  primary: React.ReactNode;
  actionPanel: React.ReactNode;
  supporting: React.ReactNode;
}> = ({ brief, primary, actionPanel, supporting }) => (
  <div className="triage-layout">
    <div className="triage-layout__brief">{brief}</div>
    <div className="triage-layout__primary">{primary}</div>
    <aside className="triage-layout__actions">{actionPanel}</aside>
    <div className="triage-layout__supporting">{supporting}</div>
  </div>
);

export const ListWorkspaceLayout: React.FC<{
  filters: React.ReactNode;
  list: React.ReactNode;
  preview?: React.ReactNode;
}> = ({ filters, list, preview }) => (
  <div className="list-workspace">
    <div className="list-workspace__filters">{filters}</div>
    <div className="list-workspace__body">
      <div className="list-workspace__list">{list}</div>
      {preview && <aside className="list-workspace__preview">{preview}</aside>}
    </div>
  </div>
);

export const EntityDetailLayout: React.FC<{
  narrative: React.ReactNode;
  actionPanel: React.ReactNode;
  activity?: React.ReactNode;
}> = ({ narrative, actionPanel, activity }) => (
  <div className="entity-detail-layout">
    <article className="entity-detail-layout__narrative">{narrative}</article>
    <aside className="entity-detail-layout__actions">{actionPanel}</aside>
    {activity && <div className="entity-detail-layout__activity">{activity}</div>}
  </div>
);

export const AnalysisCanvasLayout: React.FC<{
  insight: React.ReactNode;
  controls: React.ReactNode;
  visualization: React.ReactNode;
  explanation: React.ReactNode;
  detail?: React.ReactNode;
}> = ({ insight, controls, visualization, explanation, detail }) => (
  <div className="analysis-canvas-layout">
    <div className="analysis-canvas-layout__insight">{insight}</div>
    <div className="analysis-canvas-layout__controls">{controls}</div>
    <div className="analysis-canvas-layout__visualization">{visualization}</div>
    <aside className="analysis-canvas-layout__explanation">{explanation}</aside>
    {detail && <div className="analysis-canvas-layout__detail">{detail}</div>}
  </div>
);

export const SettingsLayout: React.FC<{
  navigation: React.ReactNode;
  children: React.ReactNode;
}> = ({ navigation, children }) => (
  <div className="settings-layout">
    <nav className="settings-layout__navigation" aria-label="设置分类">{navigation}</nav>
    <div className="settings-layout__content">{children}</div>
  </div>
);

export const FocusedStatusLayout: React.FC<TemplateProps> = ({ children, className = '' }) => (
  <main className={`focused-status-layout ${className}`.trim()}>{children}</main>
);
