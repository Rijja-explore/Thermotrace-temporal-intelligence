import React from 'react';
import type { Alert } from '../../services/api';

export interface AlertRowProps {
  alert: Alert;
  onInvestigate?: (eventId: string) => void;
  selected?: boolean;
}

export const AlertRow: React.FC<AlertRowProps> = ({
  alert,
  onInvestigate,
  selected = false,
}) => {
  const getSeverityVariant = (sev: string): 'critical' | 'high' | 'medium' | 'low' => {
    switch (sev.toLowerCase()) {
      case 'critical': return 'critical';
      case 'high': return 'high';
      case 'medium': return 'medium';
      default: return 'low';
    }
  };

  const sevVariant = getSeverityVariant(alert.severity);

  return (
    <div
      className={`alert-row alert-row--${sevVariant} ${selected ? 'alert-row--selected' : ''}`}
      onClick={() => onInvestigate?.(alert.event_id)}
      role="button"
      tabIndex={0}
    >
      <div className="alert-row__main">
        <div className="alert-row__id">{alert.event_id}</div>
        <div className="alert-row__title">{alert.title}</div>
        <div className="alert-row__meta">
          <span className="alert-row__facility">{alert.location || 'Off-site'}</span>
          <span>·</span>
          <span>{alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}</span>
        </div>
      </div>
      <div className="alert-row__side">
        <span className={`risk-badge risk-badge--${sevVariant === 'critical' ? 'critical' : sevVariant === 'high' ? 'high' : 'medium'}`}>
          {alert.severity}
        </span>
        <span className="alert-row__arrow">→</span>
      </div>
    </div>
  );
};

export default AlertRow;
