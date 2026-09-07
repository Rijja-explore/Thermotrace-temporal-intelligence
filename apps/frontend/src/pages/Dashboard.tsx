import { useEffect, useState, useCallback } from 'react';
import MapView from '../components/MapView';
import EventPanel from '../components/EventPanel';
import type { ThermoEvent, SummaryResponse, Alert } from '../services/api';
import { fetchEvents, fetchSummary, fetchAlerts, fetchEventsFromJson } from '../services/api';
import LayerByLayerPipeline from '../components/ui/LayerByLayerPipeline';
import { autoDispatchCriticalAlerts } from '../services/alertEmail';

interface DashboardProps {
  onNavigate?: (page: string, params?: any) => void;
}

// ─── Metric Card ───
function MetricCard({
  label,
  value,
  icon,
  trend,
  trendDir,
  desc,
  accent,
  loading,
}: {
  label: string;
  value: number | string;
  icon: string;
  trend?: string;
  trendDir?: 'up' | 'down' | 'neutral';
  desc: string;
  accent: string;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="metric-card skeleton" style={{ '--metric-accent': accent } as any}>
        <div style={{ height: '100%' }} />
      </div>
    );
  }

  return (
    <div className="metric-card" style={{ '--metric-accent': accent } as any}>
      <div className="metric-card__icon">{icon}</div>
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__value">{value}</div>
      {trend && (
        <div className={`metric-card__trend metric-card__trend--${trendDir ?? 'neutral'}`}>
          {trend}
        </div>
      )}
      <div className="metric-card__desc">{desc}</div>
    </div>
  );
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [events, setEvents] = useState<ThermoEvent[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<ThermoEvent | null>(null);
  const [autoEmailCount, setAutoEmailCount] = useState(0);
  const [showEmailToast, setShowEmailToast] = useState(false);

  const [viewMode, setViewMode] = useState<'map' | 'intelligence'>('map');

  // Filters
  const [filterRegion, setFilterRegion] = useState('India');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [filterClass, setFilterClass] = useState('');
  const [filterEscalation, setFilterEscalation] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [timeRange, setTimeRange] = useState('30D');
  const [showPipelineModal, setShowPipelineModal] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { region: filterRegion };
      if (filterStatus) params.status = filterStatus;
      if (filterRisk) params.risk_min = parseInt(filterRisk);
      if (filterClass) params.event_class = filterClass;

      const [eventsRes, summaryRes, alertsRes] = await Promise.all([
        fetchEvents(params),
        fetchSummary(filterRegion),
        fetchAlerts(undefined, filterRegion),
      ]);

      setEvents(eventsRes.events);
      (window as any).__lastLoadedEvents = eventsRes.events;
      setSummary(summaryRes);
      setAlerts(alertsRes.alerts.slice(0, 15));
    } catch {
      console.warn('[Dashboard] Backend unavailable, using local data');
      const localEvents = await fetchEventsFromJson(filterRegion);
      setEvents(localEvents);
      (window as any).__lastLoadedEvents = localEvents;
      setSummary({
        total: localEvents.length,
        critical: localEvents.filter(e => (e.scores?.operational_risk || 0) >= 80).length,
        high: localEvents.filter(e => { const r = e.scores?.operational_risk || 0; return r >= 60 && r < 80; }).length,
        industrial: localEvents.filter(e => (e.scores?.industrial_likelihood || 0) >= 70).length,
        persistent: localEvents.filter(e => (e.temporal_features?.persistence_ratio || 0) >= 0.6).length,
        abnormal: localEvents.filter(e => e.anomaly?.is_abnormal).length,
        unknown: localEvents.filter(e => (e.classification?.label || '').includes('unknown')).length,
        requires_verification: localEvents.filter(e => e.status === 'requires_verification').length,
        by_status: {},
      });
      setAlerts([]);
    }
    setLoading(false);

    // Auto-dispatch email alerts for critical events
    const sent = await autoDispatchCriticalAlerts(
      (window as any).__lastLoadedEvents || []
    );
    if (sent > 0) {
      setAutoEmailCount(sent);
      setShowEmailToast(true);
      setTimeout(() => setShowEmailToast(false), 5000);
    }
  }, [filterRegion, filterStatus, filterRisk, filterClass]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3600000);
    return () => clearInterval(interval);
  }, [loadData]);

  const displayedEvents = events.filter(e => {
    if (searchQuery) {
      const match =
        e.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.classification?.class || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.facility_context?.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.facility_context?.nearest_facility_name || '').toLowerCase().includes(searchQuery.toLowerCase());
      if (!match) return false;
    }
    if (filterPriority) {
      const p = e.incident_priority || ((e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0) >= 75 ? 'CRITICAL' : (e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0) >= 50 ? 'HIGH' : 'MEDIUM');
      if (p !== filterPriority) return false;
    }
    if (filterEscalation) {
      const esc = e.early_warning?.escalation_state || ((e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0) >= 75 ? 'CRITICAL_ESCALATION' : (e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0) >= 50 ? 'ESCALATING' : 'STABLE');
      if (esc !== filterEscalation) return false;
    }
    return true;
  });

  const criticalAlerts = alerts.filter(a => a.severity === 'critical');
  const highAlerts = alerts.filter(a => a.severity === 'high');
  const verifyAlerts = alerts.filter(a => a.status === 'requires_verification');
  const displayAlerts = [...criticalAlerts, ...highAlerts, ...verifyAlerts].slice(0, 12);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* ─── Auto Email Toast ─── */}
      {showEmailToast && (
        <div style={{
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
          background: 'rgba(13, 25, 41, 0.97)',
          border: '1px solid rgba(79,209,139,0.4)',
          borderLeft: '3px solid #4FD18B',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          display: 'flex', alignItems: 'center', gap: '10px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          animation: 'fadeIn 0.3s ease-out',
          maxWidth: '340px',
        }}>
          <span style={{ fontSize: '16px' }}>📧</span>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#4FD18B', marginBottom: '2px' }}>
              Alert Email Auto-Dispatched
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {autoEmailCount} critical event{autoEmailCount > 1 ? 's' : ''} notified to rijja2310119@ssn.edu.in
            </div>
          </div>
        </div>
      )}

      {/* ─── KPI Strip ─── */}
      <div className="kpi-strip">
        <MetricCard
          label="Total Anomalies"
          value={summary?.total ?? '—'}
          icon="🛰️"
          trend={loading ? undefined : `${displayedEvents.length} visible`}
          desc="Active thermal detections in period"
          accent="var(--accent-cyan)"
          loading={loading}
        />
        <MetricCard
          label="Industrial Sources"
          value={summary?.industrial ?? '—'}
          icon="🏭"
          trend={summary ? `${Math.round(((summary.industrial || 0) / Math.max(summary.total, 1)) * 100)}% of total` : undefined}
          trendDir="neutral"
          desc="Probable industrial origin events"
          accent="var(--accent-amber)"
          loading={loading}
        />
        <MetricCard
          label="Persistent Sources"
          value={summary?.persistent ?? '—'}
          icon="📡"
          trend={loading ? undefined : '+recurring behaviour'}
          trendDir="up"
          desc="Recurring thermal behaviour detected"
          accent="var(--accent-blue)"
          loading={loading}
        />
        <MetricCard
          label="Abnormal Events"
          value={summary?.abnormal ?? '—'}
          icon="⚡"
          desc="Statistically above facility baseline"
          accent="var(--risk-high)"
          loading={loading}
        />
        <MetricCard
          label="High-Risk Alerts"
          value={summary?.critical ?? '—'}
          icon="🚨"
          trend={loading ? undefined : 'Requires verification'}
          trendDir="up"
          desc="Operational risk score ≥ 80"
          accent="var(--risk-critical)"
          loading={loading}
        />
      </div>

      {/* ─── Body: Map + Alert Rail ─── */}
      <div className="dashboard-body">
        <div className="dashboard-map-area">
          {/* Map Toolbar */}
          <div className="dashboard-map-toolbar">
            <div className="dashboard-map-toolbar__title">
              {filterRegion} <span>· thermal event map</span>
            </div>

            {/* Mode Switcher */}
            <div className="toolbar-btn-group" style={{ background: 'rgba(0,0,0,0.3)', padding: '2px', borderRadius: '6px' }}>
              <button
                className={`toolbar-btn ${viewMode === 'map' ? 'toolbar-btn--active' : ''}`}
                onClick={() => setViewMode('map')}
                title="Geospatial satellite event map view"
              >
                🗺️ Map Mode
              </button>
              <button
                className={`toolbar-btn ${viewMode === 'intelligence' ? 'toolbar-btn--active' : ''}`}
                style={viewMode === 'intelligence' ? { background: 'rgba(67, 217, 232, 0.25)', borderColor: 'var(--accent-cyan)', color: 'var(--accent-cyan)' } : {}}
                onClick={() => setViewMode('intelligence')}
                title="Unified intelligence matrix across all monitored facilities"
              >
                ⚡ Intelligence Mode
              </button>
            </div>

            {/* Time range */}
            <div className="toolbar-btn-group">
              {['7D', '30D', '90D'].map(r => (
                <button
                  key={r}
                  className={`toolbar-btn ${timeRange === r ? 'toolbar-btn--active' : ''}`}
                  onClick={() => setTimeRange(r)}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Region filter */}
            <div className="toolbar-filter-group">
              <span className="toolbar-label">Region</span>
              <select className="toolbar-select" value={filterRegion} onChange={e => setFilterRegion(e.target.value)}>
                <optgroup label="Broad">
                  <option value="India">🇮🇳 India</option>
                  <option value="Global">🌍 Global</option>
                  <option value="All">🌐 All</option>
                </optgroup>
                <optgroup label="Indian States">
                  <option value="Gujarat">Gujarat</option>
                  <option value="Maharashtra">Maharashtra</option>
                  <option value="Odisha">Odisha</option>
                  <option value="West Bengal">West Bengal</option>
                  <option value="Tamil Nadu">Tamil Nadu</option>
                  <option value="Jharkhand">Jharkhand</option>
                  <option value="Assam">Assam</option>
                  <option value="Karnataka">Karnataka</option>
                  <option value="Kerala">Kerala</option>
                  <option value="Andhra Pradesh">Andhra Pradesh</option>
                </optgroup>
              </select>
            </div>

            {/* Priority filter */}
            <div className="toolbar-filter-group">
              <span className="toolbar-label">Priority</span>
              <select className="toolbar-select" value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
                <option value="">All Priorities</option>
                <option value="CRITICAL">🔴 Critical</option>
                <option value="HIGH">🟠 High</option>
                <option value="MEDIUM">🟡 Medium</option>
                <option value="LOW">🟢 Low</option>
              </select>
            </div>

            {/* Escalation filter */}
            <div className="toolbar-filter-group">
              <span className="toolbar-label">Escalation</span>
              <select className="toolbar-select" value={filterEscalation} onChange={e => setFilterEscalation(e.target.value)}>
                <option value="">All Escalation</option>
                <option value="CRITICAL_ESCALATION">Critical Escalation</option>
                <option value="ESCALATING">Escalating</option>
                <option value="WATCH">Watch</option>
                <option value="STABLE">Stable</option>
              </select>
            </div>

            {/* Status filter */}
            <div className="toolbar-filter-group">
              <span className="toolbar-label">Status</span>
              <select className="toolbar-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                <option value="">All Statuses</option>
                <option value="requires_verification">Needs Verification</option>
                <option value="critical_alert">Critical Alert</option>
                <option value="monitored">Monitored</option>
                <option value="confirmed">Confirmed</option>
              </select>
            </div>

            {/* NASA Layer-by-Layer Pipeline Inspector Button */}
            <button
              className="toolbar-btn"
              style={{
                background: 'rgba(67, 217, 232, 0.15)',
                color: 'var(--accent-cyan)',
                borderColor: 'rgba(67, 217, 232, 0.4)',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              onClick={() => setShowPipelineModal(true)}
              title="Inspect the 7-layer data processing pipeline from NASA satellites to ground sectors"
            >
              <span>🛰️</span> NASA Pipeline Layers
            </button>

            {/* Search */}
            <div className="toolbar-search">
              <span className="toolbar-search__icon">🔍</span>
              <input
                type="text"
                placeholder="Search event ID, facility..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {/* Map or Intelligence Grid */}
          <div className="map-area" style={{ overflow: viewMode === 'intelligence' ? 'auto' : 'hidden' }}>
            {loading ? (
              <div style={{ height: '100%' }}>
                <div className="skeleton" style={{ height: '100%', borderRadius: 0 }} />
              </div>
            ) : displayedEvents.length === 0 ? (
              <div className="empty-state" style={{ height: '100%' }}>
                <div className="empty-state__icon">🗺️</div>
                <div className="empty-state__title">No events match the current filters</div>
                <div className="empty-state__desc">Try expanding the time range or resetting priority/escalation filters.</div>
                <button className="empty-state__action" onClick={() => { setFilterStatus(''); setFilterRisk(''); setFilterClass(''); setFilterEscalation(''); setFilterPriority(''); setSearchQuery(''); }}>
                  Reset Filters
                </button>
              </div>
            ) : viewMode === 'map' ? (
              <MapView
                events={displayedEvents}
                selectedEventId={selectedEvent?.event_id}
                onSelectEvent={setSelectedEvent}
              />
            ) : (
              /* ─── MODULE N: INTELLIGENCE MODE MATRIX ─── */
              <div style={{ padding: '20px', background: '#0B111E', minHeight: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#FFF', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      Command Center — Facility Thermal Intelligence Matrix
                    </h3>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Facility Baseline Deviation (σ) · Temporal Trend Velocity · Dispersion Risk · Incident Priority Ranking
                    </p>
                  </div>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '4px 10px', borderRadius: '4px', background: 'rgba(67, 217, 232, 0.15)', color: 'var(--accent-cyan)', border: '1px solid rgba(67, 217, 232, 0.3)' }}>
                    {displayedEvents.length} MONITORED EVENTS
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
                  {displayedEvents.map(ev => {
                    const rScore = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 50;
                    const devZ = ev.abnormality_z || (ev.temporal_features?.deviation_sigma) || (rScore >= 75 ? 4.2 : rScore >= 50 ? 2.1 : 0.8);
                    const escState = ev.early_warning?.escalation_state || (rScore >= 75 ? 'CRITICAL_ESCALATION' : rScore >= 50 ? 'ESCALATING' : 'STABLE');
                    const prio = ev.incident_priority || (rScore >= 75 ? 'CRITICAL' : rScore >= 50 ? 'HIGH' : 'MEDIUM');
                    const facName = ev.facility_context?.nearest_facility_name || ev.facility_context?.name || 'Industrial Facility';
                    const cLabel = (ev.classification?.label || ev.classification?.class || 'Thermal Source').replace(/_/g, ' ');

                    return (
                      <div
                        key={ev.event_id}
                        style={{
                          background: '#101927',
                          border: `1px solid ${prio === 'CRITICAL' ? 'rgba(239,68,68,0.4)' : '#1E293B'}`,
                          borderRadius: '10px',
                          padding: '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                          transition: 'transform 0.2s, border-color 0.2s',
                        }}
                      >
                        <div>
                          {/* Card Header */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                              {ev.event_id}
                            </span>
                            <span
                              style={{
                                fontSize: '10px',
                                fontFamily: 'var(--font-mono)',
                                fontWeight: 800,
                                padding: '3px 8px',
                                borderRadius: '4px',
                                textTransform: 'uppercase',
                                background: prio === 'CRITICAL' ? 'rgba(239,68,68,0.2)' : prio === 'HIGH' ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)',
                                color: prio === 'CRITICAL' ? '#FF5C6C' : prio === 'HIGH' ? '#F59E0B' : '#10B981',
                                border: `1px solid ${prio === 'CRITICAL' ? 'rgba(239,68,68,0.4)' : 'transparent'}`,
                              }}
                            >
                              {prio} PRIORITY
                            </span>
                          </div>

                          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FFF', marginBottom: '2px', textTransform: 'capitalize' }}>
                            {cLabel}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '14px' }}>
                            📍 {facName}
                          </div>

                          {/* 3 Metric Pills */}
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '14px' }}>
                            <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '6px', padding: '8px' }}>
                              <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                                Deviation
                              </div>
                              <div style={{ fontSize: '14px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: devZ >= 3 ? '#FF5C6C' : devZ >= 1.5 ? '#F59E0B' : '#10B981' }}>
                                +{typeof devZ === 'number' ? devZ.toFixed(1) : devZ}σ
                              </div>
                            </div>

                            <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '6px', padding: '8px' }}>
                              <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                                Escalation
                              </div>
                              <div style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: escState.includes('CRITICAL') ? '#FF5C6C' : '#F59E0B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {escState.replace('_ESCALATION', '')}
                              </div>
                            </div>

                            <div style={{ background: '#0B1321', border: '1px solid #1E293B', borderRadius: '6px', padding: '8px' }}>
                              <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                                Risk Score
                              </div>
                              <div style={{ fontSize: '14px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: rScore >= 70 ? '#FF5C6C' : '#43D9E8' }}>
                                {rScore}/100
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Card Action */}
                        <button
                          className="btn btn--cyan btn--sm"
                          style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
                          onClick={() => onNavigate?.('investigation', { eventId: ev.event_id })}
                        >
                          Open Intelligence Dossier →
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ─── Event Detail Panel ─── */}
        {selectedEvent && (
          <div className="event-panel-container">
            <EventPanel
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
              onNavigate={eventId => onNavigate?.('investigation', { eventId })}
            />
          </div>
        )}

        {/* ─── Alert Rail ─── */}
        {!selectedEvent && (
          <div className="alert-rail">
            <div className="alert-rail__header">
              <div className="alert-rail__title">Priority Queue</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="alert-rail__count">
                  {criticalAlerts.length + highAlerts.length}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  pending review
                </span>
              </div>
              <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                <span className="risk-badge risk-badge--critical">{criticalAlerts.length} Critical</span>
                <span className="risk-badge risk-badge--high">{highAlerts.length} High</span>
              </div>
            </div>

            <div className="alert-rail__body">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <div className="skeleton skeleton--text" style={{ width: '60%' }} />
                    <div className="skeleton skeleton--text" style={{ width: '90%' }} />
                    <div className="skeleton skeleton--text" style={{ width: '40%' }} />
                  </div>
                ))
              ) : displayAlerts.length === 0 ? (
                <div className="empty-state" style={{ padding: '32px 16px' }}>
                  <div style={{ fontSize: '24px', opacity: 0.4 }}>✓</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', lineHeight: '1.5' }}>
                    No high-priority alerts for this region and filter combination.
                  </div>
                </div>
              ) : (
                displayAlerts.map(alert => (
                  <button
                    key={alert.alert_id}
                    className="alert-row"
                    onClick={() => {
                      const ev = events.find(e => e.event_id === alert.event_id);
                      if (ev) setSelectedEvent(ev);
                      else onNavigate?.('investigation', { eventId: alert.event_id });
                    }}
                  >
                    <div className={`alert-row__priority-bar alert-row__priority-bar--${alert.severity}`} />
                    <div className="alert-row__content">
                      <div className="alert-row__id">{alert.event_id}</div>
                      <div className="alert-row__title">{alert.title}</div>
                      <div className="alert-row__location">{alert.location}</div>
                      <div className="alert-row__meta">
                        <span className={`alert-row__score alert-row__score--${alert.severity}`}>
                          Risk {alert.operational_risk}
                        </span>
                        <span className="alert-row__time">
                          {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}
                        </span>
                        <button className="alert-row__action" onClick={e => {
                          e.stopPropagation();
                          onNavigate?.('investigation', { eventId: alert.event_id });
                        }}>
                          Investigate →
                        </button>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>

            {/* View all */}
            <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border-subtle)', flexShrink: 0 }}>
              <button
                className="btn btn--ghost btn--sm"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => onNavigate?.('alerts')}
              >
                View All Alerts →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ─── NASA Layer-by-Layer Pipeline Modal ─── */}
      {showPipelineModal && (
        <div className="notif-modal-backdrop" onClick={() => setShowPipelineModal(false)}>
          <div
            className="notif-modal"
            style={{ maxWidth: '980px', maxHeight: '90vh', overflowY: 'auto' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '12px 16px 0' }}>
              <button
                className="notif-modal__close-btn"
                onClick={() => setShowPipelineModal(false)}
              >
                ✕
              </button>
            </div>
            <div style={{ padding: '0 16px 16px' }}>
              <LayerByLayerPipeline />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
