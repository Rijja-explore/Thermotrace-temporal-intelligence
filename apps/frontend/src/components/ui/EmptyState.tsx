import React from 'react';

export interface EmptyStateProps {
  icon?: string | React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  height?: string | number;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '🔭',
  title,
  description,
  actionLabel,
  onAction,
  height = '320px',
}) => {
  return (
    <div className="empty-state" style={{ height }}>
      <div className="empty-state__icon">{icon}</div>
      <div className="empty-state__title">{title}</div>
      <div className="empty-state__desc">{description}</div>
      {actionLabel && onAction && (
        <button className="empty-state__action" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
