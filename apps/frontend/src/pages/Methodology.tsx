import React from 'react';
import LayerByLayerPipeline from '../components/ui/LayerByLayerPipeline';

const Methodology: React.FC = () => {
  const confidenceLabels = [
    { label: 'Confirmed / Strongly Supported', threshold: '≥ 85%', colour: 'var(--accent-teal)', desc: 'Multiple independent evidence streams agree. High repeatability in satellite observations.' },
    { label: 'Probable', threshold: '70–84%', colour: 'var(--accent-green)', desc: 'Strong primary evidence with minor gaps. Recommended for expedited review.' },
    { label: 'Possible', threshold: '55–69%', colour: 'var(--accent-cyan)', desc: 'Moderate evidence. Context-dependent — facility proximity and persistence are key discriminators.' },
    { label: 'Requires Verification', threshold: '40–54%', colour: 'var(--accent-amber)', desc: 'Conflicting or insufficient evidence. Do not act on this classification without analyst review.' },
    { label: 'Unknown', threshold: '< 40%', colour: 'var(--accent-purple)', desc: 'System is unable to classify with reasonable certainty. Presented as unknown — this is intentional and honest.' },
  ];

  const dataSources = [
    { name: 'NASA FIRMS — MODIS', description: '1 km resolution thermal anomaly data, global coverage, 2 passes/day per satellite', type: 'Primary' },
    { name: 'NASA FIRMS — VIIRS 375m', description: '375 m resolution, improved sensitivity for smaller sources', type: 'Primary' },
    { name: 'ESA WorldCover 2021', description: '10 m land cover classification (urban, forest, cropland, water, shrubland)', type: 'Context' },
    { name: 'OpenStreetMap + GeoJSON', description: 'Industrial facility locations: refineries, steel mills, mining sites, power plants', type: 'Context' },
    { name: 'GADM v3.6', description: 'Administrative boundaries for regional filtering and report attribution', type: 'Context' },
    { name: 'Analyst Ground Truth (N=30)', description: 'Human-verified labels for model training and evaluation', type: 'Ground Truth' },
  ];

  return (
    <div className="methodology-page">
      <div className="methodology-page-inner">
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <div className="page-title">Methodology</div>
          <div className="page-subtitle">
            How ThermoTrace identifies, classifies, and explains industrial thermal events using satellite intelligence, temporal analysis, and explainable AI.
          </div>
        </div>

        {/* Core value proposition */}
        <div style={{
          background: 'rgba(67, 217, 232, 0.06)',
          border: '1px solid rgba(67, 217, 232, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: '16px 20px',
          marginBottom: '20px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          lineHeight: '1.7',
        }}>
          <strong style={{ color: 'var(--accent-cyan)' }}>ThermoTrace does not merely show where heat was detected.</strong>
          {' '}It transforms raw satellite observations into facility-aware intelligence: learning what normal thermal behavior looks like for each plant, detecting statistically significant deviations, forecasting escalation trends, explaining decisions through XAI, and calculating downwind population impact for response prioritization.
        </div>

        {/* ─── MODULE M: NOVELTY BEYOND SIH REQUIREMENT ─── */}
        <div className="methodology-section" style={{ border: '1px solid rgba(167,139,250,0.3)', background: 'rgba(167,139,250,0.03)' }}>
          <div className="methodology-section__title" style={{ color: '#A78BFA', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>🏆 Novelty Architecture — Beyond SIH Requirement</span>
            <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(167,139,250,0.2)', color: '#DDD6FE' }}>
              SIH 26162 DIFFERENTIATION
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '14px' }}>
            {/* Column 1: SIH Baseline */}
            <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '8px', padding: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '8px' }}>
                SIH Problem Statement Requirement
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                "AI-based detection and classification of industrial fires and persistent thermal sources using NASA FIRMS, OSM and satellite data."
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {['1. Satellite Ingestion (NASA FIRMS)', '2. Land Cover & OSM Spatial Join', '3. ML Classification (Industrial / Natural / Agri)', '4. Geospatial Map Visualization'].map((item, idx) => (
                  <div key={idx} style={{ fontSize: '11px', color: '#CBD5E1', padding: '6px 10px', background: '#101927', borderRadius: '4px', borderLeft: '3px solid #64748B' }}>
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Column 2: ThermoTrace Innovation */}
            <div style={{ background: '#0B1321', border: '1px solid rgba(67,217,232,0.3)', borderRadius: '8px', padding: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase', marginBottom: '8px' }}>
                ThermoTrace Final Novelty Pipeline
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                "Explainable Facility-Aware Thermal Intelligence, Early-Warning & Decision Support System."
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {[
                  '⭐ Facility Thermal Fingerprint (Baseline Mean, Normal Envelope, +Zσ Abnormality)',
                  '⭐ Early Warning & Escalation (FRP Slope & Acceleration, 48h Trend Corridor)',
                  '⭐ Explainable AI (SHAP TreeExplainer, DiCE Counterfactuals, LSTM Attention)',
                  '⭐ Impact & Plume Dispersion (API 521 Radii, Downwind Heading, Population Exposure)',
                  '⭐ Response Prioritization & SOP (Transparent Decision Support SOP, Human-in-the-Loop)',
                ].map((item, idx) => (
                  <div key={idx} style={{ fontSize: '11px', color: '#FFF', padding: '6px 10px', background: '#101927', borderRadius: '4px', borderLeft: '3px solid var(--accent-cyan)' }}>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Layer-by-Layer Processing Pipeline */}
        <div className="methodology-section">
          <LayerByLayerPipeline />
        </div>

        {/* Data sources */}
        <div className="methodology-section">
          <div className="methodology-section__title">Data Sources</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
            {dataSources.map((ds, i) => (
              <div key={i} style={{
                display: 'flex',
                gap: '12px',
                padding: '10px 12px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-sm)',
                alignItems: 'flex-start',
              }}>
                <span style={{
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '9px',
                  fontWeight: '700',
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  flexShrink: 0,
                  background: ds.type === 'Primary' ? 'rgba(67,217,232,0.12)' : ds.type === 'Ground Truth' ? 'rgba(79,209,139,0.12)' : 'rgba(77,141,255,0.12)',
                  color: ds.type === 'Primary' ? 'var(--accent-cyan)' : ds.type === 'Ground Truth' ? 'var(--accent-green)' : 'var(--accent-blue)',
                  border: `1px solid ${ds.type === 'Primary' ? 'rgba(67,217,232,0.25)' : ds.type === 'Ground Truth' ? 'rgba(79,209,139,0.25)' : 'rgba(77,141,255,0.25)'}`,
                  alignSelf: 'flex-start',
                  marginTop: '2px',
                }}>{ds.type}</span>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '2px' }}>{ds.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{ds.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Feature engineering */}
        <div className="methodology-section">
          <div className="methodology-section__title">Feature Engineering</div>
          <div className="methodology-section__body">
            <p style={{ marginBottom: '10px' }}>
              The classification model uses four categories of features, each contributing measurable F1 improvement (see Thermal Analytics for ablation results):
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {[
                { title: 'Thermal (Raw)', items: ['Fire Radiative Power (FRP, MW)', 'Brightness temperature (K)', 'Satellite detection confidence', 'Observation timestamp'] },
                { title: 'Temporal Windows', items: ['7d/30d/90d detection counts', 'FRP mean per window', 'Persistence ratio (active days %)', 'FRP Z-score vs baseline'] },
                { title: 'Land Cover', items: ['Urban/built-up fraction', 'Forest cover fraction', 'Cropland fraction', 'Water body fraction'] },
                { title: 'Industrial Context', items: ['Distance to nearest refinery (m)', 'Distance to steel/mining facility', 'Facility type classification', 'OSM facility presence flag'] },
              ].map((group, i) => (
                <div key={i} style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', borderTop: '2px solid var(--border-active)' }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px' }}>{group.title}</div>
                  <ul style={{ paddingLeft: '14px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    {group.items.map((item, j) => (
                      <li key={j} style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Confidence system */}
        <div className="methodology-section">
          <div className="methodology-section__title">Confidence & Uncertainty Labels</div>
          <div className="methodology-section__body" style={{ marginBottom: '12px' }}>
            ThermoTrace uses calibrated confidence labels rather than raw probability values. The system is designed to be
            honest about uncertainty — ambiguous cases are presented as unknown, not forced into an incorrect classification.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {confidenceLabels.map((c, i) => (
              <div key={i} style={{
                padding: '12px 14px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-sm)',
                borderLeft: `3px solid ${c.colour}`,
                display: 'flex',
                gap: '14px',
                alignItems: 'flex-start',
              }}>
                <div style={{ minWidth: '70px', flexShrink: 0 }}>
                  <div style={{ fontSize: '12px', fontWeight: '700', color: c.colour }}>{c.threshold}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '3px' }}>{c.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{c.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Limitations */}
        <div className="methodology-section" style={{ borderLeft: '3px solid var(--accent-amber)', borderTopLeftRadius: 0, borderBottomLeftRadius: 0 }}>
          <div className="methodology-section__title" style={{ color: 'var(--accent-amber)' }}>Known Limitations</div>
          <div className="methodology-section__body">
            <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li>FIRMS 375 m resolution cannot distinguish between individual point sources in dense industrial clusters.</li>
              <li>Cloud cover &gt;40% significantly degrades detection reliability in affected pixels.</li>
              <li>Night-time VIIRS observations may be unavailable or degraded for certain satellite passes.</li>
              <li>The ground truth dataset (N=30) is sufficient for prototype evaluation but not production-grade model training.</li>
              <li>Facility database is based on publicly available OSM data and may not include all industrial sources.</li>
              <li>Seasonal agricultural burning events can briefly overlap with industrial thermal signatures in timing and location.</li>
            </ul>
          </div>
        </div>

        {/* Footer note */}
        <div style={{ fontSize: '11px', color: 'var(--text-disabled)', textAlign: 'center', marginTop: '20px', lineHeight: '1.6' }}>
          ThermoTrace — Industrial Thermal GeoAI Platform · SIH26162 · Prototype Research System<br />
          Thermal detections represent area-level evidence at 375 m resolution. Building-level attribution requires high-resolution optical verification.
        </div>
      </div>
    </div>
  );
};

export default Methodology;
