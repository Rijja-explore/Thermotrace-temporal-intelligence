import { useEffect, useState, useRef } from 'react';
import { MapView } from '../components/MapView';
import type { ThermoEvent, FacilityThermalFingerprint, EarlyWarningForecast, ImpactIntelligence } from '../services/api';
import {
  fetchEvents,
  fetchEventById,
  getReportUrl,
  fetchFacilityFingerprint,
  fetchEarlyWarning,
  fetchImpactIntelligence,
} from '../services/api';
import ThermalFingerprintChart from '../components/ui/ThermalFingerprintChart';
import EvidenceTimeline from '../components/ui/EvidenceTimeline';
import ExplainabilityDrawer from '../components/ui/ExplainabilityDrawer';
import XAIPanel from '../components/ui/XAIPanel';
import AnalystActionBar from '../components/ui/AnalystActionBar';
import ReportPreviewModal from '../components/ui/ReportPreviewModal';
import CompareEventsPanel from '../components/ui/CompareEventsPanel';
import { FacilityThermalFingerprintCard } from '../components/ui/FacilityThermalFingerprintCard';
import { EarlyWarningForecastCard } from '../components/ui/EarlyWarningForecastCard';
import { ImpactIntelligenceCard } from '../components/ui/ImpactIntelligenceCard';
import { UnifiedEventIntelligenceScorecard } from '../components/ui/UnifiedEventIntelligenceScorecard';

interface EventInvestigationProps {
  eventId?: string;
  onNavigate?: (page: string, params?: any) => void;
}

// ─── Risk Score Card ───
function RiskScoreCard({
  label,
  value,
  max = 100,
  variant = 'cyan',
  sub,
  components,
}: {
  label: string;
  value: number;
  max?: number;
  variant?: 'cyan' | 'amber' | 'red' | 'orange' | 'green' | 'purple';
  sub?: string;
  components?: Record<string, number>;
}) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.min(100, (value / max) * 100);

  const urgency = value >= 70 ? 'Critical' : value >= 50 ? 'High' : value >= 30 ? 'Moderate' : 'Low';
  const displaySub = sub ?? urgency;

  return (
    <div className={`risk-score-card risk-score-card--${variant}`}>
      <div className="risk-score-card__label">{label}</div>
      <div className="risk-score-card__value">
        {value}<span style={{ fontSize: '16px', fontWeight: 400, color: 'var(--text-muted)' }}>/{max}</span>
      </div>
      <div className="risk-score-card__sub">{displaySub}</div>
      <div className="risk-score-card__bar-track">
        <div className="risk-score-card__bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <button className="risk-score-card__explain-btn" onClick={() => setExpanded(e => !e)}>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {expanded ? 'Hide' : 'Explain'}
      </button>
      {expanded && components && Object.keys(components).length > 0 && (
        <div className="risk-score-card__breakdown">
          {Object.entries(components).map(([k, v]) => (
            <div key={k} className="risk-score-card__breakdown-row">
              <span className="risk-score-card__breakdown-label">{k.replace(/_/g, ' ')}</span>
              <div className="risk-score-card__breakdown-bar">
                <div className="risk-score-card__breakdown-bar-fill" style={{ width: `${v}%` }} />
              </div>
              <span className="risk-score-card__breakdown-val">{v}</span>
            </div>
          ))}
        </div>
      )}
      {expanded && (!components || Object.keys(components).length === 0) && (
        <div className="risk-score-card__breakdown" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Composite score — component breakdown unavailable for this event.
        </div>
      )}
    </div>
  );
}

// ─── Evidence Card ───
function EvidenceCard({
  icon,
  title,
  explanation,
  strength,
  source,
  type = 'positive',
}: {
  icon: string;
  title: string;
  explanation: string;
  strength: string;
  source?: string;
  type?: 'positive' | 'warning' | 'limitation';
}) {
  return (
    <div className={`evidence-card evidence-card--${type}`}>
      <div className="evidence-card__header">
        <div className="evidence-card__icon">{icon}</div>
        <div className="evidence-card__title">{title}</div>
      </div>
      <div className="evidence-card__explanation">{explanation}</div>
      <div className="evidence-card__footer">
        <span className="evidence-card__strength">{strength}</span>
        {source && <span className="evidence-card__source">{source}</span>}
      </div>
    </div>
  );
}

export default function EventInvestigation({ eventId = 'TT-CASE-001', onNavigate }: EventInvestigationProps) {
  const [event, setEvent] = useState<ThermoEvent | null>(null);
  const [allEvents, setAllEvents] = useState<ThermoEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [showExplain, setShowExplain] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [showReclassify, setShowReclassify] = useState(false);
  const [reclassifyLabel, setReclassifyLabel] = useState('persistent_industrial_source');
  const [reclassifyNotes, setReclassifyNotes] = useState('');

  // Novelty Module State
  const [fingerprint, setFingerprint] = useState<FacilityThermalFingerprint | null>(null);
  const [earlyWarning, setEarlyWarning] = useState<EarlyWarningForecast | null>(null);
  const [impact, setImpact] = useState<ImpactIntelligence | null>(null);
  const [activeSection, setActiveSection] = useState<string>('fingerprint');

  const fingerprintRef = useRef<HTMLDivElement>(null);
  const earlyWarningRef = useRef<HTMLDivElement>(null);
  const xaiRef = useRef<HTMLDivElement>(null);
  const impactRef = useRef<HTMLDivElement>(null);

  const scrollToSection = (secId: string) => {
    setActiveSection(secId);
    if (secId === 'fingerprint' && fingerprintRef.current) {
      fingerprintRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (secId === 'early-warning' && earlyWarningRef.current) {
      earlyWarningRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (secId === 'xai' && xaiRef.current) {
      xaiRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (secId === 'impact' && impactRef.current) {
      impactRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleSelectEvent = async (targetEvent: ThermoEvent) => {
    setEvent(targetEvent);
    setStatus(targetEvent.status || 'requires_verification');

    const curFrp = (targetEvent as any).frp || (targetEvent as any).raw_firms?.frp || targetEvent.temporal_features?.current_frp || 340;
    const facId = targetEvent.facility_context?.nearest_facility_id || 'FAC-JAMNAGAR-01';
    const facName = targetEvent.facility_context?.nearest_facility_name || targetEvent.facility_context?.name || 'Jamnagar Mega Refinery';
    const rScore = targetEvent.operational_risk?.risk_score ?? targetEvent.scores?.operational_risk ?? 84;

    try {
      const [fpRes, ewRes, impRes] = await Promise.all([
        fetchFacilityFingerprint(facId, curFrp).catch(() => null),
        fetchEarlyWarning(targetEvent.event_id, curFrp, targetEvent.temporal_features?.baseline_frp_mean, targetEvent.temporal_features?.baseline_frp_std).catch(() => null),
        fetchImpactIntelligence(targetEvent.event_id, facName, curFrp, rScore).catch(() => null),
      ]);

      setFingerprint(fpRes);
      setEarlyWarning(ewRes);
      setImpact(impRes);
    } catch (err) {
      console.warn('Error loading event novelty data:', err);
    }
  };

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [evRes, detailRes] = await Promise.all([
          fetchEvents({ limit: 500 }),
          fetchEventById(eventId).catch(() => null),
        ]);
        setAllEvents(evRes.events);
        const found = detailRes || evRes.events.find(e => e.event_id === eventId) || evRes.events[0];
        if (found) {
          await handleSelectEvent(found);
        }
      } catch (err) {
        console.error('Failed to load investigation data:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [eventId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100%', gap: '0' }}>
        <div style={{ flex: 1, background: 'var(--bg-primary)' }} />
        <div style={{ flex: 1, padding: '24px', background: 'var(--bg-secondary)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[80, 60, 100, 60, 100, 100].map((w, i) => (
              <div key={i} className="skeleton" style={{ width: `${w}%`, height: i === 2 ? '120px' : i === 4 ? '200px' : '20px' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="empty-state" style={{ height: '100%' }}>
        <div className="empty-state__icon">🔭</div>
        <div className="empty-state__title">Event not found: {eventId}</div>
        <div className="empty-state__desc">This event ID could not be located in the current dataset.</div>
        <button className="empty-state__action" onClick={() => onNavigate?.('dashboard')}>
          ← Back to Command Center
        </button>
      </div>
    );
  }

  const facility = event.facility_context || {};
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
  const industrial = event.industrial_likelihood?.score ?? event.scores?.industrial_likelihood ?? 0;
  const anomaly = event.anomaly?.anomaly_score ?? 0;
  const confidence = Math.round((event.classification?.confidence || 0) * (event.classification?.confidence <= 1.0 ? 100 : 1));
  const classLabel = (event.classification?.label || event.classification?.class || 'unknown_requires_verification').replace(/_/g, ' ');
  const lat = event.geometry?.latitude ?? event.geometry?.lat;
  const lon = event.geometry?.longitude ?? event.geometry?.lon;
  const probs = event.classification?.probabilities || {};
  const tf = event.temporal_features;
  const isAbnormal = event.anomaly?.is_abnormal ?? false;
  const deviationPct = event.deviation?.frp_deviation_pct;

  let evidenceFor: string[] = [];
  let evidenceAgainst: string[] = [];
  let missingEvidence: string[] = [];
  if (typeof event.evidence === 'object' && !Array.isArray(event.evidence)) {
    evidenceFor = event.evidence.evidence_for || [];
    evidenceAgainst = event.evidence.evidence_against || [];
    missingEvidence = event.evidence.missing_evidence || [];
  } else if (Array.isArray(event.evidence)) {
    evidenceFor = event.evidence;
  }

  const riskVariant = risk >= 70 ? 'red' : risk >= 50 ? 'orange' : 'green';
  const facilityDist = facility.distance_to_facility_m
    ? `${(facility.distance_to_facility_m / 1000).toFixed(2)} km`
    : facility.nearby_refinery_km ? `${facility.nearby_refinery_km} km` : 'N/A';

  return (
    <div className="investigation-layout">
      {/* ─── Left: Map ─── */}
      <div className="investigation-layout__map">
        <MapView
          events={allEvents}
          facilities={[]}
          selectedEventId={event.event_id}
          onSelectEvent={ev => handleSelectEvent(ev)}
          center={lat && lon ? [lat, lon] : [21.1458, 79.0882]}
          zoom={12}
        />
      </div>

      {/* ─── Right: Analyst Workspace ─── */}
      <div className="investigation-layout__detail">
        {/* Header bar */}
        <div className="investigation-header-bar">
          <button className="investigation-back-btn" onClick={() => onNavigate?.('dashboard')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6" /></svg>
            Command Center
          </button>
          <div className="investigation-header-actions">
            <button className="btn btn--icon btn--sm" title="Bookmark">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>
            </button>
            <button className="btn btn--ghost btn--sm" onClick={() => setShowExplain(true)} style={{ background: 'rgba(167,139,250,0.12)', borderColor: 'rgba(167,139,250,0.35)', color: 'var(--accent-purple)' }}>
              🤖 XAI Deep Drill
            </button>
            <button className="btn btn--ghost btn--sm" onClick={() => setShowCompare(true)} title="Compare with another event">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="3" width="9" height="18" rx="1" />
                <rect x="13" y="3" width="9" height="18" rx="1" />
              </svg>
              Compare
            </button>
            <button className="btn btn--cyan btn--sm" onClick={() => onNavigate?.('what-if', { eventId: event.event_id })} title="Simulate counterfactual scenarios and mitigations">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
                <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
                <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
              </svg>
              What-If Simulator
            </button>
            <button className="btn btn--ghost btn--sm" onClick={() => setShowReport(true)}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
              Report
            </button>
          </div>
        </div>

        {/* Event ID + Title + Location */}
        <div className="investigation-event-id">{event.event_id}</div>
        <div className="investigation-title">{classLabel}</div>
        <div className="investigation-subtitle">
          {facility.nearest_facility_name || facility.name
            ? <>📍 {event.region || 'India'} · {facilityDist} from {facility.nearest_facility_name || facility.name}</>
            : <>📍 {event.region || 'India'}</>}
          <span className={`status-badge status-badge--${status}`}>{status.replace(/_/g, ' ')}</span>
        </div>

        {/* ─── MODULE D: UNIFIED EVENT INTELLIGENCE SCORECARD ─── */}
        <UnifiedEventIntelligenceScorecard
          classificationLabel={classLabel}
          confidencePct={confidence}
          abnormalityZ={fingerprint?.current_observation?.deviation_z || 4.2}
          abnormalityLevel={fingerprint?.current_observation?.abnormality_level || 'HIGHLY_ABNORMAL'}
          escalationState={earlyWarning?.escalation_state || 'CRITICAL_ESCALATION'}
          riskScore={risk}
          incidentPriority={impact?.incident_priority || 'CRITICAL'}
          activeSection={activeSection}
          onSelectSection={scrollToSection}
        />

        {/* 3 Traditional Score Cards */}
        <div className="score-cards-grid" style={{ marginBottom: '20px' }}>
          <RiskScoreCard
            label="Classification Confidence"
            value={confidence}
            max={100}
            variant="cyan"
            sub={confidence >= 80 ? 'Strongly supported' : confidence >= 60 ? 'Probable' : confidence >= 40 ? 'Possible' : 'Requires verification'}
            components={probs ? Object.fromEntries(Object.entries(probs).map(([k, v]) => [k, Math.round(v * 100)])) : {}}
          />
          <RiskScoreCard
            label="Industrial Likelihood"
            value={industrial}
            max={100}
            variant="amber"
            sub={industrial >= 80 ? 'Strong industrial indicators' : industrial >= 60 ? 'Probable industrial origin' : 'Mixed indicators'}
            components={event.industrial_likelihood?.component_scores}
          />
          <RiskScoreCard
            label="Operational Risk"
            value={risk}
            max={100}
            variant={riskVariant}
            sub={risk >= 70 ? 'Critical — verify urgently' : risk >= 50 ? 'High — review within 24h' : risk >= 30 ? 'Moderate — monitor' : 'Low risk'}
            components={event.operational_risk?.component_scores}
          />
        </div>

        {/* ─── MODULE A: FACILITY THERMAL FINGERPRINT ─── */}
        <div ref={fingerprintRef} style={{ marginBottom: '24px' }}>
          <FacilityThermalFingerprintCard
            fingerprint={fingerprint}
            loading={false}
          />
        </div>

        {/* ─── MODULE B: EARLY WARNING & ESCALATION FORECAST ─── */}
        <div ref={earlyWarningRef} style={{ marginBottom: '24px' }}>
          <EarlyWarningForecastCard
            forecast={earlyWarning}
            loading={false}
          />
        </div>

        {/* ─── MODULE H / XAI PANEL ─── */}
        <div ref={xaiRef} style={{ marginBottom: '24px' }}>
          <XAIPanel
            eventId={event.event_id}
            frp={(event as any).frp || (event as any).raw_firms?.frp || 340}
            confidence={confidence}
            label={classLabel}
          />
        </div>

        {/* ─── MODULE C: IMPACT & RESPONSE INTELLIGENCE ─── */}
        <div ref={impactRef} style={{ marginBottom: '24px' }}>
          <ImpactIntelligenceCard
            impact={impact}
            loading={false}
          />
        </div>

        {/* Evidence Timeline */}
        <EvidenceTimeline
          label={event.classification?.label || ''}
          isAbnormal={isAbnormal}
          persistenceRatio={tf?.persistence_ratio ?? tf?.window_30d?.persistence_ratio}
          detectionCount30d={tf?.detection_count_30d ?? tf?.window_30d?.detection_count}
          firstDetection={event.time_window?.start?.split('T')[0]}
          timeWindowStart={event.time_window?.start}
          timeWindowEnd={event.time_window?.end}
          facilityName={facility.nearest_facility_name || facility.name}
          landcover={event.landcover_context?.primary_class || facility.land_cover}
        />

        {/* Thermal Fingerprint Chart */}
        <ThermalFingerprintChart
          eventId={event.event_id}
          detectionCount30d={tf?.detection_count_30d ?? tf?.window_30d?.detection_count}
          persistenceRatio={tf?.persistence_ratio ?? tf?.window_30d?.persistence_ratio}
          deviationPct={deviationPct}
          baselineFrpMean={tf?.baseline_frp_mean}
          baselineFrpStd={tf?.baseline_frp_std}
          currentFrp={tf?.current_frp}
          isAbnormal={isAbnormal}
          window30d={tf?.window_30d}
        />

        {/* Evidence Cards */}
        <div className="section-title">Supporting Evidence</div>
        <div className="evidence-grid">
          <EvidenceCard
            icon="🏭"
            title="Facility Proximity"
            explanation={
              facility.nearest_facility_name
                ? `Located ${facilityDist} from ${facility.nearest_facility_name}. Proximity to a major industrial facility is a strong predictor of industrial thermal origin.`
                : 'No known industrial facility within 5 km. This weakens the industrial classification.'
            }
            strength={facility.nearest_facility_name ? 'STRONG' : 'WEAK'}
            source={`OSM · GADM v3.6`}
            type={facility.nearest_facility_name ? 'positive' : 'warning'}
          />
          <EvidenceCard
            icon="🌍"
            title="Land Cover Match"
            explanation={`Primary land cover: ${event.landcover_context?.primary_class || facility.land_cover || 'Industrial'}. ${(event.landcover_context?.urban_builtup_pct || 0) > 50 ? 'Predominantly urban/industrial area — consistent with industrial source.' : 'Land cover indicates mixed or agricultural area.'}`}
            strength={(event.landcover_context?.urban_builtup_pct || 0) > 50 ? 'STRONG' : 'MODERATE'}
            source="ESA WorldCover 2021"
            type={(event.landcover_context?.urban_builtup_pct || 0) > 50 ? 'positive' : 'warning'}
          />
          <EvidenceCard
            icon="📅"
            title="Historical Persistence"
            explanation={`Thermal signal detected on ${tf?.detection_count_30d ?? tf?.window_30d?.detection_count ?? '—'} of 30 days. Persistence above 60% is a strong indicator of continuous industrial process versus transient natural event.`}
            strength={((tf?.persistence_ratio || tf?.window_30d?.persistence_ratio || 0) >= 0.6) ? 'STRONG' : 'MODERATE'}
            source="FIRMS 30-day window"
            type={((tf?.persistence_ratio || tf?.window_30d?.persistence_ratio || 0) >= 0.6) ? 'positive' : 'warning'}
          />
          <EvidenceCard
            icon="📍"
            title="Spatial Stability"
            explanation={`Source location drift: ±${tf?.spatial_stability_m ?? 120} m across detections. Low spatial drift indicates a fixed point source consistent with industrial infrastructure, not a spreading fire.`}
            strength={(tf?.spatial_stability_m ?? 120) < 300 ? 'STRONG' : 'MODERATE'}
            source="FIRMS spatial clustering"
            type={(tf?.spatial_stability_m ?? 120) < 300 ? 'positive' : 'warning'}
          />
          {evidenceAgainst.length > 0 && (
            <EvidenceCard
              icon="⚠️"
              title="Conflicting Indicators"
              explanation={evidenceAgainst[0]}
              strength="NOTE"
              type="warning"
            />
          )}
          {missingEvidence.length > 0 && (
            <EvidenceCard
              icon="🔍"
              title="Data Limitation"
              explanation={missingEvidence[0]}
              strength="MISSING"
              type="limitation"
            />
          )}
          {event.satellite_context?.cloud_cover_pct !== undefined && event.satellite_context.cloud_cover_pct > 20 && (
            <EvidenceCard
              icon="☁️"
              title="Cloud Cover Warning"
              explanation={`Cloud cover ${event.satellite_context.cloud_cover_pct}% — optical imagery may be obscured. Thermal data remains valid but visual confirmation is not possible.`}
              strength={`${event.satellite_context.cloud_cover_pct}% CLOUD`}
              source={event.satellite_context.source || 'Sentinel-2'}
              type="limitation"
            />
          )}
        </div>

        {/* Probability Breakdown (if available) */}
        {Object.keys(probs).length > 0 && (
          <div className="card" style={{ marginBottom: '20px' }}>
            <div className="card-title">AI Probability Breakdown</div>
            <div className="prob-breakdown">
              {Object.entries(probs).map(([cls, prob]) => (
                <div key={cls} className="prob-row">
                  <span className="prob-row__label">{cls.replace(/_/g, ' ')}</span>
                  <div className="prob-row__track">
                    <div
                      className="prob-row__fill"
                      style={{
                        width: `${Math.round(prob * 100)}%`,
                        background: cls === (event.classification?.label || event.classification?.class) ? 'var(--accent-teal)' : 'var(--accent-blue)',
                      }}
                    />
                  </div>
                  <span className="prob-row__val">{Math.round(prob * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}


        {/* Facility & Geographic Context */}
        <div className="card" style={{ marginBottom: '20px' }}>
          <div className="card-title">Geographic & Population Context</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
            {[
              ['Nearest Facility', facility.nearest_facility_name || facility.name || 'None'],
              ['Distance', facilityDist],
              ['Facility Type', facility.facility_type || 'Industrial'],
              ['Population (5km)', facility.population_within_5km?.toLocaleString() || 'N/A'],
              ['Coordinates', lat && lon ? `${lat.toFixed(4)}°, ${lon.toFixed(4)}°` : '—'],
              ['Time Window', `${event.time_window?.start?.split('T')[0]} → ${event.time_window?.end?.split('T')[0]}`],
            ].map(([k, v]) => (
              <div key={k}>
                <div style={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: 600, marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{k}</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: 500, fontFamily: k === 'Coordinates' ? 'var(--font-mono)' : undefined, fontSize: k === 'Coordinates' ? '11px' : '12px' }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Provenance */}
        <div className="provenance-panel">
          <div className="provenance-panel__title">Data Provenance</div>
          <div className="provenance-grid">
            {[
              ['Data source', 'NASA FIRMS'],
              ['Sensor', 'MODIS · VIIRS 375m'],
              ['Model version', event.model_version || event.engine_version || 'v2.1.0'],
              ['Data version', event.data_version || 'FIRMS-2024'],
              ['Imagery', event.satellite_context?.imagery_available ? 'Available' : 'Unavailable'],
              ['Acquisition', event.time_window?.end?.split('T')[0] || '—'],
            ].map(([k, v]) => (
              <div key={k} className="provenance-row">
                <span className="provenance-row__key">{k}</span>
                <span className="provenance-row__val">{v}</span>
              </div>
            ))}
          </div>
          {event.satellite_context?.cloud_cover_pct && event.satellite_context.cloud_cover_pct > 20 && (
            <div className="provenance-warning">
              ⚠ Cloud cover {event.satellite_context.cloud_cover_pct}% — optical imagery may not be available for visual confirmation
            </div>
          )}
        </div>

        {/* Analyst Action Bar */}
        <AnalystActionBar
          event={event}
          status={status}
          onStatusChange={setStatus}
        />

        {/* Anomaly score */}
        {anomaly > 0 && (
          <div className="card" style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '6px' }}>
              Statistical Anomaly Score
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ fontSize: '28px', fontWeight: '800', color: anomaly > 50 ? 'var(--risk-critical)' : 'var(--accent-cyan)', fontVariantNumeric: 'tabular-nums' }}>
                {anomaly}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                {anomaly > 50
                  ? 'Statistically significant deviation from baseline. Warrants immediate review.'
                  : 'Within expected variance range. No statistically significant anomaly detected.'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ─── Explainability Drawer ─── */}
      {showExplain && (
        <ExplainabilityDrawer
          onClose={() => setShowExplain(false)}
          eventId={event.event_id}
          label={event.classification?.label || 'unknown'}
          evidenceFor={evidenceFor}
          evidenceAgainst={evidenceAgainst}
          missingEvidence={missingEvidence}
          modelVersion={event.model_version}
          dataVersion={event.data_version}
        />
      )}

      {/* ─── Report Preview Modal ─── */}
      {showReport && (
        <ReportPreviewModal
          onClose={() => setShowReport(false)}
          eventId={event.event_id}
          title={classLabel}
          location={`${event.region || 'India'} · ${facilityDist} from ${facility.nearest_facility_name || facility.name || 'nearest facility'}`}
          confidence={event.classification?.confidence || 0}
          industrialLikelihood={industrial}
          operationalRisk={risk}
          evidenceFor={evidenceFor}
          label={event.classification?.label || 'unknown'}
          getReportUrl={getReportUrl}
        />
      )}

      {/* ─── Compare Events Panel ─── */}
      {showCompare && event && (
        <CompareEventsPanel
          currentEvent={event}
          availableEvents={allEvents}
          onClose={() => setShowCompare(false)}
          onSelectEvent={(newId) => {
            setShowCompare(false);
            const nextEv = allEvents.find(e => e.event_id === newId);
            if (nextEv) {
              handleSelectEvent(nextEv);
            }
          }}
        />
      )}

      {/* ─── Reclassify Modal ─── */}
      {showReclassify && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal__title">Reclassify Event {event.event_id}</div>
            <label className="modal__label">Select Correct Class</label>
            <select className="modal__select" value={reclassifyLabel} onChange={e => setReclassifyLabel(e.target.value)}>
              <option value="persistent_industrial_source">Persistent Industrial Source</option>
              <option value="industrial_fire_or_abnormal_event">Industrial Fire / Abnormal Event</option>
              <option value="wildfire_or_forest_fire">Wildfire / Forest Fire</option>
              <option value="agricultural_burning">Agricultural Burning</option>
              <option value="mining_or_other_industrial_activity">Mining / Other Industrial</option>
              <option value="unknown_requires_verification">Unknown — Requires Verification</option>
            </select>
            <label className="modal__label">Analyst Rationale</label>
            <textarea
              className="modal__textarea"
              value={reclassifyNotes}
              onChange={e => setReclassifyNotes(e.target.value)}
              placeholder="Enter justification for label override..."
            />
            <div className="modal__actions">
              <button className="btn btn--ghost" onClick={() => setShowReclassify(false)}>Cancel</button>
              <button
                className="btn btn--cyan"
                onClick={() => {
                  setShowReclassify(false);
                  setStatus('reclassified');
                }}
              >
                Submit Reclassification
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
