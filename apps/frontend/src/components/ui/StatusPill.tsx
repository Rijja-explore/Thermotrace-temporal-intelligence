import React from 'react';

export type StatusPillVariant = 'demo' | 'live' | 'nominal' | 'alert' | 'warning' | 'neutral';

interface StatusPillProps {
  label: string;
  variant?: StatusPillVariant;
  icon?: React.ReactNode;
  pulsing?: boolean;
  className?: string;
  onClick?: () => void;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  label,
  variant = 'neutral',
  icon,
  pulsing = false,
  className = '',
  onClick,
}) => {
  return (
    <span
      className={`status-pill status-pill--${variant} ${pulsing ? 'status-pill--pulse' : ''} ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {icon && <span style={{ display: 'inline-flex', marginRight: '4px' }}>{icon}</span>}
      {label}
    </span>
  );
};

export default StatusPill;
