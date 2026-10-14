import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useRouter } from '../../router/RouterContext';

export const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useRouter();

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 24,
        right: 24,
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        pointerEvents: 'none',
      }}
    >
      {toasts.map((toast) => {
        let icon = <CheckCircle2 size={18} color="var(--color-success)" />;
        let borderLeft = '4px solid var(--color-success)';

        if (toast.type === 'error') {
          icon = <AlertCircle size={18} color="var(--color-danger)" />;
          borderLeft = '4px solid var(--color-danger)';
        } else if (toast.type === 'warning') {
          icon = <AlertTriangle size={18} color="var(--color-warning)" />;
          borderLeft = '4px solid var(--color-warning)';
        } else if (toast.type === 'info') {
          icon = <Info size={18} color="var(--color-info)" />;
          borderLeft = '4px solid var(--color-info)';
        }

        return (
          <div
            key={toast.id}
            style={{
              pointerEvents: 'auto',
              minWidth: 280,
              maxWidth: 380,
              padding: '12px 16px',
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-lg)',
              border: '1px solid var(--border-default)',
              borderLeft,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 12,
              animation: 'fadeIn 0.2s ease-out',
            }}
          >
            <div style={{ flexShrink: 0, marginTop: 2 }}>{icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {toast.title}
              </div>
              {toast.message && (
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: 2 }}>
                  {toast.message}
                </div>
              )}
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              style={{ color: 'var(--text-muted)', cursor: 'pointer', padding: 2 }}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
