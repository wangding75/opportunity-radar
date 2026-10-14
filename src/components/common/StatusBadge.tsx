import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'score' | 'priority' | 'health' | 'stage' | 'status' | 'tag' | 'source';
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'status', size = 'md' }) => {
  let badgeClass = 'badge-neutral';

  if (type === 'score') {
    const num = parseInt(status, 10);
    if (num >= 80) badgeClass = 'badge-success';
    else if (num >= 65) badgeClass = 'badge-primary';
    else if (num >= 50) badgeClass = 'badge-warning';
    else badgeClass = 'badge-danger';
    
    return (
      <span className={`badge ${badgeClass}`} style={{ fontWeight: 600, padding: '2px 8px' }}>
        {status}
      </span>
    );
  }

  if (type === 'priority') {
    if (status === '高' || status === '高相关' || status === '高优先级' || status === 'P0') badgeClass = 'badge-danger';
    else if (status === '中' || status === '中相关' || status === '中优先级' || status === 'P1') badgeClass = 'badge-warning';
    else badgeClass = 'badge-info';
    
    return <span className={`badge ${badgeClass}`}>{status}</span>;
  }

  if (type === 'health') {
    if (status === '正常' || status === '已解决' || status === '成功' || status === 'connected') badgeClass = 'badge-success';
    else if (status === '需关注' || status === '处理中' || status === '部分失败' || status === '已暂停') badgeClass = 'badge-warning';
    else badgeClass = 'badge-danger';
    
    return (
      <span className={`badge ${badgeClass}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
        <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }} />
        {status}
      </span>
    );
  }

  // Generic status map
  if (['研判中', '运行中', '新发现'].includes(status)) badgeClass = 'badge-primary';
  else if (['已完成', '正常', '高置信度', '资料收集', '撰写报告'].includes(status)) badgeClass = 'badge-success';
  else if (['持续跟踪', '需关注', '假设验证', '初步分析'].includes(status)) badgeClass = 'badge-warning';
  else if (['异常', '失败', '已停用', '错误'].includes(status)) badgeClass = 'badge-danger';
  else if (['已忽略', '已归档'].includes(status)) badgeClass = 'badge-neutral';

  return <span className={`badge ${badgeClass}`}>{status}</span>;
};
