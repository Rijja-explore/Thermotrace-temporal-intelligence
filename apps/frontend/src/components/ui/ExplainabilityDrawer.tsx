import React, { useState } from 'react';

interface ShapFeature {
  feature: string;
  category: string;
  value: string;
  shapWeight: number; // e.g. +0.32 or -0.12
  impact: 'elevates_risk' | 'lowers_risk';
  description: string;
}

interface CounterfactualRule {
  targetLabel: string;
  condition: string;
  feasibility: string;
  confidenceDelta: string;
}

interface ExplainabilityDrawerProps {
  onClose: () => void;
  eventId: string;
  label?: string;
  evidenceFor?: string[];
  evidenceAgainst?: string[];
  missingEvidence?: string[];
  modelVersion?: string;
  dataVersion?: string;
  lastUpdated?: string;
}

const DEFAULT_SHAP_FEATURES: ShapFeature[] = [
  {
    feature: 'FRP Radiant Power Surge',
    category: 'Thermal (NASA VIIRS)',
    value: '340.0 MW (+4.2σ vs baseline)',
    shapWeight: 0.34,
    impact: 'elevates_risk',
    description: 'Extreme thermal output far exceeds normal steady-state flaring profile (median 65 MW).'
  },
  {
    feature: 'Multi-Day Temporal Persistence',
    category: 'Temporal Memory',
    value: '24 / 30 Active Days (80.0%)',
    shapWeight: 0.28,
    impact: 'elevates_risk',
    description: 'High repeatability across satellite orbits strongly indicates a fixed industrial infrastructure source rather than moving wildfire.'
  },
  {
    feature: 'Proximity to Refinery Perimeter',
    category: 'Geospatial Context',
    value: '180 m from Stack #4',
    shapWeight: 0.22,
    impact: 'elevates_risk',
    description: 'High spatial alignment with registered hydrocarbon processing boundary in ISRO/OSM database.'
  },
  {
    feature: 'Nighttime Detection Ratio',
    category: 'Diurnal Cycle',
    value: '68% Night Passes (VIIRS NRT)',
    shapWeight: 0.16,
    impact: 'elevates_risk',
    description: 'Nighttime thermal signatures confirm continuous 24/7 industrial operations; agricultural fires typically cease at dusk.'
  },
  {
    feature: 'ESA WorldCover Land Classification',
    category: 'Land Cover 10m',
    value: '88% Industrial Built-up',
    shapWeight: 0.12,
    impact: 'elevates_risk',
    description: 'Negligible vegetation / cropland within 500m radius completely rules out crop stubble burning.'
  },
  {
    feature: 'Atmospheric Wind Dispersion Vector',
    category: 'Meteorology (ECMWF)',
    value: '25 km/h at 210° SW',
    shapWeight: -0.06,
    impact: 'lowers_risk',
    description: 'Moderate prevailing crosswind slightly dilutes ground-level radiant heat concentration.'
  }
];

const DEFAULT_COUNTERFACTUALS: CounterfactualRule[] = [
  {
    targetLabel: 'Normal Industrial Steady-State Flaring',
    condition: 'Reduce Fire Radiative Power (FRP) from 340 MW to < 85 MW via Flare Gas Recovery (FGRS)',
    feasibility: 'Actionable (Operator Valve Divert)',
    confidenceDelta: 'Shifts risk from 84/100 (CRITICAL) to 28/100 (NOMINAL)'
  },
  {
    targetLabel: 'Transient Agricultural / Crop Stubble Burn',
    condition: 'If 30-day persistence ratio drops from 80% to < 15% and distance to industrial zone > 2.5 km',
    feasibility: 'Structural (Non-industrial environment)',
    confidenceDelta: 'Reclassifies event taxonomy with 91% confidence'
  },
  {
    targetLabel: 'Sensor False Alarm / Solar Glint Specular',
    condition: 'If brightness temperature differential ΔT4-11 drops below 8.0 K and solar zenith angle matches glint cone',
    feasibility: 'Sensor artifact condition',
    confidenceDelta: 'Flags detection as invalid pixel with 99% certainty'
  }
];

const ExplainabilityDrawer: React.FC<ExplainabilityDrawerProps> = ({
  onClose,
  eventId,
  label = 'Persistent Industrial Flaring Surge',
  evidenceFor = [],
  evidenceAgainst = [],
  missingEvidence = [],
  modelVersion = 'v2.4.0 (XGBoost + SHAP TreeExplainer)',
  dataVersion = 'NASA-FIRMS-VIIRS-2024-NRT',
  lastUpdated = 'Live Downlink',
}) => {
  const [activeTab, setActiveTab] = useState<'shap' | 'counterfactual' | 'evidence' | 'provenance'>('shap');

  const hasFor = evidenceFor.length > 0;
  const hasAgainst = evidenceAgainst.length > 0;
  const hasMissing = missingEvidence.length > 0;

  const defaultFor = [
    'Persistent thermal signal over 24 of 30 days — consistent with continuous industrial processing.',
    'Nearest facility (Jamnagar Refinery Stack #4) is within 180 m — strong spatial correlation.',
    'Land cover classified as 88% built-up / industrial — completely rules out agricultural or forest fire.',
    'Night-time detections present — industrial facilities operate 24/7; wildland fires typically follow diurnal cooling.',
  ];

  const defaultAgainst = [
    'No sub-meter optical satellite imagery acquired in the last 6 hours to visually confirm flame height.',
    'Slight spatial spread (±85 m) across orbits — reflects sensor point-spread function (PSF) smearing.',
  ];

  const defaultMissing = [
    'Sentinel-2 MSI cloud-free optical acquisition (next scheduled pass in 14 hours).',
    'Direct SCADA telemetry stream from facility flare stack manifold.',
  ];

  const forItems = hasFor ? evidenceFor : defaultFor;
  const againstItems = hasAgainst ? evidenceAgainst : defaultAgainst;
  const missingItems = hasMissing ? missingEvidence : defaultMissing;

  return (
    <>
      <div className="explainability-drawer-backdrop" onClick={onClose} />
      <aside className="explainability-drawer" role="complementary" aria-label="Explainable AI Drawer">
        {/* Header */}
        <div className="explainability-drawer__header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '16px' }}>🤖</span>
              <div className="explainability-drawer__title">EXPLAINABLE AI (XAI) INTELLIGENCE</div>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              Event Ref: {eventId} · Model: {modelVersion.split(' ')[0]}
            </div>
          </div>
          <button className="explainability-drawer__close" onClick={onClose} title="Close">✕</button>
        </div>

        {/* Navigation Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'var(--bg-secondary)',
          padding: '0 8px'
        }}>
          {[
            { id: 'shap', label: '📊 SHAP Attribution' },
            { id: 'counterfactual', label: '🔮 Counterfactuals' },
            { id: 'evidence', label: '📋 Evidence Ledger' },
            { id: 'provenance', label: '🛰️ Provenance' }
          ].map(tab => (
            <button
              key={tab.id}
              style={{
                padding: '10px 12px',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                color: activeTab === tab.id ? 'var(--accent-cyan)' : 'var(--text-muted)',
                fontWeight: activeTab === tab.id ? '700' : '500',
                fontSize: '11px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="explainability-drawer__body" style={{ overflowY: 'auto' }}>
          
          {/* AI Decision Summary Card */}
          <div style={{
            background: 'rgba(67, 217, 232, 0.08)',
            border: '1px solid rgba(67, 217, 232, 0.25)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 14px',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            lineHeight: '1.6',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', fontWeight: '800', color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                Classification Inference
              </span>
              <span style={{
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'rgba(79, 209, 139, 0.15)',
                color: 'var(--accent-green)',
                fontSize: '10px',
                fontWeight: '700'
              }}>
                94.2% Calibrated Confidence
              </span>
            </div>
            The GeoAI model classifies this event as a <strong style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{label.replace(/_/g, ' ')}</strong> based
            on an anomalous FRP spike (+4.2σ above baseline), high 80% multi-day persistence, and 180m spatial correlation with registered refinery infrastructure.
          </div>

          {/* TAB 1: SHAP Waterfall Feature Attributions */}
          {activeTab === 'shap' && (
            <div>
              <div className="explainability-drawer__section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>SHAP Feature Attribution Waterfall</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'none', fontWeight: 'normal' }}>
                  Base Value: E[f(x)] = 0.12 → f(x) = 0.94
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '10px' }}>
                Quantitative contribution of each satellite & temporal feature toward the final classification:
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {DEFAULT_SHAP_FEATURES.map((feat, idx) => {
                  const isPositive = feat.shapWeight > 0;
                  const barWidth = Math.min(100, Math.abs(feat.shapWeight) * 220);

                  return (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 12px',
                        background: 'var(--bg-secondary)',
                        borderRadius: 'var(--radius-sm)',
                        borderLeft: `3px solid ${isPositive ? 'var(--accent-cyan)' : 'var(--accent-green)'}`
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2px' }}>
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)' }}>
                            {feat.feature}
                          </div>
                          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                            {feat.category} · <strong style={{ color: 'var(--text-secondary)' }}>{feat.value}</strong>
                          </div>
                        </div>
                        <span style={{
                          fontSize: '12px',
                          fontWeight: '800',
                          fontFamily: 'var(--font-mono)',
                          color: isPositive ? 'var(--accent-cyan)' : 'var(--accent-green)'
                        }}>
                          {isPositive ? `+${feat.shapWeight.toFixed(2)}` : feat.shapWeight.toFixed(2)} SHAP
                        </span>
                      </div>

                      {/* SHAP Bar */}
                      <div style={{
                        height: '5px',
                        background: 'rgba(255,255,255,0.06)',
                        borderRadius: '3px',
                        margin: '6px 0',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${barWidth}%`,
                          background: isPositive
                            ? 'linear-gradient(90deg, #43D9E8, #FF5C6C)'
                            : 'linear-gradient(90deg, #4FD18B, #43D9E8)',
                          borderRadius: '3px'
                        }} />
                      </div>

                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                        {feat.description}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: Counterfactual Explanations */}
          {activeTab === 'counterfactual' && (
            <div>
              <div className="explainability-drawer__section-title">
                Counterfactual "What-If" Perturbation Bounds
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px', lineHeight: '1.5' }}>
                Counterfactual reasoning identifies the minimal feature changes required to invert or shift the AI decision boundary:
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {DEFAULT_COUNTERFACTUALS.map((rule, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      background: 'var(--bg-secondary)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--accent-amber)' }}>
                        Target State: {rule.targetLabel}
                      </span>
                      <span style={{
                        fontSize: '9px',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        background: 'rgba(255,181,71,0.15)',
                        color: 'var(--accent-amber)'
                      }}>
                        {rule.feasibility}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-primary)', marginBottom: '6px', lineHeight: '1.4' }}>
                      <strong>Required Input Change:</strong> {rule.condition}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--accent-cyan)', background: 'rgba(67,217,232,0.06)', padding: '6px 8px', borderRadius: '4px' }}>
                      💡 <strong>Impact:</strong> {rule.confidenceDelta}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: Evidence Ledger */}
          {activeTab === 'evidence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Supporting evidence */}
              <div>
                <div className="explainability-drawer__section-title" style={{ color: 'var(--accent-green)' }}>
                  ✓ Supporting Evidence ({forItems.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {forItems.map((item, i) => (
                    <div key={i} className="explain-factor explain-factor--positive">
                      <div className="explain-factor__indicator" />
                      <div className="explain-factor__text">{item}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Conflicting evidence */}
              <div>
                <div className="explainability-drawer__section-title" style={{ color: 'var(--accent-amber)' }}>
                  ⚠ Conflicting / Uncertain Observations ({againstItems.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {againstItems.map((item, i) => (
                    <div key={i} className="explain-factor explain-factor--conflict">
                      <div className="explain-factor__indicator" />
                      <div className="explain-factor__text">{item}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Missing evidence */}
              <div>
                <div className="explainability-drawer__section-title" style={{ color: 'var(--accent-purple)' }}>
                  ℹ️ Data Gaps & Unacquired Telemetry ({missingItems.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {missingItems.map((item, i) => (
                    <div key={i} className="explain-factor explain-factor--missing">
                      <div className="explain-factor__indicator" />
                      <div className="explain-factor__text">{item}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Provenance */}
          {activeTab === 'provenance' && (
            <div className="explainability-drawer__provenance">
              <div className="explainability-drawer__section-title">Satellite Data & Model Provenance</div>
              {[
                ['Model version', modelVersion],
                ['Data version', dataVersion],
                ['Primary Satellite Sensor', 'NASA VIIRS (Suomi-NPP / NOAA-20) 375m'],
                ['Secondary Sensor', 'NASA MODIS (Aqua / Terra) 1km'],
                ['Land Cover Registry', 'ESA WorldCover 10m Multi-Spectral'],
                ['Infrastructure Vectors', 'ISRO Bhuvan Industrial Directory + OSM'],
                ['Atmospheric Reanalysis', 'ECMWF ERA5 / GFS Wind Velocity'],
                ['Confidence Calibration', 'Platt Scaling / Temperature Scaling'],
                ['Explainability Engine', 'SHAP TreeExplainer & Counterfactual Optimizer'],
                ['Last Telemetry Downlink', lastUpdated]
              ].map(([k, v]) => (
                <div key={k} className="explainability-drawer__provenance-row">
                  <span className="explainability-drawer__provenance-key">{k}</span>
                  <span className="explainability-drawer__provenance-val">{v}</span>
                </div>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <div style={{
            fontSize: '10px',
            color: 'var(--text-disabled)',
            lineHeight: '1.5',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '12px',
            marginTop: '8px'
          }}>
            ThermoTrace Explainable AI provides quantitative decision support for facility safety officers and environmental auditors. Thermal detections at 375 m pixel footprint represent area-level radiant energy measurements.
          </div>
        </div>
      </aside>
    </>
  );
};

export default ExplainabilityDrawer;
