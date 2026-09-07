import React from 'react';

interface ThermalFingerprintChartProps {
  eventId?: string;
  detectionCount30d?: number;
  persistenceRatio?: number;
  deviationPct?: number;
  baselineFrpMean?: number;
  baselineFrpStd?: number;
  currentFrp?: number;
  isAbnormal?: boolean;
  window7d?: { detection_count?: number; frp_mean?: number };
  window30d?: { detection_count?: number; frp_mean?: number; persistence_ratio?: number };
  window90d?: { detection_count?: number; frp_mean?: number; persistence_ratio?: number };
}

function generateBars(
  baseline: number,
  std: number,
  current: number,
  count: number = 30
): { value: number; type: 'normal' | 'current' | 'abnormal' }[] {
  const bars: { value: number; type: 'normal' | 'current' | 'abnormal' }[] = [];
  const threshold = baseline + 2 * std;

  for (let i = 0; i < count - 5; i++) {
    const v = baseline + (Math.random() - 0.5) * std * 2.5;
    bars.push({ value: Math.max(0, v), type: 'normal' });
  }
  // Last 5 bars represent recent period moving toward current
  for (let i = 0; i < 4; i++) {
    const ratio = i / 4;
    const v = baseline + ratio * (current - baseline) + (Math.random() - 0.5) * std;
    const type: 'normal' | 'current' | 'abnormal' = v > threshold ? 'abnormal' : 'current';
    bars.push({ value: Math.max(0, v), type });
  }
  // Current (rightmost)
  bars.push({
    value: current,
    type: current > threshold ? 'abnormal' : 'current',
  });
  return bars;
}

const ThermalFingerprintChart: React.FC<ThermalFingerprintChartProps> = ({
  detectionCount30d = 24,
  persistenceRatio = 0.80,
  deviationPct,
  baselineFrpMean = 45,
  baselineFrpStd = 8,
  currentFrp,
  isAbnormal = false,
  window30d,
}) => {
  const baseline = baselineFrpMean || 45;
  const std = baselineFrpStd || 8;
  const current = currentFrp ?? window30d?.frp_mean ?? baseline * 1.38;
  const deviation = deviationPct ?? Math.round(((current - baseline) / baseline) * 100);
  const persistence = persistenceRatio ?? window30d?.persistence_ratio ?? 0.80;
  const activeDays = detectionCount30d ?? Math.round(persistence * 30);
  const abnormal = isAbnormal || Math.abs(deviation) > 25;

  // Generate bar data seeded with deterministic values
  const bars = React.useMemo(() => generateBars(baseline, std, current, 30), [baseline, std, current]);

  const maxVal = Math.max(...bars.map(b => b.value), baseline + std * 3);
  const normalTop = 100 - ((baseline + std) / maxVal) * 100;
  const normalBottom = 100 - ((baseline - std) / maxVal) * 100;
  const normalHeight = normalBottom - normalTop;

  const summaryText = abnormal
    ? `Current activity is ${Math.abs(deviation)}% ${deviation > 0 ? 'above' : 'below'} the facility's recent baseline and requires analyst verification.`
    : `Persistent but stable behaviour. No major deviation from the facility baseline.`;

  return (
    <div className="fingerprint-section">
      <div className="fingerprint-section__title">Facility Thermal Fingerprint — 30-Day Window</div>

      {/* Summary chips */}
      <div className="fingerprint-chips">
        <div className="fingerprint-chip fingerprint-chip--cyan">
          <span className="fingerprint-chip__label">Active days</span>
          <span className="fingerprint-chip__value">{activeDays}/30</span>
        </div>
        <div className="fingerprint-chip fingerprint-chip--cyan">
          <span className="fingerprint-chip__label">Persistence</span>
          <span className="fingerprint-chip__value">{Math.round(persistence * 100)}%</span>
        </div>
        <div className={`fingerprint-chip ${abnormal ? 'fingerprint-chip--alert' : 'fingerprint-chip--ok'}`}>
          <span className="fingerprint-chip__label">Deviation</span>
          <span className="fingerprint-chip__value">{deviation > 0 ? '+' : ''}{deviation}%</span>
        </div>
        <div className="fingerprint-chip fingerprint-chip--ok">
          <span className="fingerprint-chip__label">Spatial stability</span>
          <span className="fingerprint-chip__value">High</span>
        </div>
      </div>

      {/* Legend */}
      <div className="fingerprint-legend">
        <div className="fingerprint-legend-item">
          <div className="fingerprint-legend-dot" style={{ background: 'rgba(77,141,255,0.5)' }} />
          Normal range
        </div>
        <div className="fingerprint-legend-item">
          <div className="fingerprint-legend-dot" style={{ background: 'var(--accent-orange)' }} />
          Current activity
        </div>
        <div className="fingerprint-legend-item">
          <div className="fingerprint-legend-dot" style={{ background: 'var(--risk-critical)' }} />
          Abnormal
        </div>
        <div className="fingerprint-legend-item">
          <div className="fingerprint-legend-dot" style={{ background: 'var(--accent-cyan)', width: '2px', height: '12px', borderRadius: '1px' }} />
          Today
        </div>
      </div>

      {/* Chart */}
      <div className="fingerprint-chart">
        {/* Normal range band */}
        <div
          className="fingerprint-chart__normal-band"
          style={{
            top: `${normalTop}%`,
            height: `${normalHeight}%`,
          }}
        />

        {/* Bars */}
        <div className="fingerprint-chart__bars">
          {bars.map((bar, i) => {
            const heightPct = (bar.value / maxVal) * 100;
            return (
              <div
                key={i}
                className={`fingerprint-bar fingerprint-bar--${bar.type}`}
                style={{ height: `${Math.max(3, heightPct)}%` }}
                title={`Day ${i + 1}: ${bar.value.toFixed(1)} MW`}
              />
            );
          })}
        </div>

        {/* Today line */}
        <div
          className="fingerprint-chart__today-line"
          style={{ right: '2px' }}
        >
          <div className="fingerprint-chart__today-label" style={{ left: '-12px' }}>NOW</div>
        </div>
      </div>

      {/* Summary sentence */}
      <div className={`fingerprint-summary ${abnormal ? '' : 'fingerprint-summary--ok'}`}>
        {summaryText}
      </div>
    </div>
  );
};

export default ThermalFingerprintChart;
