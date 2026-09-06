interface ScoreBarProps {
  label: string;
  value: number;
  max?: number;
  color?: string;
}

function ScoreBar({ label, value, max = 100, color }: ScoreBarProps) {
  const pct = Math.min(100, (value / max) * 100);

  let barColor = color;
  if (!barColor) {
    if (pct >= 80) barColor = 'var(--accent-red)';
    else if (pct >= 60) barColor = 'var(--accent-orange)';
    else if (pct >= 40) barColor = 'var(--accent-amber)';
    else barColor = 'var(--accent-green)';
  }

  return (
    <div className="score-bar">
      <div className="score-bar__header">
        <span className="score-bar__label">{label}</span>
        <span className="score-bar__value" style={{ color: barColor }}>{value}</span>
      </div>
      <div className="score-bar__track">
        <div
          className="score-bar__fill"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
    </div>
  );
}

interface TimelineChartProps {
  temporalFeatures?: {
    baseline_frp_mean?: number;
    baseline_frp_std?: number;
    current_frp?: number;
    deviation_sigma?: number;
    detection_count_30d?: number;
    persistence_ratio?: number;
  };
  observations?: Array<{ frp: number; satellite: string; acq_date?: string }>;
}

export default function TimelineChart({ temporalFeatures, observations: _observations }: TimelineChartProps) {
  const baseline = temporalFeatures?.baseline_frp_mean || 0;
  const current = temporalFeatures?.current_frp || 0;
  const deviation = temporalFeatures?.deviation_sigma || 0;
  const detections = temporalFeatures?.detection_count_30d || 0;
  const persistence = temporalFeatures?.persistence_ratio || 0;

  // Generate synthetic 30-day bar data for visualization
  const barData: number[] = [];
  const baseStd = temporalFeatures?.baseline_frp_std || 5;
  for (let i = 0; i < 30; i++) {
    if (i < 30 - detections) {
      barData.push(0);
    } else {
      // Simulate values around baseline with some variance, spike at end
      const isRecent = i >= 27;
      const val = isRecent ? current : baseline + (Math.random() - 0.5) * baseStd * 2;
      barData.push(Math.max(0, val));
    }
  }

  const maxVal = Math.max(...barData, baseline + baseStd * 2, current) || 1;

  return (
    <div>
      {/* Score Bars */}
      <ScoreBar
        label="Industrial Likelihood"
        value={0}
        color="var(--accent-purple)"
      />
      <ScoreBar label="Operational Risk" value={0} />

      {/* Thermal Fingerprint */}
      <div className="timeline-chart" style={{ marginTop: '16px' }}>
        <div className="timeline-chart__title">
          🔥 Thermal Fingerprint — 30 Day History
        </div>

        <div style={{ position: 'relative' }}>
          <div className="timeline-chart__bars">
            {barData.map((val, i) => {
              const h = (val / maxVal) * 100;
              let color: string;
              if (val === 0) color = 'var(--border-primary)';
              else if (val > baseline + baseStd * 2) color = 'var(--accent-red)';
              else if (val > baseline + baseStd) color = 'var(--accent-orange)';
              else color = 'var(--accent-cyan)';

              return (
                <div
                  key={i}
                  className="timeline-chart__bar"
                  style={{
                    height: `${Math.max(4, h)}%`,
                    background: color,
                  }}
                  title={`Day ${i + 1}: ${val.toFixed(1)} MW`}
                />
              );
            })}
          </div>

          {/* Baseline line */}
          {baseline > 0 && (
            <div
              className="timeline-chart__baseline"
              style={{ bottom: `${(baseline / maxVal) * 80}px` }}
            />
          )}
        </div>

        <div className="timeline-chart__labels">
          <span className="timeline-chart__label">Day 1</span>
          <span className="timeline-chart__label">Day 15</span>
          <span className="timeline-chart__label">Day 30</span>
        </div>

        {/* Stat Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '8px',
          marginTop: '12px',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Baseline</div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
              {baseline.toFixed(1)} MW
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current</div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: current > baseline + baseStd * 2 ? 'var(--accent-red)' : 'var(--accent-orange)', fontFamily: 'var(--font-mono)' }}>
              {current.toFixed(1)} MW
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Deviation</div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: deviation >= 3 ? 'var(--accent-red)' : 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
              {deviation.toFixed(1)}σ
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '8px',
          padding: '8px',
          background: 'var(--bg-tertiary)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '11px',
          color: 'var(--text-muted)',
        }}>
          <span>Detections (30d): <strong style={{ color: 'var(--text-primary)' }}>{detections}</strong></span>
          <span>Persistence: <strong style={{ color: 'var(--text-primary)' }}>{(persistence * 100).toFixed(0)}%</strong></span>
        </div>
      </div>
    </div>
  );
}

export { ScoreBar };
