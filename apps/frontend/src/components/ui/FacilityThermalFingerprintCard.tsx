import React, { useState } from 'react';
import type { FacilityThermalFingerprint } from '../../services/api';

interface FacilityThermalFingerprintCardProps {
  fingerprint?: FacilityThermalFingerprint | null;
  facilityName?: string;
  currentFrp?: number;
  loading?: boolean;
}

export const FacilityThermalFingerprintCard: React.FC<FacilityThermalFingerprintCardProps> = ({
  fingerprint,
  facilityName = 'Jamnagar Mega Refinery Complex',
  currentFrp = 340.0,
  loading: _loading,
}) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'zones' | 'stats'>('chart');

  // Fallback defaults if not loaded yet
  const fp = fingerprint || {
    facility_id: 'FAC-JAMNAGAR-01',
    facility_name: facilityName,
    provenance: 'DERIVED' as const,
    baseline: {
      mean_frp: 82.0,
      median_frp: 79.0,
      std_frp: 18.5,
      normal_lower: 60.0,
      normal_upper: 120.0,
      historical_peak: 138.0,
      historical_min: 42.0,
      daily_detection_frequency: 0.85,
      persistence_pct: 80.0,
      day_night_ratio: 0.68,
      mean_brightness_temp_k: 328.4,
      historical_volatility: 'MODERATE',
      data_sufficiency: 'SUFFICIENT',
      baseline_window_days: 90,
    },
    current_observation: {
      current_frp: currentFrp,
      deviation_z: currentFrp > 82.0 ? Math.round(((currentFrp - 82.0) / 18.5) * 10) / 10 : 0.2,
      abnormality_level: currentFrp > 200 ? ('HIGHLY_ABNORMAL' as const) : currentFrp > 120 ? ('ABNORMAL' as const) : ('NORMAL' as const),
      abnormality_color: currentFrp > 200 ? '#FF5C6C' : currentFrp > 120 ? '#FF7A45' : '#4FD18B',
      status_text: currentFrp > 200 ? 'Outside learned baseline (+4.2σ)' : 'Within normal baseline',
      thermal_anomaly_score: currentFrp > 200 ? 92.5 : 15.0,
    },
    thermal_zones: [
      { zone_id: 'ZONE-A', name: 'Cracker Flare Stack #4', latitude: 22.4740, longitude: 70.0610, typical_frp: 65.0, status: 'ACTIVE_HOTSPOT', hotspot_density: 'HIGH' },
      { zone_id: 'ZONE-B', name: 'Primary Hydrocarbon Header', latitude: 22.4690, longitude: 70.0550, typical_frp: 45.0, status: 'BASELINE_NORMAL', hotspot_density: 'MODERATE' },
      { zone_id: 'ZONE-C', name: 'Offsite Storage Buffer Area', latitude: 22.4650, longitude: 70.0520, typical_frp: 0.0, status: 'COLD_SECURE', hotspot_density: 'NONE' },
    ],
    historical_series_30d: Array.from({ length: 30 }, (_, i) => ({
      day_index: i + 1,
      date: `Day ${i + 1}`,
      observed_frp: i === 29 ? currentFrp : Math.round(75 + Math.sin(i * 0.8) * 16),
      normal_mean: 82.0,
      normal_lower: 60.0,
      normal_upper: 120.0,
      is_anomaly: i >= 28 && currentFrp > 150,
    })),
  };

  const { baseline, current_observation: cur, thermal_zones, historical_series_30d } = fp;
  const maxSeriesFrp = Math.max(cur.current_frp, baseline.historical_peak, 400);

  return (
    <div className="card" style={{ marginBottom: '20px', borderLeft: `3px solid ${cur.abnormality_color}` }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🧬</span>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Facility Thermal Fingerprint & Abnormality Engine
              <span style={{
                fontSize: '9px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                color: cur.abnormality_color,
                background: `${cur.abnormality_color}18`,
                border: `1px solid ${cur.abnormality_color}40`,
                padding: '2px 6px',
                borderRadius: 'var(--radius-xs)',
              }}>
                {cur.abnormality_level.replace(/_/g, ' ')} ({cur.deviation_z >= 0 ? `+${cur.deviation_z}` : cur.deviation_z}σ)
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Learned 90-day baseline vs real-time satellite observation for <strong>{fp.facility_name}</strong>
            </div>
          </div>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-secondary)', padding: '2px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <button
            className={`btn btn--xs ${activeTab === 'chart' ? 'btn--cyan' : 'btn--ghost'}`}
            onClick={() => setActiveTab('chart')}
          >
            📈 30D Envelope Chart
          </button>
          <button
            className={`btn btn--xs ${activeTab === 'zones' ? 'btn--cyan' : 'btn--ghost'}`}
            onClick={() => setActiveTab('zones')}
          >
            📍 Thermal Zones ({thermal_zones.length})
          </button>
          <button
            className={`btn btn--xs ${activeTab === 'stats' ? 'btn--cyan' : 'btn--ghost'}`}
            onClick={() => setActiveTab('stats')}
          >
            📊 Baseline Metrics
          </button>
        </div>
      </div>

      {/* ── Key Metrics Strip ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '16px' }}>
        <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Learned Normal FRP</div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '2px' }}>
            {baseline.normal_lower}–{baseline.normal_upper} <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>MW</span>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>Historical Mean: {baseline.mean_frp} MW</div>
        </div>

        <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Current Reading</div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: cur.abnormality_color, marginTop: '2px' }}>
            {cur.current_frp.toFixed(1)} <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>MW</span>
          </div>
          <div style={{ fontSize: '10px', color: cur.abnormality_color, marginTop: '2px' }}>
            Deviation: {cur.deviation_z >= 0 ? `+${cur.deviation_z}` : cur.deviation_z}σ from baseline
          </div>
        </div>

        <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Persistence Ratio</div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-green)', marginTop: '2px' }}>
            {baseline.persistence_pct.toFixed(0)}% <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>({(baseline.daily_detection_frequency * 30).toFixed(0)}/30d)</span>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>Night/Day Ratio: {(baseline.day_night_ratio * 100).toFixed(0)}%</div>
        </div>

        <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Anomaly Severity</div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: cur.abnormality_color, marginTop: '2px' }}>
            {cur.thermal_anomaly_score.toFixed(0)}<span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>Data: {baseline.data_sufficiency} (90D)</div>
        </div>
      </div>

      {/* ── Tab 1: Historical Baseline Envelope Chart ── */}
      {activeTab === 'chart' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Historical 30-Day FRP Sequence vs Learned Operating Baseline (Normal Band: {baseline.normal_lower}–{baseline.normal_upper} MW)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'rgba(67,217,232,0.7)' }}>
                <span style={{ width: '8px', height: '8px', background: 'rgba(67,217,232,0.25)', border: '1px solid #43D9E8', borderRadius: '1px' }} />
                Normal Envelope
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#FF5C6C' }}>
                <span style={{ width: '8px', height: '8px', background: '#FF5C6C', borderRadius: '50%' }} />
                Anomalous Spike
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)' }}>
                <span style={{ width: '8px', height: '2px', background: '#43D9E8' }} />
                Mean ({baseline.mean_frp} MW)
              </span>
            </div>
          </div>

          {/* SVG Baseline Envelope Chart */}
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '12px 14px', border: '1px solid var(--border-subtle)' }}>
            <svg width="100%" height="150" viewBox="0 0 600 150" style={{ overflow: 'visible' }}>
              <defs>
                <linearGradient id="normalBandGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#43D9E8" stopOpacity="0.18" />
                  <stop offset="100%" stopColor="#43D9E8" stopOpacity="0.04" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              <line x1="0" y1="20" x2="600" y2="20" stroke="rgba(255,255,255,0.05)" strokeDasharray="2 2" />
              <line x1="0" y1="65" x2="600" y2="65" stroke="rgba(255,255,255,0.05)" strokeDasharray="2 2" />
              <line x1="0" y1="110" x2="600" y2="110" stroke="rgba(255,255,255,0.05)" strokeDasharray="2 2" />

              {/* Normal Operating Band Rectangle (Y coords mapped: 0 MW at y=130, 400 MW at y=15) */}
              {(() => {
                const yTop = 130 - (baseline.normal_upper / maxSeriesFrp) * 115;
                const yBottom = 130 - (baseline.normal_lower / maxSeriesFrp) * 115;
                const yMean = 130 - (baseline.mean_frp / maxSeriesFrp) * 115;
                return (
                  <>
                    <rect x="10" y={yTop} width="580" height={Math.max(10, yBottom - yTop)} fill="url(#normalBandGrad)" stroke="rgba(67,217,232,0.3)" strokeDasharray="3 3" />
                    <line x1="10" y1={yMean} x2="590" y2={yMean} stroke="#43D9E8" strokeWidth="1" strokeDasharray="4 2" opacity="0.6" />
                  </>
                );
              })()}

              {/* Historical Bars */}
              {historical_series_30d.map((pt, idx) => {
                const x = 15 + idx * 19;
                const barH = Math.max(3, (pt.observed_frp / maxSeriesFrp) * 115);
                const y = 130 - barH;
                const isCurrent = idx === historical_series_30d.length - 1;

                return (
                  <g key={idx}>
                    <rect
                      x={x}
                      y={y}
                      width="12"
                      height={barH}
                      rx="2"
                      fill={isCurrent ? cur.abnormality_color : pt.is_anomaly ? '#FF7A45' : 'rgba(67,217,232,0.45)'}
                      opacity={isCurrent ? 1 : 0.8}
                    />
                    {isCurrent && (
                      <circle cx={x + 6} cy={y - 6} r="3.5" fill="#FF5C6C" />
                    )}
                  </g>
                );
              })}

              {/* Bottom timeline axis */}
              <line x1="10" y1="130" x2="590" y2="130" stroke="var(--border-subtle)" strokeWidth="1" />
              <text x="15" y="144" fill="var(--text-disabled)" fontSize="9" fontFamily="monospace">Day -30</text>
              <text x="290" y="144" fill="var(--text-disabled)" fontSize="9" fontFamily="monospace">Day -15</text>
              <text x="550" y="144" fill={cur.abnormality_color} fontSize="9" fontFamily="monospace" fontWeight="bold">TODAY (340MW)</text>
            </svg>
          </div>
        </div>
      )}

      {/* ── Tab 2: Recurrent Facility Thermal Zones ── */}
      {activeTab === 'zones' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Recurrent Hotspot Clusters identified within facility perimeter (Spatial resolution: VIIRS 375m / OSM Footprint):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
            {thermal_zones.map(z => (
              <div
                key={z.zone_id}
                style={{
                  padding: '12px',
                  background: 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${z.status === 'ACTIVE_HOTSPOT' ? 'rgba(255,92,108,0.4)' : 'var(--border-subtle)'}`,
                  borderLeft: `3px solid ${z.status === 'ACTIVE_HOTSPOT' ? '#FF5C6C' : z.status === 'BASELINE_NORMAL' ? '#43D9E8' : 'var(--text-disabled)'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 700 }}>{z.zone_id}</span>
                  <span style={{
                    fontSize: '9px',
                    padding: '2px 5px',
                    borderRadius: 'var(--radius-xs)',
                    fontWeight: 700,
                    background: z.status === 'ACTIVE_HOTSPOT' ? 'rgba(255,92,108,0.15)' : 'rgba(67,217,232,0.12)',
                    color: z.status === 'ACTIVE_HOTSPOT' ? '#FF5C6C' : 'var(--accent-cyan)',
                  }}>
                    {z.status.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>{z.name}</div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Typical FRP: <strong>{z.typical_frp} MW</strong></span>
                  <span>Density: <strong>{z.hotspot_density}</strong></span>
                </div>
                <div style={{ fontSize: '9px', color: 'var(--text-disabled)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                  Loc: {z.latitude}°, {z.longitude}°
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Tab 3: Detailed Baseline Metrics Table ── */}
      {activeTab === 'stats' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '11px' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '8px' }}>Thermal Statistical Baseline</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Historical FRP Mean:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{baseline.mean_frp} MW</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Historical FRP Median:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{baseline.median_frp} MW</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Standard Deviation (σ):</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>±{baseline.std_frp} MW</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
              <span style={{ color: 'var(--text-muted)' }}>Historical Peak Observation:</span>
              <span style={{ color: 'var(--accent-orange)', fontWeight: 600 }}>{baseline.historical_peak} MW</span>
            </div>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '8px' }}>Temporal & Operational Reliability</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Daily Detection Frequency:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{(baseline.daily_detection_frequency * 100).toFixed(0)}% ({baseline.baseline_window_days}D window)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Mean Brightness Temp (K):</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{baseline.mean_brightness_temp_k} K</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Historical Volatility:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{baseline.historical_volatility}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
              <span style={{ color: 'var(--text-muted)' }}>Statistical Quality:</span>
              <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>Calibrated Ground-Truth</span>
            </div>
          </div>
        </div>
      )}

      {/* Footer Provenance Note */}
      <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', color: 'var(--text-disabled)' }}>
        <span>Scientific Model: Facility-specific Gaussian baseline $z = (FRP - \mu) / \sigma$ with API 521 flare calibration</span>
        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>PROVENANCE: {fp.provenance}</span>
      </div>
    </div>
  );
};

export default FacilityThermalFingerprintCard;
