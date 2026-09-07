import React, { useState } from 'react';

export interface RiskScoreCardProps {
  label: string;
  value: number;
  max?: number;
  variant?: 'cyan' | 'amber' | 'red' | 'orange' | 'green' | 'purple';
  sub?: string;
  components?: Record<string, number>;
}

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  label,
  value,
  max = 100,
  variant = 'cyan',
  sub,
  components,
}) => {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const urgency = value >= 70 ? 'Critical' : value >= 50 ? 'High' : value >= 30 ? 'Moderate' : 'Low';
  const displaySub = sub ?? urgency;

  return (
    <div className={`risk-score-card risk-score-card--${variant}`}>
      <div className="risk-score-card__label">{label}</div>
      <div className="risk-score-card__value">
        {value}
        <span style={{ fontSize: '16px', fontWeight: 400, color: 'var(--text-muted)' }}>/{max}</span>
      </div>
      <div className="risk-score-card__sub">{displaySub}</div>
      <div className="risk-score-card__bar-track">
        <div className="risk-score-card__bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <button className="risk-score-card__explain-btn" onClick={() => setExpanded(e => !e)}>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {expanded ? 'Hide Breakdown' : 'Explain'}
      </button>
      {expanded && components && Object.keys(components).length > 0 && (
        <div className="risk-score-card__breakdown">
          {Object.entries(components).map(([k, v]) => (
            <div key={k} className="risk-score-card__breakdown-row">
              <span className="risk-score-card__breakdown-label">{k.replace(/_/g, ' ')}</span>
              <div className="risk-score-card__breakdown-bar">
                <div className="risk-score-card__breakdown-bar-fill" style={{ width: `${Math.min(100, v)}%` }} />
              </div>
              <span className="risk-score-card__breakdown-val">{v}</span>
            </div>
          ))}
        </div>
      )}
      {expanded && (!components || Object.keys(components).length === 0) && (
        <div className="risk-score-card__breakdown" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Composite score — component breakdown unavailable for this event.
        </div>
      )}
    </div>
  );
};

export default RiskScoreCard;
