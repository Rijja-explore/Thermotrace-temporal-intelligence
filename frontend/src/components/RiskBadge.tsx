interface RiskBadgeProps {
  value: number;
  label?: string;
  type?: 'risk' | 'likelihood' | 'confidence';
}

export default function RiskBadge({ value, label, type = 'risk' }: RiskBadgeProps) {
  let severity: string;
  let displayLabel = label;

  if (type === 'risk') {
    if (value >= 80) severity = 'critical';
    else if (value >= 60) severity = 'high';
    else if (value >= 40) severity = 'medium';
    else severity = 'low';
    if (!displayLabel) displayLabel = `Risk: ${value}`;
  } else if (type === 'likelihood') {
    if (value >= 80) severity = 'critical';
    else if (value >= 60) severity = 'high';
    else if (value >= 30) severity = 'medium';
    else severity = 'low';
    if (!displayLabel) displayLabel = `Industrial: ${value}%`;
  } else {
    if (value >= 90) severity = 'monitored';
    else if (value >= 70) severity = 'high';
    else if (value >= 50) severity = 'medium';
    else severity = 'low';
    if (!displayLabel) displayLabel = `Confidence: ${value}%`;
  }

  return (
    <span className={`risk-badge risk-badge--${severity}`}>
      <span style={{ fontSize: '10px' }}>
        {severity === 'critical' ? '🔴' : severity === 'high' ? '🟠' : severity === 'medium' ? '🟡' : '🟢'}
      </span>
      {displayLabel}
    </span>
  );
}
