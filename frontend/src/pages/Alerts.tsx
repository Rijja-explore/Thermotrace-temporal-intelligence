import { useEffect, useState } from 'react';
import type { Alert } from '../services/api';
import { fetchAlerts } from '../services/api';
import RiskBadge from '../components/RiskBadge';

interface AlertsProps {
  onNavigate?: (page: string, params?: any) => void;
}

export default function Alerts({ onNavigate }: AlertsProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterRegion, setFilterRegion] = useState('India');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [criticalCount, setCriticalCount] = useState(0);
  const [highCount, setHighCount] = useState(0);
  const [mediumCount, setMediumCount] = useState(0);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetchAlerts(filterSeverity || undefined, filterRegion);
        setAlerts(res.alerts);
        setCriticalCount(res.critical_count);
        setHighCount(res.high_count);
        setMediumCount(res.medium_count);
      } catch {
        setAlerts([]);
      }
      setLoading(false);
    }
    load();
  }, [filterSeverity, filterRegion]);

  return (
    <div className="main-content">
      <div className="alerts-page">
        {/* Header */}
        <div className="alerts-header">
          <div>
            <h1 className="alerts-header__title">
              🔔 Alert Centre
              {filterRegion === 'India' && (
                <span style={{ fontSize: '13px', marginLeft: '12px', color: 'var(--accent-cyan)', fontWeight: 500 }}>
                  🇮🇳 Focused on India
                </span>
              )}
            </h1>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <span className="risk-badge risk-badge--critical">Critical: {criticalCount}</span>
              <span className="risk-badge risk-badge--high">High: {highCount}</span>
              <span className="risk-badge risk-badge--medium">Medium: {mediumCount}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              className="filter-select"
              style={{
                width: '210px',
                borderColor: filterRegion === 'India' ? 'var(--accent-cyan)' : undefined,
                fontWeight: 600,
              }}
              value={filterRegion}
              onChange={e => setFilterRegion(e.target.value)}
            >
              <optgroup label="Broad Geographies">
                <option value="India">🇮🇳 India (Primary Focus)</option>
                <option value="Global">🌍 Global (Outside India)</option>
                <option value="All">🌐 All Detections Worldwide</option>
              </optgroup>
              <optgroup label="Indian States">
                <option value="Gujarat">Gujarat Hub</option>
                <option value="Maharashtra">Maharashtra Hub</option>
                <option value="Odisha">Odisha Hub</option>
                <option value="West Bengal">West Bengal Hub</option>
                <option value="Tamil Nadu">Tamil Nadu Hub</option>
                <option value="Jharkhand">Jharkhand Hub</option>
                <option value="Assam">Assam Hub</option>
              </optgroup>
            </select>

            <select
              className="filter-select"
              style={{ width: '150px' }}
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <span className="loading-text">Loading alerts...</span>
          </div>
        ) : alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            No alerts match the current filter.
          </div>
        ) : (
          <table className="alerts-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Event ID</th>
                <th>Classification</th>
                <th>Location</th>
                <th>Risk</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map(alert => (
                <tr
                  key={alert.alert_id}
                  onClick={() => onNavigate?.('investigation', { eventId: alert.event_id })}
                >
                  <td>
                    <span className={`alert-dot alert-dot--${alert.severity}`} style={{ display: 'inline-block', marginRight: '8px' }} />
                    {alert.severity}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{alert.event_id}</td>
                  <td>{alert.title}</td>
                  <td>{alert.location}</td>
                  <td><RiskBadge value={alert.operational_risk} type="risk" /></td>
                  <td><RiskBadge value={alert.confidence} type="confidence" /></td>
                  <td><span className={`status-badge status-badge--${alert.status}`}>{alert.status.replace(/_/g, ' ')}</span></td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {alert.timestamp ? alert.timestamp.split('T')[0] : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
