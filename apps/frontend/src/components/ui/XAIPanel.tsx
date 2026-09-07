import React, { useState } from 'react';

interface ShapFeature {
  feature: string;
  category: string;
  value: string;
  shapWeight: number;
  impact: 'elevates_risk' | 'lowers_risk';
  description: string;
}

interface XAIPanelProps {
  eventId?: string;
  frp?: number;
  confidence?: number;
  label?: string;
  features?: ShapFeature[];
}

const DEFAULT_FEATURES: ShapFeature[] = [
  { feature: 'FRP Radiant Power Surge', category: 'Thermal · NASA VIIRS', value: '340.0 MW (+4.2σ)', shapWeight: 0.34, impact: 'elevates_risk', description: 'Extreme thermal output far exceeds normal steady-state flaring (median 65 MW). This is the strongest single contributor to the critical risk score.' },
  { feature: 'Multi-Day Temporal Persistence', category: 'Temporal Memory', value: '24/30 Days (80%)', shapWeight: 0.28, impact: 'elevates_risk', description: 'High repeatability across satellite orbits strongly indicates a fixed industrial infrastructure source rather than a moving wildfire.' },
  { feature: 'Industrial Facility Proximity', category: 'Geospatial · OSM', value: '180 m from Stack #4', shapWeight: 0.22, impact: 'elevates_risk', description: 'High spatial alignment with registered hydrocarbon processing boundary in ISRO/OSM database.' },
  { feature: 'Nighttime Detection Ratio', category: 'Diurnal Cycle · VIIRS NRT', value: '68% Night Passes', shapWeight: 0.16, impact: 'elevates_risk', description: 'Nighttime thermal signatures confirm continuous 24/7 industrial operations; agricultural fires typically cease at dusk.' },
  { feature: 'ESA WorldCover Land Class', category: 'Land Cover 10m', value: '88% Industrial Built-up', shapWeight: 0.12, impact: 'elevates_risk', description: 'Negligible vegetation / cropland within 500m radius completely rules out crop stubble burning.' },
  { feature: 'Wind Dispersion Vector', category: 'Meteorology · ECMWF', value: '25 km/h at 210° SW', shapWeight: -0.06, impact: 'lowers_risk', description: 'Moderate prevailing crosswind slightly dilutes ground-level radiant heat concentration.' },
];

const maxAbs = Math.max(...DEFAULT_FEATURES.map(f => Math.abs(f.shapWeight)));

const XAIPanel: React.FC<XAIPanelProps> = ({
  eventId = 'TT-CASE-001',
  frp: _frp = 340.0,
  confidence = 84,
  label = 'Confirmed Industrial Fire',
  features = DEFAULT_FEATURES,
}) => {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'shap' | 'counterfactual' | 'attention' | 'intelligence-xai'>('shap');

  const positiveSum = features.filter(f => f.impact === 'elevates_risk').reduce((s, f) => s + f.shapWeight, 0);
  const negativeSum = Math.abs(features.filter(f => f.impact === 'lowers_risk').reduce((s, f) => s + f.shapWeight, 0));

  return (
    <div className="xai-inline-panel">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-purple)', background: 'rgba(167,139,250,0.12)', border: '1px solid rgba(167,139,250,0.3)', padding: '2px 8px', borderRadius: 'var(--radius-xs)' }}>
              🤖 XAI ENGINE v2 · SHAP + LIME
            </span>
            <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{eventId}</span>
          </div>
          <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>
            Explainable AI — Why This Classification?
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Model decision breakdown for <strong style={{ color: 'var(--accent-cyan)' }}>{label}</strong> · Confidence: <strong style={{ color: confidence >= 70 ? 'var(--accent-red)' : 'var(--accent-amber)' }}>{confidence}/100</strong>
          </div>
        </div>

        {/* Confidence donut visual */}
        <div style={{ textAlign: 'center', flexShrink: 0 }}>
          <svg width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
            <circle
              cx="32" cy="32" r="26"
              fill="none"
              stroke={confidence >= 70 ? '#FF5C6C' : confidence >= 50 ? '#FFB547' : '#43D9E8'}
              strokeWidth="8"
              strokeDasharray={`${(confidence / 100) * 163.4} 163.4`}
              strokeLinecap="round"
              transform="rotate(-90 32 32)"
            />
            <text x="32" y="36" textAnchor="middle" fill="var(--text-primary)" fontSize="14" fontWeight="800">{confidence}</text>
          </svg>
          <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '2px' }}>RISK SCORE</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px' }}>
        {(['shap', 'counterfactual', 'attention', 'intelligence-xai'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 600,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              cursor: 'pointer',
              transition: 'all 0.15s',
              background: activeTab === tab ? 'rgba(67,217,232,0.15)' : 'transparent',
              borderColor: activeTab === tab ? 'rgba(67,217,232,0.4)' : 'rgba(255,255,255,0.08)',
              color: activeTab === tab ? 'var(--accent-cyan)' : 'var(--text-muted)',
            }}
          >
            {tab === 'shap'
              ? '📊 SHAP Features'
              : tab === 'counterfactual'
              ? '🔄 Counterfactuals'
              : tab === 'attention'
              ? '⏱ Temporal Attention'
              : '💡 Why Abnormal & Escalating?'}
          </button>
        ))}
      </div>

      {/* Tab: SHAP */}
      {activeTab === 'shap' && (
        <div>
          {/* Summary bar */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ flex: 1, padding: '10px 12px', background: 'rgba(255,92,108,0.08)', border: '1px solid rgba(255,92,108,0.2)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '9px', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>↑ RISK-ELEVATING FACTORS</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-red)' }}>+{positiveSum.toFixed(2)}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>cumulative SHAP weight</div>
            </div>
            <div style={{ flex: 1, padding: '10px 12px', background: 'rgba(79,209,139,0.08)', border: '1px solid rgba(79,209,139,0.2)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '9px', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>↓ RISK-LOWERING FACTORS</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-green)' }}>−{negativeSum.toFixed(2)}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>cumulative SHAP weight</div>
            </div>
            <div style={{ flex: 1, padding: '10px 12px', background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '9px', color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>MODEL FEATURES USED</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-purple)' }}>{features.length}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>across 4 data modalities</div>
            </div>
          </div>

          {/* Column headers */}
          <div style={{ display: 'grid', gridTemplateColumns: '190px 1fr 55px 80px', gap: '10px', fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-disabled)', marginBottom: '6px', padding: '0 2px' }}>
            <span>FEATURE</span>
            <span>SHAP WEIGHT ← LOWERS · ELEVATES →</span>
            <span style={{ textAlign: 'right' }}>WEIGHT</span>
            <span style={{ textAlign: 'center' }}>IMPACT</span>
          </div>

          {/* SHAP bars */}
          {features.map((f, i) => {
            const barPct = (Math.abs(f.shapWeight) / maxAbs) * 100;
            const isExpanded = expandedIdx === i;
            return (
              <div key={i} style={{ marginBottom: '2px' }}>
                <div
                  className="xai-shap-bar-row"
                  style={{ cursor: 'pointer', borderRadius: isExpanded ? 'var(--radius-xs) var(--radius-xs) 0 0' : 'var(--radius-xs)', padding: '8px 2px', background: isExpanded ? 'rgba(255,255,255,0.03)' : 'transparent' }}
                  onClick={() => setExpandedIdx(isExpanded ? null : i)}
                >
                  <div>
                    <div className="xai-shap-feature-name" style={{ marginBottom: '1px' }}>{f.feature}</div>
                    <div style={{ fontSize: '9px', color: 'var(--text-disabled)', fontFamily: 'var(--font-mono)' }}>{f.category}</div>
                  </div>
                  <div className="xai-shap-track">
                    <div
                      className={`xai-shap-fill xai-shap-fill--${f.impact === 'elevates_risk' ? 'positive' : 'negative'}`}
                      style={{ width: `${barPct}%` }}
                    />
                  </div>
                  <span className={`xai-shap-weight xai-shap-weight--${f.shapWeight > 0 ? 'positive' : 'negative'}`}>
                    {f.shapWeight > 0 ? '+' : ''}{f.shapWeight.toFixed(2)}
                  </span>
                  <span className={`xai-shap-impact-pill xai-shap-impact-pill--${f.impact === 'elevates_risk' ? 'elevates' : 'lowers'}`}>
                    {f.impact === 'elevates_risk' ? '↑ RISK' : '↓ RISK'}
                  </span>
                </div>
                {isExpanded && (
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderTop: 'none', borderRadius: '0 0 var(--radius-xs) var(--radius-xs)', padding: '10px 12px', animation: 'fadeIn 0.15s ease-out' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                      <div>
                        <div style={{ fontSize: '9px', color: 'var(--text-disabled)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>OBSERVED VALUE</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{f.value}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '9px', color: 'var(--text-disabled)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>ATTRIBUTION</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: f.shapWeight > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                          {f.impact === 'elevates_risk' ? 'Elevates risk classification' : 'Reduces risk classification'}
                        </div>
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{f.description}</div>
                  </div>
                )}
              </div>
            );
          })}

          <div style={{ fontSize: '10px', color: 'var(--text-disabled)', marginTop: '12px', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
            SHAP TreeExplainer · XGBoost v1.7 · Model v2.1.4 · Click any row to expand
          </div>
        </div>
      )}

      {/* Tab: Counterfactuals */}
      {activeTab === 'counterfactual' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px', lineHeight: 1.5 }}>
            Counterfactual explanations show <strong>what would have to change</strong> in the input data for the model to produce a <strong>different classification</strong>. These are generated using a DiCE (Diverse Counterfactual Explanations) approach.
          </div>
          {[
            { target: 'Normal Industrial Steady-State Flaring', condition: 'Reduce FRP from 340 MW to < 85 MW via Flare Gas Recovery (FGRS)', feasibility: 'Actionable (Operator Valve Divert)', delta: '84/100 CRITICAL → 28/100 NOMINAL', color: 'var(--accent-green)' },
            { target: 'Transient Agricultural / Crop Stubble Burn', condition: 'Persistence ratio drops from 80% to < 15% AND facility distance > 2.5 km', feasibility: 'Structural (Non-industrial environment)', delta: 'Reclassifies event with 91% confidence', color: 'var(--accent-amber)' },
            { target: 'Sensor False Alarm / Solar Glint', condition: 'ΔT4-11 < 8.0 K AND solar zenith angle within glint cone (< 15°)', feasibility: 'Sensor artifact condition', delta: 'Flags detection as invalid with 99% certainty', color: 'var(--accent-purple)' },
          ].map((cf, i) => (
            <div key={i} style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderLeft: `3px solid ${cf.color}`, borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: cf.color, marginBottom: '8px' }}>
                If Instead: <span style={{ color: 'var(--text-primary)' }}>{cf.target}</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                <strong>Condition required:</strong> {cf.condition}
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '11px' }}>
                <div>
                  <span style={{ color: 'var(--text-disabled)' }}>Feasibility: </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{cf.feasibility}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-disabled)' }}>Outcome: </span>
                  <span style={{ color: cf.color, fontWeight: 600 }}>{cf.delta}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Temporal Attention */}
      {activeTab === 'attention' && (
        <div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
            The LSTM temporal attention layer learns to focus on the <strong>most diagnostically relevant time windows</strong> in the 30-day observation history. Higher attention weight → stronger influence on the final classification.
          </div>
          {/* Attention heatmap mock */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(30, 1fr)', gap: '3px', marginBottom: '8px' }}>
            {Array.from({ length: 30 }, (_, i) => {
              // Simulate attention peaks at days 2, 7, 15, 22, 28
              const peaks = [2, 7, 15, 22, 28];
              const isPeak = peaks.includes(i);
              const base = 0.1 + Math.random() * 0.2;
              const attn = isPeak ? 0.7 + Math.random() * 0.3 : base;
              const alpha = Math.min(1, attn);
              return (
                <div
                  key={i}
                  title={`Day ${i + 1}: Attention = ${attn.toFixed(2)}`}
                  style={{
                    height: '28px',
                    borderRadius: '2px',
                    background: isPeak
                      ? `rgba(255, 92, 108, ${alpha})`
                      : `rgba(67, 217, 232, ${alpha * 0.6})`,
                    transition: 'transform 0.1s',
                    cursor: 'pointer',
                  }}
                />
              );
            })}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-disabled)', fontFamily: 'var(--font-mono)', marginBottom: '16px' }}>
            <span>Day 1 (T-30)</span>
            <span>← 30-Day Observation Window →</span>
            <span>Day 30 (Now)</span>
          </div>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '12px', height: '12px', background: 'rgba(255,92,108,0.7)', borderRadius: '2px', display: 'inline-block' }} />High Attention (Peak Event Days)</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '12px', height: '12px', background: 'rgba(67,217,232,0.4)', borderRadius: '2px', display: 'inline-block' }} />Baseline Monitoring</span>
          </div>
          <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 'var(--radius-sm)', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--accent-purple)' }}>Model architecture:</strong> Bidirectional LSTM (128 hidden units) with scaled dot-product attention mechanism. The model assigns attention weights to each day in the 30-day window. Peak attention on days with anomalous FRP surges (&gt;+2σ) confirms the system is correctly focusing on thermally significant satellite passes.
          </div>
        </div>
      )}

      {/* Tab: 3-Way Intelligence XAI */}
      {activeTab === 'intelligence-xai' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Question 1 */}
          <div style={{ padding: '14px 16px', background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#FF5C6C' }}>1. Why is this event abnormal?</span>
              <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: '4px', background: 'rgba(239,68,68,0.2)', color: '#FF8A96' }}>+4.2σ DEVIATION</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Current observed FRP of <strong style={{ color: '#FFF' }}>340.0 MW</strong> exceeds the learned facility historical baseline mean of <strong style={{ color: 'var(--accent-cyan)' }}>82.0 MW</strong> (normal band: 60–120 MW) by <strong>4.2 standard deviations (p &lt; 0.0001)</strong>. Spatial clustering indicates heat flux concentrated in Cracker Flare Stack #4 exceeding typical diurnal flaring limits.
            </div>
          </div>

          {/* Question 2 */}
          <div style={{ padding: '14px 16px', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#F59E0B' }}>2. Why is it escalating?</span>
              <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: '4px', background: 'rgba(245,158,11,0.2)', color: '#FCD34D' }}>VELOCITY: +42.5 MW/DAY</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Temporal derivative analysis across the last 4 consecutive satellite passes shows positive slope (<strong style={{ color: '#F59E0B' }}>+42.5 MW/day</strong>) and positive acceleration (<strong style={{ color: '#F59E0B' }}>+14.2 MW/d²</strong>). This continuous growth pattern satisfies the criteria for <strong style={{ color: '#FFF' }}>CRITICAL_ESCALATION</strong>, indicating uncontained combustible venting rather than a stable planned process.
            </div>
          </div>

          {/* Question 3 */}
          <div style={{ padding: '14px 16px', background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#A78BFA' }}>3. Why is incident priority ranked CRITICAL?</span>
              <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: '4px', background: 'rgba(167,139,250,0.2)', color: '#DDD6FE' }}>UNIFIED RISK MATRIX</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Incident priority synthesizes 4 quantitative risk layers: <strong>High Fire Probability (89%)</strong> + <strong>Severe Baseline Deviation (+4.2σ)</strong> + <strong>Tier-1 Facility Vulnerability (Refinery storage within 600m)</strong> + <strong>Downwind Plume Exposure (3.2 km corridor towards populated zone)</strong>. This triggers mandatory Level-1 multi-agency response protocols.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default XAIPanel;
