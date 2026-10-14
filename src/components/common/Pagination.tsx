import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  total: number;
  pageSize?: number;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  pageSizeOptions?: number[];
  style?: React.CSSProperties;
}

export const Pagination: React.FC<PaginationProps> = ({
  total,
  pageSize = 20,
  currentPage = 1,
  onPageChange,
  style,
}) => {
  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 16px',
        fontSize: 'var(--font-size-xs)',
        color: 'var(--text-secondary)',
        borderTop: '1px solid var(--border-subtle)',
        marginTop: 12,
        ...style,
      }}
    >
      <div>共 {total} 条数据</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <button
          onClick={() => onPageChange && onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage <= 1}
          className="btn btn-secondary btn-sm"
          style={{ padding: '4px 8px', opacity: currentPage <= 1 ? 0.4 : 1 }}
        >
          <ChevronLeft size={14} />
        </button>

        {[1, 2, 3, 4, 5].filter((p) => p <= totalPages).map((p) => (
          <button
            key={p}
            onClick={() => onPageChange && onPageChange(p)}
            style={{
              width: 28,
              height: 28,
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: p === currentPage ? 'var(--color-primary)' : 'transparent',
              color: p === currentPage ? '#ffffff' : 'var(--text-primary)',
              fontWeight: p === currentPage ? 600 : 400,
              cursor: 'pointer',
            }}
          >
            {p}
          </button>
        ))}

        {totalPages > 5 && <span style={{ padding: '0 4px' }}>...</span>}
        {totalPages > 5 && (
          <button
            onClick={() => onPageChange && onPageChange(totalPages)}
            style={{
              width: 28,
              height: 28,
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: totalPages === currentPage ? 'var(--color-primary)' : 'transparent',
              color: totalPages === currentPage ? '#ffffff' : 'var(--text-primary)',
              cursor: 'pointer',
            }}
          >
            {totalPages}
          </button>
        )}

        <button
          onClick={() => onPageChange && onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage >= totalPages}
          className="btn btn-secondary btn-sm"
          style={{ padding: '4px 8px', opacity: currentPage >= totalPages ? 0.4 : 1 }}
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};
