import React, { useState, useEffect } from 'react';

interface GuidedDemoOverlayProps {
  onClose: () => void;
  onNavigate: (page: string, params?: any) => void;
}

const DEMO_STEPS = [
  {
    title: 'Near-Real-Time (NRT) Thermal Ingestion',
    desc: 'ThermoTrace ingests near-real-time satellite thermal anomaly observations from NASA FIRMS (MODIS 1km and VIIRS 375m). Continuous processing identifies industrial thermal sources across the subcontinent with high precision.',
    nav: 'command-center',
    params: {},
  },
  {
    title: 'Persistent Industrial Source Intelligence',
    desc: 'This event — TT-CASE-001 — has exhibited stationary recurrence across 24 of the last 30 days. High temporal persistence and spatial stability distinguish persistent industrial assets from transient agricultural or wild fires.',
    nav: 'investigation',
    params: { eventId: 'TT-CASE-001' },
  },
  {
    title: 'Facility Baseline & GIS Context',
    desc: 'The thermal source is matched with the Jamnagar Mega Refinery Complex using OpenStreetMap polygons and ESA WorldCover (87% built-up). Geographic context and infrastructure boundaries are key evidence factors.',
    nav: 'investigation',
    params: { eventId: 'TT-CASE-001' },
  },
  {
    title: 'Learned Operating Envelope & Z-Score',
    desc: 'Each facility has a learned 90-day baseline mean (μ) and standard deviation (σ). Statistically significant deviations (+Zσ) reveal true operational anomalies rather than routine operations.',
    nav: 'investigation',
    params: { eventId: 'TT-CASE-001' },
  },
  {
    title: 'Contextual ML & Risk Scoring',
    desc: 'HistGradientBoosting (HGB) evaluates 24 engineered spatial, temporal, and radiative features. The decomposed scorecard provides full transparency into the classification and operational risk rating.',
    nav: 'investigation',
    params: { eventId: 'TT-CASE-001' },
  },
  {
    title: 'Natural & Agricultural Event Separation',
    desc: 'Agricultural crop residue burning is classified with high confidence and segregated from industrial infrastructure, effectively preventing false alarm fatigue.',
    nav: 'command-center',
    params: {},
  },
  {
    title: 'Calibrated Uncertainty & Review Queue',
    desc: 'Ambiguous observations are categorized as "Requires Verification". The system presents conflicting evidence to the Analyst for human-in-the-loop audit before any action.',
    nav: 'alert-center',
    params: {},
  },
  {
    title: 'Analyst-Controlled Report Dossier Dispatch',
    desc: 'After reviewing the evidence chain, the analyst can click "Dispatch Report Dossier" to generate a certified 19-section intelligence PDF and transmit the brief to thermotrace.india@gmail.com.',
    nav: 'investigation',
    params: { eventId: 'TT-CASE-001' },
  },
];

const GuidedDemoOverlay: React.FC<GuidedDemoOverlayProps> = ({ onClose, onNavigate }) => {
  const [step, setStep] = useState(0);
  const total = DEMO_STEPS.length;

  const go = (dir: 1 | -1) => {
    const next = step + dir;
    if (next < 0 || next >= total) return;
    setStep(next);
    const s = DEMO_STEPS[next];
    onNavigate(s.nav, s.params);
  };

  useEffect(() => {
    const s = DEMO_STEPS[0];
    onNavigate(s.nav, s.params);
  }, []);

  const current = DEMO_STEPS[step];
  const progress = ((step + 1) / total) * 100;

  return (
    <>
      <div className="demo-overlay-backdrop" />
      <div className="demo-overlay-panel" role="dialog" aria-modal="true" aria-label="Guided demo">
        <div className="demo-progress-bar">
          <div className="demo-progress-bar__fill" style={{ width: `${progress}%` }} />
        </div>

        <div className="demo-overlay-panel__header">
          <div className="demo-overlay-panel__step-counter">
            {DEMO_STEPS.map((_, i) => (
              <div
                key={i}
                className={`demo-step-dot ${i === step ? 'demo-step-dot--active' : i < step ? 'demo-step-dot--done' : ''}`}
              />
            ))}
          </div>
          <button className="demo-overlay-panel__close" onClick={onClose} title="Close demo (Esc)">✕</button>
        </div>

        <div className="demo-overlay-panel__step-label">
          Step {step + 1} of {total} · SIH 26162 Interactive Tour
        </div>
        <div className="demo-overlay-panel__title">{current.title}</div>
        <div className="demo-overlay-panel__desc">{current.desc}</div>

        <div className="demo-overlay-panel__nav">
          <button
            className="demo-nav-btn demo-nav-btn--prev"
            onClick={() => go(-1)}
            disabled={step === 0}
            style={{ opacity: step === 0 ? 0.4 : 1 }}
          >
            ← Prev
          </button>
          {step < total - 1 ? (
            <button className="demo-nav-btn demo-nav-btn--next" onClick={() => go(1)}>
              Next Step →
            </button>
          ) : (
            <button
              className="demo-nav-btn demo-nav-btn--next"
              onClick={onClose}
              style={{ background: 'rgba(79,209,139,0.12)', borderColor: 'rgba(79,209,139,0.4)', color: 'var(--accent-green)' }}
            >
              ✓ Complete Tour
            </button>
          )}
        </div>
      </div>
    </>
  );
};

export default GuidedDemoOverlay;
