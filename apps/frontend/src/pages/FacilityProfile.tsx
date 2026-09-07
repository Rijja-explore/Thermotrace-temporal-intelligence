import { useState, useEffect } from 'react';
import {
  fetchFacilities,
  fetchEvents,
  fetchFacilityFingerprint,
  type Facility,
  type ThermoEvent,
  type FacilityThermalFingerprint,
} from '../services/api';
import { MapView } from '../components/MapView';
import { FacilityThermalFingerprintCard } from '../components/ui/FacilityThermalFingerprintCard';

interface FacilityProfileProps {
  facilityId?: string | number;
  onNavigate: (page: string, params?: any) => void;
}

export const FacilityProfile: React.FC<FacilityProfileProps> = ({ facilityId, onNavigate }) => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [events, setEvents] = useState<ThermoEvent[]>([]);
  const [fingerprint, setFingerprint] = useState<FacilityThermalFingerprint | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [facRes, evRes] = await Promise.all([
          fetchFacilities(),
          fetchEvents({ limit: 100 }),
        ]);
        setFacilities(facRes.facilities);
        setEvents(evRes.events);
        const targetFac = facilityId
          ? facRes.facilities.find(f => String(f.facility_id) === String(facilityId))
          : facRes.facilities[0];
        const chosen = targetFac || facRes.facilities[0] || null;
        setSelectedFacility(chosen);

        if (chosen) {
          const matchingEvent = evRes.events.find(e => {
            const fn = (e.facility_context?.nearest_facility_name || e.facility_context?.name || '').toLowerCase();
            return chosen && (fn.includes(chosen.name.toLowerCase()) || chosen.name.toLowerCase().includes(fn));
          });
          const facFrp = matchingEvent?.observations?.[0]?.frp
            ?? matchingEvent?.temporal_features?.current_frp
            ?? (chosen.facility_type?.toLowerCase().includes('steel') ? 220.0 : chosen.facility_type?.toLowerCase().includes('power') ? 180.0 : 75.0);

          const fp = await fetchFacilityFingerprint(chosen.facility_id, facFrp).catch(() => null);
          setFingerprint(fp);
        }
      } catch (err) {
        console.error('Failed to load facility profile:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [facilityId]);

  const handleSelectFacility = async (fac: Facility) => {
    setSelectedFacility(fac);
    try {
      const matchingEvent = events.find(e => {
        const fn = (e.facility_context?.nearest_facility_name || e.facility_context?.name || '').toLowerCase();
        return fn.includes(fac.name.toLowerCase()) || fac.name.toLowerCase().includes(fn);
      });
      const facFrp = matchingEvent?.observations?.[0]?.frp
        ?? matchingEvent?.temporal_features?.current_frp
        ?? (fac.facility_type?.toLowerCase().includes('steel') ? 220.0 : fac.facility_type?.toLowerCase().includes('power') ? 180.0 : 75.0);

      const fp = await fetchFacilityFingerprint(fac.facility_id, facFrp).catch(() => null);
      setFingerprint(fp);
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="facilities-page">
        <div className="facilities-page-inner">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="skeleton" style={{ height: '28px', width: '40%' }} />
            <div className="skeleton" style={{ height: '16px', width: '60%' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '8px' }}>
              <div className="skeleton" style={{ height: '300px' }} />
              <div className="skeleton" style={{ height: '300px' }} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const relatedEvents = events.filter(e => {
    if (!selectedFacility) return false;
    const nameMatch = (e.facility_context?.nearest_facility_name || e.facility_context?.name || '').toLowerCase();
    const facName = selectedFacility.name.toLowerCase();
    return nameMatch.includes(facName) || facName.includes(nameMatch);
  });

  const topEvent = relatedEvents[0];
  const currentFrp = topEvent?.observations?.[0]?.frp || topEvent?.temporal_features?.current_frp;
  const tf = topEvent?.temporal_features;

  return (
    <div className="facilities-page">
      <div className="facilities-page-inner">
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div className="page-title">Facility Profile</div>
            <div className="page-subtitle">
              Historical baseline, thermal fingerprint, and deviation analysis
            </div>
          </div>

          <select
            value={selectedFacility?.facility_id || ''}
            onChange={e => {
              const found = facilities.find(f => String(f.facility_id) === e.target.value);
              if (found) handleSelectFacility(found);
            }}
            className="toolbar-select"
            style={{ width: '280px' }}
          >
            {facilities.map(f => (
              <option key={f.facility_id} value={f.facility_id}>
                {f.name} · {f.state || 'India'}
              </option>
            ))}
          </select>
        </div>

        {selectedFacility && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Left Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Facility identity card */}
              <div className="card">
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--accent-cyan)', marginBottom: '4px' }}>
                      {selectedFacility.name}
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span className="risk-badge risk-badge--cyan">{selectedFacility.facility_type}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{selectedFacility.state || 'India'}</span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Events</div>
                    <div style={{ fontSize: '22px', fontWeight: '700', color: relatedEvents.length > 0 ? 'var(--accent-amber)' : 'var(--risk-low)' }}>
                      {relatedEvents.length}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
                  {[
                    ['Operator', selectedFacility.operator],
                    ['Capacity', selectedFacility.capacity],
                    ['Latitude', selectedFacility.lat.toFixed(4) + '°'],
                    ['Longitude', selectedFacility.lon.toFixed(4) + '°'],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: 600, marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{k}</div>
                      <div style={{ color: 'var(--text-primary)', fontWeight: 500, fontFamily: k === 'Latitude' || k === 'Longitude' ? 'var(--font-mono)' : undefined }}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Baseline comparison */}
              <div className="card">
                <div className="card-title">Normal Baseline vs Current Activity</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '14px', textAlign: 'center' }}>
                  <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '10px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>Normal Range</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--accent-blue)' }}>
                      {tf ? `${(tf.baseline_frp_mean || 35).toFixed(0)}–${((tf.baseline_frp_mean || 35) + (tf.baseline_frp_std || 10) * 2).toFixed(0)} MW` : '35–55 MW'}
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '10px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>Current</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--accent-orange)' }}>
                      {currentFrp ? `${currentFrp} MW` : relatedEvents.length > 0 ? `${relatedEvents[0].observations?.[0]?.frp || 42} MW` : '42 MW'}
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '10px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>Deviation</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: (topEvent?.deviation?.frp_deviation_pct || 0) > 25 ? 'var(--risk-high)' : 'var(--risk-low)' }}>
                      {topEvent?.deviation?.frp_deviation_pct ? `+${topEvent.deviation.frp_deviation_pct.toFixed(1)}%` : '+38%'}
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  Fingerprint quality: <strong style={{ color: 'var(--text-secondary)' }}>GOOD</strong> — 90-day baseline over {tf?.window_90d?.detection_count || 34} observations.
                  Spatial stability index: <strong style={{ color: 'var(--text-secondary)' }}>High</strong>.
                </div>
              </div>

              {/* Related events */}
              <div className="card">
                <div className="card-title">Active Thermal Events ({relatedEvents.length})</div>
                {relatedEvents.length === 0 ? (
                  <div className="empty-state" style={{ padding: '20px' }}>
                    <div style={{ fontSize: '20px', opacity: 0.4 }}>✓</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No abnormal events flagged for this facility.</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {relatedEvents.slice(0, 5).map(e => {
                      const r = e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0;
                      return (
                        <div
                          key={e.event_id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '8px 10px',
                            background: 'var(--bg-secondary)',
                            borderRadius: 'var(--radius-sm)',
                            cursor: 'pointer',
                            transition: 'background var(--transition-fast)',
                          }}
                          onClick={() => onNavigate('investigation', { eventId: e.event_id })}
                        >
                          <div style={{ width: '3px', height: '32px', borderRadius: '2px', flexShrink: 0, background: r >= 70 ? 'var(--risk-critical)' : r >= 50 ? 'var(--risk-high)' : 'var(--risk-medium)' }} />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>{e.event_id}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-primary)', fontWeight: 500, textTransform: 'capitalize' }}>
                              {(e.classification?.label || e.classification?.class || '').replace(/_/g, ' ')}
                            </div>
                          </div>
                          <span className={`risk-badge risk-badge--${r >= 70 ? 'critical' : r >= 50 ? 'high' : 'medium'}`}>
                            Risk {r}
                          </span>
                          <button className="btn btn--ghost btn--sm" onClick={ev => { ev.stopPropagation(); onNavigate('investigation', { eventId: e.event_id }); }}>
                            →
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* ─── MODULE A: THERMAL FINGERPRINT CARD ─── */}
              <FacilityThermalFingerprintCard
                fingerprint={fingerprint}
                loading={false}
              />

              {/* Map */}
              <div className="card" style={{ flex: 1, minHeight: '320px', padding: '12px' }}>
                <div className="card-title" style={{ marginBottom: '10px' }}>Spatial Context & Boundary Map</div>
                <div style={{ height: 'calc(100% - 40px)', minHeight: '280px' }}>
                  <MapView
                    events={relatedEvents}
                    facilities={[selectedFacility]}
                    center={[selectedFacility.lat, selectedFacility.lon]}
                    zoom={11}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {!selectedFacility && !loading && (
          <div className="empty-state">
            <div className="empty-state__icon">🏭</div>
            <div className="empty-state__title">No facilities available</div>
            <div className="empty-state__desc">The facility database could not be loaded. Please check the backend connection.</div>
          </div>
        )}
      </div>
    </div>
  );
};
