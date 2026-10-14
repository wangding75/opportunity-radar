import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ApiError } from '@/api/client';

export const LoadingState: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="async-state async-state--loading" aria-busy="true" aria-label="正在加载">
    {Array.from({ length: lines }, (_, index) => <span key={index} className="async-state__skeleton" />)}
  </div>
);

export const EmptyState: React.FC<{ title: string; description: string; action?: React.ReactNode }> = ({ title, description, action }) => (
  <section className="async-state" aria-live="polite">
    <h2>{title}</h2><p>{description}</p>{action && <div className="async-state__action">{action}</div>}
  </section>
);

export const ErrorState: React.FC<{ error: Error; onRetry?: () => void }> = ({ error, onRetry }) => {
  const apiError = error instanceof ApiError ? error : undefined;
  return (
    <section className="async-state async-state--error" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <div><h2>暂时无法加载内容</h2><p>{apiError?.message || '请稍后重试。'}</p>
        {apiError?.payload.requestId && <small>请求 ID：{apiError.payload.requestId}</small>}
      </div>
      {onRetry && <button type="button" className="btn btn-secondary" onClick={onRetry}><RefreshCw size={16} />重试</button>}
    </section>
  );
};

export const PartialState: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="partial-state" role="status">{children}</div>
);
