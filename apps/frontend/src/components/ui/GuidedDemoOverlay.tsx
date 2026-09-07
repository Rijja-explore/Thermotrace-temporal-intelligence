import React, { useState, useEffect } from 'react';
import { dispatchDemoRunEmail } from '../../services/alertEmail';

interface GuidedDemoOverlayProps {
  onClose: () => void;
  onNavigate: (page: string, params?: any) => void;
}

const DEMO_STEPS = [
  {
    title: 'Raw Thermal Hotspots',
    desc: 'ThermoTrace ingests real-time FIRMS data from NASA MODIS and VIIRS satellites. Each dot on the map is a thermal anomaly detected at 375m resolution. Industrial clusters are immediately visible against the dark basemap.',
    nav: 'dashboard',
    params: {},
  },
  {
    title: 'Persistent Industrial Source',
    desc: 'This event — TT-IND-00427 — has been active for 24 of the last 30 days. Temporal persistence is the first indicator of industrial origin versus a transient natural fire. The system automatically flags persistent sources for review.',
    nav: 'investigation',
    params: { eventId: undefined },
  },
  {
    title: 'Facility Context',
    desc: 'The thermal source is located 0.43 km from the Jamnagar Refinery Complex — the world\'s largest oil refinery. The land cover is classified as industrial (87% built-up). This geographic context is a strong positive evidence factor.',
    nav: 'investigation',
    params: {},
  },
  {
    title: 'Baseline Comparison',
    desc: 'Every industrial facility has a learned thermal fingerprint — its normal operational range. The current reading is 38% above baseline. The Thermal Fingerprint chart shows exactly when and by how much the source deviated.',
    nav: 'investigation',
    params: {},
  },
  {
    title: 'Classification & Risk Score',
    desc: 'The hybrid ML model assigns: Classification Confidence 84%, Industrial Likelihood 91/100, Operational Risk 72/100. Each score is decomposed into its contributing factors so analysts can verify the reasoning.',
    nav: 'investigation',
    params: {},
  },
  {
    title: 'Natural & Agricultural Events',
    desc: 'Agricultural burning events are shown in green — spatially dispersed, low persistence, cropland land cover. The system classifies these with high confidence and separates them from industrial sources, reducing false positives.',
    nav: 'dashboard',
    params: {},
  },
  {
    title: 'Unknown State',
    desc: 'Ambiguous events are shown in purple and labelled "Requires Verification". The system is deliberately uncertain — it presents the conflicting evidence and asks the analyst to decide. Honesty about uncertainty is a core design principle.',
    nav: 'alerts',
    params: {},
  },
  {
    title: 'Report Generation',
    desc: 'Analysts can export a structured intelligence report for any event: event summary, map snapshot, scores, evidence timeline, and recommended action. Reports can be shared with regulators, operations teams, or incident commanders.',
    nav: 'investigation',
    params: {},
  },
];

const GuidedDemoOverlay: React.FC<GuidedDemoOverlayProps> = ({ onClose, onNavigate }) => {
  const [step, setStep] = useState(0);
  const [emailDispatched, setEmailDispatched] = useState(false);
  const total = DEMO_STEPS.length;

  const go = (dir: 1 | -1) => {
    const next = step + dir;
    if (next < 0 || next >= total) return;
    setStep(next);
    const s = DEMO_STEPS[next];
    onNavigate(s.nav, s.params);
  };

  // Navigate to initial step page on open AND automatically dispatch alert email
  useEffect(() => {
    const s = DEMO_STEPS[0];
    onNavigate(s.nav, s.params);

    // Auto-dispatch alert email every time demo runs
    dispatchDemoRunEmail().then(() => {
      setEmailDispatched(true);
    });
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

        {/* Live email auto-dispatch banner */}
        {emailDispatched && (
          <div style={{
            margin: '0 0 10px',
            padding: '4px 8px',
            background: 'rgba(79, 209, 139, 0.12)',
            border: '1px solid rgba(79, 209, 139, 0.3)',
            borderRadius: 'var(--radius-xs)',
            fontSize: '10px',
            color: 'var(--accent-green)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontFamily: 'var(--font-mono)'
          }}>
            <span>✉</span> Auto-Dispatched Alert Email → <strong>rijja2310119@ssn.edu.in</strong>
          </div>
        )}

        <div className="demo-overlay-panel__step-label">
          Step {step + 1} of {total}
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
              ✓ Demo Complete
            </button>
          )}
        </div>
      </div>
    </>
  );
};

export default GuidedDemoOverlay;
