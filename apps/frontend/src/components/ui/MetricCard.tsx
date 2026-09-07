import React from 'react';

export interface MetricCardProps {
  label: string;
  value: number | string;
  icon: string | React.ReactNode;
  trend?: string;
  trendDir?: 'up' | 'down' | 'neutral';
  desc: string;
  accent: string;
  loading?: boolean;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  trend,
  trendDir,
  desc,
  accent,
  loading,
  onClick,
}) => {
  if (loading) {
    return (
      <div className="metric-card skeleton" style={{ '--metric-accent': accent } as React.CSSProperties}>
        <div style={{ height: '100%', minHeight: '80px' }} />
      </div>
    );
  }

  return (
    <div
      className="metric-card"
      style={{ '--metric-accent': accent, cursor: onClick ? 'pointer' : 'default' } as React.CSSProperties}
      onClick={onClick}
    >
      <div className="metric-card__icon">{icon}</div>
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__value">{value}</div>
      {trend && (
        <div className={`metric-card__trend metric-card__trend--${trendDir ?? 'neutral'}`}>
          {trend}
        </div>
      )}
      <div className="metric-card__desc">{desc}</div>
    </div>
  );
};

export default MetricCard;
