import { useEffect, useState, useCallback } from 'react';
import MapView from '../components/MapView';
import EventPanel from '../components/EventPanel';
import type { ThermoEvent, SummaryResponse, Alert } from '../services/api';
import { fetchEvents, fetchSummary, fetchAlerts, fetchEventsFromJson } from '../services/api';

interface DashboardProps {
  onNavigate?: (page: string, params?: any) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [events, setEvents] = useState<ThermoEvent[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<ThermoEvent | null>(null);

  // Filters
  const [filterRegion, setFilterRegion] = useState('India');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [filterClass, setFilterClass] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Try backend API first
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
      setSummary(summaryRes);
      setAlerts(alertsRes.alerts.slice(0, 10));
    } catch {
      // Fallback to local JSON
      console.warn('[Dashboard] Backend unavailable, using local data');
      const localEvents = await fetchEventsFromJson(filterRegion);
      setEvents(localEvents);
      setSummary({
        total: localEvents.length,
        critical: localEvents.filter(e => (e.scores?.operational_risk || 0) >= 80).length,
        high: localEvents.filter(e => { const r = e.scores?.operational_risk || 0; return r >= 60 && r < 80; }).length,
        industrial: localEvents.filter(e => (e.scores?.industrial_likelihood || 0) >= 70).length,
        persistent: 0,
        abnormal: 0,
        unknown: 0,
        requires_verification: localEvents.filter(e => e.status === 'requires_verification').length,
        by_status: {},
      });
      setAlerts([]);
    }
    setLoading(false);
  }, [filterRegion, filterStatus, filterRisk, filterClass]);

  useEffect(() => {
    loadData();
    // Poll for live data every 1 hour (3600 seconds)
    const interval = setInterval(() => {
      loadData();
    }, 3600000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Apply local search filter
  const displayedEvents = searchQuery
    ? events.filter(e =>
        e.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.classification?.class || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.facility_context?.name || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : events;

  const handleSelectEvent = (event: ThermoEvent) => {
    setSelectedEvent(event);
  };

  return (
    <div className="main-content">
      {/* ─── Left Sidebar ─── */}
      <div className="sidebar sidebar-left">
        {/* Summary Cards */}
        <div className="sidebar__section">
          <div className="sidebar__section-title">Event Summary</div>
          <div className="summary-grid">
            <div className="summary-card summary-card--total">
              <div className="summary-card__label">Total</div>
              <div className="summary-card__value">{summary?.total ?? '—'}</div>
            </div>
            <div className="summary-card summary-card--critical">
              <div className="summary-card__label">Critical</div>
              <div className="summary-card__value">{summary?.critical ?? '—'}</div>
            </div>
            <div className="summary-card summary-card--industrial">
              <div className="summary-card__label">Industrial</div>
              <div className="summary-card__value">{summary?.industrial ?? '—'}</div>
            </div>
            <div className="summary-card summary-card--high">
              <div className="summary-card__label">High Risk</div>
              <div className="summary-card__value">{summary?.high ?? '—'}</div>
            </div>
            <div className="summary-card summary-card--persistent">
              <div className="summary-card__label">Persistent</div>
              <div className="summary-card__value">{summary?.persistent ?? '—'}</div>
            </div>
            <div className="summary-card summary-card--unknown">
              <div className="summary-card__label">Unknown</div>
              <div className="summary-card__value">{summary?.unknown ?? '—'}</div>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="sidebar__section">
          <div className="sidebar__section-title">Search</div>
          <div className="search-input">
            <span className="search-input__icon">🔍</span>
            <input
              type="text"
              placeholder="Event ID, class, or facility..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Filters */}
        <div className="sidebar__section">
          <div className="sidebar__section-title">
            <span>Filters</span>
            {filterRegion === 'India' && (
              <span style={{ fontSize: '11px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                🇮🇳 India Focus
              </span>
            )}
          </div>

          <div className="filter-group">
            <label className="filter-group__label">Region / Geography</label>
            <select
              className="filter-select"
              value={filterRegion}
              onChange={e => setFilterRegion(e.target.value)}
              style={{
                borderColor: filterRegion === 'India' ? 'var(--accent-cyan)' : undefined,
                fontWeight: 600,
              }}
            >
              <optgroup label="Broad Geographies">
                <option value="India">🇮🇳 India (Primary Focus)</option>
                <option value="Global">🌍 Global (Outside India)</option>
                <option value="All">🌐 All Detections Worldwide</option>
              </optgroup>
              <optgroup label="Indian States & Industrial Hubs">
                <option value="Gujarat">Gujarat (Jamnagar, Vadinar, Koyali)</option>
                <option value="Maharashtra">Maharashtra (Mumbai Complex)</option>
                <option value="Odisha">Odisha (Paradip & Rourkela)</option>
                <option value="West Bengal">West Bengal (Haldia & Kolkata)</option>
                <option value="Tamil Nadu">Tamil Nadu (Chennai Manali)</option>
                <option value="Jharkhand">Jharkhand (Jamshedpur & Bokaro)</option>
                <option value="Chhattisgarh">Chhattisgarh (Bhilai Steel)</option>
                <option value="Assam">Assam (Digboi, Numaligarh, Bongaigaon)</option>
                <option value="Karnataka">Karnataka (Mangalore MRPL)</option>
                <option value="Kerala">Kerala (Kochi Refinery)</option>
                <option value="Haryana">Haryana (Panipat Refinery)</option>
                <option value="Uttar Pradesh">Uttar Pradesh (Mathura Refinery)</option>
                <option value="Bihar">Bihar (Barauni Refinery)</option>
                <option value="Punjab">Punjab (Bhatinda HMEL)</option>
                <option value="Madhya Pradesh">Madhya Pradesh (Bina Refinery)</option>
                <option value="Andhra Pradesh">Andhra Pradesh (Visakhapatnam)</option>
              </optgroup>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-group__label">Status</label>
            <select className="filter-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="">All</option>
              <option value="requires_verification">Requires Verification</option>
              <option value="critical_alert">Critical Alert</option>
              <option value="monitored">Monitored</option>
              <option value="investigating">Investigating</option>
              <option value="confirmed">Confirmed</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-group__label">Risk Level</label>
            <select className="filter-select" value={filterRisk} onChange={e => setFilterRisk(e.target.value)}>
              <option value="">All</option>
              <option value="80">Critical (≥80)</option>
              <option value="60">High (≥60)</option>
              <option value="40">Medium (≥40)</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-group__label">Classification</label>
            <select className="filter-select" value={filterClass} onChange={e => setFilterClass(e.target.value)}>
              <option value="">All Classes</option>
              <option value="industrial">Industrial</option>
              <option value="flaring">Flaring</option>
              <option value="anomalous">Anomalous</option>
              <option value="agricultural">Agricultural</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
        </div>
      </div>

      {/* ─── Center (Map & Panel) ─── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, padding: '16px 24px', background: 'var(--bg-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)' }}>
            <div>
              <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '4px' }}>Monitoring Surface</div>
              <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>{filterRegion} · <span style={{ color: 'var(--text-secondary)' }}>thermal events</span></div>
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
               <div style={{ display: 'flex', background: 'var(--bg-tertiary)', borderRadius: '6px', border: '1px solid var(--border-primary)', overflow: 'hidden' }}>
                 <button style={{ padding: '6px 12px', border: 'none', background: 'transparent', color: 'var(--text-muted)', fontSize: '12px', cursor: 'pointer' }}>7D</button>
                 <button style={{ padding: '6px 12px', border: 'none', background: 'white', color: 'var(--text-primary)', fontSize: '12px', fontWeight: 'bold', boxShadow: 'var(--shadow-sm)', cursor: 'pointer' }}>30D</button>
                 <button style={{ padding: '6px 12px', border: 'none', background: 'transparent', color: 'var(--text-muted)', fontSize: '12px', cursor: 'pointer' }}>90D</button>
               </div>
               <button style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'white', border: '1px solid var(--border-primary)', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                 <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                 Layers
               </button>
            </div>
          </div>
          {loading ? (
            <div className="loading-overlay">
              <div className="loading-spinner" />
              <span className="loading-text">Loading thermal data...</span>
            </div>
          ) : (
            <MapView
              events={displayedEvents}
              selectedEventId={selectedEvent?.event_id}
              onSelectEvent={handleSelectEvent}
            />
          )}
        </div>

        {/* Event Detail Panel (Side-by-side) */}
        {selectedEvent && (
          <div className="event-panel-container">
            <EventPanel
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
              onNavigate={(eventId) => onNavigate?.('investigation', { eventId })}
            />
          </div>
        )}
      </div>

      {/* ─── Right Sidebar (Alerts) ─── */}
      <div className="sidebar sidebar-right" style={{ minWidth: '320px' }}>
        <div className="sidebar__section" style={{ flex: 1 }}>
          <div className="sidebar__section-title">
            Review Queue
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Priority alerts <span style={{ color: 'var(--accent-red)' }}>{alerts.filter(a => a.severity === 'critical').length || alerts.length}</span>
            </div>
            <a href="#" style={{ fontSize: '12px', color: 'var(--accent-blue)', textDecoration: 'none', fontWeight: 500 }}>View all</a>
          </div>
          
          {alerts.length === 0 && !loading && (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
              Queue is healthy
            </div>
          )}
          {alerts.map(alert => (
            <div
              key={alert.alert_id}
              className="alert-item"
              onClick={() => {
                const ev = events.find(e => e.event_id === alert.event_id);
                if (ev) handleSelectEvent(ev);
              }}
            >
              <span className={`alert-dot alert-dot--${alert.severity}`} />
              <div className="alert-item__text" title={`${alert.title}\n${alert.location}`}>
                <div className="alert-item__title">{alert.title}</div>
                <div className="alert-item__sub">{alert.location}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                 <div style={{ fontSize: '14px', fontWeight: 600 }}>{alert.operational_risk}</div>
                 <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>1h ago</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
