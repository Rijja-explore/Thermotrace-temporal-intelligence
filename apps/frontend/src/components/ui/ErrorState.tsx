import React from 'react';

export interface ErrorStateProps {
  title?: string;
  message: string;
  cachedDataNotice?: string;
  onRetry?: () => void;
  lastUpdated?: string;
  height?: string | number;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Sensor Telemetry Feed Degraded',
  message,
  cachedDataNotice,
  onRetry,
  lastUpdated,
  height = '320px',
}) => {
  return (
    <div className="empty-state" style={{ height, borderColor: 'rgba(255, 77, 79, 0.25)' }}>
      <div className="empty-state__icon" style={{ color: 'var(--risk-critical)' }}>⚠️</div>
      <div className="empty-state__title" style={{ color: 'var(--risk-critical)' }}>{title}</div>
      <div className="empty-state__desc" style={{ maxWidth: '440px' }}>{message}</div>
      {cachedDataNotice && (
        <div style={{ fontSize: '11px', color: 'var(--accent-amber)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
          {cachedDataNotice}
        </div>
      )}
      {lastUpdated && (
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Last successful sync: {lastUpdated}
        </div>
      )}
      {onRetry && (
        <button
          className="empty-state__action"
          style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', borderColor: 'var(--border-subtle)', marginTop: '16px' }}
          onClick={onRetry}
        >
          🔄 Reconnect Telemetry
        </button>
      )}
    </div>
  );
};

export default ErrorState;
