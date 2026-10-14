import React from 'react';
import { Surface } from './Surface';

export const ChartFrame: React.FC<{
  title: string;
  conclusion: string;
  timeRange: string;
  source: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  table?: React.ReactNode;
}> = ({ title, conclusion, timeRange, source, action, children, table }) => (
  <Surface className="chart-frame" padding="default">
    <header className="chart-frame__header">
      <div>
        <h2>{title}</h2>
        <p>{conclusion}</p>
      </div>
      {action}
    </header>
    <div className="chart-frame__canvas" role="img" aria-label={`${title}。${conclusion}`}>{children}</div>
    <footer className="chart-frame__footer">
      <span>时间窗：{timeRange}</span>
      <span>来源：{source}</span>
    </footer>
    {table && <details className="chart-frame__table"><summary>查看原始数据表</summary>{table}</details>}
  </Surface>
);
