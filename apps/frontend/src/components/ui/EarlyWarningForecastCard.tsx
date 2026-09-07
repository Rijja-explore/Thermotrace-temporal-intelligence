import React from 'react';
import type { EarlyWarningForecast } from '../../services/api';
import { TrendingUp, AlertTriangle, ShieldAlert, Activity, ArrowUpRight, Info } from 'lucide-react';

interface EarlyWarningForecastCardProps {
  forecast?: EarlyWarningForecast | null;
  loading?: boolean;
}

export const EarlyWarningForecastCard: React.FC<EarlyWarningForecastCardProps> = ({ forecast, loading }) => {
  if (loading) {
    return (
      <div className="card skeleton" style={{ height: '220px', marginBottom: '20px' }}>
        <div style={{ height: '100%' }} />
      </div>
    );
  }

  if (!forecast) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', marginBottom: '20px' }}>
        No early warning data available for this event.
      </div>
    );
  }

  const {
    escalation_state,
    early_warning_level,
    warning_color,
    escalation_score,
    thermal_trend: _thermal_trend,
    trend_slope_mw_per_day,
    frp_acceleration,
    consecutive_anomalies,
    forecast_confidence,
    forecast_model_type,
    explanation,
    forecast_series,
    provenance,
  } = forecast;

  const points = forecast_series || [];
  const maxFrp = Math.max(...points.map(p => Math.max(p.frp, p.upper_bound || p.frp)), 100) * 1.15;
  const minFrp = 0;
  const chartW = 500;
  const chartH = 150;
  const padX = 40;
  const padY = 20;

  const getX = (idx: number) => padX + (idx / Math.max(points.length - 1, 1)) * (chartW - 2 * padX);
  const getY = (val: number) => chartH - padY - ((val - minFrp) / (maxFrp - minFrp)) * (chartH - 2 * padY);

  const histPoints = points.map((p, idx) => ({ ...p, x: getX(idx), y: getY(p.frp) }));
  const splitIdx = points.findIndex(p => p.type === 'CURRENT_OBSERVED');
  const histSlice = splitIdx >= 0 ? histPoints.slice(0, splitIdx + 1) : histPoints;
  const foreSlice = splitIdx >= 0 ? histPoints.slice(splitIdx) : [];

  const histLinePath = histSlice.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const foreLinePath = foreSlice.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  const upperPath = foreSlice.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${getY(p.upper_bound)}`).join(' ');
  const lowerPathRev = [...foreSlice].reverse().map(p => `L ${p.x} ${getY(p.lower_bound)}`).join(' ');
  const corridorPath = foreSlice.length > 1 ? `${upperPath} ${lowerPathRev} Z` : '';

  const getBadgeStyle = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return { color: 'var(--risk-critical)', bg: 'rgba(255, 92, 108, 0.15)', border: 'rgba(255, 92, 108, 0.35)' };
      case 'ESCALATING':
        return { color: 'var(--risk-high)', bg: 'rgba(255, 122, 69, 0.15)', border: 'rgba(255, 122, 69, 0.35)' };
      case 'WATCH':
        return { color: 'var(--accent-amber)', bg: 'rgba(255, 181, 71, 0.15)', border: 'rgba(255, 181, 71, 0.35)' };
      default:
        return { color: 'var(--accent-green)', bg: 'rgba(79, 209, 139, 0.15)', border: 'rgba(79, 209, 139, 0.35)' };
    }
  };

  const badgeStyle = getBadgeStyle(early_warning_level);

  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-md)',
        marginBottom: '20px',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 18px',
          background: 'var(--bg-primary)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(255, 92, 108, 0.12)',
              border: '1px solid rgba(255, 92, 108, 0.3)',
              color: 'var(--risk-critical)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <TrendingUp size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}
              >
                Early Warning & Escalation Forecast
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 800,
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'rgba(67, 217, 232, 0.12)',
                  color: 'var(--accent-cyan)',
                  border: '1px solid rgba(67, 217, 232, 0.3)',
                }}
              >
                MODULE B
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'rgba(167, 139, 250, 0.12)',
                  color: 'var(--accent-purple)',
                  border: '1px solid rgba(167, 139, 250, 0.3)',
                }}
              >
                {provenance || 'DERIVED'}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Temporal sequence velocity, FRP acceleration & 48h trend corridor
            </div>
          </div>
        </div>

        <span
          style={{
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            textTransform: 'uppercase',
            color: badgeStyle.color,
            background: badgeStyle.bg,
            border: `1px solid ${badgeStyle.border}`,
          }}
        >
          {escalation_state.replace('_', ' ')}
        </span>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Metric Strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Activity size={13} color="var(--accent-cyan)" />
              Escalation Score
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {escalation_score}
              </span>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>/ 100</span>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', marginTop: '8px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, escalation_score)}%`,
                  background: warning_color || 'var(--risk-critical)',
                  borderRadius: '2px',
                }}
              />
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <ArrowUpRight size={13} color="var(--accent-amber)" />
              Trend Slope
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: trend_slope_mw_per_day > 0 ? 'var(--risk-critical)' : 'var(--accent-green)' }}>
                {trend_slope_mw_per_day > 0 ? `+${trend_slope_mw_per_day}` : trend_slope_mw_per_day}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>MW / d</span>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
              Acc: <strong style={{ color: 'var(--text-secondary)' }}>{frp_acceleration > 0 ? `+${frp_acceleration}` : frp_acceleration} MW/d²</strong>
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <AlertTriangle size={13} color="var(--risk-high)" />
              Consecutive Hits
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--risk-high)' }}>
                {consecutive_anomalies}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>passes</span>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Sustained breach
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <ShieldAlert size={13} color="var(--accent-green)" />
              Confidence
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                {Math.round(forecast_confidence * 100)}%
              </span>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
              BiLSTM Enriched
            </div>
          </div>
        </div>

        {/* Forecast Projection Chart */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={13} color="var(--accent-cyan)" />
              Thermal Trajectory & 48h Escalation Corridor
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '10px', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '8px', height: '2px', background: 'var(--accent-cyan)', display: 'inline-block' }} /> Historical
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--risk-critical)', display: 'inline-block' }} /> Current
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '8px', height: '2px', background: 'var(--accent-amber)', display: 'inline-block' }} /> Forecast (T+48h)
              </span>
            </div>
          </div>

          <div style={{ width: '100%', overflowX: 'auto' }}>
            <svg viewBox={`0 0 ${chartW} ${chartH}`} style={{ width: '100%', height: '160px', display: 'block' }}>
              <defs>
                <linearGradient id="corridorGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.05" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              {[0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
                const y = padY + ratio * (chartH - 2 * padY);
                const val = Math.round(maxFrp - ratio * (maxFrp - minFrp));
                return (
                  <g key={i}>
                    <line x1={padX} y1={y} x2={chartW - padX} y2={y} stroke="#233B56" strokeDasharray="3 3" />
                    <text x={padX - 6} y={y + 3} fill="#71869B" fontSize="9" textAnchor="end" fontFamily="var(--font-mono)">
                      {val}M
                    </text>
                  </g>
                );
              })}

              {/* Forecast corridor polygon */}
              {corridorPath && <path d={corridorPath} fill="url(#corridorGrad)" />}

              {/* Historical line */}
              {histLinePath && (
                <path d={histLinePath} fill="none" stroke="var(--accent-cyan)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              )}

              {/* Forecast dashed line */}
              {foreLinePath && (
                <path
                  d={foreLinePath}
                  fill="none"
                  stroke="var(--accent-amber)"
                  strokeWidth="2.5"
                  strokeDasharray="4 4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* Data points */}
              {points.map((p, idx) => {
                const cx = getX(idx);
                const cy = getY(p.frp);
                const isCurrent = p.type === 'CURRENT_OBSERVED';
                const isForecast = p.type === 'FORECAST';

                return (
                  <g key={idx}>
                    {isCurrent && (
                      <circle cx={cx} cy={cy} r="8" fill="var(--risk-critical)" fillOpacity="0.25" />
                    )}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isCurrent ? 4.5 : isForecast ? 4 : 3}
                      fill={isCurrent ? 'var(--risk-critical)' : isForecast ? 'var(--accent-amber)' : 'var(--accent-cyan)'}
                      stroke="var(--bg-void)"
                      strokeWidth="1.5"
                    />
                    <text
                      x={cx}
                      y={cy - 8}
                      fill={isCurrent ? 'var(--risk-critical)' : isForecast ? 'var(--accent-amber)' : 'var(--text-secondary)'}
                      fontSize="9"
                      fontWeight={isCurrent ? 'bold' : 'normal'}
                      textAnchor="middle"
                      fontFamily="var(--font-mono)"
                    >
                      {Math.round(p.frp)} MW
                    </text>
                    <text
                      x={cx}
                      y={chartH - 4}
                      fill="var(--text-muted)"
                      fontSize="9"
                      textAnchor="middle"
                      fontFamily="var(--font-mono)"
                    >
                      {p.timestamp}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Diagnosis Note */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
          }}
        >
          <Info size={15} color="var(--accent-cyan)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--text-primary)' }}>Temporal Diagnosis: </strong>
            {explanation}
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Methodology: {forecast_model_type}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
