import React from 'react';

export interface ConfidenceBarProps {
  value: number; // 0 to 100 or 0 to 1.0
  variant?: 'cyan' | 'amber' | 'red' | 'green' | 'blue' | 'purple';
  height?: number;
  showLabel?: boolean;
  label?: string;
  animate?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  value,
  variant = 'cyan',
  height = 6,
  showLabel = false,
  label,
}) => {
  const normalized = value <= 1.0 && value >= 0 ? Math.round(value * 100) : Math.round(Math.min(100, Math.max(0, value)));

  const colorMap: Record<string, string> = {
    cyan: 'var(--accent-cyan)',
    amber: 'var(--accent-amber)',
    red: 'var(--risk-critical)',
    green: 'var(--risk-low)',
    blue: 'var(--accent-blue)',
    purple: 'var(--badge-unknown)',
  };

  const barColor = colorMap[variant] || 'var(--accent-cyan)';

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
          <span style={{ color: 'var(--text-muted)' }}>{label || 'Confidence'}</span>
          <span style={{ color: barColor, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{normalized}%</span>
        </div>
      )}
      <div
        style={{
          width: '100%',
          height: `${height}px`,
          background: 'rgba(255,255,255,0.08)',
          borderRadius: `${height / 2}px`,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${normalized}%`,
            height: '100%',
            background: barColor,
            borderRadius: `${height / 2}px`,
            transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>
    </div>
  );
};

export default ConfidenceBar;
